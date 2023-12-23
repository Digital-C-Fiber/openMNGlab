

from openmnglab.datamodel.exceptions import DataSchemaCompatibilityError
from openmnglab.datamodel.pandas.model import PandasDataSchema, PanderaSchemaAcceptor
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.windows import WindowsFunc, LEVEL_COLUMN
from openmnglab.model.datamodel.interface import IDataSchema
from openmnglab.model.planning.interface import IDataReference
from openmnglab.util.hashing import HashBuilder

from openmnglab.datamodel.pandas.model import PanderaSchemaAcceptor, PandasDataSchema
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.analysis.funcs.spdf_components import SPDFComponentsFunc, SPDF_COMPONENTS
from openmnglab.functions.processing.windows import WindowDataAcceptor
from openmnglab.model.planning.interface import IDataReference
import pandera as pa
from pandas import DataFrame



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

class SimpleFeatures(FunctionDefinitionBase[IDataReference[DataFrame]]):
    """Computes windows from a series of numbers based on a list of intervals. Can also compute the change(rate)
    for the windows, optionally relative to their time delta.
    Can re-base the timestamps to their relative offset.

    In: [Intervals, Continuous Series]

    Out: Interval Data

    Consumes
    ........

    * Intervals: Series of intervals. Any index.
    * Continuous Series: Series to take the interval data from.

    Returns
    -------
    * Interval Data: A dataframe with the Intervals input index, concatenated with an additional index which is either the concrete timestamp of the data or
      the normalized timestamps of each interval based on its start. Contained columns are based on the first_level and levels parameter.

    :param first_level: first level (diff or derivative) to include in the output data frame
    :param levels: additional levels to include in the output data frame
    :param derivative_base: quantity to base the time of the derivative on. If None, it will only calculate the absolute changes between consecutive values.
    :param interval: The sampling interval of the signal. If this is not given, the interval will be approximated by calculating the diff of the first two samples.
    :param use_time_offsets: if True, will use the offset the index timestamps to the start of each interval. USE ONLY WITH REGULARLY SAMPLED SGINALS!
        """

    def __init__(self):
        super().__init__("thorekoritzius.simplefeatures")

    @property
    def config_hash(self) -> bytes:
        return bytes()

    @property
    def slot_acceptors(self) -> WindowDataAcceptor:
        return WindowDataAcceptor( 0, 1)

    @staticmethod
    def output_for(diffs: PandasDataSchema[pa.DataFrameSchema]) -> SPDFComponentsDynamicSchema:
        return SPDFComponentsDynamicSchema(pa.MultiIndex(indexes=diffs.pandera_schema.index.indexes[:-1]))

    @staticmethod
    def new_function() -> SPDFComponentsFunc:
        return SPDFComponentsFunc()
