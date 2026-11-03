import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from app.llm.base import ChatMessage
from app.models import CardGeneration, GenerationStatus
from app.schemas.product import ProductInput

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "input"


class FakeLLM:
    model_name = "fake/model"

    def __init__(self, responses: list[str | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[list[ChatMessage]] = []

    async def complete(self, messages: list[ChatMessage]) -> str:
        self.calls.append(messages)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class InMemoryStore:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, CardGeneration] = {}

    async def _save(self, **fields: Any) -> CardGeneration:
        generation = CardGeneration(id=uuid.uuid4(), **fields)
        self.items[generation.id] = generation
        return generation

    async def create_success(self, product_name, input_data, result, llm_model):
        return await self._save(
            product_name=product_name, input_data=input_data, result=result,
            llm_model=llm_model, status=GenerationStatus.SUCCESS,
        )

    async def create_failed(self, product_name, input_data, error_message, llm_model):
        return await self._save(
            product_name=product_name, input_data=input_data, error_message=error_message,
            llm_model=llm_model, status=GenerationStatus.FAILED,
        )

    async def get(self, entity_id):
        return self.items.get(entity_id)

    async def list_recent(self, limit, offset):
        return list(self.items.values())[offset : offset + limit]


@pytest.fixture
def manometer() -> ProductInput:
    return ProductInput.model_validate_json((EXAMPLES / "01_manometer_dm02.json").read_text(encoding="utf-8"))


@pytest.fixture
def transmitter() -> ProductInput:
    return ProductInput.model_validate_json((EXAMPLES / "02_pressure_transmitter.json").read_text(encoding="utf-8"))


def make_draft(**overrides: Any) -> str:
    draft = {
        "seo_title": "Манометр показывающий DM 02 Манотомь 0–1,6 МПа",
        "seo_description": "Манометр показывающий DM 02 предназначен для измерения избыточного давления. " * 12,
        "search_queries": ["манометр dm 02", "манометр манотомь", "манометр 1,6 мпа"],
        "commercial": {"target_audience": ["службы ЖКХ"], "tasks": ["контроль давления в трубопроводах"]},
        "extracted_specs": [],
    }
    draft.update(overrides)
    return json.dumps(draft, ensure_ascii=False)
