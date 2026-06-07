from __future__ import annotations

from math import ceil
from math import hypot

from pdf_analyzer.models import PageSizeClassification


POINTS_PER_INCH = 72
MM_PER_INCH = 25.4
MM_PER_METER = 1000
DEFAULT_TOLERANCE_MM = 3.0

A_SERIES_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0),
    "A1": (594.0, 841.0),
    "A0": (841.0, 1189.0),
}


def points_to_mm(points: float) -> float:
    return points * MM_PER_INCH / POINTS_PER_INCH


def dimensions_from_points(width_points: float, height_points: float) -> tuple[float, float]:
    width_mm = points_to_mm(width_points)
    height_mm = points_to_mm(height_points)
    return normalize_dimensions_mm(width_mm, height_mm)


def normalize_dimensions_mm(width_mm: float, height_mm: float) -> tuple[float, float]:
    short_side, long_side = sorted((width_mm, height_mm))
    return round(short_side, 2), round(long_side, 2)


def area_m2(width_mm: float, height_mm: float) -> float:
    return (width_mm / MM_PER_METER) * (height_mm / MM_PER_METER)


def ceil_to_one_decimal(value: float) -> float:
    return ceil(value * 10) / 10


def billable_width_for_page(
    width_mm: float,
    *,
    tolerance_mm: float = DEFAULT_TOLERANCE_MM,
) -> tuple[float, str]:
    for name, (target_width, _target_height) in A_SERIES_MM.items():
        if width_mm <= target_width + tolerance_mm:
            return target_width, name
    return width_mm, "A0+"


def classify_page_size(
    width_points: float,
    height_points: float,
    *,
    tolerance_mm: float = DEFAULT_TOLERANCE_MM,
) -> PageSizeClassification:
    width_mm, height_mm = dimensions_from_points(width_points, height_points)
    page_area_m2 = area_m2(width_mm, height_mm)

    for name, target in A_SERIES_MM.items():
        if _matches_dimensions((width_mm, height_mm), target, tolerance_mm):
            billable = calculate_billable_area(
                name=name,
                category="standard",
                width_mm=width_mm,
                height_mm=height_mm,
                tolerance_mm=tolerance_mm,
            )
            return PageSizeClassification(
                name=name,
                category="standard",
                width_mm=width_mm,
                height_mm=height_mm,
                area_m2=round(page_area_m2, 4),
                billable_area_m2=billable[0],
                billable_size_name=billable[1],
                billable_width_mm=billable[2],
                billable_height_mm=billable[3],
                closest_standard_size=name,
            )

    if _is_a0_plus(width_mm, height_mm, tolerance_mm):
        billable = calculate_billable_area(
            name="A0+",
            category="a0_plus",
            width_mm=width_mm,
            height_mm=height_mm,
            tolerance_mm=tolerance_mm,
        )
        return PageSizeClassification(
            name="A0+",
            category="a0_plus",
            width_mm=width_mm,
            height_mm=height_mm,
            area_m2=round(page_area_m2, 4),
            billable_area_m2=billable[0],
            billable_size_name=billable[1],
            billable_width_mm=billable[2],
            billable_height_mm=billable[3],
            closest_standard_size="A0",
            note=_format_custom_dimension_note(width_mm, height_mm),
        )

    custom_length_match = _find_custom_length_match(width_mm, height_mm, tolerance_mm)
    if custom_length_match is not None:
        name = f"{custom_length_match} custom length"
        billable = calculate_billable_area(
            name=name,
            category="custom_length",
            width_mm=width_mm,
            height_mm=height_mm,
            tolerance_mm=tolerance_mm,
        )
        return PageSizeClassification(
            name=name,
            category="custom_length",
            width_mm=width_mm,
            height_mm=height_mm,
            area_m2=round(page_area_m2, 4),
            billable_area_m2=billable[0],
            billable_size_name=billable[1],
            billable_width_mm=billable[2],
            billable_height_mm=billable[3],
            closest_standard_size=custom_length_match,
            note=_format_custom_dimension_note(width_mm, height_mm),
        )

    closest = closest_a_series_size(width_mm, height_mm)
    name = f"Custom ({closest})"
    billable = calculate_billable_area(
        name=name,
        category="custom",
        width_mm=width_mm,
        height_mm=height_mm,
        tolerance_mm=tolerance_mm,
    )
    return PageSizeClassification(
        name=name,
        category="custom",
        width_mm=width_mm,
        height_mm=height_mm,
        area_m2=round(page_area_m2, 4),
        billable_area_m2=billable[0],
        billable_size_name=billable[1],
        billable_width_mm=billable[2],
        billable_height_mm=billable[3],
        closest_standard_size=closest,
        note=_format_custom_dimension_note(width_mm, height_mm),
    )


def closest_a_series_size(width_mm: float, height_mm: float) -> str:
    normalized = normalize_dimensions_mm(width_mm, height_mm)
    return min(
        A_SERIES_MM,
        key=lambda name: hypot(
            normalized[0] - A_SERIES_MM[name][0],
            normalized[1] - A_SERIES_MM[name][1],
        ),
    )


def calculate_billable_area(
    *,
    name: str,
    category: str,
    width_mm: float,
    height_mm: float,
    tolerance_mm: float = DEFAULT_TOLERANCE_MM,
) -> tuple[float, str, float, float]:
    if category == "standard" and name in {"A4", "A3"}:
        return 0.0, name, width_mm, height_mm

    billable_width_mm, billable_size_name = billable_width_for_page(
        width_mm,
        tolerance_mm=tolerance_mm,
    )
    billable_area_m2 = ceil_to_one_decimal(area_m2(billable_width_mm, height_mm))
    if category == "custom_length":
        billable_size_name = f"{billable_size_name} custom length"
    elif category == "custom":
        billable_size_name = f"Custom ({billable_size_name})"
    return billable_area_m2, billable_size_name, billable_width_mm, height_mm


def _matches_dimensions(
    dimensions: tuple[float, float],
    target: tuple[float, float],
    tolerance_mm: float,
) -> bool:
    return (
        abs(dimensions[0] - target[0]) <= tolerance_mm
        and abs(dimensions[1] - target[1]) <= tolerance_mm
    )


def _is_a0_plus(width_mm: float, height_mm: float, tolerance_mm: float) -> bool:
    a0_width, a0_height = A_SERIES_MM["A0"]
    return width_mm >= a0_width - tolerance_mm and height_mm > a0_height + tolerance_mm


def _find_custom_length_match(
    width_mm: float,
    height_mm: float,
    tolerance_mm: float,
) -> str | None:
    del height_mm
    for name, (target_width, _target_height) in A_SERIES_MM.items():
        if abs(width_mm - target_width) <= tolerance_mm:
            return name
    return None


def _format_custom_dimension_note(width_mm: float, height_mm: float) -> str:
    return f"{_format_length(width_mm)} x {_format_length(height_mm)}"


def _format_length(length_mm: float) -> str:
    if length_mm >= MM_PER_METER:
        return f"{length_mm / MM_PER_METER:.2f} m"
    return f"{length_mm / 10:.1f} cm"
