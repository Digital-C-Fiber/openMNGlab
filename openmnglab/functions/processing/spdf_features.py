import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.pandas.model import PandasDataSchema, PanderaSchemaAcceptor
from openmnglab.datamodel.pandas.verification import compare_index
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.spdf_features import SPDF_FEATURES, FeatureFunc
from openmnglab.functions.processing.interval_data import IntervalDataAcceptor, IntervalDataDynamicSchema
from openmnglab.functions.processing.spdf_components import SPDFComponentsDynamicSchema, \
    SPDFComponentsAcceptor
from openmnglab.model.planning.interface import IDataReference


class SPDFFeaturesAcceptor(PanderaSchemaAcceptor[pa.DataFrameSchema]):
    def __init__(self, index=None):
        super().__init__(pa.DataFrameSchema({
            feature: pa.Column(float, nullable=True) for feature in SPDF_FEATURES}, title="Principle Components",
            index=index))


class SPDFFeaturesDynamicSchema(SPDFFeaturesAcceptor, PandasDataSchema):
    def __init__(self, idx: pa.Index | pa.MultiIndex):
        super().__init__(index=idx)


class SPDFFeatures(FunctionDefinitionBase[IDataReference[DataFrame]]):
    """Calculates the SPDF features of waveforms based on their components and waveforms.

    In: [WaveformComponents, IntervalData with levels 0,1,2] WaveformComponents and IntervalData must have the same base multiindex

    Out: Dataframe with the features, indexed by the same index as the WaveformComponents input. F4 will always be None.

    """

    def __init__(self):
        super().__init__("codingchipmunk.spdf.features")

    @property
    def config_hash(self) -> bytes:
        return bytes()

    @property
    def slot_acceptors(self) -> tuple[SPDFComponentsAcceptor, IntervalDataAcceptor]:
        return SPDFComponentsAcceptor(), IntervalDataAcceptor(0, 1, 2)

    def output_for(self, principle_compo: SPDFComponentsDynamicSchema,
                   diffs: IntervalDataDynamicSchema) -> SPDFFeaturesDynamicSchema:
        compare_index(principle_compo.pandera_schema.index, pa.MultiIndex(diffs.pandera_schema.index.indexes[:-1]))
        return SPDFFeaturesDynamicSchema(principle_compo.pandera_schema.index)

    def new_function(self) -> FeatureFunc:
        return FeatureFunc()
