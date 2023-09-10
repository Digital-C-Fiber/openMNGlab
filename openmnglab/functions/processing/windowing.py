from __future__ import annotations

from typing import Literal

import quantities as pq
from pandas import DataFrame, DatetimeTZDtype, CategoricalDtype, PeriodDtype, SparseDtype, IntervalDtype, \
    StringDtype, BooleanDtype
from pandera import SeriesSchema

from openmnglab.datamodel.exceptions import DataSchemaCompatibilityError
from openmnglab.model.datamodel.interface import IDataContainer, IInputDataSchema, IOutputDataSchema
from openmnglab.datamodel.pandas.model import PandasOutputDataSchema
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.model.functions.interface import IFunction
from openmnglab.functions.processing.funcs.windowing import WindowingFunc
from openmnglab.model.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class WindowingInputDataSchema(IInputDataSchema):

    def accepts(self, output_data_scheme: IOutputDataSchema) -> bool:
        if not isinstance(output_data_scheme, PandasOutputDataSchema):
            raise DataSchemaCompatibilityError("Data scheme is not a pandas data scheme")
        schema = output_data_scheme.pandera_schema
        if not isinstance(schema, SeriesSchema):
            raise DataSchemaCompatibilityError("Data scheme must be a series")
        schema: SeriesSchema
        assert schema.dtype not in (
            DatetimeTZDtype, CategoricalDtype, PeriodDtype, SparseDtype, IntervalDtype, StringDtype, BooleanDtype)
        return True

    def transform(self, data_container: IDataContainer) -> IDataContainer:
        return data_container


class DynamicIndexIntervalSchema(PandasOutputDataSchema[SeriesSchema]):

    @staticmethod
    def for_input(inp: PandasOutputDataSchema[SeriesSchema], name: str) -> DynamicIndexIntervalSchema:
        return DynamicIndexIntervalSchema(SeriesSchema(IntervalDtype, index=inp.pandera_schema.index, name=name))


class Windowing(FunctionDefinitionBase[IProxyData[DataFrame]]):
    """Takes a set of values and transforms them based on a fixed window.

    In: series of numbers

    Out: Series of pd.Interval, with the same index as the input series.

    :param offset_low: quantity of low offset
    :param offset_high: quantity of high offset
    :param name: name of the returned series
    :param closed: how the interval is closed / open
    """

    def __init__(self, offset_low: pq.Quantity, offset_high: pq.Quantity, name: str,
                 closed: Literal["left", "right", "both", "neither"] = "right"):

        FunctionDefinitionBase.__init__(self, "openmnglab.windowing")
        assert (isinstance(offset_low, pq.Quantity))
        assert (isinstance(offset_high, pq.Quantity))
        assert (isinstance(name, str))
        assert (closed in ("left", "right", "both", "neither"))
        self._lo = offset_low
        self._hi = offset_high
        self._name = name
        self._closed = closed

    @property
    def config_hash(self) -> bytes:
        return Hash() \
            .str(self._name) \
            .quantity(self._lo) \
            .quantity(self._hi) \
            .str(self._name) \
            .str(self._closed) \
            .digest()

    @property
    def consumes(self) -> WindowingInputDataSchema:
        return WindowingInputDataSchema()

    def production_for(self, inp: PandasOutputDataSchema) -> DynamicIndexIntervalSchema:
        assert isinstance(inp, PandasOutputDataSchema)
        return DynamicIndexIntervalSchema.for_input(inp, self._name)

    def new_function(self) -> IFunction:
        return WindowingFunc(self._lo, self._hi, self._name, closed=self._closed)
