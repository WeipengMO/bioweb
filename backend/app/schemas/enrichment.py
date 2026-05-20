from pydantic import BaseModel, Field


class OraRequest(BaseModel):
    genes: list[str] = Field(min_length=1, examples=[["TP53", "MDM2", "CDKN1A"]])
    up_genes: list[str] = Field(default_factory=list)
    down_genes: list[str] = Field(default_factory=list)
    background_genes: list[str] = Field(default_factory=list)
    collections: list[str] = Field(default=["hallmark", "kegg_pathways"], min_length=1)
    min_overlap: int = Field(default=2, ge=1)
    top_n: int = Field(default=10, ge=1, le=100)
    fdr_threshold: float | None = Field(default=None, ge=0, le=1)


class GseaGeneScore(BaseModel):
    gene: str
    score: float


class GseaRequest(BaseModel):
    rankings: list[GseaGeneScore] = Field(min_length=2)
    collections: list[str] = Field(default=["hallmark", "kegg_pathways"], min_length=1)
    min_overlap: int = Field(default=5, ge=1)
    top_n: int = Field(default=10, ge=1, le=100)
    fdr_threshold: float | None = Field(default=None, ge=0, le=1)
