from dataclasses import dataclass
from enum import Enum


class DiffType(Enum):
    TAGS = 0
    PIXEL_STATS = 1,
    PIXEL = 2,


@dataclass
class Difference:
    description: str
    type: DiffType
