from __future__ import annotations

from typing import Optional

import numpy as np
import quantities as pq
from pandas import Series, DataFrame, MultiIndex

from openmnglab.datamodel.interface import IDataContainer
from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.functions.base import FunctionBase
from openmnglab.functions.helpers.general import get_interval_locs, slice_diffs_flat_np, slice_derivs_flat_np


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
                 derivative_change: Optional[pq.Quantity]):
        self._levels = levels
        self._window_intervals: PandasContainer[Series] = None
        self._recording: PandasContainer[Series] = None
        self._derivative_mode = derivatives
        self._derivative_time_base = derivative_change

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

    def execute(self) -> tuple[PandasContainer[DataFrame]]:
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

        multiindex_codes = extend_multiindex(intervals.index.codes, interval_ranges)

        new_multiindex = MultiIndex(levels=(*intervals.index.levels, recording.index),
                                    names=[*intervals.index.names,
                                           recording.index.name], codes=multiindex_codes)
        return PandasContainer(DataFrame(data=diffs.T,
                                         columns=[LEVEL_COLUMN[i] for i in self._levels], index=new_multiindex),
                               units=self.build_unitdict()),

    def set_input(self, window_intervals: IDataContainer, data: IDataContainer):
        self._window_intervals = window_intervals
        self._recording = data


class LevelColumnGenerator:
    def __getitem__(self, item: int) -> str:
        if item == 0:
            return "original"
        return f"level {item} diff"


LEVEL_COLUMN = LevelColumnGenerator()
