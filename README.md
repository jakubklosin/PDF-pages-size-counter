# PDF Analyzer

Cross-platform desktop application for analyzing PDF print usage. It counts pages
by paper size, identifies custom-length sheets, calculates billable paper area in
square meters, and separates black-and-white pages from color pages.

## Features

- Select one or more PDF files from a desktop file dialog.
- Count standard A-series pages: A4, A3, A2, A1, and A0.
- Report A0+ pages and custom-length pages such as `A2 custom length`.
- Show exact custom dimensions in centimeters or meters.
- Calculate billable paper area in square meters.
- Exclude regular A4 and regular A3 pages from billable paper area.
- Round each billable page up to one decimal place before adding totals.
- Bill custom widths using the next A-series width while preserving actual length.
- Count black-and-white and color pages separately.
- Show billable paper area split into black-and-white and color pages.
- Count regular A4 and regular A3 pages split into black-and-white and color.
- Switch the UI between English and Polish.
- Show per-file errors for missing, encrypted, or unreadable PDFs.

## Technology

- Python 3.11
- pywebview desktop shell
- Local HTML/CSS/JavaScript UI
- PyMuPDF for PDF geometry, rendering, and color detection
- pytest for automated tests
- PyInstaller for initial packaging

## Run Locally

Install the app and development tools:

```bash
uv sync --extra dev --extra desktop
```

Launch the desktop app:

```bash
uv run pdf-analyzer
```

Or run the Python entrypoint:

```bash
uv run python main.py
```

Launch the web version locally:

```bash
uv run pdf-analyzer-web
```

Then open <http://127.0.0.1:8000>.

## Test

```bash
uv run pytest
```

The tests generate small PDF fixtures at runtime, so the repository does not need
to store binary PDF test files.

## Build

Create a distributable application with PyInstaller:

```bash
uv run pyinstaller pdf_analyzer.spec
```

Build outputs are written to `dist/`.

Platform notes:

- macOS uses the system WebKit webview through pywebview.
- Windows uses Edge WebView2 where available.
- Linux requires GTK/WebKit runtime packages installed by the target system.

Because webview runtimes differ by operating system, validate release builds on
macOS, Windows, and Linux separately.

## Azure App Service

The project includes a FastAPI web entrypoint for Azure hosting:

- App object: `pdf_analyzer.web_app:app`
- Startup script: `startup.sh`
- Azure dependency file: `requirements.txt`
- Health check path: `/healthz`

For a student-friendly setup, use **Azure App Service on Linux** with the **Free F1**
pricing tier when it is available in your subscription. Azure for Students also
includes credits, but paid tiers will consume those credits.

Recommended Azure settings:

- Publish: Code
- Runtime stack: Python 3.11
- Operating system: Linux
- Pricing plan: Free F1
- Startup command: `bash startup.sh`

Deployment steps:

1. Push this repository to GitHub.
2. In Azure Portal, create an App Service Web App.
3. Select Python 3.11 on Linux and the Free F1 plan.
4. In Deployment Center, connect the GitHub repository.
5. Set the startup command to `bash startup.sh`.
6. Add application setting `SCM_DO_BUILD_DURING_DEPLOYMENT=true` if Azure does not
   install dependencies during deployment.

After deployment, Azure provides a public URL like:

```text
https://your-app-name.azurewebsites.net
```

Free tier notes:

- The app may sleep after inactivity.
- CPU and memory are limited, so very large PDFs may fail or be slow.
- The hosted upload endpoint limits requests to 10 PDF files and 50 MB per file.
- A custom domain such as `www.example.com` may require moving from Free F1 to a
  paid App Service tier. The default `azurewebsites.net` URL works on the free tier.

## Analysis Rules

PDF page dimensions are converted from points to millimeters using `72 points`
per inch and `25.4 mm` per inch. Page orientation is normalized before size
classification, so portrait and landscape versions count together.

`Paper area` is a billable print-area total, not the raw sum of PDF page areas.
Regular A4 and regular A3 pages contribute `0.0 m²`. Larger pages, custom pages,
and A3 pages with custom length are counted. Each counted page is rounded up to
one decimal place before totals are added, so `0.41 m² + 0.64 m²` is counted as
`0.5 + 0.7 = 1.2 m²`.

For custom widths, the app uses the next standard A-series width and preserves
the actual page length. For example, a page width between A2 and A1 is billed
using A1 width.

Color detection renders each page at low DPI and checks sampled RGB pixels. A
page is treated as color when enough sampled pixels have channel differences
above the configured tolerance. This keeps the result deterministic and fast,
but scanned documents with compression noise may need threshold tuning.
