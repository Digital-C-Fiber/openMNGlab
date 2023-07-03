from typing import Mapping, TypeVar, Optional, Iterable, Callable, MutableMapping

_KT = TypeVar('_KT')
_VT_co = TypeVar('_VT_co', covariant=True)


def get_any_key(map: Mapping[_KT, _VT_co], *keys: _KT) -> Optional[_KT]:
    """
    Returns any of the given keys if they exist in the mapping
    :param map: mapping in which the keys should be contained
    :param keys: key to check for in the mapping
    :return: anyone of the given keys that exists or None if no key exists
    """
    for key in keys:
        if key in map.keys():
            return key
    return None


def get_and_incr(dct: dict[_KT, int], key: _KT) -> int:
    n = dct.get(key, 0)
    dct[key] = n + 1
    return n


def get_any(map: Mapping[_KT, _VT_co], *keys: _KT, default: Optional[_VT_co] = None) -> Optional[_VT_co]:
    """
    Gets any value mapped by one of the existing keys if it exists in the mapping
    :param map: the mapping to work on
    :param keys: keys to look for in the mapping
    :param default: default value to return when none of the given keys exist in the mapping
    :return: an existing value of any of the given keys or the default
    """
    key = get_any_key(map, *keys)
    if key is not None:
        return map[key]
    return default


def setfactory(map: MutableMapping[_KT, _VT_co], key: _KT, factory: Callable[[], _VT_co]) -> _VT_co:
    """
    Equivalant of dict.setdefault with a factory instead of a value.
    :param map: mapping to work on
    :param key: key to look for
    :param factory: factory to create a new value
    :return: The value for the given key
    """
    v = map.get(key)
    if v is None:
        v = factory()
        map[key] = v
    return v


def group_dict(vals: Iterable[_VT_co], key_getter: Callable[[_VT_co], _KT]) -> dict[_KT, list[_VT_co]]:
    """
    groups the given vals in a dictionary by the key returned from the key getter. More robust as the groupby variant of
    itertools, as it doesn't require the data to be sorted first.
    :param vals: values to be grouped
    :param key_getter: function that produces the key the given value should be grouped by
    :return: a dictionary containing the grouped values
    """
    d: dict[_KT, list[_VT_co]] = dict()
    for v in vals:
        setfactory(d, key_getter(v), list).append(v)
    return d
