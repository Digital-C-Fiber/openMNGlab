from abc import ABC

import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.pandas.model import PanderaContainer, PandasDataSchema
from openmnglab.datamodel.pandas.verification import compare_index
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.spdf_features import SPDF_FEATURES, FeatureFunc
from openmnglab.functions.processing.interval_data import IntervalDataAcceptor, IntervalDataOutputSchema
from openmnglab.functions.processing.waveform_components import PrincipleComponentsInputSchema, \
    PrincipleComponentsDynamicOutputSchema
from openmnglab.model.datamodel.interface import IDataSchema
from openmnglab.model.planning.interface import IProxyData


class SPDFFeaturesBaseSchema(PanderaContainer[pa.DataFrameSchema], ABC):
    def __init__(self):
        super().__init__(pa.DataFrameSchema({
            feature: pa.Column(float, nullable=True) for feature in SPDF_FEATURES}, title="Principle Components"))


class SPDFFeatureOutputSchema(SPDFFeaturesBaseSchema, PandasDataSchema):
    def __init__(self, idx: pa.Index | pa.MultiIndex):
        super().__init__()
        self.pandera_schema.index = idx


class SPDFFeatures(FunctionDefinitionBase[IProxyData[DataFrame]]):
    """Calculates the SPDF features of waveforms based on their components and waveforms.

    In: [WaveformComponents, IntervalData with levels 0,1,2] WaveformComponents and IntervalData must have the same base multiindex

    Out: Dataframe with the features, indexed by the same index as the WaveformComponents input. F4 will always be None.

    """

    def __init__(self):
        super().__init__("omngl.spdffeatures")

    @property
    def consumes(self) -> tuple[PrincipleComponentsInputSchema, IntervalDataAcceptor]:
        return PrincipleComponentsInputSchema(), IntervalDataAcceptor(0, 1, 2)

    def production_for(self, principle_compo: PrincipleComponentsDynamicOutputSchema,
                       diffs: IntervalDataOutputSchema) -> SPDFFeatureOutputSchema:
        compare_index(principle_compo.pandera_schema.index, pa.MultiIndex(diffs.pandera_schema.index.indexes[:-1]))
        return SPDFFeatureOutputSchema(principle_compo.pandera_schema.index)

    def new_function(self) -> FeatureFunc:
        return FeatureFunc()
