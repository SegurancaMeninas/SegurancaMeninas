from app.services.indicator_service import safe_ratio


def test_safe_ratio_handles_zero_denominator() -> None:
    assert safe_ratio(10, 0) is None


def test_safe_ratio_calculates_value() -> None:
    assert safe_ratio(10, 20) == 0.5
