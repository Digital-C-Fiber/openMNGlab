import sys
from abc import ABC
from math import log, e
from typing import Self

import numpy as np
import pandera as pa
import quantities as pq
from pandas import DataFrame, Series

from openmnglab.datamodel.pandas.model import PandasContainer, PandasDataScheme, PandasOutputDataScheme
from openmnglab.datamodel.pandas.verification import compare_index
from openmnglab.functions.base import FunctionBase, FunctionDefinitionBase
from openmnglab.functions.processing.principle_components import PRINCIPLE_COMPONENTS, \
    PrincipleComponentsInputScheme
from openmnglab.functions.processing.interval_data import IntervalDataInputSchema, LEVEL_COLUMN
from openmnglab.planning.interface import IProxyData

SPDF_FEATURES = tuple((f"F{i + 1}" for i in range(24)))


def closest_binsearch(v, seq) -> int:
    ...


def mean_change_between(series: Series, high: float, low: float):
    return np.linalg.norm([high - low, series[high] - series[low]])


def slope_ratio(sequence, a, b, c):
    part_a = (sequence[b] - sequence[a]) * (c - b)
    part_b = (sequence[c] - sequence[b]) * (b - a)
    return part_a / part_b


def rms(sequence):
    return np.sqrt(sequence.dot(sequence) / sequence.size)


def iqr(sequence):
    Q3 = np.quantile(sequence, 0.75)
    Q1 = np.quantile(sequence, 0.25)
    return Q3 - Q1


def sampling_moment_dev(sequence, n) -> float:
    return pow(np.std(sequence), n)  # moment(sequence, n) / pow(np.dev(sequence), n)


class FeatureFunc(FunctionBase):
    def __init__(self, dtype=np.float64, mode="diff"):
        self._components: PandasContainer[DataFrame] = None
        self._diffs: PandasContainer[DataFrame] = None
        self._dtype = dtype

    def _calc_features(self, fd: Series, sd: Series, p1: float, p2: float, p3: float, p4: float, p5: float, p6: float):
        f = np.full(24, np.NaN, dtype=self._dtype)
        p1_i, = fd.index.get_indexer([p1], method='nearest', tolerance=sys.float_info.epsilon)
        f[0] = p5 - p1
        if not np.isnan(p2):
            if not np.isnan(p4):
                f[1] = fd[p4] - fd[p2]
                mbf = mean_change_between(fd, p4, p2)
                f[4] = log(mbf, e)
                if not np.isnan(p6):
                    f[5] = mean_change_between(fd, p4, p6)
                f[10] = fd[p2] / fd[p4]
            if not np.isnan(p6):
                f[2] = fd[p6] - fd[p2]
                mbf = mean_change_between(fd, p6, p2)
                f[6] = log(mbf, e)
            if not np.isnan(p3) and not np.isnan(p1):
                f[8] = slope_ratio(fd, p1, p2, p3)
        if not np.isnan(p1_i):
            f[7] = rms(fd.iloc[:p1_i + 1].values)

        for i, p in enumerate((p1, p2, p3, p4, p5, p6)):
            if not np.isnan(p):
                f[11 + i] = fd[p]
        for i, p in enumerate((p1, p3, p5)):
            if not np.isnan(p):
                f[16 + i] = sd[p]
        # distribution based features
        if not np.isnan(p5):
            if not np.isnan(p3) and not np.isnan(p4):
                f[9] = slope_ratio(fd, p3, p4, p5)
            if not np.isnan(p1):
                for i, ser in enumerate((fd, sd)):
                    f[19 + i] = iqr(ser.loc[p1:p5])
                f[21] = sampling_moment_dev(fd.loc[p1:p5], 4)
                f[22] = sampling_moment_dev(fd.loc[p1:p5], 3)
                f[23] = sampling_moment_dev(sd.loc[p1:p5], 3)
        return f

    def build_unitdict(self):
        units: dict[str, pq.Quantity] = dict()
        fd_u = self._diffs.units[LEVEL_COLUMN[1]]
        sd_u = self._diffs.units[LEVEL_COLUMN[2]]
        base_u = self._diffs.units[LEVEL_COLUMN[0]]
        units[SPDF_FEATURES[0]] = base_u
        units[SPDF_FEATURES[1]] = fd_u
        units[SPDF_FEATURES[2]] = fd_u
        units[SPDF_FEATURES[3]] = fd_u
        units[SPDF_FEATURES[4]] = pq.dimensionless
        units[SPDF_FEATURES[5]] = fd_u
        units[SPDF_FEATURES[6]] = pq.dimensionless
        units[SPDF_FEATURES[7]] = fd_u
        units[SPDF_FEATURES[8]] = pq.dimensionless
        units[SPDF_FEATURES[9]] = pq.dimensionless
        units[SPDF_FEATURES[10]] = pq.dimensionless
        for i in range(11, 16):
            units[SPDF_FEATURES[i]] = fd_u
        for i in range(16, 19):
            units[SPDF_FEATURES[i]] = sd_u
        units[SPDF_FEATURES[19]] = fd_u
        units[SPDF_FEATURES[20]] = sd_u
        units[SPDF_FEATURES[21]] = pq.dimensionless
        units[SPDF_FEATURES[22]] = pq.dimensionless
        units[SPDF_FEATURES[23]] = pq.dimensionless
        return units

    def execute(self) -> tuple[PandasContainer[DataFrame]]:
        stuff = self._components.data.index

        nmpy = np.empty((len(stuff), 24), dtype=self._dtype)
        for i, (spike_loc, spike_components) in enumerate(self._components.data.iterrows()):
            diff = self._diffs.data.loc[spike_loc]
            nmpy[i] = self._calc_features(diff[LEVEL_COLUMN[1]], diff[LEVEL_COLUMN[2]],
                                          *(spike_components[component] for component in PRINCIPLE_COMPONENTS))
        df = DataFrame(data=nmpy, columns=SPDF_FEATURES, index=self._components.data.index)

        return PandasContainer(df, self.build_unitdict()),

    def set_input(self, components: PandasContainer[DataFrame], diffs: PandasContainer[DataFrame]) -> Self:
        self._components = components
        self._diffs = diffs
        return self


class SPDFFeaturesBaseSchema(PandasDataScheme[pa.DataFrameSchema], ABC):
    def __init__(self):
        super().__init__(pa.DataFrameSchema({
            feature: pa.Column(float, nullable=True) for feature in SPDF_FEATURES}, title="Principle Components"))


class SPDFFeatureOutputSchema(SPDFFeaturesBaseSchema, PandasOutputDataScheme):
    def __init__(self, idx: pa.Index | pa.MultiIndex):
        super().__init__()
        self.pandera_schema.index = idx


class SPDFFeatures(FunctionDefinitionBase[IProxyData[DataFrame]]):
    def __init__(self):
        super().__init__("omngl.spdffeatures")

    @property
    def consumes(self) -> tuple[PrincipleComponentsInputScheme, IntervalDataInputSchema]:
        return PrincipleComponentsInputScheme(), IntervalDataInputSchema(0, 1, 2)

    def production_for(self, principle_compo: PrincipleComponentsInputScheme, diffs: IntervalDataInputSchema) -> tuple[
        SPDFFeatureOutputSchema]:
        compare_index(principle_compo.pandera_schema.index, pa.MultiIndex(diffs.pandera_schema.index.indexes[:-1]))
        return SPDFFeatureOutputSchema(principle_compo.pandera_schema.index),

    def new_function(self) -> FeatureFunc:
        return FeatureFunc()
