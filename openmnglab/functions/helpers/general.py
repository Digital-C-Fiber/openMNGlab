from typing import Optional

import numpy as np
import pandas as pd
import quantities as pq
from numba import njit

from openmnglab.datamodel.pandas.model import PandasContainer


def get_index_quantities(container: PandasContainer) -> dict[str, pq.Quantity]:
    return {idx_name: container.units[idx_name] for idx_name in container.data.index.names}


def get_interval_locs(interval: pd.Interval, index: pd.Index):
    """
    returns the locs of an interval in an index
    :param interval:
    :param index:
    :return:
    """
    left_loc, right_loc = index.slice_locs(start=interval.left, end=interval.right)
    # temporarly reduce right_loc by one, as slice_locs will always return the position of the next greater value beyond end (or an out of bounds position)
    right_loc -= 1
    # STATE: index[left_loc] >= interval.left ; index[right_loc] >= interval.right
    # we can avoid the float comparison with the system epsilon by just checking if it is greater; has same effect as the epsilon is the smallest differentiateable value anyway.
    if interval.open_left and not index[left_loc] > interval.left:
        left_loc += 1
        # STATE: index[left_loc] > interval.left
    if interval.open_right and not index[right_loc] < interval.right:
        right_loc -= 1
        # STATE: index[right_loc] < interval.right
    return left_loc, right_loc + 1


def _slice_diff(series: np.ndarray, diffs: np.ndarray, start_i: int, stop_i: int, diff_levels: int, dtype):
    if start_i - diff_levels >= 0:
        overhang = series[start_i - diff_levels:start_i].copy()
    else:
        overhang = np.zeros(diff_levels, dtype=dtype)
        overhang[diff_levels - start_i:] = series[:start_i]
    diffs[0] = series[start_i:stop_i]

    for level_i in range(1, diff_levels + 1):
        last_level = diffs[level_i - 1]
        curr_level = diffs[level_i]
        curr_level[0] = last_level[0] - overhang[-1]
        for diff_i in range(1, len(curr_level)):
            curr_level[diff_i] = last_level[diff_i] - last_level[diff_i - 1]
        for overhang_i in range(len(overhang) - 1, 0, -1):
            overhang[overhang_i] -= overhang[overhang_i - 1]
    return diffs


_slice_diff_njit = njit()(_slice_diff)


def _slice_deriv(values: np.ndarray, times: np.ndarray, derivatives: np.ndarray, start_i: int, stop_i: int,
                 diff_levels: int, dtype):
    if start_i > 0:
        time_diffs = np.diff(times[start_i - 1:stop_i])[1:]
    else:
        time_diffs = np.diff(times[start_i:stop_i])
    if start_i - diff_levels >= 0:
        overhang = values[start_i - diff_levels:start_i].copy()
    else:
        overhang = np.zeros(diff_levels, dtype=dtype)
        overhang[diff_levels - start_i:] = values[:start_i]

    if start_i - diff_levels > 0:
        overhang_times = np.diff(times[start_i - diff_levels - 1:start_i])
    else:
        overhang_times = np.zeros(diff_levels, dtype=dtype)
        overhang_times[diff_levels - start_i:] = np.diff(times[:start_i])

    derivatives[0] = values[start_i:stop_i]

    for level_i in range(1, diff_levels + 1):
        last_level = derivatives[level_i - 1]
        curr_level = derivatives[level_i]
        curr_level[0] = (last_level[0] - overhang[-1]) / time_diffs[0]
        for diff_i in range(1, len(curr_level)):
            curr_level[diff_i] = (last_level[diff_i] - last_level[diff_i - 1]) / time_diffs[diff_i - 1]
        for overhang_i in range(len(overhang) - 1, 0, -1):
            overhang[overhang_i] = (overhang[overhang_i] - overhang[overhang_i - 1]) / overhang_times[overhang_i - 1]
    return derivatives


_slice_deriv_njit = njit()(_slice_deriv)


def slice_diff(series, start_i: int, stop_i: int, diff_levels: int = 0, allow_njit=True, dtype=None):
    if isinstance(series, pd.Series):
        series = series.values
    if allow_njit and isinstance(series, np.ndarray):
        dtype = series.dtype if dtype is None else dtype
        func = _slice_diff_njit
    else:
        dtype = float
        func = _slice_diff
    diffs = np.empty((diff_levels + 1, stop_i - start_i), dtype=dtype)
    func(series, diffs, start_i, stop_i, diff_levels, dtype)
    return diffs


def _slice_diffs_flat(series, slices: tuple[tuple[int, int], ...], diff_levels, func, dtype):
    total_len = 0
    n = len(slices)
    lens = np.empty(n, dtype=np.int64)
    for i in range(n):
        lens[i] = slices[i][1] - slices[i][0]
        total_len += lens[i]
    diffs = np.empty((diff_levels + 1, total_len), dtype=dtype)
    curr_pos = 0
    for i in range(n):
        func(series, diffs[:, curr_pos:curr_pos + lens[i]], slices[i][0], slices[i][1], diff_levels, dtype)
        curr_pos += lens[i]
    return diffs


def slice_diffs_flat_np(series, slices, diff_levels, diffs: Optional[np.ndarray] = None):
    total_len = 0
    n = len(slices[0])
    lens = np.empty(n, dtype=np.int64)
    for i in range(n):
        lens[i] = slices[1, i] - slices[0, i]
        total_len += lens[i]
    if diffs is None:
        diffs = np.empty((diff_levels + 1, total_len), dtype=series.dtype)
    else:
        assert (diffs.shape[0] > diff_levels + 1)
        assert (diffs.shape[1] > total_len)

    curr_pos = 0

    for i in range(n):
        d = diffs[:, curr_pos:curr_pos + lens[i]]
        _slice_diff_njit(series, d, slices[0, i], slices[1, i], diff_levels,
                         series.dtype)
        curr_pos += lens[i]
    return diffs


def slice_derivs_flat_np(series, times, slices, diff_levels, diffs: Optional[np.ndarray] = None):
    total_len = 0
    n = len(slices[0])
    lens = np.empty(n, dtype=np.int64)
    for i in range(n):
        lens[i] = slices[1, i] - slices[0, i]
        total_len += lens[i]
    if diffs is None:
        diffs = np.empty((diff_levels + 1, total_len), dtype=series.dtype)
    else:
        assert (diffs.shape[0] > diff_levels + 1)
        assert (diffs.shape[1] > total_len)

    curr_pos = 0

    for i in range(n):
        d = diffs[:, curr_pos:curr_pos + lens[i]]
        _slice_deriv(series, times, d, slices[0, i], slices[1, i], diff_levels,
                     series.dtype)
        curr_pos += lens[i]
    return diffs


def slice_diffs_flat(series, *slices: tuple[int, int], diff_levels: int = 0,
                     allow_njit=True, dtype=None) -> np.ndarray:
    if isinstance(series, pd.Series):
        series = series.values
    if allow_njit and isinstance(series, np.ndarray):
        dtype = series.dtype if dtype is None else dtype
        func = _slice_diff_njit
    else:
        dtype = type(series[0])
        func = _slice_diff
    return _slice_diffs_flat(series, slices, diff_levels, func, dtype)





