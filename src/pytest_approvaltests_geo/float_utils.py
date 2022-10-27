from dataclasses import dataclass
from typing import Mapping


@dataclass
class Tolerance:
    rel: float = 1e-09
    abs: float = 0.0

    def to_kwargs(self) -> Mapping:
        return dict(rtol=self.rel, atol=self.abs)
