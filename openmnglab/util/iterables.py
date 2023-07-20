from typing import TypeVar, Type, Iterable, Sequence

T = TypeVar('T')


def ensure_iterable(inp: Iterable[T] | T | None, type: Type[T]) -> Iterable[T]:
    """
    Ensures that the input is an iterable of the given type.

    ..warning::
        Only works if :param:`inp` is either ``None``, of type :param:`type` or an iterable of said type (see checks)



    performs the following checks:

        1. :param:`inp` is ``None``: returns an empty tuple
        2. :param:`inp` is an instace of :param:`type`: returns a tuple with :param:`inp` as sole element
        3. return :param:`inp` without modification

    ..seealso::
        :func:`unpack_sequence` for the inverse operation for sequences


    :param inp: Iterable, a single item of type :param:`type` or ``None``
    :param type: Base type of data in :param:`inp`
    :return: An iterable of  element(s) from :param:`inp` or an empty tuple if :param:`inp`is ``None``
    """
    if inp is None:
        return tuple()
    elif isinstance(inp, type):
        return (inp,)
    else:
        return inp


def unpack_sequence(inp: Sequence[T]) -> Sequence[T] | T | None:
    """ Unpacks a sequence, based on the following conditions:

        1. :param:`inp` has no items: return ``None``
        2. :param:`inp` has one item: return that item
        3. :param:`inp` has more items: return :param:`inp`

    ..seealso::
        :func:`ensure_iterable` for the inverse operation

    :param inp: A sequence of items
    :return: ``None`` if :param:`inp` is empty, the single value of :param:`inp` or :param:`inp` if it contains more than one item
    """
    if len(inp) == 0:
        return None
    elif len(inp) == 1:
        return inp[0]
    else:
        return inp
