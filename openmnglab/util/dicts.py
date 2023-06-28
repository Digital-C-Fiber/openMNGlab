from typing import Mapping, TypeVar, Optional

_KT = TypeVar('_KT')
_VT_co = TypeVar('_VT_co', covariant=True)


def get_any_key(dct: Mapping[_KT, _VT_co], *keys: _KT) -> Optional[_KT]:
    for key in keys:
        candidate = dct.get(key)
        if candidate is not None:
            return candidate
    return None


def get_any(dct: Mapping[_KT, _VT_co], *keys: _KT, default: Optional[_VT_co] = None) -> Optional[_VT_co]:
    key = get_any_key(dct, *keys)
    if key is not None:
        return dct[key]
    return default
