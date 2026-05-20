from dataclasses import dataclass
from typing import Literal

GroupingMethod = Literal["median", "percentile", "optimal"]


@dataclass(frozen=True)
class AnalysisTable:
    records: list[dict]

