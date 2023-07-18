from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import pandas as pd
import pandera as pa
import quantities as pq

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError, DataSchemeConformityError
from openmnglab.model.datamodel.interface import IDataContainer, IInputDataScheme, IOutputDataScheme, \
    IStaticDataScheme
from openmnglab.datamodel.pandas.verification import compare_schemas
from openmnglab.util.pandas import pandas_names

TPandas = TypeVar('TPandas', pd.Series, pd.DataFrame)


class PandasContainer(IDataContainer[TPandas], Generic[TPandas]):

    @staticmethod
    def check_all_indexes_named(idx: pd.Index | pd.MultiIndex):
        if isinstance(idx, pd.MultiIndex):
            for level_i, level_name in enumerate(idx.names):
                if not level_name:
                    raise KeyError(f"Multiindex level {level_i} is not named")
        elif isinstance(idx, pd.Index):
            if not idx.name:
                raise KeyError("Index is not named")
        else:
            raise TypeError("Passed object is neither a pandas index nor a multiindex")

    @classmethod
    def check_all_named(cls, data: TPandas):
        cls.check_all_indexes_named(data.index)
        if isinstance(data, pd.Series):
            if not data.name:
                raise KeyError("Series not named")
        elif isinstance(data, pd.DataFrame):
            for col_i, col_name in enumerate(data.columns):
                if not col_name:
                    raise KeyError(f"Column {col_i} of data frame is not named")
        else:
            raise TypeError("Passed object is neither a pandas dataframe nor a series")



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
                    f"Value of key {k} in the 'units' dictionary is of type {type(v).__qualname__}, but must be of type {pq.Quantity.__qualname__} or a subtype thereof.")
        self.check_all_named(data)
        for col_name in pandas_names(data):
            if col_name not in units:
                raise KeyError(f"No quantity for element \'{col_name}\' in unit dict")
        self._data = data
        self._units = units

    @property
    def data(self) -> TPandas:
        return self._data

    @property
    def units(self) -> dict[str, pq.Quantity]:
        return self._units

    def __repr__(self):
        index_names = (self.data.index.name,) if not isinstance(self.data.index, pd.MultiIndex) else (idx.name for idx in self.data.index.levels)
        col_names = (self.data.name,) if isinstance(self.data, pd.Series) else self.data.columns
        units = ",".join((f"'{col}':{self.units[col].dimensionality}" for col in (*index_names, *col_names)))
        return f"""PandasContainer @{id(self)}
Units: {units}
{repr(self.data)}"""

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
