from __future__ import annotations

import numpy as np
import pandas
import quantities as pq
from pandas import Series, Interval, IntervalDtype

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

        # window_series: Series = origin_series.transform(to_interval)

        if len(origin_series) > 0:
            window_series: Series = origin_series.transform(to_interval)
        else:
            if isinstance(origin_series.index, pandas.MultiIndex):
                idx = pandas.MultiIndex.from_arrays(
                    [np.empty(0, dtype=lvl.dtype) for lvl in origin_series.index.levels],
                    names=[lvl.name for lvl in origin_series.index.levels])
            elif isinstance(origin_series.index, pandas.Index):
                idx = pandas.Index(np.empty(0, dtype=origin_series.index.dtype), name=origin_series.index.name)
            window_series = Series(data=[], dtype=IntervalDtype(), index=idx)
        window_series.name = self._name
        q_dict = get_index_quantities(self._target_series_container)
        q_dict[window_series.name] = series_quantity
        return PandasContainer(window_series, q_dict)

    def set_input(self, series: PandasContainer[Series]):
        self._target_series_container = series
