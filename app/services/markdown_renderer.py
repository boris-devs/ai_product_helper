from app.schemas.card import ProductCard, SpecSource

SOURCE_LABELS = {
    SpecSource.INPUT: "",
    SpecSource.DESCRIPTION: " *(из описания)*",
    SpecSource.MISSING: " ⚠️",
}


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) or "- данных нет"


def render_card_markdown(product_name: str | None, card: ProductCard) -> str:
    specs = "\n".join(
        f"| {spec.name} | {spec.value}{SOURCE_LABELS[spec.source]} |" for spec in card.key_specs
    )
    sections = [
        f"# {product_name or 'Товар без названия'}",
        f"## SEO-заголовок ({len(card.seo_title)} симв.)\n\n{card.seo_title}",
        f"## SEO-описание ({len(card.seo_description)} симв.)\n\n{card.seo_description}",
        f"## Ключевые характеристики\n\n| Характеристика | Значение |\n|---|---|\n{specs}",
        f"## Поисковые запросы\n\n{_bullets(card.search_queries)}",
        "## Для менеджера\n\n"
        f"**Кому подходит:**\n\n{_bullets(card.commercial.target_audience)}\n\n"
        f"**Какие задачи решает:**\n\n{_bullets(card.commercial.tasks)}",
    ]
    if card.missing_fields:
        sections.append(
            "## Требует уточнения\n\n" + _bullets([f"`{i.field}` — {i.message}" for i in card.missing_fields])
        )
    if card.warnings:
        sections.append("## Предупреждения проверки\n\n" + _bullets(card.warnings))
    return "\n\n".join(sections) + "\n"
