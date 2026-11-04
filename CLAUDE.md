# AI Product Helper

A service that generates a draft product card (measuring instruments) for a B2B store from a JSON with the device data. FastAPI + PostgreSQL + OpenRouter. This is a take-home assignment for an AI developer position: code quality and readability matter, not volume.

## Commands

- Tests (no DB or API key needed): `uv run pytest`
- Run everything: `docker compose up --build`; after editing `.env`, `docker compose up -d` is enough
- DB only, app locally: `docker compose up -d db`, then `uv run alembic upgrade head` and `uv run uvicorn app.main:app --reload`
- Dependencies: `uv add <package>` (`--dev` for dev dependencies); `requirements.txt` is not used
- Example outputs: `docker compose exec app python scripts/generate_examples.py` (writes to `examples/output/`)

## Architecture

Layers: `api` (routes, DI) → `services` (business logic) → `repositories` (DB access only) → `models`. Everything else: `schemas` (Pydantic), `llm` (the `LLMClient` contract and the OpenRouter client), `prompts`, `core` (settings, exceptions, logging, spec catalog), `db`.

- Services depend on protocols (`CardGenerationStore`, `LLMClient`), not on concrete classes. Dependencies are wired only in `app/api/dependencies.py`.
- Shared CRUD lives in `BaseRepository`; application errors inherit `AppError` (each class has a `status_code`) and are handled by a single handler.
- Principles: SOLID, KISS, DRY; one module, one responsibility.

## Core invariant: the model must not invent specifications

- The code (`KeySpecBuilder`) builds the specification list; the LLM writes only the texts. Anything missing is marked "данных нет" (no data).
- A specification found in the description is accepted only with a verbatim quote that is actually present in the text.
- `FactChecker` compares numbers in the generated texts against the input data; a response that fails `DraftValidator` is sent back to the model for correction (up to `GENERATION_MAX_ATTEMPTS`), and whatever remains goes into `warnings`.
- Any change to the prompt or the checks must not weaken this.

## Conventions

- No comments or docstrings in code (the user deliberately removed them). The only exception is `# noqa`.
- Logging only via `from loguru import logger`, with `{}` formatting, not `%s`.
- User-facing text and error messages are in Russian; identifiers are in English.
- Commits go to the `develop` branch, one per logical module, in the `feat(scope): ...` style. Do not add a `Co-Authored-By` line. Do not commit to `main`.
- Tests use `FakeLLM` and `InMemoryStore` from `tests/conftest.py`; new tests must not require a DB or network.

## Gotchas

- `.env` is in `.gitignore`; the user enters the OpenRouter key there themselves. Never commit or print it.
- Reasoning models (e.g. `liquid/lfm-*`) can return an empty `content`, and free `:free` models often answer 429. Recommend a regular instruct model.
- Development is on Windows: Docker Desktop may not be running; git warns about CRLF, which is normal.
- `core/spec_catalog.py` is shared by all instruments, so for a pressure gauge "питание" (power supply) will show "данных нет": a known limitation.
