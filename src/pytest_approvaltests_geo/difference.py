from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import numpy as np
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
