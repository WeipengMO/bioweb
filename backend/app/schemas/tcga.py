from enum import Enum

from pydantic import BaseModel, Field


class GroupingMethod(str, Enum):
    median = "median"
    percentile = "percentile"
    optimal = "optimal"


class TcgaBaseRequest(BaseModel):
    project: str = Field(examples=["TCGA-LUAD"])
    genes: list[str] = Field(min_length=1, examples=[["TP53"], ["CD3D", "CD3E"]])


class SurvivalRequest(TcgaBaseRequest):
    grouping_method: GroupingMethod = GroupingMethod.median
    low_percentile: float | None = Field(default=None, ge=0, le=100)
    high_percentile: float | None = Field(default=None, ge=0, le=100)
    survival_metric: str = "OS"
    axis_unit: str = "days"


class CorrelationRequest(TcgaBaseRequest):
    target_genes: list[str] = Field(min_length=1, examples=[["PDCD1", "CD274"]])
    method: str = "pearson"


class TumorNormalRequest(TcgaBaseRequest):
    show_points: bool = True


class ExpressionRequest(TcgaBaseRequest):
    show_points: bool = True
    sort_by: str = "alphabetical"
