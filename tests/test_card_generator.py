import pytest

from app.core.exceptions import InsufficientDataError, LLMError
from app.models import GenerationStatus
from app.schemas.card import ProductCard
from app.schemas.product import ProductInput
from app.services.card_generator import CardGeneratorService
from app.services.draft_validator import DraftValidator
from app.services.input_analyzer import InputAnalyzer
from app.services.spec_builder import KeySpecBuilder
from tests.conftest import FakeLLM, InMemoryStore, make_draft


def make_service(llm: FakeLLM, store: InMemoryStore, max_attempts: int = 2) -> CardGeneratorService:
    return CardGeneratorService(llm, store, InputAnalyzer(), DraftValidator(), KeySpecBuilder(), max_attempts)


async def test_generates_and_saves_card(manometer):
    store = InMemoryStore()

    generation = await make_service(FakeLLM([make_draft()]), store).generate(manometer)

    card = ProductCard.model_validate(generation.result)
    assert generation.status == GenerationStatus.SUCCESS
    assert {"name": "питание", "value": "данных нет", "source": "missing"} in [s.model_dump() for s in card.key_specs]
    assert card.warnings == []


async def test_asks_model_to_fix_and_uses_corrected_answer(manometer):
    llm = FakeLLM(["не json", make_draft(seo_title="Манометр DM 02 на 4 МПа"), make_draft()])

    generation = await make_service(llm, InMemoryStore(), max_attempts=3).generate(manometer)

    assert len(llm.calls) == 3
    assert "4" in llm.calls[2][-1].content
    assert ProductCard.model_validate(generation.result).warnings == []


async def test_unresolved_issues_become_warnings(manometer):
    long_title = "Манометр показывающий DM 02 Манотомь " * 3

    generation = await make_service(FakeLLM([make_draft(seo_title=long_title)]), InMemoryStore(), 1).generate(manometer)

    card = ProductCard.model_validate(generation.result)
    assert len(card.seo_title) <= 70
    assert any("обрезан" in w for w in card.warnings)


async def test_llm_failure_is_saved_and_reraised(manometer):
    store = InMemoryStore()

    with pytest.raises(LLMError):
        await make_service(FakeLLM([LLMError("timeout")]), store).generate(manometer)

    [saved] = store.items.values()
    assert saved.status == GenerationStatus.FAILED and saved.error_message == "timeout"


async def test_insufficient_data_does_not_call_llm():
    llm = FakeLLM([])

    with pytest.raises(InsufficientDataError) as exc:
        await make_service(llm, InMemoryStore()).generate(ProductInput(manufacturer="Манотомь"))

    assert llm.calls == []
    assert exc.value.details["missing_fields"][0]["field"] == "name"
