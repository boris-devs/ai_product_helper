from app.schemas.llm_draft import ExtractedSpec
from app.schemas.card import SpecSource
from app.services.draft_parser import parse_draft
from app.services.draft_validator import DraftValidator
from app.services.fact_checker import FactChecker, extract_numbers
from app.services.input_analyzer import InputAnalyzer
from app.services.spec_builder import KeySpecBuilder
from tests.conftest import make_draft


def test_numbers_are_normalized():
    assert extract_numbers("0–1,6 МПа, DM 02, 100 мм") == {"0", "1.6", "2", "100"}


def test_validator_flags_invented_numbers(manometer):
    draft = parse_draft(make_draft(seo_title="Манометр DM 02 класс точности 2,5"))

    issues = DraftValidator().review(draft, FactChecker.from_product(manometer))

    assert any("2.5" in issue for issue in issues)


def test_validator_accepts_valid_draft(manometer):
    draft = parse_draft(make_draft())

    assert DraftValidator().review(draft, FactChecker.from_product(manometer)) == []


def test_parser_handles_markdown_fence():
    draft = parse_draft("```json\n" + make_draft() + "\n```")

    assert draft.seo_title.startswith("Манометр")


def test_spec_builder_keeps_only_confirmed_description_specs(transmitter):
    missing = InputAnalyzer().analyze(transmitter).missing_spec_groups
    extracted = [
        ExtractedSpec(name="степень защиты", value="IP65", source_quote="Степень защиты корпуса IP65"),
        ExtractedSpec(name="материал мембраны", value="сталь 316L", source_quote="мембрана из стали 316L"),
    ]

    result = KeySpecBuilder().build(transmitter, extracted, missing)
    by_name = {spec.name: spec for spec in result.key_specs}

    assert by_name["степень защиты"].source == SpecSource.DESCRIPTION
    assert "материал мембраны" not in by_name
    assert by_name["класс точности"].value == "данных нет"
    assert "степень защиты" not in result.still_missing
    assert len(result.warnings) == 1
