from __future__ import annotations

import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from pdf_analyzer.analyzer import analyze_file
from pdf_analyzer.models import FileAnalysis, OverallAnalysis


STATIC_DIR = Path(__file__).parent / "static"
MAX_FILES = 10
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024

app = FastAPI(title="PDF Analyzer", version="0.1.0")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/app.js")
def app_js() -> FileResponse:
    return FileResponse(STATIC_DIR / "app.js", media_type="text/javascript")


@app.get("/styles.css")
def styles_css() -> FileResponse:
    return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze_uploads(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one PDF file.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Upload at most {MAX_FILES} files.")

    with tempfile.TemporaryDirectory(prefix="pdf-analyzer-") as temp_dir:
        saved_files: list[tuple[Path, str]] = []
        for upload in files:
            saved_files.append(await _save_upload(upload, Path(temp_dir)))

        return _analyze_saved_files(saved_files)


async def _save_upload(upload: UploadFile, temp_dir: Path) -> tuple[Path, str]:
    original_name = Path(upload.filename or "uploaded.pdf").name
    if Path(original_name).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail=f"{original_name} is not a PDF file.")

    target_path = temp_dir / f"{uuid4().hex}.pdf"
    bytes_written = 0
    with target_path.open("wb") as output:
        while chunk := await upload.read(CHUNK_SIZE):
            bytes_written += len(chunk)
            if bytes_written > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"{original_name} exceeds the {MAX_UPLOAD_BYTES // 1024 // 1024} MB limit.",
                )
            output.write(chunk)

    await upload.close()
    return target_path, original_name


def _analyze_saved_files(saved_files: Sequence[tuple[Path, str]]) -> dict:
    overall = OverallAnalysis()
    file_results: list[FileAnalysis] = []

    for path, original_name in saved_files:
        file_result = analyze_file(str(path))
        file_result.file_name = original_name
        file_result.file_path = original_name
        overall.add_file(file_result)
        file_results.append(file_result)

    return {
        "summary": overall.to_dict(),
        "files": [file_result.to_dict() for file_result in file_results],
    }


def run_server() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("pdf_analyzer.web_app:app", host="0.0.0.0", port=port)
