from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping, Any, Iterable, Match

import numpy as np
import pandas as pd
import pymatreader as pymat
import quantities as pq
from pandas import Index

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.datamodel.pandas.schemes import TIMESTAMP, SIGNAL, MASS, TEMPERATURE, COMMENT
from openmnglab.functions.base import SourceFunctionBase
from openmnglab.functions.input.readers.funcs.dapsys_reader import _kernel_offset_assign

SPIKE2_CHANID = int | str

SPIKE2_LEVEL = "level"
SPIKE2_V_CHAN = "V chan"
SPIKE2_DIGMARK = "digmark"
SPIKE2_KEYBOARD = "keyboard"


class Spike2ReaderFunc(SourceFunctionBase):
    class Spike2Channels:
        _channelno_regex = r"_Ch(\d*)"

        def __init__(self, structs: dict):
            self._structs = structs
            self._id_map: dict[str | int, str] | None = None
            self._supports_chan_no: bool | None = None

        @classmethod
        def _make_idmap(cls, structs: dict) -> dict[str | int, str]:
            def unpack_match(result: Match[str] | None) -> int | None:
                return int(result.group(1)) if result is not None else None

            channel_no_regex = re.compile(cls._channelno_regex)
            idmap: dict[str | int, str] = dict()
            for struct_name, fields in structs.items():
                chan_no = unpack_match(channel_no_regex.search(struct_name))
                if chan_no is not None:
                    idmap[chan_no] = struct_name
                chan_name = fields.get("title", None)
                if chan_name:
                    idmap[chan_name] = struct_name
            return idmap

        @property
        def structs(self) -> dict:
            return self._structs

        @property
        def id_map(self) -> dict[str | int, str]:
            if self._id_map is None:
                self._id_map = self._make_idmap(self.structs)
            return self._id_map

        @property
        def supports_chan_no(self) -> bool:
            if self._supports_chan_no is None:
                pattern = re.compile(self._channelno_regex)
                self._supports_chan_no = any(pattern.search(struct_name) is not None for struct_name in self.structs)
            return self._supports_chan_no

        def get_chan(self, chan_id: SPIKE2_CHANID, default: dict | None = None) -> dict | None:
            if isinstance(chan_id, int) and not self.supports_chan_no:
                raise KeyError(
                    "A channel number was provided as a channel id. However, channel numbers are not contained in the exported Matlab file and are thus unavailable.")
            struct_name = self.id_map.get(chan_id)
            if struct_name is None:
                return default
            return self.structs[struct_name]

        def __getitem__(self, item: SPIKE2_CHANID) -> dict:
            value = self.get_chan(item)
            if value is None:
                raise KeyError(f"No channel with the id {item} found")
            return value

    _channel_regex = re.compile(r"_Ch(\d*)")

    def __init__(self, path: str | Path,
                 signal: SPIKE2_CHANID | None = "Signal",
                 temp: SPIKE2_CHANID | None = "Temp",
                 mass: SPIKE2_CHANID | None = "Force",
                 v_chan: SPIKE2_CHANID | None = "V",
                 ext_pul: SPIKE2_CHANID | None = 10,
                 comments: SPIKE2_CHANID | None = 30,
                 keyboard: SPIKE2_CHANID | None = 31,
                 digmark: SPIKE2_CHANID | None = 32,
                 wavemarks: SPIKE2_CHANID | None | Iterable[int | str] = "nw-1",
                 mass_unit: pq.Quantity = pq.g,
                 signal_unit: pq.Quantity = pq.microvolt,
                 temp_unit: pq.Quantity = pq.celsius,
                 v_chan_unit: pq.Quantity = pq.dimensionless,
                 time_unit: pq.Quantity = pq.second):
        self._signal_chan = signal
        self._temp_chan = temp
        self._mass = mass
        self._v_chan = v_chan
        self._ext_pul = ext_pul
        self._comments = comments
        self._keyboard = keyboard
        self._digmark = digmark
        self._wavemarks = wavemarks
        self._mass_unit = mass_unit
        self._signal_unit = signal_unit
        self._temp_unit = temp_unit
        self._v_chan_unit = v_chan_unit
        self._time_unit = time_unit
        self._path = path
        self._channels: Spike2ReaderFunc.Spike2Channels | None = None

    @classmethod
    def _get_chan_identifier(cls, matlab_struct_name: str) -> str | int:
        res = cls._channel_regex.search(matlab_struct_name)
        return int(res.group(1)) if res is not None else matlab_struct_name

    @property
    def channels(self) -> Spike2Channels:
        if self._channels is None:
            self._channels = Spike2ReaderFunc.Spike2Channels(pymat.read_mat(self._path))
        return self._channels

    @staticmethod
    def codes_to_int(codes: np.ndarray) -> np.ndarray:
        return codes.view(np.int8).flatten().view(np.uint32)

    @staticmethod
    def _get_channel_name(channel_struct: dict | None, name_override: str | None = None) -> str:
        if name_override is not None:
            return name_override
        if channel_struct is None:
            channel_struct = dict()
        return channel_struct.get("title", "unknown channel")

    @staticmethod
    def _waveform_chan_to_series(matlab_struct: Mapping[str, Any] | None,
                                 name: str, index_name: str = TIMESTAMP) -> pd.Series:
        values, times = tuple(), tuple()
        if matlab_struct is not None and matlab_struct.get('length', 0) > 0:
            values = matlab_struct['values']
            if 'times' not in matlab_struct:
                times = np.empty(len(matlab_struct['values']))
                _kernel_offset_assign(times, matlab_struct['start'], matlab_struct['interval'], 0, len(times))
            else:
                times = matlab_struct['times']

        series = pd.Series(data=values, index=pd.Index(times, name=index_name, copy=False),
                           name=name, copy=False)
        return series

    @classmethod
    def _marker_chan_to_series(cls, matlab_struct: Mapping[str, Any] | None, name: str,
                               index_name: str = TIMESTAMP) -> pd.Series:
        times, codes = tuple(), tuple()
        if matlab_struct is not None and matlab_struct.get('length', 0) > 0:
            times = (matlab_struct['times'],) if isinstance(matlab_struct['times'], float) else matlab_struct['times']
            codes = cls.codes_to_int(matlab_struct['codes'])
        series = pd.Series(data=codes, dtype="category", name=name,
                           index=Index(data=times, copy=False, name=index_name))
        return series

    @staticmethod
    def _textmarker_chan_to_series(matlab_struct: Mapping[str, Any] | None, name: str,
                                   index_name: str = TIMESTAMP) -> pd.Series:
        texts, times, codes = tuple(), tuple(), tuple()
        if matlab_struct is not None and matlab_struct.get('length', 0) > 0:
            times = matlab_struct['times']
            texts = [t.rstrip("\x00") for t in matlab_struct['text']]
        series = pd.Series(data=texts, index=pd.Index(times, name=index_name, copy=False), copy=False,
                           name=name)
        return series

    @staticmethod
    def _unbinned_event_chant_to_series(matlab_struct: Mapping[str, Any] | None, name: str,
                                        index_name: str = TIMESTAMP):
        times, levels = tuple(), tuple()
        if matlab_struct is not None and matlab_struct.get('length', 0) > 0:
            times = matlab_struct['times']
            levels = matlab_struct['level'].astype(np.int8)
        series = pd.Series(data=levels, index=pd.Index(times, name=index_name, copy=False), copy=False, name=name)
        return series

    @classmethod
    def _load_sig_chan(cls, chan_struct: dict | None, quantity: pq.Quantity, time_quantity: pq.Quantity = pq.second,
                       name: str | None = None):
        series = cls._waveform_chan_to_series(chan_struct, cls._get_channel_name(chan_struct, name_override=name))
        return PandasContainer(series, {series.name: quantity, series.index.name: time_quantity})

    @classmethod
    def _load_unbinned_event(cls, chan_struct: dict | None, quantity: pq.Quantity = pq.dimensionless,
                             time_quantity: pq.Quantity = pq.second):
        series = cls._unbinned_event_chant_to_series(chan_struct, SPIKE2_LEVEL)
        return PandasContainer(series, {series.name: quantity, series.index.name: time_quantity})

    @classmethod
    def _load_texts(cls, chan_struct: dict | None, time_quantity: pq.Quantity = pq.second, name: str | None = None):
        series = cls._textmarker_chan_to_series(chan_struct, cls._get_channel_name(chan_struct, name_override=name))
        return PandasContainer(series, {series.name: pq.dimensionless, series.index.name: time_quantity})

    @classmethod
    def _load_marker(cls, chan_struct: dict | None, time_quantity: pq.Quantity = pq.second, name: str | None = None):
        series = cls._marker_chan_to_series(chan_struct, name = cls._get_channel_name(chan_struct, name_override=name))
        return PandasContainer(series, {series.name: pq.dimensionless, series.index.name: time_quantity})

    def execute(self) -> tuple[PandasContainer, ...]:
        mass = self._load_sig_chan(self.channels.get_chan(self._mass), self._mass_unit, name=MASS)
        sig = self._load_sig_chan(self.channels.get_chan(self._signal_chan), self._signal_unit, name=SIGNAL)
        temp = self._load_sig_chan(self.channels.get_chan(self._temp_chan), self._temp_unit, name=TEMPERATURE)
        v_chan = self._load_sig_chan(self.channels.get_chan(self._v_chan), self._v_chan_unit, name=SPIKE2_V_CHAN)
        ext_pull = self._load_unbinned_event(self.channels.get_chan(self._ext_pul))
        comments = self._load_texts(self.channels.get_chan(self._comments), name=COMMENT)
        dig_mark = self._load_marker(self.channels.get_chan(self._digmark), name=SPIKE2_DIGMARK)
        keyboard = self._load_marker(self.channels.get_chan(self._keyboard), name=SPIKE2_KEYBOARD)
        return sig, mass, temp, v_chan, ext_pull, comments, dig_mark, keyboard
