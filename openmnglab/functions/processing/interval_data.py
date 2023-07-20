from __future__ import annotations

from abc import ABC
from typing import Optional

import numpy as np
import pandera as pa
import quantities as pq
from pandas import DataFrame, DatetimeTZDtype, PeriodDtype, SparseDtype, IntervalDtype, CategoricalDtype, StringDtype, \
    BooleanDtype

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.pandas.model import PandasOutputDataScheme, PandasInputDataScheme, \
    PandasDataScheme
from openmnglab.datamodel.pandas.schemes import generic_interval_list
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.interval_data import IntervalDataFunc, LEVEL_COLUMN
from openmnglab.model.datamodel.interface import IDataContainer, IInputDataScheme, IOutputDataScheme
from openmnglab.model.functions.interface import IFunction
from openmnglab.model.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


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
    """Extracts the data of intervals from a continuous series. Also calculates derivatives or differences between the values.
    Can re-base the timestamps to their relative offset. A derivative is a diff divided by the change of time.

    In: [Intervals, Continuous Series]

    Out: Interval Data

    Consumes
    ........

    * Intervals: Series of intervals. Any index.
    * Continuous Series: Series to take the interval data from.

    Returns
    -------
    * Interval Data: A dataframe with the Intervals input index, concatenated with an additional index which is either the concrete timestamp of the data or
      the normalized timestamps of each interval based on its start. Contained columns are based on the first_level and levels parameter.

    :param first_level: first level (diff or derivative) to include in the output data frame
    :param levels: additional levels to include in the output data frame
    :param derivative_base: quantity to base the time of the derivative on. If None, will calculate the diffs
    :param interval: The sampling interval of the signal. If this is not given, the interval will be approximated by calculating the diff of the first two samples.
    :param use_time_offsets: if True, will use the offset the index timestamps to the start of each interval. USE ONLY WITH REGULARLY SAMPLED SGINALS!
        """

    def __init__(self, first_level: int, *levels: int,
                 derivative_base: Optional[pq.Quantity] = None, interval: Optional[float] = None,
                 use_time_offsets=True):
        super().__init__("openmnglab.windowdata")
        self._levels = tuple((first_level, *levels))
        self._derivatives = derivative_base is not None
        self._derivate_change = derivative_base
        self._interval = interval
        self._use_time_offsets = use_time_offsets

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
                       data: IOutputDataScheme[pa.SeriesSchema]) -> IntervalDataOutputSchema:
        window_scheme, data_scheme = self.consumes
        assert (window_scheme.accepts(window_intervals))
        assert (data_scheme.accepts(data))
        window_intervals: PandasOutputDataScheme[pa.SeriesSchema]
        data: PandasOutputDataScheme[pa.SeriesSchema]
        if not isinstance(window_intervals.pandera_schema.index, pa.MultiIndex):
            idx = pa.MultiIndex([window_intervals.pandera_schema.index, data.pandera_schema.index])
        else:
            idx = pa.MultiIndex([*window_intervals.pandera_schema.index.indexes, data.pandera_schema.index])
        return IntervalDataOutputSchema(idx, *self._levels)

    def new_function(self) -> IntervalDataFunc:
        return IntervalDataFunc(self._levels,
                                derivatives=self._derivatives,
                                derivative_change=self._derivate_change, use_time_offsets=self._use_time_offsets,
                                interval=self._interval)
