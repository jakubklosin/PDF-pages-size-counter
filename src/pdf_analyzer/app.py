from __future__ import annotations

from pathlib import Path

from pdf_analyzer.analyzer import analyze_files


STATIC_DIR = Path(__file__).parent / "static"


class PdfAnalyzerApi:
    def select_pdf_files(self) -> list[str]:
        import webview

        if not webview.windows:
            return []

        selected = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=("PDF files (*.pdf)", "All files (*.*)"),
        )
        return list(selected or [])

    def analyze_files(self, paths: list[str]) -> dict:
        return analyze_files(paths)


def run_app() -> None:
    import webview

    webview.create_window(
        "PDF Analyzer",
        (STATIC_DIR / "index.html").as_uri(),
        js_api=PdfAnalyzerApi(),
        width=1180,
        height=780,
        min_size=(920, 620),
    )
    webview.start()
