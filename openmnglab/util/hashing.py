import hashlib
import struct
from array import array
from mmap import mmap
from typing import Self


class Hash:
    def __init__(self):
        self.hash = hashlib.sha3_224()

    def str(self, s: str) -> Self:
        self.update(s.encode("UTF8"))
        return self

    def int(self, i: int) -> Self:
        self.update(struct.pack("<q", i))
        return self

    def update(self, b: bytes | bytearray | memoryview | array | mmap) -> Self:
        self.hash.update(b)
        return self

    def digest(self) -> bytes:
        return self.hash.digest()
