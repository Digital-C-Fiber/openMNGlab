from __future__ import annotations

from typing import Tuple

import quantities as pq
from pandas import Series, Interval

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.functions.base import FunctionBase
from openmnglab.functions.helpers.general import get_index_quantities
from openmnglab.functions.helpers.quantity_helpers import magnitudes, rescale_pq


class WindowingFunc(FunctionBase):
    def __init__(self, lo: pq.Quantity, hi: pq.Quantity, name: str, closed="right"):
        assert (isinstance(lo, pq.Quantity))
        assert (isinstance(hi, pq.Quantity))
        self._target_series_container: PandasContainer[Series] = None
        self._lo = lo
        self._hi = hi
        self._closed = closed
        self._name = name

    def execute(self) -> PandasContainer[Series]:
        origin_series = self._target_series_container.data
        series_quantity = self._target_series_container.units[origin_series.name]
        lo, hi = magnitudes(*rescale_pq(series_quantity, self._lo, self._hi))

        def to_interval(val):
            return Interval(val + lo, val + hi) if val is not None else None

        window_series = origin_series.transform(to_interval)
        window_series.name = self._name
        q_dict = get_index_quantities(self._target_series_container)
        q_dict[window_series.name] = series_quantity
        return PandasContainer(window_series, q_dict)

    def set_input(self, series: PandasContainer[Series]):
        self._target_series_container = series
