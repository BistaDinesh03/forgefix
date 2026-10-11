"""Render logo.png and social-preview.png from the hand-drawn SVG geometry.

The coordinates below mirror assets/logo.svg and assets/banner.svg point for
point. When the SVGs move, move these too, then re-run:

    python assets/render_rasters.py
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
SS = 4  # supersample factor; downscaled with LANCZOS for clean edges

# 24-unit viewbox geometry (mirrors logo.svg)
HEXAGON = [(12.0, 2.0), (20.66, 7.0), (20.66, 17.0), (12.0, 22.0), (3.34, 17.0), (3.34, 7.0)]
F_STEM = [(10.0, 17.0), (10.0, 7.0), (15.0, 7.0)]
F_BAR = [(10.0, 12.0), (13.5, 12.0)]
CHECK_VB = [(21.6, 19.0), (23.0, 20.6), (26.2, 16.6)]  # just outside the hexagon's lower-right edge

# Palette (see assets/brand.md)
ACCENT = (37, 99, 235)  # #2563EB
SLATE_900 = (15, 23, 42)  # #0F172A
SLATE_800 = (30, 41, 59)  # #1E293B
SLATE_200 = (226, 232, 240)  # #E2E8F0
SLATE_400 = (148, 163, 184)  # #94A3B8
SLATE_500 = (100, 116, 139)  # #64748B
WHITE = (248, 250, 252)  # #F8FAFC

HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".")


def _scaled(
    points: list[tuple[float, float]], scale: float, ox: float, oy: float
) -> list[tuple[float, float]]:
    return [(ox + x * scale, oy + y * scale) for x, y in points]


def _draw_mark(
    draw: ImageDraw.ImageDraw,
    *,
    scale: float,
    ox: float,
    oy: float,
    color: tuple[int, int, int],
    stroke: float,
) -> None:
    """Draw the hexagon + F mark; stroke is in 24-viewbox units."""
    width = max(1, int(round(stroke * scale)))
    hexagon = _scaled(HEXAGON, scale, ox, oy)
    # Per-edge segments (centered strokes, like SVG) plus vertex dots for the
    # round line-joins. A closed polyline would leave a seam at the start
    # vertex, and a polygon outline would draw inside the path.
    for index in range(len(hexagon)):
        start, end = hexagon[index], hexagon[(index + 1) % len(hexagon)]
        draw.line([start, end], fill=color, width=width)
    radius = width / 2
    for x, y in hexagon:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    stem = _scaled(F_STEM, scale, ox, oy)
    bar = _scaled(F_BAR, scale, ox, oy)
    draw.line(stem, fill=color, width=width, joint="curve")
    draw.line(bar, fill=color, width=width, joint="curve")
    # Round caps on the open ends (SVG uses stroke-linecap="round").
    for point in (stem[0], stem[-1], bar[0], bar[-1]):
        x, y = point
        radius = width / 2
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def _font(candidates: list[Path], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _bold(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _font(
        [
            Path("C:/Windows/Fonts/segoeuib.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            HOME / "AppData/Local/Microsoft/Windows/Fonts/JetBrainsMono-Bold.ttf",
        ],
        size,
    )


def _sans(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _font(
        [
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            HOME / "AppData/Local/Microsoft/Windows/Fonts/JetBrainsMono-Regular.ttf",
        ],
        size,
    )


def _mono(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _font(
        [
            HOME / "AppData/Local/Microsoft/Windows/Fonts/JetBrainsMono-Regular.ttf",
            Path("C:/Windows/Fonts/consola.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        ],
        size,
    )


def render_logo_png() -> Path:
    """512x512 accent-blue mark on transparent background."""
    size = 512 * SS
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    mark_px = 410  # mark height in final pixels
    scale = (mark_px / 24) * SS
    offset = (size - mark_px * SS) / 2
    _draw_mark(draw, scale=scale, ox=offset, oy=offset, color=ACCENT, stroke=2.0)
    out = HERE / "logo.png"
    image.resize((512, 512), Image.LANCZOS).save(out)
    return out


def render_social_preview() -> Path:
    """1280x640 card: mark + wordmark + tagline + repo URL."""
    width, height = 1280 * SS, 640 * SS
    image = Image.new("RGBA", (width, height), SLATE_900 + (255,))
    # One subtle glow behind the mark (slate-800, heavily blurred).
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-200 * SS, 60 * SS, 760 * SS, 640 * SS), fill=SLATE_800 + (150,))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90 * SS)))

    draw = ImageDraw.Draw(image)
    scale = 12.0 * SS
    _draw_mark(draw, scale=scale, ox=196 * SS, oy=176 * SS, color=SLATE_200, stroke=2.0)
    # Checkmark accent just outside the hexagon's lower-right edge (viewbox units).
    check = _scaled(CHECK_VB, scale, 196 * SS, 176 * SS)
    draw.line(check, fill=(22, 163, 74), width=17 * SS, joint="curve")
    for x, y in (check[0], check[-1]):
        radius = 8.5 * SS
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(22, 163, 74))

    draw.text((522 * SS, 296 * SS), "ForgeFix", font=_bold(76 * SS), fill=WHITE, anchor="ls")
    draw.text(
        (524 * SS, 358 * SS),
        "One command to fix any repo's setup.",
        font=_sans(32 * SS),
        fill=SLATE_400,
        anchor="ls",
    )
    draw.text(
        (524 * SS, 418 * SS),
        "github.com/BistaDinesh03/forgefix",
        font=_mono(26 * SS),
        fill=SLATE_500,
        anchor="ls",
    )
    out = HERE / "social-preview.png"
    image.convert("RGB").resize((1280, 640), Image.LANCZOS).save(out)
    return out


def main() -> None:
    for path in (render_logo_png(), render_social_preview()):
        print(f"wrote {path.name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
