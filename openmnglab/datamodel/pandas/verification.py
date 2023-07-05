from __future__ import annotations

from typing import Optional, Any

import pandera as pa
from pandera.api.base.schema import BaseSchema
from pandera.api.pandas.array import ArraySchema
from pandera.api.pandas.types import PandasDtypeInputTypes
from pandera.dtypes import is_subdtype


class ComparisonError(Exception):
    def __init__(self, subject: str, base_val: Any, other_val: Any, reason: str = "not equal"):
        self.subject = subject
        self.base_val = base_val
        self.other_val = other_val
        self.reason = reason

    def __str__(self):
        return f"Failed comparison on subject {self.subject}: {self.reason} (base: {self.base_val}, other: {self.other_val})"


def compare_dtype(base: Optional[PandasDtypeInputTypes], other: Optional[PandasDtypeInputTypes]) -> bool:
    if base is not None and (other is None or not is_subdtype(other, base)):
        raise ComparisonError("datatype", base, other, reason="not a subtype")
    return True


def compare_baseschema(base: BaseSchema, other: BaseSchema) -> bool:
    if base.name is not None and (other.name is None or base.name != other.name):
        raise ComparisonError("name", base.name, other.name)
    return compare_dtype(base.dtype, other.dtype)


def compare_arrayschema(base: ArraySchema, other: ArraySchema) -> bool:
    if base.nullable != other.nullable:
        raise ComparisonError("nullability", base.nullable, other.nullable)
    if base.unique != other.unique:
        raise ComparisonError("unique elements", base.unique, other.unique)
    return compare_baseschema(base, other)


def compare_index(base: Optional[pa.Index | pa.MultiIndex], other: Optional[pa.Index | pa.MultiIndex]) -> bool:
    if base is None:
        return True
    if isinstance(base, pa.Index) and isinstance(other, pa.Index):
        return compare_arrayschema(base, other)
    if isinstance(base, pa.MultiIndex) and isinstance(other, pa.MultiIndex):
        return all(
            compare_arrayschema(base_i, other_i) for base_i, other_i in zip(base.indexes, other.indexes))
    if not isinstance(other, type(base)):
        raise ComparisonError("type", type(base), type(other))
    return True


def compare_column(base: pa.Column, other: pa.Column) -> bool:
    if base.required and not other.required:
        raise ComparisonError("required", base.required, other.required)
    return compare_arrayschema(base, other)


def compare_columns(base: Optional[dict[Any, pa.Column]], other: Optional[dict[Any, pa.Column]]) -> bool:
    if base is None:
        return True
    for key, column in base.items():
        if key not in other:
            raise ComparisonError("column", key, None, "exists")
        assert (compare_column(column, other[key]))
    return True


def compare_dataframe_schemas(base: pa.DataFrameSchema, other: pa.DataFrameSchema) -> bool:
    if base.ordered and not other.ordered:
        raise ComparisonError("ordered", base.ordered, other.ordered)
    if base.unique != other.unique:
        raise ComparisonError("uniqueness", base.unique, other.unique)
    return compare_baseschema(base, other) and \
        compare_index(base.index, other.index) and \
        compare_columns(base.columns, other.columns)


def compare_series_schemas(base: pa.SeriesSchema, other: pa.SeriesSchema) -> bool:
    return compare_arrayschema(base, other) and compare_index(base.index, other.index)


def compare_schemas(base, other) -> bool:
    if isinstance(base, pa.SeriesSchema):
        if not isinstance(other, pa.SeriesSchema):
            raise ComparisonError("schema type", type(base), type(other))
        return compare_series_schemas(base, other)
    elif isinstance(base, pa.DataFrameSchema):
        if not isinstance(other, pa.DataFrameSchema):
            raise ComparisonError("schema type", type(base), type(other))
        return compare_dataframe_schemas(base, other)
    raise TypeError("provided base schema is neither a DataFrameSchema, nor a SeriesSchema")
    return False