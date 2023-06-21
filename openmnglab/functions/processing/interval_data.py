from __future__ import annotations

from abc import ABC
from typing import Optional

import numpy as np
import pandera as pa
import quantities as pq
from pandas import DataFrame, DatetimeTZDtype, PeriodDtype, SparseDtype, IntervalDtype, CategoricalDtype, StringDtype, \
    BooleanDtype, Series, MultiIndex

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.interface import IDataContainer, IInputDataScheme, IOutputDataScheme
from openmnglab.datamodel.pandas.model import PandasOutputDataScheme, PandasContainer, PandasInputDataScheme, \
    PandasDataScheme
from openmnglab.datamodel.pandas.schemes import generic_interval_list
from openmnglab.functions.base import FunctionDefinitionBase, FunctionBase
from openmnglab.functions.helpers.general import get_interval_locs, slice_diffs_flat_np, slice_derivs_flat_np
from openmnglab.functions.interface import IFunction
from openmnglab.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class LevelColumnGenerator:
    def __getitem__(self, item: int) -> str:
        if item == 0:
            return "original"
        return f"level {item} diff"


LEVEL_COLUMN = LevelColumnGenerator()


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


class WindowDataInputScheme(IInputDataScheme):

    def accepts(self, output_data_scheme: IOutputDataScheme) -> bool:
        if not isinstance(output_data_scheme, PandasOutputDataScheme):
            raise DataSchemeCompatibilityError("Data scheme is not a pandas data scheme")
        schema = output_data_scheme.schema
        if not isinstance(schema, pa.SeriesSchema):
            raise DataSchemeCompatibilityError("Data scheme is not a series")
        schema: pa.SeriesSchema
        assert schema.dtype not in (
            DatetimeTZDtype, CategoricalDtype, PeriodDtype, SparseDtype, IntervalDtype, StringDtype, BooleanDtype)
        return True

    def transform(self, data_container: IDataContainer) -> IDataContainer:
        return data_container


class NumericIndexedList(PandasInputDataScheme[pa.SeriesSchema]):

    def __init__(self):
        super().__init__(pa.SeriesSchema())

    def accepts(self, output_data_scheme: IOutputDataScheme) -> bool:
        super_accepts = super().accepts(output_data_scheme)
        output_data_scheme: PandasOutputDataScheme
        if not pa.dtypes.is_numeric(output_data_scheme.pandera_schema.index.dtype):
            raise DataSchemeCompatibilityError("Requires a numerically series")
        return super_accepts


class DynamicIndexWindowDataScheme(PandasOutputDataScheme[pa.SeriesSchema]):

    @staticmethod
    def for_input(inp_series: PandasOutputDataScheme[pa.SeriesSchema],
                  inp_interval: PandasOutputDataScheme[pa.SeriesSchema],
                  name: str) -> DynamicIndexWindowDataScheme:
        if inp_interval.pandera_schema.dtype != IntervalDtype:
            raise Exception("Input interval does not contain intervals!")
        interval_indexes = [pa.Index(int, name="interval_idx")] if not isinstance(inp_interval.pandera_schema.index,
                                                                                  pa.MultiIndex) else inp_interval.pandera_schema.index.indexes[
                                                                                                      :-1]
        return DynamicIndexWindowDataScheme(pa.SeriesSchema(inp_series.pandera_schema.dtype, index=pa.MultiIndex(
            indexes=[*interval_indexes,
                     pa.Index(inp_series.pandera_schema.dtype, name=inp_series.pandera_schema.name)]), name=name))


def default_name_generator(i: int):
    return f"level {i} diff"


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


class IntervalDataBaseSchema(PandasDataScheme[pa.DataFrameSchema], ABC):
    def __init__(self, first_level: int, *levels: int):
        super().__init__(
            pa.DataFrameSchema({LEVEL_COLUMN[i]: pa.Column(np.float32) for i in sorted([first_level, *levels])}))


class IntervalDataInputSchema(IntervalDataBaseSchema, PandasInputDataScheme):
    def __init__(self, first_level: int, *levels: int):
        super().__init__(first_level, *levels)

    def accepts(self, output_data_scheme: IOutputDataScheme) -> bool:
        super_accepts = super().accepts(output_data_scheme)
        output_data_scheme: PandasOutputDataScheme
        if isinstance(output_data_scheme.pandera_schema.index, pa.MultiIndex):
            num_idx = output_data_scheme.pandera_schema.index.indexes[-1]
        else:
            num_idx = output_data_scheme.pandera_schema.index
        if not pa.dtypes.is_numeric(num_idx.dtype):
            raise DataSchemeCompatibilityError(
                f'Index (or last index of a multiindex) must be numeric, is "{num_idx.dtype}"')
        return super_accepts


class IntervalDataOutputSchema(IntervalDataBaseSchema, PandasOutputDataScheme):
    def __init__(self, idx: pa.Index | pa.MultiIndex, first_level: int, *levels: int):
        super().__init__(first_level, *levels)
        self.pandera_schema.index = idx


class IntervalData(FunctionDefinitionBase[IProxyData[DataFrame]]):

    def __init__(self, first_level: int, *levels: int,
                 derivative_base: Optional[pq.Quantity] = None):
        super().__init__("openmnglab.windowdata")
        self._levels = tuple((first_level, *levels))
        self._derivatives = derivative_base is not None
        self._derivate_change = derivative_base

    @property
    def config_hash(self) -> bytes:
        hsh = Hash()
        for i in self._levels:
            hsh.int(i)
        hsh.bool(self._derivatives)
        if self._derivate_change is not None:
            hsh.quantity(self._derivate_change)
        return hsh.digest()

    @property
    def consumes(self) -> tuple[PandasInputDataScheme[pa.SeriesSchema], PandasInputDataScheme[pa.SeriesSchema]]:
        return generic_interval_list(), NumericIndexedList()

    def production_for(self, window_intervals: IOutputDataScheme[pa.SeriesSchema],
                       data: IOutputDataScheme[pa.SeriesSchema]) -> tuple[IntervalDataOutputSchema]:
        window_scheme, data_scheme = self.consumes
        assert (window_scheme.accepts(window_intervals))
        assert (data_scheme.accepts(data))
        window_intervals: PandasOutputDataScheme[pa.SeriesSchema]
        data: PandasOutputDataScheme[pa.SeriesSchema]
        if not isinstance(window_intervals.pandera_schema.index, pa.MultiIndex):
            idx = pa.MultiIndex([window_intervals.pandera_schema.index, data.pandera_schema.index])
        else:
            idx = pa.MultiIndex([*window_intervals.pandera_schema.index.indexes, data.pandera_schema.index])
        return IntervalDataOutputSchema(idx, *self._levels),

    def new_function(self) -> IFunction:
        return IntervalDataFunc(self._levels,
                                derivatives=self._derivatives,
                                derivative_change=self._derivate_change)
