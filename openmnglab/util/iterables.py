from typing import TypeVar, Type, Iterable, Sequence, Callable

T = TypeVar('T')

def ensure_sequence(inp: Iterable[T] | T | None, type: Type[T], sequence_constructor: Callable[[Iterable[T]], Sequence[T]] = tuple) -> Sequence[T]:
    """Ensures that the input is a sequence.

    .. seealso::
        :func:`ensure_iterable` for a varaint of this function which will return an interable

    .. seealso::
        :func:`unpack_sequence` for the inverse operation

    Run checks:

        1. ``inp`` is ``None``: returns an empty tuple
        2. ``inp`` is an instace of ``type``: returns a tuple with ``inp`` as sole element
        3. ``inp`` implements type ``Sequence``: return ``inp`` without modification
        4. Attempts to convert ``inp`` to a ``Sequence`` by invoking ``sequence_constructor``



    :param inp: Value to convert to a sequence
    :param type: Type of the value(s) passed to ``inp``
    :param sequence_constructor: Callable used to convert ``inp`` to a ``Sequence``, defaults to ``tuple``.
    :return: A sequence of values
    """
    if inp is None:
        return tuple()
    elif isinstance(inp, type):
        return (inp,)
    elif isinstance(inp, Sequence):
        return inp
    else:
        return sequence_constructor(inp)

def ensure_iterable(inp: Iterable[T] | T | None, type: Type[T]) -> Iterable[T]:
    """Ensures that the input is an iterable of the given type.

    .. warning::
        Only works if ``inp`` is either ``None``, of type ``type`` or an iterable of said type (see checks)

    .. seealso::
        :func:`ensure_sequence` for a varaint of this function which will ensure a sequence
        (including automatic conversion from iterable to tuple)

    .. seealso::
        :func:`unpack_sequence` for the inverse operation for sequences


    performs the following checks:

        1. ``inp`` is ``None``: returns an empty tuple
        2. ``inp`` is an instace of ``type``: returns a tuple with ``inp`` as sole element
        3. return ``inp`` without modification


    :param inp: Iterable, a single item of type ``type`` or ``None``
    :param type: Base type of data in ``inp``
    :return: An iterable of  element(s) from ``inp`` or an empty tuple if ``inp`` is ``None``
    """
    if inp is None:
        return tuple()
    elif isinstance(inp, type):
        return (inp,)
    else:
        return inp


def unpack_sequence(inp: Sequence[T]) -> Sequence[T] | T | None:
    """Unpacks a sequence, based on the following conditions:
    .. seealso::
        :func:`ensure_iterable` for the inverse operation

    1. ``inp`` has no items: return ``None``
    2. ``inp`` has one item: return that item
    3. ``inp`` has more items: return ``inp``


    :param inp: A sequence of items
    :return: ``None`` if ``inp`` is empty, the single value of ``inp`` or ``inp`` if it contains more than one item
    """
    if len(inp) == 0:
        return None
    elif len(inp) == 1:
        return inp[0]
    else:
        return inp
