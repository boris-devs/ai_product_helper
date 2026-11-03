from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.llm.base import LLMClient
from app.repositories.card_generation import CardGenerationRepository
from app.services.card_generator import CardGeneratorService
from app.services.card_history import CardHistoryService
from app.services.draft_validator import DraftValidator
from app.services.input_analyzer import InputAnalyzer
from app.services.spec_builder import KeySpecBuilder


def get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client


def get_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> CardGenerationRepository:
    return CardGenerationRepository(session)


def get_input_analyzer() -> InputAnalyzer:
    return InputAnalyzer()


def get_generator_service(
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    repository: Annotated[CardGenerationRepository, Depends(get_repository)],
    analyzer: Annotated[InputAnalyzer, Depends(get_input_analyzer)],
) -> CardGeneratorService:
    return CardGeneratorService(
        llm=llm,
        repository=repository,
        analyzer=analyzer,
        validator=DraftValidator(),
        spec_builder=KeySpecBuilder(),
        max_attempts=get_settings().generation_max_attempts,
    )


def get_history_service(
    repository: Annotated[CardGenerationRepository, Depends(get_repository)],
) -> CardHistoryService:
    return CardHistoryService(repository)
