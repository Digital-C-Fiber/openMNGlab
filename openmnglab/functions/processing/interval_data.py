from __future__ import annotations

from typing import Optional

import pandera as pa
import quantities as pq
from pandas import DataFrame, IntervalDtype

from openmnglab.datamodel.exceptions import DataSchemaCompatibilityError
from openmnglab.datamodel.pandas.model import PandasDataSchema, PanderaSchemaAcceptor
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.interval_data import IntervalDataFunc, LEVEL_COLUMN
from openmnglab.model.datamodel.interface import IDataSchema
from openmnglab.model.planning.interface import IDataReference
from openmnglab.util.hashing import HashBuilder


class NumericIndexedListAcceptor(PanderaSchemaAcceptor[pa.SeriesSchema]):

    def __init__(self):
        super().__init__(pa.SeriesSchema())

    def accepts(self, data_schema: IDataSchema) -> bool:
        super_accepts = super().accepts(data_schema)
        data_schema: PandasDataSchema
        if not pa.dtypes.is_numeric(data_schema.pandera_schema.index.dtype):
            raise DataSchemaCompatibilityError("Requires a numerically series")
        return super_accepts


class IntervalDataAcceptor(PanderaSchemaAcceptor[pa.DataFrameSchema]):
    def __init__(self, first_level: int, *levels: int, idx=None):
        super().__init__(
            pa.DataFrameSchema({LEVEL_COLUMN[i]: pa.Column(float) for i in sorted([first_level, *levels])}, index=idx))

    def accepts(self, data_schema: IDataSchema) -> bool:
        super_accepts = super().accepts(data_schema)
        data_schema: PandasDataSchema
        if isinstance(data_schema.pandera_schema.index, pa.MultiIndex):
            num_idx = data_schema.pandera_schema.index.indexes[-1]
        else:
            num_idx = data_schema.pandera_schema.index
        if not pa.dtypes.is_numeric(num_idx.dtype):
            raise DataSchemaCompatibilityError(
                f'Index (or last index of a multiindex) must be numeric, is "{num_idx.dtype}"')
        return super_accepts


class IntervalDataDynamicSchema(IntervalDataAcceptor, PandasDataSchema):
    def __init__(self, idx: pa.Index | pa.MultiIndex, first_level: int, *levels: int):
        super().__init__(first_level, *levels, idx=idx)


class IntervalData(FunctionDefinitionBase[IDataReference[DataFrame]]):
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
        hsh = HashBuilder()
        for i in self._levels:
            hsh.int(i)
        hsh.bool(self._derivatives)
        if self._derivate_change is not None:
            hsh.quantity(self._derivate_change)
        return hsh.digest()

    @property
    def slot_acceptors(self) -> tuple[
        PanderaSchemaAcceptor[pa.SeriesSchema], PanderaSchemaAcceptor[pa.SeriesSchema]]:
        return PanderaSchemaAcceptor(pa.SeriesSchema(IntervalDtype)), NumericIndexedListAcceptor()

    def output_for(self, window_intervals: IDataSchema[pa.SeriesSchema],
                   data: IDataSchema[pa.SeriesSchema]) -> IntervalDataDynamicSchema:
        window_scheme, data_scheme = self.slot_acceptors
        assert (window_scheme.accepts(window_intervals))
        assert (data_scheme.accepts(data))
        window_intervals: PandasDataSchema[pa.SeriesSchema]
        data: PandasDataSchema[pa.SeriesSchema]
        if not isinstance(window_intervals.pandera_schema.index, pa.MultiIndex):
            idx = pa.MultiIndex([window_intervals.pandera_schema.index, data.pandera_schema.index])
        else:
            idx = pa.MultiIndex([*window_intervals.pandera_schema.index.indexes, data.pandera_schema.index])
        return IntervalDataDynamicSchema(idx, *self._levels)

    def new_function(self) -> IntervalDataFunc:
        return IntervalDataFunc(self._levels,
                                derivatives=self._derivatives,
                                derivative_change=self._derivate_change, use_time_offsets=self._use_time_offsets,
                                interval=self._interval)
