from abc import ABC

import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.model.datamodel.interface import IOutputDataScheme
from openmnglab.datamodel.pandas.model import PandasInputDataScheme, PandasOutputDataScheme, \
    PandasDataScheme
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.waveform_components import WaveformComponentsFunc, PRINCIPLE_COMPONENTS
from openmnglab.functions.processing.interval_data import IntervalDataInputSchema
from openmnglab.model.planning.interface import IProxyData

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


class WaveformComponents(FunctionDefinitionBase[IProxyData[DataFrame]]):
    """
    Calculates the components of waveforms. Takes an IntervalData dataframe with the base signal and the first level as input.
    """
    def __init__(self):
        super().__init__("openmnglab.principlecomponents")

    @property
    def consumes(self) -> tuple[IntervalDataInputSchema]:
        return IntervalDataInputSchema(0, 1),

    @staticmethod
    def production_for(diffs: PandasInputDataScheme[pa.DataFrameSchema]) -> tuple[
        PrincipleComponentsDynamicOutputScheme]:
        return PrincipleComponentsDynamicOutputScheme(diffs.pandera_schema.index),

    @staticmethod
    def new_function() -> WaveformComponentsFunc:
        return WaveformComponentsFunc()