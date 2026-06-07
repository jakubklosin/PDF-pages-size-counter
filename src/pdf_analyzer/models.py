from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


ColorMode = Literal["black_white", "color"]
SizeCategory = Literal["standard", "custom_length", "a0_plus", "custom"]


@dataclass(frozen=True)
class PageSizeClassification:
    name: str
    category: SizeCategory
    width_mm: float
    height_mm: float
    area_m2: float
    billable_area_m2: float
    billable_size_name: str
    billable_width_mm: float
    billable_height_mm: float
    closest_standard_size: str | None = None
    note: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PageAnalysis:
    page_number: int
    width_mm: float
    height_mm: float
    area_m2: float
    billable_area_m2: float
    billable_size_name: str
    billable_width_mm: float
    billable_height_mm: float
    size_name: str
    size_category: SizeCategory
    closest_standard_size: str | None
    size_note: str | None
    color_mode: ColorMode

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileAnalysis:
    file_path: str
    file_name: str
    success: bool
    error: str | None = None
    total_pages: int = 0
    total_area_m2: float = 0.0
    measured_area_m2: float = 0.0
    page_size_counts: dict[str, int] = field(default_factory=dict)
    page_size_area_m2: dict[str, float] = field(default_factory=dict)
    measured_page_size_area_m2: dict[str, float] = field(default_factory=dict)
    color_counts: dict[ColorMode, int] = field(
        default_factory=lambda: {"black_white": 0, "color": 0}
    )
    color_area_m2: dict[ColorMode, float] = field(
        default_factory=lambda: {"black_white": 0.0, "color": 0.0}
    )
    regular_page_color_counts: dict[str, dict[ColorMode, int]] = field(
        default_factory=lambda: _empty_regular_page_color_counts()
    )
    pages: list[PageAnalysis] = field(default_factory=list)

    def add_page(self, page: PageAnalysis) -> None:
        self.pages.append(page)
        self.total_pages += 1
        self.total_area_m2 += page.billable_area_m2
        self.measured_area_m2 += page.area_m2
        self.page_size_counts[page.size_name] = (
            self.page_size_counts.get(page.size_name, 0) + 1
        )
        self.page_size_area_m2[page.size_name] = (
            self.page_size_area_m2.get(page.size_name, 0.0) + page.billable_area_m2
        )
        self.measured_page_size_area_m2[page.size_name] = (
            self.measured_page_size_area_m2.get(page.size_name, 0.0) + page.area_m2
        )
        self.color_counts[page.color_mode] += 1
        self.color_area_m2[page.color_mode] += page.billable_area_m2
        if page.size_category == "standard" and page.size_name in {"A4", "A3"}:
            self.regular_page_color_counts[page.size_name][page.color_mode] += 1

    def to_dict(self, include_pages: bool = True) -> dict:
        data = asdict(self)
        data["total_area_m2"] = round(self.total_area_m2, 1)
        data["measured_area_m2"] = round(self.measured_area_m2, 4)
        data["page_size_area_m2"] = _rounded_float_dict(self.page_size_area_m2)
        data["measured_page_size_area_m2"] = _rounded_float_dict(
            self.measured_page_size_area_m2
        )
        data["color_area_m2"] = _rounded_float_dict(self.color_area_m2)
        data["regular_page_color_counts"] = _sorted_nested_count_dict(
            self.regular_page_color_counts
        )
        if include_pages:
            data["pages"] = [page.to_dict() for page in self.pages]
        else:
            data["pages"] = []
        return data


@dataclass
class OverallAnalysis:
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_pages: int = 0
    total_area_m2: float = 0.0
    measured_area_m2: float = 0.0
    page_size_counts: dict[str, int] = field(default_factory=dict)
    page_size_area_m2: dict[str, float] = field(default_factory=dict)
    measured_page_size_area_m2: dict[str, float] = field(default_factory=dict)
    color_counts: dict[ColorMode, int] = field(
        default_factory=lambda: {"black_white": 0, "color": 0}
    )
    color_area_m2: dict[ColorMode, float] = field(
        default_factory=lambda: {"black_white": 0.0, "color": 0.0}
    )
    regular_page_color_counts: dict[str, dict[ColorMode, int]] = field(
        default_factory=lambda: _empty_regular_page_color_counts()
    )

    def add_file(self, file_result: FileAnalysis) -> None:
        self.total_files += 1
        if not file_result.success:
            self.failed_files += 1
            return

        self.successful_files += 1
        self.total_pages += file_result.total_pages
        self.total_area_m2 += file_result.total_area_m2
        self.measured_area_m2 += file_result.measured_area_m2
        for size_name, count in file_result.page_size_counts.items():
            self.page_size_counts[size_name] = (
                self.page_size_counts.get(size_name, 0) + count
            )
        for size_name, area in file_result.page_size_area_m2.items():
            self.page_size_area_m2[size_name] = (
                self.page_size_area_m2.get(size_name, 0.0) + area
            )
        for size_name, area in file_result.measured_page_size_area_m2.items():
            self.measured_page_size_area_m2[size_name] = (
                self.measured_page_size_area_m2.get(size_name, 0.0) + area
            )
        for color_mode, count in file_result.color_counts.items():
            self.color_counts[color_mode] += count
        for color_mode, area in file_result.color_area_m2.items():
            self.color_area_m2[color_mode] += area
        for size_name, color_counts in file_result.regular_page_color_counts.items():
            for color_mode, count in color_counts.items():
                self.regular_page_color_counts[size_name][color_mode] += count

    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "total_pages": self.total_pages,
            "total_area_m2": round(self.total_area_m2, 1),
            "measured_area_m2": round(self.measured_area_m2, 4),
            "page_size_counts": dict(sorted(self.page_size_counts.items())),
            "page_size_area_m2": _rounded_float_dict(self.page_size_area_m2),
            "measured_page_size_area_m2": _rounded_float_dict(
                self.measured_page_size_area_m2
            ),
            "color_counts": dict(self.color_counts),
            "color_area_m2": _rounded_float_dict(self.color_area_m2),
            "regular_page_color_counts": _sorted_nested_count_dict(
                self.regular_page_color_counts
            ),
        }


def _rounded_float_dict(values: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 4) for key, value in sorted(values.items())}


def _empty_regular_page_color_counts() -> dict[str, dict[ColorMode, int]]:
    return {
        "A4": {"black_white": 0, "color": 0},
        "A3": {"black_white": 0, "color": 0},
    }


def _sorted_nested_count_dict(
    values: dict[str, dict[ColorMode, int]],
) -> dict[str, dict[ColorMode, int]]:
    return {
        size_name: dict(color_counts)
        for size_name, color_counts in sorted(values.items())
    }
