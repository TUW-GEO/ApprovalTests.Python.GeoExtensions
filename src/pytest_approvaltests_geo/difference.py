from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import numpy as np
import xarray as xr
from numpy.typing import ArrayLike


class DiffType(Enum):
    TAGS = 0
    PIXEL_STATS = 1,
    PIXEL = 2,
    DATASET = 3


DIFF_TYPE_PREFIXES = {
    DiffType.TAGS: "Differences in meta data:\n",
    DiffType.PIXEL_STATS: "Differences in pixel data:\n",
    DiffType.PIXEL: "Differences in pixels:\n",
    DiffType.DATASET: "Differences in dataset:\n",
}


@dataclass
class Difference:
    description: str
    type: DiffType


@dataclass
class Stats:
    min: float = 0
    max: float = 0
    mean: float = 0
    median: float = 0

    def __str__(self):
        return ', '.join([f"{n}={getattr(self, n)}" for n in self.__dict__])

    @property
    def is_empty(self):
        return self.min == 0 and self.max == 0


def calculate_pixel_diff_stats(approved_pixels: ArrayLike, received_pixels: ArrayLike) -> Stats:
    diff_pixels = np.abs(received_pixels - approved_pixels)
    diff_min = np.nanmin(diff_pixels).item()
    diff_max = np.nanmax(diff_pixels).item()
    diff_mean = np.nanmean(diff_pixels).item()
    diff_median = np.nanmedian(diff_pixels).item()
    return Stats(diff_min, diff_max, diff_mean, diff_median)


def print_diffs(diffs: Sequence[Difference]) -> None:
    for diff in diffs:
        print(f"{DIFF_TYPE_PREFIXES[diff.type]}{diff.description}")


def add_common_meta_data_diffs(a, b, diffs):
    a_data_vars = set(getattr(a, 'data_vars', {}))
    b_data_vars = set(getattr(b, 'data_vars', {}))
    common_data_vars = a_data_vars & b_data_vars
    a_coords = set(b.coords)
    b_coords = set(a.coords)
    common_coords = a_coords & b_coords
    common_sub_arrays = list(common_data_vars) + list(common_coords)
    diff_attrs = xr.testing.formatting.diff_attrs_repr(a.attrs, b.attrs, 'identical')
    if diff_attrs:
        diffs.append(Difference(diff_attrs, DiffType.TAGS))
    for name in common_sub_arrays:
        d = xr.testing.formatting.diff_attrs_repr(a[name].attrs, b[name].attrs, 'identical')
        if d:
            diffs.append(Difference(d, DiffType.TAGS))

    return diffs
