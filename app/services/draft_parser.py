import json

from pydantic import ValidationError

from app.core.exceptions import LLMResponseError
from app.schemas.llm_draft import LLMCardDraft


def parse_draft(raw: str) -> LLMCardDraft:
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise LLMResponseError("В ответе модели не найден JSON-объект")
    try:
        return LLMCardDraft.model_validate(json.loads(raw[start : end + 1]))
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"Модель вернула некорректный JSON: {exc.msg}") from exc
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, err["loc"])) for err in exc.errors())
        raise LLMResponseError(f"JSON модели не соответствует схеме, проблемные поля: {fields}") from exc
