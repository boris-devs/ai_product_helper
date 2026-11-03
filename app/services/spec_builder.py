from dataclasses import dataclass, field

from app.core.spec_catalog import NO_DATA, find_spec_group
from app.schemas.card import KeySpec, SpecSource
from app.schemas.llm_draft import ExtractedSpec
from app.schemas.product import ProductInput
from app.services.fact_checker import extract_numbers, normalize_text


@dataclass
class SpecBuildResult:
    key_specs: list[KeySpec]
    still_missing: list[str]
    warnings: list[str] = field(default_factory=list)


class KeySpecBuilder:
    def build(
        self, product: ProductInput, extracted: list[ExtractedSpec], missing_groups: list[str]
    ) -> SpecBuildResult:
        specs = [KeySpec(name=k, value=v, source=SpecSource.INPUT) for k, v in product.filled_specs.items()]
        specs += [KeySpec(name=k, value=NO_DATA, source=SpecSource.MISSING) for k in product.empty_spec_keys]

        known_names = {normalize_text(k) for k in product.specs}
        still_missing = list(missing_groups)
        warnings: list[str] = []
        description = normalize_text(product.description or "")

        for item in extracted:
            name = normalize_text(item.name)
            if name in known_names:
                continue
            if not self._is_confirmed(item, description):
                warnings.append(f"Отброшена характеристика «{item.name}: {item.value}» — не подтверждена текстом описания")
                continue
            specs.append(KeySpec(name=item.name, value=item.value, source=SpecSource.DESCRIPTION))
            known_names.add(name)
            group = find_spec_group(item.name)
            if group in still_missing:
                still_missing.remove(group)

        specs += [KeySpec(name=group, value=NO_DATA, source=SpecSource.MISSING) for group in still_missing]
        return SpecBuildResult(key_specs=specs, still_missing=still_missing, warnings=warnings)

    @staticmethod
    def _is_confirmed(item: ExtractedSpec, description: str) -> bool:
        quote = normalize_text(item.source_quote)
        if not quote or quote not in description:
            return False
        value_numbers = extract_numbers(item.value)
        if value_numbers:
            return value_numbers <= extract_numbers(quote)
        return normalize_text(item.value) in quote
