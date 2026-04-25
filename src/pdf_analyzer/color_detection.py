from __future__ import annotations

from pdf_analyzer.models import ColorMode


DEFAULT_RENDER_DPI = 50
DEFAULT_CHANNEL_TOLERANCE = 8
DEFAULT_COLOR_PIXEL_RATIO = 0.001
DEFAULT_MIN_COLOR_PIXELS = 20
MAX_SAMPLED_PIXELS = 250_000


def detect_page_color(
    page,
    *,
    dpi: int = DEFAULT_RENDER_DPI,
    channel_tolerance: int = DEFAULT_CHANNEL_TOLERANCE,
    color_pixel_ratio: float = DEFAULT_COLOR_PIXEL_RATIO,
    min_color_pixels: int = DEFAULT_MIN_COLOR_PIXELS,
) -> ColorMode:
    """Classify a PyMuPDF page as black-and-white or color."""
    import fitz

    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
    samples = pixmap.samples
    total_pixels = pixmap.width * pixmap.height
    if total_pixels == 0:
        return "black_white"

    pixel_step = max(1, total_pixels // MAX_SAMPLED_PIXELS)
    byte_step = pixel_step * 3
    sampled_pixels = 0
    color_pixels = 0

    for index in range(0, len(samples), byte_step):
        red = samples[index]
        green = samples[index + 1]
        blue = samples[index + 2]
        sampled_pixels += 1

        if _is_colored_pixel(red, green, blue, channel_tolerance):
            color_pixels += 1
            if (
                color_pixels >= min_color_pixels
                and color_pixels / sampled_pixels >= color_pixel_ratio
            ):
                return "color"

    if sampled_pixels == 0:
        return "black_white"
    if color_pixels >= min_color_pixels and color_pixels / sampled_pixels >= color_pixel_ratio:
        return "color"
    return "black_white"


def _is_colored_pixel(red: int, green: int, blue: int, channel_tolerance: int) -> bool:
    return max(red, green, blue) - min(red, green, blue) > channel_tolerance
