import asyncio
from dataclasses import asdict
from typing import Any

import httpx
from loguru import logger

from app.core.exceptions import LLMConfigError, LLMError, LLMResponseError
from app.llm.base import ChatMessage

RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
        max_retries: int,
        json_mode: bool,
        app_name: str,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_retries = max_retries
        self._json_mode = json_mode
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            headers={"X-Title": app_name},
        )

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, messages: list[ChatMessage]) -> str:
        self._ensure_configured()
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [asdict(message) for message in messages],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if self._json_mode:
            payload["response_format"] = {"type": "json_object"}
        return self._extract_content(await self._post_with_retries(payload))

    async def aclose(self) -> None:
        await self._http.aclose()

    def _ensure_configured(self) -> None:
        required = {"OPENROUTER_API_KEY": self._api_key, "OPENROUTER_MODEL": self._model}
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise LLMConfigError(f"LLM не настроена: задайте {', '.join(missing)} в .env")

    async def _post_with_retries(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        last_error = "неизвестная ошибка"
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._http.post("/chat/completions", json=payload, headers=headers)
            except httpx.TimeoutException:
                last_error = "превышено время ожидания ответа"
            except httpx.TransportError as exc:
                last_error = f"сетевая ошибка: {exc}"
            else:
                if response.status_code in RETRYABLE_STATUSES:
                    last_error = f"HTTP {response.status_code}: {self._error_text(response)}"
                elif response.status_code in (401, 403):
                    raise LLMConfigError(f"OpenRouter отклонил ключ (HTTP {response.status_code}): {self._error_text(response)}")
                elif response.status_code >= 400:
                    raise LLMError(f"OpenRouter вернул HTTP {response.status_code}: {self._error_text(response)}")
                else:
                    return self._parse_json(response)

            if attempt < self._max_retries:
                delay = 2**attempt
                logger.warning("OpenRouter: {}, повтор через {} с", last_error, delay)
                await asyncio.sleep(delay)
        raise LLMError(f"OpenRouter недоступен после {self._max_retries + 1} попыток: {last_error}")

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise LLMResponseError("OpenRouter вернул не-JSON ответ") from exc

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        if "error" in data:
            raise LLMError(f"Ошибка провайдера модели: {data['error']}")
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError("В ответе OpenRouter нет choices[0].message.content") from exc
        if not content or not content.strip():
            finish_reason = choice.get("native_finish_reason") or choice.get("finish_reason")
            has_reasoning = bool(choice["message"].get("reasoning"))
            raise LLMResponseError(
                f"Модель вернула пустой ответ (finish_reason={finish_reason}, "
                f"рассуждения={'есть' if has_reasoning else 'нет'}, модель={data.get('model')})"
            )
        return content

    @staticmethod
    def _error_text(response: httpx.Response) -> str:
        try:
            error = response.json().get("error", {})
        except ValueError:
            return response.text[:300]
        if not isinstance(error, dict):
            return str(error)
        text = error.get("message", str(error))
        metadata = error.get("metadata") or {}
        details = []
        if metadata.get("provider_name"):
            details.append(f"провайдер {metadata['provider_name']}")
        if metadata.get("raw"):
            details.append(f"ответ провайдера: {str(metadata['raw'])[:300]}")
        return f"{text} ({'; '.join(details)})" if details else text
