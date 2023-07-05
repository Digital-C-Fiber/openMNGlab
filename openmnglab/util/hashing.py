import hashlib
import struct
from array import array
from mmap import mmap
from os import PathLike
from pathlib import Path
from typing import Self, Any

try:
    from quantities import Quantity
except ImportError as _:
    Quantity = None


class Hash:
    def __init__(self):
        self._hash = hashlib.sha3_224()

    def path(self, d: Path | PathLike | bytes | str) -> Self:
        d = str(d) if isinstance(d, (Path, PathLike)) else d
        if isinstance(d, str):
            return self.str(d)
        elif isinstance(d, bytes):
            return self.update(d)
        return self

    def str(self, s: str) -> Self:
        self.update(s.encode("UTF8"))
        return self

    def int(self, i: int) -> Self:
        self.update(struct.pack("<q", i))
        return self

    def float(self, f: float) -> Self:
        self.update(struct.pack("<d", f))
        return self

    def dict(self, d: dict, fail=True) -> Self:
        for k, v in d.items():
            self.dynamic(k, fail=fail)
            self.dynamic(v, fail=fail)
        return self



    def dynamic(self, v: Any, fail=True) -> Self:
        if isinstance(v, int):
            return self.int(v)
        elif isinstance(v, float):
            return self.float(v)
        elif isinstance(v, str):
            return self.str(v)
        elif isinstance(v, bool):
            return self.bool(v)
        elif isinstance(v, (bytes, bytearray, memoryview, array, mmap)):
            return self.update(v)
        elif isinstance(v, Quantity):
            return self.quantity(v)
        elif hasattr(v, "__hash__"):
            return self.update(v.__hash__())
        if fail:
            raise Exception(f"Could not hash type {type(v)}")
        else:
            self.int(id(v))
        return self

    def update(self, b: bytes | bytearray | memoryview | array | mmap) -> Self:
        self._hash.update(b)
        return self

    def digest(self) -> bytes:
        return self._hash.digest()

    def quantity(self, q: Quantity) -> Self:
        self.float(q.magnitude.item())
        self.str(str(q.units))
        return self

    def bool(self, b: bool) -> Self:
        int_repr = int(b)
        self.update(struct.pack("<q", int_repr))
        return self
