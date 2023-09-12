from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import numpy as np
import pandas as pd
import pandera as pa
import quantities as pq

from openmnglab.datamodel.exceptions import DataSchemaCompatibilityError, DataSchemaConformityError
from openmnglab.datamodel.pandas.verification import compare_schemas
from openmnglab.model.datamodel.interface import IDataContainer, ISchemaAcceptor, IDataSchema
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
        index_names = (self.data.index.name,) if not isinstance(self.data.index, pd.MultiIndex) else (idx.name for idx
                                                                                                      in
                                                                                                      self.data.index.levels)
        col_names = (self.data.name,) if isinstance(self.data, pd.Series) else self.data.columns
        units = ",".join((f"'{col}':{self.units[col].dimensionality}" for col in (*index_names, *col_names)))
        return f"""PandasContainer @{id(self)}
Units: {units}
{repr(self.data)}"""

    def deep_copy(self) -> PandasContainer[TPandas]:
        return PandasContainer(self.data.copy(), self.units.copy())


TPanderaSchema = TypeVar("TPanderaSchema", pa.DataFrameSchema, pa.SeriesSchema)


class PanderaSchemaAcceptor(Generic[TPanderaSchema], ISchemaAcceptor):

    def __init__(self, schema: TPanderaSchema):
        if not isinstance(schema, (pa.DataFrameSchema, pa.SeriesSchema)):
            raise TypeError(
                f"Argument 'model' must be either a pandas series or a dataframe, is {type(schema).__qualname__}")
        self._schema = schema

    def accepts(self, output_data_scheme: IDataSchema) -> bool:
        if not isinstance(output_data_scheme, IPandasDataSchema):
            raise DataSchemaCompatibilityError(
                f"Other data scheme of type {type(output_data_scheme).__qualname__} is not a pandas data schema")
        return compare_schemas(self._schema, output_data_scheme.pandera_schema)


class IPandasDataSchema(Generic[TPanderaSchema], IDataSchema, ABC):
    """Contains a Pandera schema with all elements named"""

    @property
    @abstractmethod
    def pandera_schema(self) -> TPanderaSchema:
        ...


class PandasDataSchema(Generic[TPanderaSchema], IPandasDataSchema[TPanderaSchema],
                       PanderaSchemaAcceptor[TPanderaSchema]):
    """Implements IDataSchema for PanderaContainer. Will ensure that all elements in the schema are named.
    """

    def __init__(self, schema: TPanderaSchema):
        super().__init__(schema)
        self.ensure_all_schema_elements_named(schema)

    @staticmethod
    def ensure_all_schema_elements_named(schema: TPanderaSchema) -> bool:
        if isinstance(schema, pa.SeriesSchema):
            if not schema.name:
                raise KeyError("Series defined by the series schema is not named")
        elif not isinstance(schema, pa.DataFrameSchema):
            raise TypeError(
                f"Argument 'model' must be either a pandas series or a dataframe, is {type(schema).__qualname__}")
        if not schema.index:
            raise KeyError("Schema is missing an index")
        if isinstance(schema.index, pa.Index) and not schema.index.name:
            raise KeyError("Index is not named")
        elif isinstance(schema.index, pa.MultiIndex):
            for i, l in enumerate(schema.index.indexes):
                if not l.name:
                    raise KeyError(f"Index level {i} is not named")
        return True

    @property
    def pandera_schema(self) -> TPanderaSchema:
        return self._schema

    def validate(self, data_container: IDataContainer) -> bool:
        if not isinstance(data_container, PandasContainer):
            raise DataSchemaConformityError(
                f"PandasDataSchema expects a PandasContainer for validation but got an object of type {type(data_container).__qualname__}")
        try:
            _ = self._schema.validate(data_container.data)
        except pa.errors.SchemaError as schema_err:
            # zero length multiindeces are currently not correctly evaluated by
            if schema_err.reason_code == pa.errors.SchemaErrorReason.WRONG_DATATYPE and len(
                    data_container.data) == 0 and isinstance(data_container.data.index, pd.MultiIndex) and isinstance(
                self.pandera_schema.index, pa.MultiIndex):
                for index_name, index_dtype in data_container.data.index.dtypes.items():
                    if index_name in self._schema.index.columns:
                        expected_dtype = self._schema.index.columns[index_name].dtype
                        if not (index_dtype == np.dtype(object) or expected_dtype == index_dtype or np.issubdtype(
                                index_dtype, expected_dtype)):
                            raise Exception(
                                f"Index column {index_name} was expected to be type '{expected_dtype}', but is '{index_dtype}")

        except Exception as e:
            raise DataSchemaConformityError("Pandera model validation failed") from e

        return True
