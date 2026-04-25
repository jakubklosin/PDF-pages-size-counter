# PDF Analyzer

FastAPI web application for analyzing PDF print usage. It counts pages by paper
size, identifies custom-length sheets, calculates total paper area in square
meters, and separates black-and-white pages from color pages.

## Features

- Upload one or more PDF files in a browser.
- Count standard A-series pages: A4, A3, A2, A1, and A0.
- Report A0+ pages and custom-length pages such as `A2 custom length`.
- Show exact custom dimensions in centimeters or meters.
- Calculate total paper area in square meters.
- Calculate total square meters again with A4 pages excluded.
- Count black-and-white and color pages separately.
- Show per-file errors for encrypted or unreadable PDFs.

## Technology

- Python 3.11
- FastAPI
- Uvicorn
- Local HTML/CSS/JavaScript UI
- PyMuPDF for PDF geometry, rendering, and color detection
- pytest for automated tests

## Run Locally

Install the app and development tools:

```bash
uv sync --extra dev
```

Launch the web app:

```bash
uv run uvicorn pdf_analyzer.app:app --reload
```

Or use the console script, which starts the server on `0.0.0.0:8000` by default:

```bash
uv run pdf-analyzer
```

Open <http://127.0.0.1:8000> in your browser.

## Test

```bash
uv run pytest
```

The tests generate small PDF fixtures at runtime, so the repository does not need
to store binary PDF test files.

## Deploy on Render

The repository includes `render.yaml`, so Render can create the web service from
the repo automatically.

Render settings:

- Runtime: Python
- Build command: `pip install -e .`
- Start command: `uvicorn pdf_analyzer.app:app --host 0.0.0.0 --port $PORT`
- Health check path: `/healthz`

The FastAPI server accepts uploaded PDFs at `POST /api/analyze`, stores them only
in a temporary directory during analysis, and deletes them after the request is
finished.

## API

Analyze PDFs:

```http
POST /api/analyze
Content-Type: multipart/form-data
```

Form field:

- `files`: one or more PDF files

Limits:

- Maximum files per request: `20`
- Maximum file size: `100 MB`

## Analysis Rules

PDF page dimensions are converted from points to millimeters using `72 points`
per inch and `25.4 mm` per inch. Page orientation is normalized before size
classification, so portrait and landscape versions count together.

Color detection renders each page at low DPI and checks sampled RGB pixels. A
page is treated as color when enough sampled pixels have channel differences
above the configured tolerance. This keeps the result deterministic and fast,
but scanned documents with compression noise may need threshold tuning.
