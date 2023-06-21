from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import pandas as pd
import pandera as pa
import quantities as pq

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError, DataSchemeConformityError
from openmnglab.datamodel.interface import IDataContainer, IInputDataScheme, IOutputDataScheme, \
    IStaticDataScheme
from openmnglab.datamodel.pandas.verification import compare_schemas

TPandas = TypeVar('TPandas', pd.Series, pd.DataFrame)


class PandasContainer(IDataContainer[TPandas], Generic[TPandas]):

    def __init__(self, data: TPandas, units: dict[str, pq.Quantity]):
        if not isinstance(data, (pd.Series, pd.DataFrame)):
            raise TypeError(
                f"Argument 'data' must be either a pandas series or a dataframe, is {type(data).__qualname__}")
        for k, v in units.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"Key {k} in the 'units' dictionary is of type {type(k).__qualname__}, but must be of type {str} or a subtype thereof. ")
            if not isinstance(v, pq.Quantity):
                raise TypeError(
                    f"Value of key {k} in the 'units' dictionary is of type {type(v).__qualname__}, but must be of type {pq.Quantity.__qualname__} or a subtype thereof. ")
        self._data = data
        self._units = units

    @property
    def data(self) -> TPandas:
        return self._data

    @property
    def units(self) -> dict[str, pq.Quantity]:
        return self._units

    def deep_copy(self) -> PandasContainer[TPandas]:
        return PandasContainer(self.data.copy(), self.units.copy())


TPandasScheme = TypeVar("TPandasScheme", pa.DataFrameSchema, pa.SeriesSchema)

class IPandasDataScheme(Generic[TPandasScheme], ABC):
    @property
    @abstractmethod
    def pandera_schema(self) -> TPandasScheme:
        ...

class PandasDataScheme(Generic[TPandasScheme], IPandasDataScheme[TPandasScheme], ABC):

    def __init__(self, schema: TPandasScheme):
        if not isinstance(schema, (pa.DataFrameSchema, pa.SeriesSchema)):
            raise TypeError(
                f"Argument 'model' must be either a pandas series or a dataframe, is {type(schema).__qualname__}")
        self._schema = schema

    @property
    def pandera_schema(self) -> TPandasScheme:
        return self._schema


class PandasInputDataScheme(Generic[TPandasScheme], PandasDataScheme[TPandasScheme], IInputDataScheme):

    def accepts(self, output_data_scheme: IOutputDataScheme) -> bool:
        if not isinstance(output_data_scheme, IPandasDataScheme):
            raise DataSchemeCompatibilityError(
                f"Other data scheme of type {type(output_data_scheme).__qualname__} is not a pandas data scheme")
        return compare_schemas(self.pandera_schema, output_data_scheme.pandera_schema)
    def transform(self, data_container: IDataContainer) -> IDataContainer:
        return data_container


class PandasOutputDataScheme(Generic[TPandasScheme], PandasDataScheme[TPandasScheme], IOutputDataScheme):

    def validate(self, data_container: IDataContainer) -> bool:
        if not isinstance(data_container, PandasContainer):
            raise DataSchemeConformityError(
                f"PandasDataScheme expects a PandasContainer for validation but got an object of type {type(data_container).__qualname__}")
        try:
            _ = self._schema.validate(data_container.data)
            return True
        except Exception as e:
            raise DataSchemeConformityError("Pandera model validation failed") from e


class PandasStaticDataScheme(Generic[TPandasScheme], PandasInputDataScheme[TPandasScheme],
                             PandasOutputDataScheme[TPandasScheme], IStaticDataScheme):
    ...
