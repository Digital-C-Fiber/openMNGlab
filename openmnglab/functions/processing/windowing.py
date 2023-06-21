from __future__ import annotations

from typing import Tuple, Literal

import quantities as pq
from pandas import DataFrame, Series, DatetimeTZDtype, CategoricalDtype, PeriodDtype, SparseDtype, IntervalDtype, \
    StringDtype, BooleanDtype, Interval
from pandera import SeriesSchema

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.interface import IDataContainer, IInputDataScheme, IOutputDataScheme
from openmnglab.datamodel.pandas.model import PandasContainer, PandasOutputDataScheme, PandasInputDataScheme
from openmnglab.functions.base import FunctionDefinitionBase, FunctionBase
from openmnglab.functions.helpers.general import get_index_quantities
from openmnglab.functions.helpers.quantity_helpers import magnitudes, rescale_pq
from openmnglab.functions.interface import IFunction
from openmnglab.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class WindowingInputDataScheme(IInputDataScheme):

    def accepts(self, output_data_scheme: IOutputDataScheme) -> bool:
        if not isinstance(output_data_scheme, PandasOutputDataScheme):
            raise DataSchemeCompatibilityError("Data scheme is not a pandas data scheme")
        schema = output_data_scheme.pandera_schema
        if not isinstance(schema, SeriesSchema):
            raise DataSchemeCompatibilityError("Data scheme must be a series")
        schema: SeriesSchema
        assert schema.dtype not in (
            DatetimeTZDtype, CategoricalDtype, PeriodDtype, SparseDtype, IntervalDtype, StringDtype, BooleanDtype)
        return True

    def transform(self, data_container: IDataContainer) -> IDataContainer:
        return data_container


class DynamicIndexIntervalScheme(PandasOutputDataScheme[SeriesSchema]):

    @staticmethod
    def for_input(inp: PandasOutputDataScheme[SeriesSchema], name: str) -> DynamicIndexIntervalScheme:
        return DynamicIndexIntervalScheme(SeriesSchema(IntervalDtype, index=inp.pandera_schema.index, name=name))


class WindowingFunc(FunctionBase):
    def __init__(self, lo: pq.Quantity, hi: pq.Quantity, name: str, closed="right"):
        assert (isinstance(lo, pq.Quantity))
        assert (isinstance(hi, pq.Quantity))
        self._target_series_container: PandasContainer[Series] = None
        self._lo = lo
        self._hi = hi
        self._closed = closed
        self._name = name

    def execute(self) -> Tuple[PandasContainer[Series]]:
        origin_series = self._target_series_container.data
        series_quantity = self._target_series_container.units[origin_series.name]
        lo, hi = magnitudes(*rescale_pq(series_quantity, self._lo, self._hi))

        def to_interval(val):
            return Interval(val + lo, val + hi) if val is not None else None

        window_series = origin_series.transform(to_interval)
        window_series.name = self._name
        q_dict = get_index_quantities(self._target_series_container)
        q_dict[window_series.name] = series_quantity
        return PandasContainer(window_series, q_dict),

    def set_input(self, series: PandasContainer[Series]):
        self._target_series_container = series


class Windowing(FunctionDefinitionBase[IProxyData[DataFrame]]):
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
    def consumes(self) -> tuple[WindowingInputDataScheme]:
        return WindowingInputDataScheme(),

    def production_for(self, inp: PandasOutputDataScheme) -> tuple[DynamicIndexIntervalScheme]:
        assert isinstance(inp, PandasOutputDataScheme)
        return DynamicIndexIntervalScheme.for_input(inp, self._name),

    def new_function(self) -> IFunction:
        return WindowingFunc(self._lo, self._hi, self._name, closed=self._closed)
