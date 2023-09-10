from abc import ABC

import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.pandas.model import PandasSchemaAcceptor, PandasOutputDataSchema, \
    PandasDataSchemaBase
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.waveform_components import WaveformComponentsFunc, PRINCIPLE_COMPONENTS
from openmnglab.functions.processing.interval_data import IntervalDataAcceptor
from openmnglab.model.planning.interface import IProxyData


class PrincipleComponentsBaseSchema(PandasDataSchemaBase[pa.DataFrameSchema], ABC):
    def __init__(self):
        super().__init__(pa.DataFrameSchema({
            PRINCIPLE_COMPONENTS[0]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[1]: pa.Column(float),
            PRINCIPLE_COMPONENTS[2]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[3]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[4]: pa.Column(float, nullable=True),
            PRINCIPLE_COMPONENTS[5]: pa.Column(float, nullable=True)}, title="Principle Components"))


class PrincipleComponentsInputSchema(PrincipleComponentsBaseSchema, PandasSchemaAcceptor):
    ...


class PrincipleComponentsDynamicOutputSchema(PrincipleComponentsBaseSchema, PandasOutputDataSchema):
    def __init__(self, index: pa.MultiIndex | pa.Index):
        super().__init__()
        self.pandera_schema.index = index


class WaveformComponents(FunctionDefinitionBase[IProxyData[DataFrame]]):
    """
    Calculates the components of waveforms.

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
    def production_for(diffs: PandasOutputDataSchema[pa.DataFrameSchema]) -> PrincipleComponentsDynamicOutputSchema:
        return PrincipleComponentsDynamicOutputSchema(diffs.pandera_schema.index)

    @staticmethod
    def new_function() -> WaveformComponentsFunc:
        return WaveformComponentsFunc()
