import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.pandas.model import PanderaSchemaAcceptor, PandasDataSchema
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.spdf_components import SPDFComponentsFunc, SPDF_COMPONENTS
from openmnglab.functions.processing.interval_data import IntervalDataAcceptor
from openmnglab.model.planning.interface import IDataReference


class SPDFComponentsAcceptor(PanderaSchemaAcceptor[pa.DataFrameSchema]):
    def __init__(self, index=None):
        super().__init__(pa.DataFrameSchema({
            SPDF_COMPONENTS[0]: pa.Column(float, nullable=True),
            SPDF_COMPONENTS[1]: pa.Column(float),
            SPDF_COMPONENTS[2]: pa.Column(float, nullable=True),
            SPDF_COMPONENTS[3]: pa.Column(float, nullable=True),
            SPDF_COMPONENTS[4]: pa.Column(float, nullable=True),
            SPDF_COMPONENTS[5]: pa.Column(float, nullable=True)}, index=index))


class SPDFComponentsDynamicSchema(SPDFComponentsAcceptor, PandasDataSchema):
    def __init__(self, index: pa.MultiIndex | pa.Index):
        super().__init__(index)


class SPDFComponents(FunctionDefinitionBase[IDataReference[DataFrame]]):
    """
    Calculates the SPDF components of waveforms.

    In: Interval data with level 0 and 1.

    Out: Dataframe with the waveform components, columns are named based on PRINCIPLE_COMPONENTS constant.
         Index is taken from the input series non-timestamp multiindex.
    """

    def __init__(self):
        super().__init__("codingchipmunk.spdf.components")

    @property
    def config_hash(self) -> bytes:
        return bytes()

    @property
    def slot_acceptors(self) -> IntervalDataAcceptor:
        return IntervalDataAcceptor(0, 1)

    @staticmethod
    def output_for(diffs: PandasDataSchema[pa.DataFrameSchema]) -> SPDFComponentsDynamicSchema:
        return SPDFComponentsDynamicSchema(pa.MultiIndex(indexes=diffs.pandera_schema.index.indexes[:-1]))

    @staticmethod
    def new_function() -> SPDFComponentsFunc:
        return SPDFComponentsFunc()
