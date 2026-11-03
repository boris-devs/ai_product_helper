from pydantic import BaseModel, Field

from app.schemas.card import CommercialBlock


class ExtractedSpec(BaseModel):
    name: str
    value: str
    source_quote: str


class LLMCardDraft(BaseModel):
    seo_title: str
    seo_description: str
    search_queries: list[str] = Field(default_factory=list)
    commercial: CommercialBlock = Field(default_factory=CommercialBlock)
    extracted_specs: list[ExtractedSpec] = Field(default_factory=list)
