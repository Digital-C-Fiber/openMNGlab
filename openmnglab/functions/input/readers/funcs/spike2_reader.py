import re
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Optional, Mapping, Sequence, Any

import numpy as np
import pandas as pd
import pymatreader as pymat

import quantities as pq

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.datamodel.pandas.schemes import TIMESTAMP
from openmnglab.functions.base import SourceFunctionBase
from openmnglab.functions.input.readers.funcs.dapsys_reader import _kernel_offset_assign
from openmnglab.util.dicts import get_any


@dataclass
class Spike2Channel:
    ident: int | str
    unit: pq.Quantity = pq.dimensionless
    idx_unit: pq.Quantity = pq.s
    name: Optional[str] = None
    read_codes: bool = False
    code_map: Optional[Mapping[int,str]] = None
    codes_label: Optional[str] = None


class Spike2ReaderFunc(SourceFunctionBase):
    _channel_regex = re.compile(r"_Ch(\d*)")

    def __init__(self, path: str | Path, cont_signals: Optional[Sequence[Spike2Channel]] = None,
                 markers: Optional[Sequence[Spike2Channel]] = None,
                 text: Optional[Sequence[Spike2Channel]] = None,
                 matstruct_prefix=""):
        self._cont_signals = cont_signals if cont_signals is not None else tuple()
        self._markers = markers if markers is not None else tuple()
        self._text_structs = text if text is not None else tuple()
        self._path = path
        self._matstruct_prefix = matstruct_prefix

    @classmethod
    def _get_chan_identifier(cls, matlab_struct_name: str) -> str | int:
        res = cls._channel_regex.search(matlab_struct_name)
        return int(res.group(1)) if res is not None else matlab_struct_name

    def _read_spike2mat_structs(self) -> dict[str | int, dict[str, Any]]:
        matfile = pymat.read_mat(self._path)
        structs = dict()
        chan_idents: dict[str|int, Spike2Channel] = {v.ident: v for v in chain(self._cont_signals, self._text_structs, self._markers)}
        for matname, struct in matfile.items():
            struct_key = self._get_chan_identifier(matname)
            if matname.startswith(self._matstruct_prefix) and 'title' in struct:
                candidate: Optional[Spike2Channel] = get_any(chan_idents, str(struct['title']), struct_key)
                if candidate is not None:
                    struct['title'] = candidate.name if candidate.name is not None else struct['title']
                    structs[candidate.ident] = struct
        return structs

    @staticmethod
    def _load_sig_chan(matlab_struct: Mapping[str, Any]) -> pd.Series:
        if 'times' not in matlab_struct:
            times = np.empty(len(matlab_struct['values']))
            _kernel_offset_assign(times, matlab_struct['start'], matlab_struct['interval'], 0, len(times))
        else:
            times = matlab_struct['times']
        return pd.Series(data=matlab_struct['values'], index=pd.Index(times, name=TIMESTAMP, copy=False),
                         name=matlab_struct['title'], copy=False)

    @staticmethod
    def _load_marker_chan(matlab_struct: Mapping[str, Any]) -> pd.Series:
        times = matlab_struct['times']
        return pd.Series(data=times, copy=False, name=matlab_struct['title'])

    @staticmethod
    def _load_wavemark_chan(matlab_struct: Mapping[str, Any]) -> pd.Series:
        end_offset = matlab_struct['interval'] * matlab_struct['items']
        intervals = [pd.Interval(start, start + end_offset) for start in matlab_struct['times']]
        return pd.Series(data=intervals, copy=False, name=matlab_struct['title'])

    @staticmethod
    def _load_text_chan(matlab_struct: Mapping[str, Any]) -> pd.Series:
        times = matlab_struct['times']
        cleaned_texts = [t.rstrip("\x00") for t in matlab_struct['text']]
        return pd.Series(data=cleaned_texts, index=pd.Index(times, name=TIMESTAMP, copy=False), copy=False,
                         name=matlab_struct['title'])

    def execute(self) -> list[PandasContainer, ...]:
        mat_structs = self._read_spike2mat_structs()
        ret_list = list()
        for sig_channel in self._cont_signals:
            series = self._load_sig_chan(mat_structs[sig_channel.ident])
            ret_list.append(PandasContainer(series, {series.name: sig_channel.unit, series.index.name: sig_channel.idx_unit}))
        for marker_channel in self._markers:
            marker = self._load_marker_chan(mat_structs[marker_channel.ident])
            ret_list.append(PandasContainer(marker, {marker.name: marker_channel.unit}))
        for txt_channel in self._text_structs:
            text = self._load_text_chan(mat_structs[txt_channel.ident])
            ret_list.append(PandasContainer(text, {text.name: txt_channel.unit, text.index.name: txt_channel.idx_unit}))
        return ret_list
