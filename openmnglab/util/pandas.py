from typing import Iterable
import pandas as pd


def ensure_dataframe(inp: pd.Series | pd.DataFrame) -> pd.DataFrame:
    if isinstance(inp, pd.Series):
        return inp.to_frame()
    elif isinstance(inp, pd.DataFrame):
        return inp
    raise Exception(f"No conversion from type '{type(inp)}' to DataFrame")


def index_names(inp: pd.Index | pd.MultiIndex) -> Iterable[str]:
    """Iterates over all index names of the passed index or multiindex.
    :param inp: index or multiindex to yield the name(s) from
    :return: An iterable of all names of the passed index
    """
    if isinstance(inp, pd.MultiIndex):
        yield from inp.names
    elif isinstance(inp, pd.Index):
        yield inp.name
    else:
        raise TypeError("Passed index is neither a pandas index nor a pandas multiindex")

def iterdfcols(inp: pd.DataFrame) -> Iterable[tuple[str, pd.Series]]:
    for col_name in inp.columns:
        yield col_name, inp[col_name]
