from app.schemas.product import ProductInput
from app.services.input_analyzer import InputAnalyzer


def test_complete_manometer_reports_only_missing_recommended_specs(manometer):
    analysis = InputAnalyzer().analyze(manometer)

    assert analysis.can_generate
    fields = {issue.field for issue in analysis.missing_fields}
    assert "name" not in fields and "manufacturer" not in fields
    assert "питание" in analysis.missing_spec_groups
    assert "диапазон измерений" not in analysis.missing_spec_groups
    assert "корпус" not in analysis.missing_spec_groups


def test_empty_spec_value_is_reported(transmitter):
    analysis = InputAnalyzer().analyze(transmitter)

    assert "specs.класс точности" in {issue.field for issue in analysis.missing_fields}
    assert "класс точности" not in transmitter.filled_specs


def test_without_name_generation_is_blocked():
    product = ProductInput.model_validate({"name": "  ", "specs": {"диапазон": "0–1 МПа"}})

    analysis = InputAnalyzer().analyze(product)

    assert not analysis.can_generate
    assert analysis.missing_fields[0].field == "name"
