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
    min: float
    max: float
    mean: float
    median: float

    def __str__(self):
        return ', '.join([f"{n}={getattr(self, n)}" for n in self.__dict__])


def calculate_pixel_diff_stats(approved_pixels: ArrayLike, received_pixels: ArrayLike) -> Stats:
    diff_pixels = np.abs(received_pixels - approved_pixels)
    diff_min = np.nanmin(diff_pixels).item()
    diff_max = np.nanmax(diff_pixels).item()
    diff_mean = np.nanmean(diff_pixels).item()
    diff_median = np.nanmedian(diff_pixels).item()
    return Stats(diff_min, diff_max, diff_mean, diff_median)


def shorten_pixel_diffs(diffs):
    n = len(diffs)
    if n > 10:
        half = n // 2
        diffs = diffs[:3] + ["..."] + diffs[half - 1:half + 2] + ["..."] + diffs[-3:]
    return diffs


def print_diffs(diffs: Sequence[Difference]) -> None:
    for diff in diffs:
        print(f"{DIFF_TYPE_PREFIXES[diff.type]}{diff.description}")
