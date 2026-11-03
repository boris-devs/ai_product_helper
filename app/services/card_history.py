import uuid

from app.core.exceptions import NotFoundError
from app.models import CardGeneration
from app.repositories.card_generation import CardGenerationStore


class CardHistoryService:
    def __init__(self, repository: CardGenerationStore) -> None:
        self._repository = repository

    async def get(self, generation_id: uuid.UUID) -> CardGeneration:
        generation = await self._repository.get(generation_id)
        if generation is None:
            raise NotFoundError(f"Генерация {generation_id} не найдена")
        return generation

    async def list_recent(self, limit: int, offset: int) -> list[CardGeneration]:
        return await self._repository.list_recent(limit, offset)
