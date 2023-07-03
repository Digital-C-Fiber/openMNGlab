from abc import ABC

import pandera as pa
from pandas import DataFrame

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.interface import IOutputDataScheme
from openmnglab.datamodel.pandas.model import PandasInputDataScheme, PandasOutputDataScheme, \
    PandasDataScheme
from openmnglab.functions.base import FunctionDefinitionBase
from openmnglab.functions.processing.funcs.principle_components import ComponentFunc, PRINCIPLE_COMPONENTS
from openmnglab.functions.processing.interval_data import IntervalDataInputSchema
from openmnglab.planning.interface import IProxyData


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
