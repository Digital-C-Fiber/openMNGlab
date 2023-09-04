from __future__ import annotations

from typing import Optional

import numpy as np
import quantities as pq
from pandas import Series, DataFrame, MultiIndex

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.functions.base import FunctionBase
from openmnglab.functions.helpers.general import get_interval_locs, slice_diffs_flat_np, slice_derivs_flat_np
from openmnglab.model.datamodel.interface import IDataContainer


def offset_timestamps(cont_sig_ts, intervals):
    total_len = 0
    n = len(intervals[0])
    for i in range(n):
        total_len += intervals[1, i] - intervals[0, i]
    new_ts = np.empty(total_len, dtype=np.float64)
    c_pos = 0
    for i in range(n):
        start_i, stop_i = intervals[0, i], intervals[1, i]
        slice = cont_sig_ts[start_i:stop_i]
        new_ts[c_pos:c_pos + len(slice)] = slice - slice[0]
        c_pos += len(slice)
    return new_ts


def extend_values(base, extend_by, total):
    assert (len(base) == len(extend_by))
    extended_values = np.empty_like(base, shape=total)
    current_pos = 0
    for i, repeat in enumerate(extend_by):
        extended_values[current_pos:current_pos + repeat] = base[i]
    return extended_values


def extend_numpy_by_repeat(original: np.ndarray, repeat_each_element: np.ndarray, new_length: int):
    extended_array = np.empty(new_length, dtype=original.dtype)
    extended_i = 0
    for original_i in range(len(original)):
        extended_array[extended_i:extended_i + repeat_each_element[original_i]] = original[original_i]
        extended_i += repeat_each_element[original_i]
    return extended_array


def extend_multiindex_f(base: list[np.ndarray], ranges: np.ndarray, extension):
    repeats = ranges[1] - ranges[0]
    n = np.sum(repeats)
    multiidx = [extend_numpy_by_repeat(orig_arr, repeats, n) for orig_arr in base]
    multiidx.append(extension)
    return multiidx


def extend_multiindex(base: list[np.ndarray], ranges: np.ndarray):
    repeats = ranges[1] - ranges[0]
    n = np.sum(repeats)
    multiidx = [extend_numpy_by_repeat(orig_arr, repeats, n) for orig_arr in base]
    new_codes = np.empty(n, dtype=np.int64)
    i = 0
    for range_i in range(len(ranges[0])):
        for v in range(ranges[0, range_i], ranges[1, range_i]):
            new_codes[i] = v
            i += 1
    multiidx.append(new_codes)
    return multiidx


class IntervalDataFunc(FunctionBase):
    def __init__(self, levels: tuple[int, ...],
                 derivatives: bool,
                 derivative_change: Optional[pq.Quantity], interval: Optional[float] = None, use_time_offsets=True):
        self._levels = levels
        self._window_intervals: PandasContainer[Series] = None
        self._recording: PandasContainer[Series] = None
        self._derivative_mode = derivatives
        self._derivative_time_base = derivative_change
        self._use_time_offsets = use_time_offsets
        self._interval = interval

    def build_unitdict(self):
        intervals = self._window_intervals.data
        units: dict[str, pq.Quantity] = dict()
        for interval_index_name in intervals.index.names:
            units[interval_index_name] = self._window_intervals.units[interval_index_name]
        col_unit = self._recording.units[self._recording.data.name]
        units[self._recording.data.index.name] = self._recording.units[self._recording.data.index.name]
        v_unit = self._recording.units[self._recording.data.name]
        t_unit = self._recording.units[
            self._recording.data.index.name] if self._derivative_time_base is None else self._derivative_time_base
        for i in self._levels:
            name = LEVEL_COLUMN[i]
            u = v_unit
            if self._derivative_mode:
                for _ in range(i):
                    u = u / t_unit
            units[name] = u
        return units

    def execute(self) -> PandasContainer[DataFrame]:
        intervals = self._window_intervals.data
        recording = self._recording.data
        interval_ranges = np.fromiter(
            (val for interval in intervals.values for val in get_interval_locs(interval, recording.index)), dtype=int) \
            .reshape((2, -1), order='F')
        units = self.build_unitdict()
        if not self._derivative_mode:
            diffs = slice_diffs_flat_np(recording.values, interval_ranges, diff_levels=max(self._levels))[
                self._levels,]
        else:
            diffs = slice_derivs_flat_np(recording.values.astype(np.float64), recording.index.values, interval_ranges,
                                         diff_levels=max(self._levels))[
                self._levels,]
            if self._derivative_time_base is not None:
                current_unit = units[LEVEL_COLUMN[0]] / units[recording.index.name]
                desired_unit = units[LEVEL_COLUMN[0]] / self._derivative_time_base
                scaler = current_unit.rescale(desired_unit).magnitude
                diffs[1:] *= scaler

        if self._use_time_offsets:
            interval_lens = interval_ranges[1] - interval_ranges[0]
            if len(interval_lens) > 0:
                code_cut = np.arange(interval_lens.max())

                interval = self._interval if self._interval is not None else recording.index.values[1] - \
                                                                             recording.index.values[0]
                index_values = code_cut * interval
                codes = np.concatenate([code_cut[:l] for l in interval_lens])
                multiindex_codes = extend_multiindex_f(intervals.index.codes, interval_ranges, codes)
                levels = (*intervals.index.levels, index_values)
            else:
                multiindex_codes = [[] for _ in range(len(intervals.index.names)+1)]
                levels = [tuple() for _ in range(len(intervals.index.names)+1)]

            new_multiindex = MultiIndex(levels=levels,
                                        names=[*intervals.index.names,
                                               recording.index.name], codes=multiindex_codes)
        else:
            # calculate the codes of the multiindex in relation to the actual timestamp array. This way, we can just re-use the timestamps from the recording,
            # without copying them.
            multiindex_codes = extend_multiindex(intervals.index.codes, interval_ranges)

            new_multiindex = MultiIndex(levels=(*intervals.index.levels, recording.index),
                                        names=[*intervals.index.names,
                                               recording.index.name], codes=multiindex_codes)
        return PandasContainer(DataFrame(data=diffs.T,
                                         columns=[LEVEL_COLUMN[i] for i in self._levels], index=new_multiindex),
                               units=self.build_unitdict())

    def set_input(self, window_intervals: IDataContainer, data: IDataContainer):
        self._window_intervals = window_intervals
        self._recording = data


class LevelColumnGenerator:
    def __getitem__(self, item: int) -> str:
        if item == 0:
            return "original"
        return f"level {item} diff"


LEVEL_COLUMN = LevelColumnGenerator()
