import math
import sys
from typing import Any

import h5py
import numpy as np
import numpy.typing as npt

from openmnglab.functions.input.readers.funcs.spike2.hdfmat import HDFMatGroup


def comp_float(v1, v2, delta=sys.float_info.epsilon):
    return abs(v1 - v2) <= delta


class _Spike2Base:

    def __init__(self, hdfgroup: HDFMatGroup):
        self._hdfgroup = hdfgroup

    @property
    def hdfgroup(self) -> HDFMatGroup:
        return self._hdfgroup


class _TimeRangeSliceMixin:

    def timerange_slice(self, start: float, stop: float) -> slice:
        if isinstance(self, _TimesMixin):
            times_ds = self.hdfgroup.h5group.get(self._TIMES_ITEM_NAME, default=None)
            if times_ds and times_ds.attrs.get("MATLAB_empty", 0) == 0:
                return self.timerange_slice_from_times(start, stop)
        elif isinstance(self, _CalculatedIndexMixin):
            return self.timerange_slice_from_calc_idx(start, stop)
        raise Exception("This object does not support calculating timeranges!")


class _StartMixin(_Spike2Base):
    _start = None

    @property
    def start(self) -> float:
        if self._start is None:
            val = self.hdfgroup['start']
            self._start = val.flatten()[0]
        return self._start


class _LengthMixin(_Spike2Base):
    _length = None

    @property
    def length(self) -> int:
        if self._length is None:
            val = self.hdfgroup['length'].astype(np.uint64)
            self._length = val.item()
        return self._length


class _TimesMixin(_TimeRangeSliceMixin, _Spike2Base):
    _times = None
    _TIMES_ITEM_NAME = 'times'

    @property
    def times(self) -> npt.NDArray[float]:
        if self._times is None:
            self._times = self.get_times_slice(slice(None, None, None))
        return self._times

    def get_times_slice(self, slicer: slice) -> npt.NDArray[float]:
        vals = self.hdfgroup.get_array(self._TIMES_ITEM_NAME, slicer=slicer)
        return vals

    def _binary_search_times(self, val: float, tolerance: float = sys.float_info.epsilon) -> tuple[None, None] | tuple[
        int|None, int|None]:
        h5ds: h5py.Dataset = self.hdfgroup.h5group[self._TIMES_ITEM_NAME]
        low, high = 0, h5ds.shape[1] - 1
        if low == high:
            single_val = h5ds[0,0]
            if comp_float(val, single_val, delta=tolerance):
                return low, low
            else:
                return None,None
        mid = (high - low) // 2
        low_val, mid_val, high_val = h5ds[0, [low, mid, high]]
        if comp_float(val, low_val, delta=tolerance):
            return low, low
        elif comp_float(val, high_val, delta=tolerance):
            return high, high
        elif val < low_val:
            return None,0
        elif high_val < val:
            return h5ds.shape[1], None
        while high - low > 1:
            if comp_float(val, mid_val, delta=tolerance):
                return mid, mid
            if val < mid_val:
                high, high_val = mid, mid_val
            else:
                low, low_val = mid, mid_val
            mid = low + (high - low) // 2
            mid_val = h5ds[0, mid]
        return low, high

    def timerange_slice_from_times(self, start: float, stop: float) -> slice:
        start_low, start_idx = self._binary_search_times(start)
        stop_idx, stop_high = self._binary_search_times(stop)
        if not start_low and not stop_high:
            return slice(0)
        return slice(start_idx, stop_idx + 1 if stop_idx else None)


class _TitleMixin(_Spike2Base):
    _title = None

    @property
    def title(self) -> str:
        if self._title is None:
            title_tuple = self.hdfgroup['title']
            self._title = title_tuple[0] if len(title_tuple) > 0 else ""
        return self._title


class _CommentMixin(_Spike2Base):
    _comment = None

    @property
    def comment(self) -> str:
        if self._comment is None:
            comment_tuple = self.hdfgroup['comment']
            self._comment = comment_tuple[0] if len(comment_tuple) > 0 else ""
        return self._comment


class _LevelsMixin(_Spike2Base):
    _levels = None

    @property
    def levels(self) -> npt.NDArray[np.int8]:
        if self._levels is None:
            self._levels = self.get_levels_slice(slice(None, None, None))
        return self._levels

    def get_levels_slice(self, slicer: slice) -> npt.NDArray[np.int8]:
        vals = self.hdfgroup.get_array('level', slicer=slicer)
        return vals.astype(np.int8)


class _TextsMixin(_Spike2Base):
    _texts = None

    @property
    def texts(self) -> tuple[str, ...]:
        if self._texts is None:
            self._texts = self.get_texts_slice(slice(None, None, None))
        return self._texts

    def get_texts_slice(self, slicer: slice) -> tuple[str, ...]:
        vals = self.hdfgroup.get("text", slicer)
        return vals


class _IntervalMixin(_Spike2Base):
    _interval = None

    @property
    def interval(self) -> float:
        if self._interval is None:
            val = self.hdfgroup['interval']
            self._interval = val.flatten()[0]
        return self._interval


