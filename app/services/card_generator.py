from loguru import logger

from app.core.exceptions import InsufficientDataError, LLMError, LLMResponseError
from app.llm.base import ChatMessage, LLMClient
from app.models import CardGeneration
from app.prompts.product_card import build_correction_message, build_messages
from app.repositories.card_generation import CardGenerationStore
from app.schemas.card import CommercialBlock, InputAnalysis, ProductCard
from app.schemas.llm_draft import LLMCardDraft
from app.schemas.product import ProductInput
from app.services.draft_parser import parse_draft
from app.services.draft_validator import TITLE_MAX, DraftValidator
from app.services.fact_checker import FactChecker
from app.services.input_analyzer import InputAnalyzer
from app.services.spec_builder import KeySpecBuilder


class CardGeneratorService:
    def __init__(
        self,
        llm: LLMClient,
        repository: CardGenerationStore,
        analyzer: InputAnalyzer,
        validator: DraftValidator,
        spec_builder: KeySpecBuilder,
        max_attempts: int,
    ) -> None:
        self._llm = llm
        self._repository = repository
        self._analyzer = analyzer
        self._validator = validator
        self._spec_builder = spec_builder
        self._max_attempts = max(1, max_attempts)

    async def generate(self, product: ProductInput) -> CardGeneration:
        analysis = self._analyzer.analyze(product)
        if not analysis.can_generate:
            raise InsufficientDataError(
                "Недостаточно данных для генерации карточки",
                {"missing_fields": [issue.model_dump() for issue in analysis.missing_fields]},
            )

        input_data = product.model_dump(mode="json")
        try:
            draft, unresolved = await self._request_draft(product, analysis)
        except LLMError as exc:
            logger.warning("Генерация «{}» не удалась: {}", product.name, exc.message)
            await self._repository.create_failed(product.name, input_data, exc.message, self._llm.model_name or None)
            raise

        card = self._assemble(product, analysis, draft, unresolved)
        generation = await self._repository.create_success(
            product.name, input_data, card.model_dump(mode="json"), self._llm.model_name
        )
        logger.info("Карточка «{}» сохранена: id={}, предупреждений {}", product.name, generation.id, len(card.warnings))
        return generation

    async def _request_draft(self, product: ProductInput, analysis: InputAnalysis) -> tuple[LLMCardDraft, list[str]]:
        fact_checker = FactChecker.from_product(product)
        messages = build_messages(product, analysis.missing_spec_groups + product.empty_spec_keys)

        for attempt in range(1, self._max_attempts + 1):
            is_last = attempt == self._max_attempts
            raw = await self._llm.complete(messages)
            try:
                draft = parse_draft(raw)
            except LLMResponseError as exc:
                if is_last:
                    raise
                issues = [exc.message]
            else:
                issues = self._validator.review(draft, fact_checker)
                if not issues or is_last:
                    return draft, issues

            logger.info("Попытка {}: ответ модели отправлен на исправление: {}", attempt, issues)
            messages = [*messages, ChatMessage("assistant", raw), build_correction_message(issues)]
        raise AssertionError("unreachable")

    def _assemble(
        self, product: ProductInput, analysis: InputAnalysis, draft: LLMCardDraft, unresolved: list[str]
    ) -> ProductCard:
        specs = self._spec_builder.build(product, draft.extracted_specs, analysis.missing_spec_groups)
        resolved_groups = set(analysis.missing_spec_groups) - set(specs.still_missing)
        missing_fields = [i for i in analysis.missing_fields if i.field.removeprefix("specs.") not in resolved_groups]

        warnings = [f"Требует ручной проверки: {issue}" for issue in unresolved] + specs.warnings
        title = draft.seo_title.strip()
        if len(title) > TITLE_MAX:
            title = title[:TITLE_MAX].rsplit(" ", 1)[0].rstrip(" ,.-—")
            warnings.append(f"SEO-заголовок обрезан до {TITLE_MAX} символов")

        return ProductCard(
            seo_title=title,
            seo_description=draft.seo_description.strip(),
            key_specs=specs.key_specs,
            search_queries=list(dict.fromkeys(q.strip().lower() for q in draft.search_queries if q.strip())),
            commercial=CommercialBlock(
                target_audience=[s.strip() for s in draft.commercial.target_audience if s.strip()],
                tasks=[s.strip() for s in draft.commercial.tasks if s.strip()],
            ),
            missing_fields=missing_fields,
            warnings=warnings,
        )
