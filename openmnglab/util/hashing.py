import hashlib
import struct
from array import array
from mmap import mmap
from typing import Self
try:
    from quantities import Quantity
except ImportError as _:
    Quantity = None


class Hash:
    def __init__(self):
        self._hash = hashlib.sha3_224()

    def str(self, s: str) -> Self:
        self.update(s.encode("UTF8"))
        return self

    def int(self, i: int) -> Self:
        self.update(struct.pack("<q", i))
        return self

    def float(self, f: float) -> Self:
        self.update(struct.pack("<d", f))
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





