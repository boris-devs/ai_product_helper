from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions import AppError


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("{}: {}", type(exc).__name__, exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, **exc.details})


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    json_error = next((e for e in errors if e["type"] == "json_invalid"), None)
    if json_error:
        position = json_error["loc"][-1] if len(json_error["loc"]) > 1 else "?"
        message = json_error.get("ctx", {}).get("error", "ошибка синтаксиса")
        return JSONResponse(
            status_code=400,
            content={"detail": f"Некорректный JSON (позиция {position}): {message}"},
        )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Входные данные не соответствуют формату",
            "errors": [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]} for e in errors],
        },
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error("Необработанная ошибка")
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
