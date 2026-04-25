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
    total_area_excluding_a4_m2: float = 0.0
    page_size_counts: dict[str, int] = field(default_factory=dict)
    page_size_area_m2: dict[str, float] = field(default_factory=dict)
    color_counts: dict[ColorMode, int] = field(
        default_factory=lambda: {"black_white": 0, "color": 0}
    )
    color_area_m2: dict[ColorMode, float] = field(
        default_factory=lambda: {"black_white": 0.0, "color": 0.0}
    )
    pages: list[PageAnalysis] = field(default_factory=list)

    def add_page(self, page: PageAnalysis) -> None:
        self.pages.append(page)
        self.total_pages += 1
        self.total_area_m2 += page.area_m2
        if page.closest_standard_size != "A4":
            self.total_area_excluding_a4_m2 += page.area_m2
        self.page_size_counts[page.size_name] = (
            self.page_size_counts.get(page.size_name, 0) + 1
        )
        self.page_size_area_m2[page.size_name] = (
            self.page_size_area_m2.get(page.size_name, 0.0) + page.area_m2
        )
        self.color_counts[page.color_mode] += 1
        self.color_area_m2[page.color_mode] += page.area_m2

    def to_dict(self, include_pages: bool = True) -> dict:
        data = asdict(self)
        data["total_area_m2"] = round(self.total_area_m2, 4)
        data["total_area_excluding_a4_m2"] = round(self.total_area_excluding_a4_m2, 4)
        data["page_size_area_m2"] = _rounded_float_dict(self.page_size_area_m2)
        data["color_area_m2"] = _rounded_float_dict(self.color_area_m2)
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
    total_area_excluding_a4_m2: float = 0.0
    page_size_counts: dict[str, int] = field(default_factory=dict)
    page_size_area_m2: dict[str, float] = field(default_factory=dict)
    color_counts: dict[ColorMode, int] = field(
        default_factory=lambda: {"black_white": 0, "color": 0}
    )
    color_area_m2: dict[ColorMode, float] = field(
        default_factory=lambda: {"black_white": 0.0, "color": 0.0}
    )

    def add_file(self, file_result: FileAnalysis) -> None:
        self.total_files += 1
        if not file_result.success:
            self.failed_files += 1
            return

        self.successful_files += 1
        self.total_pages += file_result.total_pages
        self.total_area_m2 += file_result.total_area_m2
        self.total_area_excluding_a4_m2 += file_result.total_area_excluding_a4_m2
        for size_name, count in file_result.page_size_counts.items():
            self.page_size_counts[size_name] = (
                self.page_size_counts.get(size_name, 0) + count
            )
        for size_name, area in file_result.page_size_area_m2.items():
            self.page_size_area_m2[size_name] = (
                self.page_size_area_m2.get(size_name, 0.0) + area
            )
        for color_mode, count in file_result.color_counts.items():
            self.color_counts[color_mode] += count
        for color_mode, area in file_result.color_area_m2.items():
            self.color_area_m2[color_mode] += area

    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "total_pages": self.total_pages,
            "total_area_m2": round(self.total_area_m2, 4),
            "total_area_excluding_a4_m2": round(self.total_area_excluding_a4_m2, 4),
            "page_size_counts": dict(sorted(self.page_size_counts.items())),
            "page_size_area_m2": _rounded_float_dict(self.page_size_area_m2),
            "color_counts": dict(self.color_counts),
            "color_area_m2": _rounded_float_dict(self.color_area_m2),
        }


def _rounded_float_dict(values: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 4) for key, value in sorted(values.items())}
