from typing import Iterable

import pandas as pd


def ensure_dataframe(inp: pd.Series | pd.DataFrame) -> pd.DataFrame:
    if isinstance(inp, pd.Series):
        return inp.to_frame()
    elif isinstance(inp, pd.DataFrame):
        return inp
    raise Exception(f"No conversion from type '{type(inp)}' to DataFrame")


def iterdfcols(inp: pd.DataFrame) -> Iterable[tuple[str, pd.Series]]:
    for col_name in inp.columns:
        yield col_name, inp[col_name]
