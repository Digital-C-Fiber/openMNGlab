import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.pandas.model import DefaultPandasSchemaAcceptor, PandasDataSchema
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.spdf_components import SPDFComponentsFunc, SPDF_COMPONENTS
from openmnglab.functions.processing.interval_data import IntervalDataAcceptor
from openmnglab.model.planning.interface import IProxyData


class SPDFComponentsAcceptor(DefaultPandasSchemaAcceptor[pa.DataFrameSchema]):
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


class SPDFComponents(FunctionDefinitionBase[IProxyData[DataFrame]]):
    """
    Calculates the SPDF components of waveforms.

    In: Interval data with level 0 and 1.

    Out: Dataframe with the waveform components, columns are named based on PRINCIPLE_COMPONENTS constant.
         Index is taken from the input series non-timestamp multiindex.
    """

    def __init__(self):
        super().__init__("openmnglab.principlecomponents")

    @property
    def consumes(self) -> IntervalDataAcceptor:
        return IntervalDataAcceptor(0, 1)

    @staticmethod
    def production_for(diffs: PandasDataSchema[pa.DataFrameSchema]) -> SPDFComponentsDynamicSchema:
        return SPDFComponentsDynamicSchema(diffs.pandera_schema.index)

    @staticmethod
    def new_function() -> SPDFComponentsFunc:
        return SPDFComponentsFunc()