"""Preview watermark for processed photos (before checkout)."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

# Matches passport-photo.online result bar: bg-[#6d6d6d]/75
_BAR_COLOR = (109, 109, 109, 191)


def _font_candidates() -> list[Path]:
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    return [
        windir / "Fonts" / "arial.ttf",
        windir / "Fonts" / "Arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _font_candidates():
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _fit_font(
    text: str,
    max_width: int,
    start_size: int,
    min_size: int = 10,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = start_size
    while size >= min_size:
        font = _load_font(size)
        bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 1
    return _load_font(min_size)


def apply_preview_watermark(
    image: Image.Image,
    text: str | None = None,
) -> Image.Image:
    """
    Apply a preview-only watermark: bottom brand bar (passport-photo.online style).

    Clean output stays in processed.jpg; watermarked copy goes to preview.jpg.
    """
    if not settings.watermark_enabled:
        return image.convert("RGB")

    label = text or settings.watermark_text
    base = image.convert("RGBA")
    width, height = base.size

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bar_font = _fit_font(label, int(width * 0.9), max(int(width * 0.075), 12))
    bbox = draw.textbbox((0, 0), label, font=bar_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    padding_y = max(int(text_h * 0.45), 8)
    bar_height = text_h + padding_y * 2

    draw.rectangle(
        [(0, height - bar_height), (width, height)],
        fill=_BAR_COLOR,
    )
    draw.text(
        ((width - text_w) / 2, height - bar_height + padding_y),
        label,
        font=bar_font,
        fill=(255, 255, 255, 255),
    )

    composited = Image.alpha_composite(base, overlay)
    return composited.convert("RGB")
