from __future__ import annotations

from pathlib import Path

from pdf_analyzer.analyzer import analyze_file, analyze_files


def points(mm: float) -> float:
    return mm * 72 / 25.4


def create_pdf(path: Path, pages: list[tuple[float, float, str]]) -> None:
    import fitz

    document = fitz.open()
    for width_mm, height_mm, color_mode in pages:
        page = document.new_page(width=points(width_mm), height=points(height_mm))
        if color_mode == "color":
            page.draw_rect(
                fitz.Rect(20, 20, 220, 220),
                color=(1, 0, 0),
                fill=(1, 0, 0),
            )
        else:
            page.draw_rect(
                fitz.Rect(20, 20, 220, 220),
                color=(0, 0, 0),
                fill=(0, 0, 0),
            )
    document.save(path)
    document.close()


def test_analyze_file_counts_sizes_area_and_color(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    create_pdf(pdf_path, [(210, 297, "black_white"), (297, 420, "color")])

    result = analyze_file(str(pdf_path))

    assert result.success is True
    assert result.total_pages == 2
    assert result.page_size_counts == {"A4": 1, "A3": 1}
    assert result.color_counts == {"black_white": 1, "color": 1}
    assert result.total_area_m2 > 0.18
    assert result.total_area_excluding_a4_m2 == result.page_size_area_m2["A3"]


def test_analyze_files_aggregates_successes_and_failures(tmp_path: Path) -> None:
    pdf_path = tmp_path / "custom.pdf"
    create_pdf(pdf_path, [(420, 1300, "black_white")])

    result = analyze_files([str(pdf_path), str(tmp_path / "missing.pdf")])

    assert result["summary"]["total_files"] == 2
    assert result["summary"]["successful_files"] == 1
    assert result["summary"]["failed_files"] == 1
    assert result["summary"]["page_size_counts"] == {"A2 custom length": 1}
    assert result["summary"]["total_area_excluding_a4_m2"] == result["summary"]["total_area_m2"]
    assert result["files"][1]["success"] is False


def test_area_without_a4_excludes_custom_pages_closest_to_a4(tmp_path: Path) -> None:
    pdf_path = tmp_path / "custom-a4.pdf"
    create_pdf(pdf_path, [(250, 360, "black_white"), (297, 420, "black_white")])

    result = analyze_file(str(pdf_path))

    assert result.page_size_counts == {"Custom (A4)": 1, "A3": 1}
    assert result.total_area_excluding_a4_m2 == result.page_size_area_m2["A3"]
