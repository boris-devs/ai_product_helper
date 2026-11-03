from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.errors import register_error_handlers
from app.api.routes.cards import router as cards_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.llm.openrouter import OpenRouterClient

STATIC_DIR = Path(__file__).parent / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.llm_client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        json_mode=settings.llm_json_mode,
        app_name=settings.app_name,
    )
    logger.info("Сервис запущен, модель LLM: {}", settings.openrouter_model or "не задана")
    yield
    await app.state.llm_client.aclose()
    await engine.dispose()
    logger.info("Сервис остановлен")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(cards_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health", tags=["service"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
