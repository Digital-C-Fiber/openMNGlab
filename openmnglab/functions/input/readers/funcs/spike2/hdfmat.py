from itertools import chain
from typing import Mapping, Iterator

import h5py
import numpy as np


class HDFMatGroup(Mapping):
    def __init__(self, h5group: h5py.Group):
        self.h5group = h5group

    @staticmethod
    def _parse_dataset(h5ds: h5py.Dataset, *slicers: slice) -> np.ndarray | tuple[str]:
        assert (len(slicers) <= len(h5ds.shape))

        def transposed_slicers(norm_slicers: tuple[slice], total_levels: int):
            # when we transpose a matrix, we have to reverse the slicers for it (since the last level will be returned as the first one)
            return tuple(chain((slice(None, None, None) for _ in range(total_levels - len(norm_slicers))),
                               reversed(norm_slicers)))

        mat_class = h5ds.attrs.get("MATLAB_class").decode("utf-8")
        if h5ds.attrs.get("MATLAB_empty", 0) == 1:
            if mat_class == "char":
                return tuple()
            return np.empty(tuple(0 for _ in h5ds.shape), dtype=h5ds.dtype)
        elif mat_class == "char":
            transposed = h5ds[transposed_slicers(slicers, len(h5ds.shape))].transpose()
            return tuple(by.tobytes().decode("utf-16").split("\x00", 1)[0] for by in transposed)
        if len(h5ds.shape) > 1 and h5ds.shape[0] > 1:
            return h5ds[transposed_slicers(slicers, len(h5ds.shape))].transpose()
        return h5ds[slicers]

    def __len__(self) -> int:
        return self.h5group.__len__()

    def __iter__(self) -> Iterator:
        return iter(self.h5group.keys())

    def get(self, key, *slicers: slice, default=None):
        dataset = self.h5group.get(key, default=None)
        if dataset is None:
            return default
        return self._parse_dataset(dataset, *slicers)

    def get_array(self, key, slicer=slice(None, None, None), default=None):
        values = self.get(key, slice(None, None, None), slicer, default=None)
        if values is None:
            return default
        return values.flatten()

    def __contains__(self, item):
        return self.h5group.__contains__(item)

    def __getitem__(self, item) -> np.ndarray | float | str | tuple[str] | None:
        if item not in self:
            raise KeyError(f"key {item} not in hdfmatgroup")
        return self.get(item)


class HDFMatFile(Mapping):

    def __len__(self) -> int:
        return len(self.h5file)

    def __iter__(self) -> Iterator:
        return iter(self.h5file.keys())

    def __init__(self, *args, **kwargs):
        self.h5file = h5py.File(*args, **kwargs)

    def __enter__(self):
        self.h5file.__enter__()
        return self

    def __exit__(self, *args):
        return self.h5file.__exit__(*args)

    def __getitem__(self, item) -> HDFMatGroup:
        item = self.h5file[item]
        return HDFMatGroup(item)
