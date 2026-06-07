from __future__ import annotations

import pytest

from pdf_analyzer.page_size import (
    billable_width_for_page,
    ceil_to_one_decimal,
    classify_page_size,
)


def points(mm: float) -> float:
    return mm * 72 / 25.4


def test_classifies_standard_a4_portrait() -> None:
    result = classify_page_size(points(210), points(297))

    assert result.name == "A4"
    assert result.category == "standard"
    assert result.closest_standard_size == "A4"
    assert result.area_m2 == pytest.approx(0.0624, abs=0.0001)
    assert result.billable_area_m2 == 0.0


def test_classifies_standard_a3_landscape() -> None:
    result = classify_page_size(points(420), points(297))

    assert result.name == "A3"
    assert result.category == "standard"
    assert result.billable_area_m2 == 0.0


def test_classifies_custom_length_by_matching_roll_width() -> None:
    result = classify_page_size(points(420), points(1300))

    assert result.name == "A2 custom length"
    assert result.category == "custom_length"
    assert result.closest_standard_size == "A2"
    assert result.note == "42.0 cm x 1.30 m"
    assert result.billable_area_m2 == 0.6
    assert result.billable_size_name == "A2 custom length"


def test_classifies_larger_than_a0_as_a0_plus() -> None:
    result = classify_page_size(points(841), points(1500))

    assert result.name == "A0+"
    assert result.category == "a0_plus"
    assert result.closest_standard_size == "A0"
    assert result.billable_area_m2 == 1.3


def test_reports_custom_page_with_closest_standard_size() -> None:
    result = classify_page_size(points(250), points(360))

    assert result.name == "Custom (A4)"
    assert result.category == "custom"
    assert result.closest_standard_size == "A4"
    assert result.billable_width_mm == 297.0
    assert result.billable_size_name == "Custom (A3)"


def test_ceil_to_one_decimal_always_rounds_up() -> None:
    assert ceil_to_one_decimal(0.41) == 0.5
    assert ceil_to_one_decimal(0.64) == 0.7
    assert ceil_to_one_decimal(0.7) == 0.7


def test_billable_width_uses_next_standard_width() -> None:
    assert billable_width_for_page(500) == (594.0, "A1")
