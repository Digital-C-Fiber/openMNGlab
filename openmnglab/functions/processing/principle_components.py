from abc import ABC
from typing import Sequence

import numpy as np
import pandera as pa
import quantities as pq
from pandas import DataFrame

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.interface import IOutputDataScheme
from openmnglab.datamodel.pandas.model import PandasContainer, PandasInputDataScheme, PandasOutputDataScheme, \
    PandasDataScheme
from openmnglab.functions.base import FunctionBase, FunctionDefinitionBase
from openmnglab.functions.processing.interval_data import IntervalDataInputSchema
from openmnglab.planning.interface import IProxyData

PRINCIPLE_COMPONENTS = tuple((f"P{i + 1}" for i in range(6)))


def get_zerocorssings(vals: np.ndarray) -> np.ndarray:
    sings = np.sign(vals)
    zerocorssings = np.empty(len(vals), dtype=bool)
    for i in range(1, len(vals)):
        zerocorssings[i] = sings[i] != sings[i - 1]
    return zerocorssings


def argmax_slice(sequence: np.ndarray, slc: slice) -> int:
    offset = slc.start if slc.start is not None else 0
    return np.argmax(sequence[slc]) + offset


def argmin_slice(sequence: np.ndarray, slc: slice) -> int:
    offset = slc.start if slc.start is not None else 0
    return np.argmin(sequence[slc]) + offset


def index_val(idx, series: Sequence):
    return idx, series[idx]


def get_principle_components(idx: np.ndarray, diff1: np.ndarray):
    def iv(i):
        return index_val(i, idx)

    zero_x = get_zerocorssings(diff1)
    p1, p2, p3, p4, p5, p6 = np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN
    p2_i, p2 = iv(np.argmin(diff1[:len(diff1) // 2]))
    try:
        p1_i, p1 = iv(p2_i - 1 - np.argmax(zero_x[p2_i - 1::-1]))
        p3_i, p3 = iv(argmax_slice(zero_x, slice(p2_i + 1, None)))
        p5_i, p5 = iv(argmax_slice(zero_x, slice(p3_i + 1, None)))
        try:
            p4_i, p4 = iv(argmax_slice(diff1, slice(p3_i + 1, p5_i)))
        except ValueError as _:
            pass
        try:
            p6_i, p6 = iv(argmin_slice(diff1, slice(p5_i + 1, None)))
        except ValueError as _:
            pass
    except ValueError as _:
        pass
    assert p1_i < p2_i
    assert p2_i < p3_i
    if not np.isnan(p4):
        assert p3_i < p4_i < p5_i
    if not np.isnan(p6):
        assert p5_i < p6_i
    return p1, p2, p3, p4, p5, p6


def get_principle_components_alt1(idx: np.ndarray, diff1: np.ndarray):
    def iv(i):
        return index_val(i, idx)

    zero_x = get_zerocorssings(diff1)
    p1, p2, p3, p4, p5, p6 = np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN
    p2_i, p2 = iv(np.argmin(diff1))
    max_i = len(idx) - 1
    if 0 < p2_i:
        p1_i, p1 = iv(p2_i - 1 - np.argmax(zero_x[p2_i - 1::-1]))
    if p2_i < max_i:
        p4_i, p4 = iv(argmax_slice(diff1, slice(p2_i + 1, None)))
        if p4_i - p2_i > 1:
            p3_i, p3 = iv(argmax_slice(zero_x, slice(p2_i + 1, p4_i)))
        if p4_i < max_i:
            p6_i, p6 = iv(argmin_slice(diff1, slice(p4_i + 1, None)))
            if p6_i - p4_i > 1:
                p5_i, p5 = iv(argmax_slice(zero_x, slice(p4_i + 1, p6_i)))
    return p1, p2, p3, p4, p5, p6


class ComponentFunc(FunctionBase):
    def __init__(self):
        self._diffs: PandasContainer[DataFrame] = None

    def calc_principle_components(self):
        grpby = self._diffs.data.groupby(level=tuple((i for i in range(self._diffs.data.index.nlevels - 1))),
                                         sort=False)
        components = np.empty((6, len(grpby)), dtype=self._diffs.data.index.levels[-1].dtype)
        for i, (loc, group) in enumerate(grpby):
            lvl_vals = group.index.get_level_values(-1)
            diff1 = group['level 1 diff'].values
            components[:, i] = get_principle_components_alt1(lvl_vals, diff1)
        return components

    def build_unitdict(self):
        units: dict[str, pq.Quantity] = dict()
        for interval_index_name in self._diffs.data.index.names[:-1]:
            units[interval_index_name] = self._diffs.units[interval_index_name]
        for column_name in PRINCIPLE_COMPONENTS:
            units[column_name] = self._diffs.units[self._diffs.data.index.names[-1]]
        return units

    def execute(self) -> tuple[PandasContainer[DataFrame]]:
        idx = self._diffs.data.index.droplevel(-1).unique()
        components = self.calc_principle_components()
        df = DataFrame(data=components.T, columns=PRINCIPLE_COMPONENTS, index=idx)
        return PandasContainer(df, units=self.build_unitdict()),

    def set_input(self, diffs: PandasContainer[DataFrame]):
        self._diffs = diffs


class GeneralDiffList(PandasInputDataScheme[pa.DataFrameSchema]):

    def __init__(self):
        super().__init__(pa.DataFrameSchema())

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


class PrincipleComponentsBaseScheme(PandasDataScheme[pa.DataFrameSchema], ABC):
    def __init__(self):
        super().__init__(pa.DataFrameSchema({
            PRINCIPLE_COMPONENTS[0]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[1]: pa.Column(float),
            PRINCIPLE_COMPONENTS[2]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[3]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[4]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[5]: pa.Column(float, nullable=True)}, title="Principle Components"))

class PrincipleComponentsInputScheme(PrincipleComponentsBaseScheme, PandasInputDataScheme):
    ...

class PrincipleComponentsDynamicOutputScheme(PrincipleComponentsBaseScheme, PandasOutputDataScheme):
    def __init__(self, index: pa.MultiIndex | pa.Index):
        super().__init__()
        self.pandera_schema.index = index


class PrincipleComponents(FunctionDefinitionBase[IProxyData[DataFrame]]):
    def __init__(self):
        super().__init__("openmnglab.principlecomponents")

    @property
    def consumes(self) -> tuple[IntervalDataInputSchema]:
        return IntervalDataInputSchema(0, 1, 2),

    @staticmethod
    def production_for(diffs: PandasInputDataScheme[pa.DataFrameSchema]) -> tuple[
        PrincipleComponentsDynamicOutputScheme]:
        return PrincipleComponentsDynamicOutputScheme(diffs.pandera_schema.index),

    @staticmethod
    def new_function() -> ComponentFunc:
        return ComponentFunc()
