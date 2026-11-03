import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_generator_service, get_history_service, get_input_analyzer
from app.models import CardGeneration
from app.schemas.api import CardGenerationRead, CardGenerationShort
from app.schemas.card import InputAnalysis, ProductCard
from app.schemas.product import ProductInput
from app.services.card_generator import CardGeneratorService
from app.services.card_history import CardHistoryService
from app.services.input_analyzer import InputAnalyzer
from app.services.markdown_renderer import render_card_markdown

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])

GeneratorDep = Annotated[CardGeneratorService, Depends(get_generator_service)]
HistoryDep = Annotated[CardHistoryService, Depends(get_history_service)]


def _to_read(generation: CardGeneration) -> CardGenerationRead:
    card = ProductCard.model_validate(generation.result) if generation.result else None
    return CardGenerationRead(
        **CardGenerationShort.model_validate(generation).model_dump(),
        card=card,
        markdown=render_card_markdown(generation.product_name, card) if card else None,
        error_message=generation.error_message,
    )


@router.post("/analyze", response_model=InputAnalysis, summary="Проверить полноту данных без вызова LLM")
async def analyze(product: ProductInput, analyzer: Annotated[InputAnalyzer, Depends(get_input_analyzer)]):
    return analyzer.analyze(product)


@router.post("", response_model=CardGenerationRead, status_code=status.HTTP_201_CREATED, summary="Сгенерировать карточку")
async def create_card(product: ProductInput, service: GeneratorDep):
    return _to_read(await service.generate(product))


@router.get("", response_model=list[CardGenerationShort], summary="История генераций")
async def list_cards(
    service: HistoryDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await service.list_recent(limit, offset)


@router.get("/{generation_id}", response_model=CardGenerationRead, summary="Карточка по id")
async def get_card(generation_id: uuid.UUID, service: HistoryDep):
    return _to_read(await service.get(generation_id))


@router.get("/{generation_id}/markdown", response_class=PlainTextResponse, summary="Карточка в Markdown")
async def get_card_markdown(generation_id: uuid.UUID, service: HistoryDep):
    read = _to_read(await service.get(generation_id))
    return PlainTextResponse(read.markdown or f"Генерация завершилась ошибкой: {read.error_message}", media_type="text/markdown")
