"""Render ForgeFix raster assets from the hand-drawn SVG geometry.

The SVGs in this directory are the source of truth. This script mirrors their
coordinates (24-unit grid, hexagon R=10.5, corner radius 2, cut stroke 4) and
renders:

- assets/logo.png            512x512, transparent, accent blue
- assets/social-preview.png  1280x640, opaque slate-900

Everything is drawn at 4x and downsampled (LANCZOS) for clean edges.
No AI image generation, no tracing, no third-party artwork.

Usage:  python assets/render_rasters.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SS = 4  # supersample factor

# --- shared 24-unit geometry (must match logo.svg) -------------------------

HEX_R = 10.5
HEX_C = (12.0, 12.0)
HEX_CORNER_R = 2.0
# ForgeFix cut: stem + top bar + checkmark crossbar, stroke width 4
CUT_POLYLINES = [
    [(9.4, 16.4), (9.4, 8.0), (12.6, 8.0)],
    [(10.8, 14.2), (12.6, 16.8), (17.2, 11.6)],
]
CUT_WIDTH = 4.0

ACCENT = (37, 99, 235)  # #2563EB
SLATE_900 = (15, 23, 42)  # #0F172A
SLATE_100 = (248, 250, 252)  # #F8FAFC
SLATE_400 = (148, 163, 184)  # #94A3B8

# --- social preview layout (must match social-preview.svg) -----------------

SP_MARK_BOX = (580.0, 96.0, 120.0)  # x, y, size (24-unit mark scaled to 120)
SP_WORDMARK = ("ForgeFix", 72, 700, 304.0, -1.5)
SP_TAGLINE = ("One command to fix any repo's setup.", 26, 400, 352.0, 0.0)
SP_URL = ("github.com/BistaDinesh03/forgefix", 18, 500, 568.0, 0.0)


def hexagon_points() -> list[tuple[float, float]]:
    """Rounded pointy-top hexagon outline for the 24-unit grid."""
    verts = []
    for angle_deg in (90, 30, -30, -90, -150, 150):
        a = math.radians(angle_deg)
        verts.append((HEX_C[0] + HEX_R * math.cos(a), HEX_C[1] - HEX_R * math.sin(a)))
    inset = HEX_CORNER_R / math.tan(math.radians(60))
    center_dist = HEX_CORNER_R / math.sin(math.radians(60))
    pts: list[tuple[float, float]] = []
    n = len(verts)
    for i, v in enumerate(verts):
        prev_v, next_v = verts[(i - 1) % n], verts[(i + 1) % n]
        d_prev = _unit((v[0] - prev_v[0], v[1] - prev_v[1]))
        d_next = _unit((next_v[0] - v[0], next_v[1] - v[1]))
        p_in = (v[0] - d_prev[0] * inset, v[1] - d_prev[1] * inset)
        p_out = (v[0] + d_next[0] * inset, v[1] + d_next[1] * inset)
        bis = _unit((HEX_C[0] - v[0], HEX_C[1] - v[1]))
        center = (v[0] + bis[0] * center_dist, v[1] + bis[1] * center_dist)
        a_in = math.atan2(p_in[1] - center[1], p_in[0] - center[0])
        a_out = math.atan2(p_out[1] - center[1], p_out[0] - center[0])
        sweep = a_out - a_in
        while sweep <= 0:
            sweep += 2 * math.pi
        steps = 16
        for s in range(steps + 1):
            a = a_in + sweep * s / steps
            pts.append(
                (center[0] + HEX_CORNER_R * math.cos(a), center[1] + HEX_CORNER_R * math.sin(a))
            )
    return pts


def _unit(vec: tuple[float, float]) -> tuple[float, float]:
    mag = math.hypot(*vec)
    return (vec[0] / mag, vec[1] / mag)


def draw_mark_mask(size_px: int) -> Image.Image:
    """L-mode mask: 255 inside the hexagon, 0 in the cut-out interior."""
    scale = size_px * SS / 24.0
    img = Image.new("L", (size_px * SS, size_px * SS), 0)
    draw = ImageDraw.Draw(img)
    hex_pts = [(x * scale, y * scale) for x, y in hexagon_points()]
    draw.polygon(hex_pts, fill=255)
    cut_w = max(1, round(CUT_WIDTH * scale))
    for line in CUT_POLYLINES:
        pts = [(x * scale, y * scale) for x, y in line]
        draw.line(pts, fill=0, width=cut_w, joint="curve")
        r = cut_w / 2
        for x, y in pts:
            draw.ellipse((x - r, y - r, x + r, y + r), fill=0)
    return img


def render_logo() -> Path:
    mask = draw_mark_mask(512)
    color = Image.new("RGBA", mask.size, ACCENT + (255,))
    color.putalpha(mask)
    out = color.resize((512, 512), Image.LANCZOS)
    path = HERE / "logo.png"
    out.save(path, optimize=True)
    return path


def _font(size: int, weight: int) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if weight >= 600 else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size * SS)


def _draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: float,
    baseline_y: float,
    size: int,
    weight: int,
    tracking: float,
    fill: tuple[int, int, int],
) -> None:
    font = _font(size, weight)
    x = center_x * SS
    if tracking:
        total = sum(font.getlength(ch) + tracking * SS for ch in text) - tracking * SS
        x -= total / 2
        for ch in text:
            draw.text((x, baseline_y * SS), ch, font=font, fill=fill, anchor="ls")
            x += font.getlength(ch) + tracking * SS
    else:
        draw.text((x, baseline_y * SS), text, font=font, fill=fill, anchor="ms")


def render_social_preview() -> Path:
    width, height = 1280, 640
    img = Image.new("RGB", (width * SS, height * SS), SLATE_900)
    draw = ImageDraw.Draw(img)

    # Mark (hexagon with cut interior), white, 120x120 centered
    mx, my, msize = SP_MARK_BOX
    mask = draw_mark_mask(int(msize))
    mark = Image.new("RGBA", mask.size, SLATE_100 + (255,))
    mark.putalpha(mask)
    mark = mark.resize((int(msize * SS), int(msize * SS)), Image.LANCZOS)
    img.paste(mark, (round(mx * SS), round(my * SS)), mark)

    _draw_text(draw, *(_take(SP_WORDMARK)), fill=SLATE_100)
    _draw_text(draw, *(_take(SP_TAGLINE)), fill=SLATE_400)
    _draw_text(draw, *(_take(SP_URL)), fill=SLATE_400)

    out = img.resize((width, height), Image.LANCZOS)
    path = HERE / "social-preview.png"
    out.save(path, optimize=True)
    return path


def _take(spec: tuple) -> tuple:
    text, size, weight, baseline, tracking = spec
    return (text, 640.0, baseline, size, weight, tracking)


def _check(path: Path, size: tuple[int, int], opaque: bool) -> None:
    with Image.open(path) as im:
        if im.size != size:
            raise SystemExit(f"{path.name}: {im.size} != {size}")
        want = "RGB" if opaque else "RGBA"
        if im.mode != want:
            raise SystemExit(f"{path.name}: mode {im.mode} != {want}")
        mode = im.mode
    kb = path.stat().st_size / 1024
    if kb >= 200:
        raise SystemExit(f"{path.name}: {kb:.0f} KB >= 200 KB")
    print(f"  {path.name}: {size[0]}x{size[1]} {mode} {kb:.1f} KB")


def main() -> None:
    logo = render_logo()
    social = render_social_preview()
    _check(logo, (512, 512), opaque=False)
    _check(social, (1280, 640), opaque=True)


if __name__ == "__main__":
    main()