class _CodesMixin(_Spike2Base):
    _codes = None

    @property
    def codes(self) -> npt.NDArray:
        if self._codes is None:
            self._codes = self.get_codes_slice(slice(None, None, None))
        return self._codes

    def get_codes_slice(self, slicer: slice) -> npt.NDArray:
        vals = self.hdfgroup.get('codes', slicer)
        return vals

    def get_int_codes_slice(self, slicer: slice) -> npt.NDArray[np.uint32]:
        return self.get_codes_slice(slicer).astype(np.int8).flatten().view(np.uint32)

    @property
    def int_codes(self) -> npt.NDArray[np.uint32]:
        return self.get_int_codes_slice(slice(None, None, None))


class _ValuesMixin(_Spike2Base):
    _values = None

    @property
    def values(self) -> npt.NDArray:
        if self._values is None:
            self._values = self.get_values_slice(slice(None, None, None))
        return self._values

    def get_values_slice(self, slicer: slice) -> npt.NDArray:
        vals = self.hdfgroup.get_array("values", slicer=slicer)
        return vals


class _CalculatedIndexMixin(_TimeRangeSliceMixin, _LengthMixin, _StartMixin, _IntervalMixin):

    def _calc_closest_idx(self, val: float) -> tuple[int, int] | tuple[None|int, None|int]:
        if self.length == 0:
            return None, None
        end = self.start + self.interval * (self.length - 1)
        if comp_float(val, self.start):
            return 0, 0
        elif comp_float(val, end):
            return self.length - 1, self.length - 1
        elif val < self.start:
            return None, 0
        elif end < val:
            return self.length, None

        float_pos = (val - self.start) / self.interval
        floor_pos = math.floor(float_pos)
        if comp_float(val, self.start + self.interval * floor_pos):
            return floor_pos, floor_pos
        ceil_pos = math.ceil(float_pos)
        if comp_float(val, self.start + self.interval * ceil_pos):
            return ceil_pos, ceil_pos
        return floor_pos, ceil_pos

    def timerange_slice_from_calc_idx(self, start: float, end: float):
        _, start_idx = self._calc_closest_idx(start)
        stop_idx, _ = self._calc_closest_idx(end)
        return slice(start_idx, stop_idx + 1)


class Spike2UnbinnedEvent(_LengthMixin, _TitleMixin, _LevelsMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2BinnedEvent(_ValuesMixin, _TitleMixin, _TimesMixin, _CalculatedIndexMixin, _Spike2Base):
    ...


class Spike2TimeView(_StartMixin, _Spike2Base):
    ...


class Spike2Marker(_LengthMixin, _TitleMixin, _CodesMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Realmark(_LengthMixin, _ValuesMixin, _TitleMixin, _CodesMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Result(_CalculatedIndexMixin, _ValuesMixin, _TitleMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Textmark(_LengthMixin, _TitleMixin, _CodesMixin, _TimesMixin, _TextsMixin, _Spike2Base):
    ...


class Spike2Realwave(_CalculatedIndexMixin, _ValuesMixin, _TitleMixin, _Spike2Base):
    ...


class Spike2Waveform(_CalculatedIndexMixin, _ValuesMixin, _TitleMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Waveform(_CalculatedIndexMixin, _ValuesMixin, _TitleMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Wavemark(_LengthMixin, _ValuesMixin, _TitleMixin, _TimesMixin, _CodesMixin, _IntervalMixin, _Spike2Base):
    ...


class Spike2XYData(_LengthMixin, _TitleMixin, _Spike2Base):
    ...


_id_order: list[dict[Any, tuple[set[str], set[str]]]] = [
    {Spike2UnbinnedEvent: ({'level'}, set()), Spike2TimeView: ({'name'}, {'length', 'title'}),
     Spike2Textmark: ({'text'}, set()), Spike2Wavemark: ({'traces', 'trigger'}, set()),
     Spike2XYData: ({'xvalues', 'yvalues'}, set()), },
    {Spike2Realwave: (set(), {'times'}), Spike2Result: ({'xunits'}, {'comment'}),
     Spike2Marker: ({'resolution'}, {'values'}), Spike2Realmark: ({'items'}, set()), },
    {Spike2Waveform: ({'offset', 'scale', 'units'}, set()), }, {Spike2BinnedEvent: (
        {'times', 'title', 'comment', 'interval', 'values', 'length', 'start'},
        {'offset', 'level', 'text', 'yvalues', 'xunits', 'scale', 'items', 'name', 'trigger', 'xvalues', 'traces',
         'resolution', 'codes', 'units'}), }, {}, ]


def spike2_struct(group: HDFMatGroup) -> Any:
    for round in _id_order:
        for cls, (included_fields, excluded_files) in round.items():
            key_set = set(group.keys())
            if included_fields.issubset(key_set) and excluded_files.isdisjoint(key_set):
                return cls(group)
    raise Exception("Could not identify struct")
