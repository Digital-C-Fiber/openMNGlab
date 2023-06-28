import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Mapping, Sequence, OrderedDict

import numpy as np
import pandas as pd
import pymatreader as pymat
import quantities as pq

from openmnglab.datamodel.interface import IDataContainer
from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.datamodel.pandas.schemes import TIMESTAMP
from openmnglab.functions.base import SourceFunctionBase
from openmnglab.functions.input.readers.dapsys_reader import _kernel_offset_assign
from openmnglab.util.dicts import get_any

@dataclass
class Spike2Channel:
    channel_unit: pq.Quantity = pq.dimensionless
    time_unit: pq.Quantity = pq.s
    chan_num: Optional[int] = None
    struct_name: Optional[str] = None
    chan_name: Optional[str] = None
    rename_to: Optional[str] = None
    code_mapping: Optional[Mapping[int,str]] = None
    code_column_name: Optional[str] = None

    @property
    def read_codes(self) -> bool:
        return self.code_column_name is not None
    

class Spike2ReaderFunc(SourceFunctionBase):
    _channel_regex = re.compile(r"_Ch(\d*)")

    def __init__(self, path: str | Path, cont_signals: Optional[OrderedDict[str | int, pq.Quantity]] = None,
                 markers: Optional[Sequence[str | int]] = None,
                 text: Optional[Sequence[str | int]] = None,
                 renames: Optional[Mapping[str | int, str]] = None, matstruct_prefix=""):
        self._cont_signals = cont_signals if cont_signals is not None else dict()
        self._markers = markers
        self._renames = renames if renames is not None else dict()
        self._path = path
        self._matstruct_prefix = matstruct_prefix
        self._text_structs = text

    @classmethod
    def _get_chan_identifier(cls, matlab_struct_name: str) -> str | int:
        res = cls._channel_regex.search(matlab_struct_name)
        return int(res.group(1)) if res is not None else matlab_struct_name

    def _read_spike2mat_structs(self) -> dict[str | int, dict[str, Any]]:
        matfile = pymat.read_mat(self._path)
        structs = dict()
        chan_idents = set(self._cont_signals.keys())
        chan_idents.update(self._text_structs)
        chan_idents.update(self._markers)
        for matname, struct in matfile.items():
            struct_key = self._get_chan_identifier(matname)
            if matname.startswith(self._matstruct_prefix) and 'title' in struct and (
                    struct_key in chan_idents or str(struct['title']) in chan_idents):
                struct['title'] = get_any(self._renames, str(struct['title']), struct_key, default=str(struct['title']))
            structs[struct_key] = struct
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
        for struct_key, cont_sig_unit in self._cont_signals.items():
            series = self._load_sig_chan(mat_structs[struct_key])
            ret_list.append(PandasContainer(series, {series.name: cont_sig_unit, series.index.name: pq.s}))
        for struct_key in self._markers:
            marker = self._load_marker_chan(mat_structs[struct_key])
            ret_list.append(PandasContainer(marker, {marker.name: pq.s}))
        for struct_key in self._text_structs:
            text = self._load_text_chan(mat_structs[struct_key])
            ret_list.append(PandasContainer(text, {text.name: pq.dimensionless, text.index.name: pq.s}))
        return ret_list
