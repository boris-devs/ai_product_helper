import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GenerationStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class CardGeneration(Base):
    __tablename__ = "card_generations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name: Mapped[str | None] = mapped_column(String(500))
    input_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    llm_model: Mapped[str | None] = mapped_column(String(200))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
