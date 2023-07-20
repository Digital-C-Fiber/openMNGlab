from typing import TypeVar, Type, Iterable, Literal

T = TypeVar('T')


def ensure_iterable(inp:  Iterable[T] | T | None, type: Type[T]) -> Iterable[T]:
    """
    Ensures that the input is an iterable of the given type.

    ..warning::
        Only works if :param:`inp` is either ``None``, of type :param:`type` or an iterable of said type (see checks)

    performs the following checks:

        1. :param:`inp` is ``None``: returns an empty tuple
        2. :param:`inp` is an instace of :param:`type`: returns a tuple with :param:`inp` as sole element
        3. return :param:`inp` without modification


    :param inp:
    :param type:
    :return:
    """
    if inp is None:
        return tuple()
    elif isinstance(inp, type):
        return (inp,)
    else:
        return inp
