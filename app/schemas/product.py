from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

SpecValue = str | int | float | bool | None


class ProductInput(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "name": "Манометр показывающий DM 02",
                "manufacturer": "Манотомь",
                "specs": {"диапазон измерений": "0–1,6 МПа", "класс точности": "1,5"},
                "description": "Прибор предназначен для измерения избыточного давления...",
            }
        },
    )

    name: str | None = None
    manufacturer: str | None = None
    specs: dict[str, SpecValue] = Field(default_factory=dict)
    description: str | None = None

    @field_validator("name", "manufacturer", "description", mode="before")
    @classmethod
    def _blank_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("specs", mode="before")
    @classmethod
    def _normalize_specs(cls, value: Any) -> Any:
        if value is None:
            return {}
        if not isinstance(value, dict):
            return value
        normalized: dict[str, SpecValue] = {}
        for key, raw in value.items():
            key = str(key).strip()
            if not key:
                continue
            if isinstance(raw, str):
                raw = raw.strip() or None
            normalized[key] = raw
        return normalized

    @property
    def filled_specs(self) -> dict[str, str]:
        return {key: str(value) for key, value in self.specs.items() if value is not None}

    @property
    def empty_spec_keys(self) -> list[str]:
        return [key for key, value in self.specs.items() if value is None]
