import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.card import ProductCard


class CardGenerationShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_name: str | None
    status: str
    llm_model: str | None
    created_at: datetime


class CardGenerationRead(CardGenerationShort):
    card: ProductCard | None = None
    markdown: str | None = None
    error_message: str | None = None
