from enum import StrEnum

from pydantic import BaseModel, Field


class SpecSource(StrEnum):
    INPUT = "specs"
    DESCRIPTION = "description"
    MISSING = "missing"


class KeySpec(BaseModel):
    name: str
    value: str
    source: SpecSource = Field(description="specs — из входных характеристик, description — из текста, missing — нет данных")


class FieldIssue(BaseModel):
    field: str
    message: str


class InputAnalysis(BaseModel):
    missing_fields: list[FieldIssue]
    missing_spec_groups: list[str]
    can_generate: bool


class CommercialBlock(BaseModel):
    target_audience: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)


class ProductCard(BaseModel):
    seo_title: str
    seo_description: str
    key_specs: list[KeySpec]
    search_queries: list[str]
    commercial: CommercialBlock
    missing_fields: list[FieldIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
