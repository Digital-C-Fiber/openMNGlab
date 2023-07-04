from abc import ABC

import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.pandas.model import PandasDataScheme, PandasOutputDataScheme
from openmnglab.datamodel.pandas.verification import compare_index
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.spdf_features import SPDF_FEATURES, FeatureFunc
from openmnglab.functions.processing.waveform_components import PrincipleComponentsInputScheme
from openmnglab.functions.processing.interval_data import IntervalDataInputSchema
from openmnglab.model.planning.interface import IProxyData


class SPDFFeaturesBaseSchema(PandasDataScheme[pa.DataFrameSchema], ABC):
    def __init__(self):
        super().__init__(pa.DataFrameSchema({
            feature: pa.Column(float, nullable=True) for feature in SPDF_FEATURES}, title="Principle Components"))


class SPDFFeatureOutputSchema(SPDFFeaturesBaseSchema, PandasOutputDataScheme):
    def __init__(self, idx: pa.Index | pa.MultiIndex):
        super().__init__()
        self.pandera_schema.index = idx


class SPDFFeatures(FunctionDefinitionBase[IProxyData[DataFrame]]):
    """Calculates the SPDF features of waveforms based on their components and waveforms."""
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