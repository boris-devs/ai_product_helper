from app.core.spec_catalog import RECOMMENDED_SPECS, find_spec_group
from app.schemas.card import FieldIssue, InputAnalysis
from app.schemas.product import ProductInput


class InputAnalyzer:
    def analyze(self, product: ProductInput) -> InputAnalysis:
        issues: list[FieldIssue] = []
        if not product.name:
            issues.append(FieldIssue(field="name", message="Не указано название товара — без него карточку не сформировать"))
        if not product.manufacturer:
            issues.append(FieldIssue(field="manufacturer", message="Не указан производитель"))
        if not product.description:
            issues.append(FieldIssue(field="description", message="Нет описания или фрагмента паспорта — тексты будут беднее"))
        if not product.filled_specs:
            issues.append(FieldIssue(field="specs", message="Не передано ни одной характеристики"))
        for key in product.empty_spec_keys:
            issues.append(FieldIssue(field=f"specs.{key}", message="Характеристика указана без значения"))

        missing_groups = self._missing_spec_groups(product)
        for group in missing_groups:
            issues.append(FieldIssue(field=f"specs.{group}", message="Рекомендуемая характеристика отсутствует — требует уточнения"))

        can_generate = bool(product.name) and bool(product.filled_specs or product.description)
        return InputAnalysis(missing_fields=issues, missing_spec_groups=missing_groups, can_generate=can_generate)

    @staticmethod
    def _missing_spec_groups(product: ProductInput) -> list[str]:
        present = {find_spec_group(key) for key in product.specs}
        return [group for group in RECOMMENDED_SPECS if group not in present]
