import hashlib
import struct
from array import array
from mmap import mmap


class Hash:
    def __init__(self):
        self.hash = hashlib.sha3_224()

    def str(self, s: str):
        self.update(s.encode("UTF8"))

    def int(self, i: int):
        self.update(struct.pack("<q", i))

    def update(self, b:  bytes | bytearray | memoryview | array | mmap):
        self.hash.update(b)

    def digest(self) -> bytes:
        return self.hash.digest()