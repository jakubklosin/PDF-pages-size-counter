from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient

from pdf_analyzer.web_app import app


def create_pdf_bytes() -> bytes:
    import fitz

    buffer = BytesIO()
    document = fitz.open()
    page = document.new_page(width=420 * 72 / 25.4, height=900 * 72 / 25.4)
    page.draw_rect(
        fitz.Rect(20, 20, 220, 220),
        color=(1, 0, 0),
        fill=(1, 0, 0),
    )
    document.save(buffer)
    document.close()
    return buffer.getvalue()


def test_index_serves_browser_ui() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "PDF Analyzer" in response.text


def test_analyze_uploads_pdf_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/analyze",
        files=[("files", ("sample.pdf", create_pdf_bytes(), "application/pdf"))],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_files"] == 1
    assert data["summary"]["total_pages"] == 1
    assert data["summary"]["total_area_m2"] > 0
    assert data["files"][0]["file_name"] == "sample.pdf"


def test_analyze_uploads_rejects_non_pdf_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/analyze",
        files=[("files", ("notes.txt", b"not a pdf", "text/plain"))],
    )

    assert response.status_code == 400
    assert "not a PDF" in response.json()["detail"]
