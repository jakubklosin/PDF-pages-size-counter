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
    assert result.regular_page_color_counts == {
        "A4": {"black_white": 1, "color": 0},
        "A3": {"black_white": 0, "color": 1},
    }
    assert result.total_area_m2 == 0.0
    assert result.color_area_m2 == {"black_white": 0.0, "color": 0.0}
    assert result.measured_area_m2 > 0.18
    assert result.page_size_area_m2 == {"A4": 0.0, "A3": 0.0}


def test_analyze_files_aggregates_successes_and_failures(tmp_path: Path) -> None:
    pdf_path = tmp_path / "custom.pdf"
    create_pdf(pdf_path, [(420, 1300, "black_white")])

    result = analyze_files([str(pdf_path), str(tmp_path / "missing.pdf")])

    assert result["summary"]["total_files"] == 2
    assert result["summary"]["successful_files"] == 1
    assert result["summary"]["failed_files"] == 1
    assert result["summary"]["page_size_counts"] == {"A2 custom length": 1}
    assert result["summary"]["total_area_m2"] == 0.6
    assert result["summary"]["regular_page_color_counts"] == {
        "A3": {"black_white": 0, "color": 0},
        "A4": {"black_white": 0, "color": 0},
    }
    assert result["files"][1]["success"] is False


def test_paper_area_includes_custom_pages_closest_to_a4(tmp_path: Path) -> None:
    pdf_path = tmp_path / "custom-a4.pdf"
    create_pdf(pdf_path, [(250, 360, "black_white"), (297, 420, "black_white")])

    result = analyze_file(str(pdf_path))

    assert result.page_size_counts == {"Custom (A4)": 1, "A3": 1}
    assert result.total_area_m2 == 0.2


def test_paper_area_uses_next_width_for_custom_sizes(tmp_path: Path) -> None:
    pdf_path = tmp_path / "between-a2-a1.pdf"
    create_pdf(pdf_path, [(500, 700, "black_white")])

    result = analyze_file(str(pdf_path))

    assert result.total_area_m2 == 0.5
    assert result.pages[0].billable_size_name == "Custom (A1)"
    assert result.pages[0].billable_width_mm == 594.0
    assert result.pages[0].billable_height_mm == 700.0


def test_paper_area_rounds_each_page_up_before_summing(tmp_path: Path) -> None:
    pdf_path = tmp_path / "rounded-sum.pdf"
    create_pdf(
        pdf_path,
        [
            (420, 976.2, "black_white"),
            (594, 1077.5, "black_white"),
        ],
    )

    result = analyze_file(str(pdf_path))

    assert [page.billable_area_m2 for page in result.pages] == [0.5, 0.7]
    assert result.total_area_m2 == 1.2


def test_paper_area_is_split_by_color_mode(tmp_path: Path) -> None:
    pdf_path = tmp_path / "color-area.pdf"
    create_pdf(
        pdf_path,
        [
            (420, 976.2, "black_white"),
            (594, 1077.5, "color"),
        ],
    )

    result = analyze_file(str(pdf_path))

    assert result.total_area_m2 == 1.2
    assert result.color_area_m2 == {"black_white": 0.5, "color": 0.7}


def test_regular_a4_a3_color_counts_ignore_custom_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "regular-counts.pdf"
    create_pdf(
        pdf_path,
        [
            (210, 297, "black_white"),
            (210, 297, "color"),
            (297, 420, "black_white"),
            (297, 420, "color"),
            (250, 360, "color"),
            (297, 700, "black_white"),
        ],
    )

    result = analyze_file(str(pdf_path))

    assert result.regular_page_color_counts == {
        "A4": {"black_white": 1, "color": 1},
        "A3": {"black_white": 1, "color": 1},
    }
