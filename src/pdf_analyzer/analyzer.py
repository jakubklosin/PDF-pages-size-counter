from __future__ import annotations

from pathlib import Path

from pdf_analyzer.color_detection import detect_page_color
from pdf_analyzer.models import FileAnalysis, OverallAnalysis, PageAnalysis
from pdf_analyzer.page_size import classify_page_size


def analyze_files(paths: list[str]) -> dict:
    overall = OverallAnalysis()
    file_results: list[FileAnalysis] = []

    for raw_path in paths:
        file_result = analyze_file(raw_path)
        overall.add_file(file_result)
        file_results.append(file_result)

    return {
        "summary": overall.to_dict(),
        "files": [file_result.to_dict() for file_result in file_results],
    }


def analyze_file(path: str) -> FileAnalysis:
    pdf_path = Path(path)
    result = FileAnalysis(
        file_path=str(pdf_path),
        file_name=pdf_path.name,
        success=False,
    )

    if not pdf_path.exists():
        result.error = "File does not exist."
        return result
    if pdf_path.suffix.lower() != ".pdf":
        result.error = "File is not a PDF."
        return result

    try:
        import fitz

        with fitz.open(pdf_path) as document:
            if document.needs_pass:
                result.error = "PDF is encrypted and requires a password."
                return result

            result.success = True
            for page_index, page in enumerate(document, start=1):
                size = classify_page_size(page.rect.width, page.rect.height)
                color_mode = detect_page_color(page)
                result.add_page(
                    PageAnalysis(
                        page_number=page_index,
                        width_mm=size.width_mm,
                        height_mm=size.height_mm,
                        area_m2=size.area_m2,
                        size_name=size.name,
                        size_category=size.category,
                        closest_standard_size=size.closest_standard_size,
                        size_note=size.note,
                        color_mode=color_mode,
                    )
                )
    except Exception as exc:
        result.success = False
        result.error = f"Unable to analyze PDF: {exc}"
        result.pages.clear()
        result.total_pages = 0
        result.total_area_m2 = 0.0
        result.total_area_excluding_a4_m2 = 0.0
        result.page_size_counts.clear()
        result.page_size_area_m2.clear()
        result.color_counts = {"black_white": 0, "color": 0}
        result.color_area_m2 = {"black_white": 0.0, "color": 0.0}

    return result
