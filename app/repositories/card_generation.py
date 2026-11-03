import uuid
from typing import Any, Protocol

from sqlalchemy import select

from app.models import CardGeneration, GenerationStatus
from app.repositories.base import BaseRepository


class CardGenerationStore(Protocol):
    async def create_success(
        self, product_name: str | None, input_data: dict[str, Any], result: dict[str, Any], llm_model: str
    ) -> CardGeneration: ...

    async def create_failed(
        self, product_name: str | None, input_data: dict[str, Any], error_message: str, llm_model: str | None
    ) -> CardGeneration: ...

    async def get(self, entity_id: uuid.UUID) -> CardGeneration | None: ...

    async def list_recent(self, limit: int, offset: int) -> list[CardGeneration]: ...


class CardGenerationRepository(BaseRepository[CardGeneration]):
    model = CardGeneration

    async def create_success(
        self, product_name: str | None, input_data: dict[str, Any], result: dict[str, Any], llm_model: str
    ) -> CardGeneration:
        return await self.add(
            CardGeneration(
                product_name=product_name,
                input_data=input_data,
                status=GenerationStatus.SUCCESS,
                result=result,
                llm_model=llm_model,
            )
        )

    async def create_failed(
        self, product_name: str | None, input_data: dict[str, Any], error_message: str, llm_model: str | None
    ) -> CardGeneration:
        return await self.add(
            CardGeneration(
                product_name=product_name,
                input_data=input_data,
                status=GenerationStatus.FAILED,
                error_message=error_message,
                llm_model=llm_model,
            )
        )

    async def list_recent(self, limit: int = 20, offset: int = 0) -> list[CardGeneration]:
        stmt = select(CardGeneration).order_by(CardGeneration.created_at.desc()).limit(limit).offset(offset)
        return list((await self._session.scalars(stmt)).all())
