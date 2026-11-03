import re
from decimal import Decimal, InvalidOperation

from app.schemas.product import ProductInput

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


def extract_numbers(text: str) -> set[str]:
    numbers = set()
    for raw in NUMBER_RE.findall(text):
        try:
            numbers.add(format(Decimal(raw.replace(",", ".")).normalize(), "f"))
        except InvalidOperation:
            continue
    return numbers


def normalize_text(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").split())


class FactChecker:
    def __init__(self, source_texts: list[str]) -> None:
        self._allowed = set().union(*(extract_numbers(text) for text in source_texts))

    @classmethod
    def from_product(cls, product: ProductInput) -> "FactChecker":
        texts = [product.name or "", product.manufacturer or "", product.description or ""]
        texts += [f"{key} {value}" for key, value in product.filled_specs.items()]
        return cls(texts)

    def unknown_numbers(self, text: str) -> list[str]:
        return sorted(extract_numbers(text) - self._allowed)
