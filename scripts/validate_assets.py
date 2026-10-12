"""Validate the visual identity assets (Phase 1F checks).

Run from anywhere:  python scripts/validate_assets.py

Checks per SVG: XML well-formed, <title> present, under 50 KB, no external
references, viewBox matches width/height, coordinates inside the viewBox.
Checks per PNG: dimensions, alpha, under 200 KB.
Checks banners/social previews: exact grid math from assets/brand.md.
Checks the sibling rule: both projects share the same hexagon path.
Prints WCAG contrast ratios for the palette pairs.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SVG_NS = "{http://www.w3.org/2000/svg}"

# Shared hexagon (must be identical in both repos)
HEX_PATH = (
    "M13 2.077 L20.093 6.173 A2 2 0 0 1 21.093 7.905 L21.093 16.095 "
    "A2 2 0 0 1 20.093 17.827 L13 21.923 A2 2 0 0 1 11 21.923 L3.907 17.827 "
    "A2 2 0 0 1 2.907 16.095 L2.907 7.905 A2 2 0 0 1 3.907 6.173 L11 2.077 "
    "A2 2 0 0 1 13 2.077 Z"
)

PROFILES = {
    "ForgeFix": {
        "wordmark": "ForgeFix",
        "tagline": "One command to fix any repo's setup.",
        "url": "github.com/BistaDinesh03/forgefix",
    },
    "TrendForge": {
        "wordmark": "TrendForge",
        "tagline": "See what's trending. Build what's missing.",
        "url": "github.com/BistaDinesh03/trendforge",
    },
}

SVG_FILES = [
    "logo.svg",
    "logo-dark.svg",
    "logo-mono.svg",
    "favicon.svg",
    "banner.svg",
    "banner-dark.svg",
    "social-preview.svg",
]

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  FAIL {msg}")


def ok(msg: str) -> None:
    print(f"  ok   {msg}")


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def attr_numbers(el: ET.Element) -> list[float]:
    nums: list[float] = []
    for name in ("x", "y", "width", "height", "cx", "cy", "r", "rx", "ry", "font-size"):
        if name in el.attrib and re.fullmatch(r"-?\d+(\.\d+)?", el.attrib[name]):
            nums.append(float(el.attrib[name]))
    if "d" in el.attrib:
        nums.extend(float(n) for n in re.findall(r"-?\d+\.?\d*", el.attrib["d"]))
    return nums


def walk(el: ET.Element):
    yield el
    for child in el:
        yield from walk(child)


def check_svg(name: str, profile: dict) -> None:
    path = ASSETS / name
    if not path.is_file():
        fail(f"{name}: missing")
        return
    size = path.stat().st_size
    if size >= 50 * 1024:
        fail(f"{name}: {size} B >= 50 KB")
    else:
        ok(f"{name}: {size} B < 50 KB")

    try:
        # S314: parses only this repo's own committed SVGs (trusted input).
        tree = ET.parse(path)  # noqa: S314
    except ET.ParseError as exc:
        fail(f"{name}: XML parse error: {exc}")
        return

    root = tree.getroot()
    if local(root.tag) != "svg":
        fail(f"{name}: root is not <svg>")
        return

    vb = root.attrib.get("viewBox", "")
    m = re.fullmatch(r"0 0 (\d+) (\d+)", vb)
    if not m:
        fail(f"{name}: viewBox '0 0 W H' expected, got '{vb}'")
        return
    vbw, vbh = int(m.group(1)), int(m.group(2))
    if (root.attrib.get("width"), root.attrib.get("height")) != (str(vbw), str(vbh)):
        fail(f"{name}: width/height do not match viewBox")

    if not any(local(e.tag) == "title" and (e.text or "").strip() for e in walk(root)):
        fail(f"{name}: missing <title>")

    raw = path.read_text(encoding="utf-8")
    for bad in ("<image", "http-equiv", "@import", "href=", "foreignObject"):
        if bad in raw:
            fail(f"{name}: external/forbidden reference: {bad}")
    if re.search(r"url\(\s*['\"]?https?://", raw):
        fail(f"{name}: external url() reference")

    # coordinates inside viewBox (arc flags and numbers included)
    for el in walk(root):
        if local(el.tag) in ("mask", "defs", "g"):
            continue
        for n in attr_numbers(el):
            if not (0 <= n <= max(vbw, vbh) + 0.01):
                fail(f"{name}: coordinate {n} outside 0..{max(vbw, vbh)} in <{local(el.tag)}>")
                break

    for el in walk(root):
        fam = el.attrib.get("font-family", "")
        if fam and not fam.rstrip().endswith("sans-serif"):
            fail(f"{name}: font-family must end with sans-serif: {fam}")

    # sibling rule: shared hexagon
    hex_paths = [
        e.attrib.get("d", "").replace("\n", " ")
        for e in walk(root)
        if "M13 2.077" in e.attrib.get("d", "")
    ]
    if name.startswith(("logo", "banner", "social")) or name == "favicon.svg":
        if not hex_paths:
            # favicon uses the 32-unit hexagon; check that variant instead
            if name == "favicon.svg" and not any(
                "M17.35 2.78" in e.attrib.get("d", "") for e in walk(root)
            ):
                fail(f"{name}: shared hexagon path not found")
        else:
            normalized = " ".join(hex_paths[0].split())
            if normalized != HEX_PATH:
                fail(f"{name}: hexagon path deviates from the shared path")

    if name == "logo.svg" and "currentColor" not in raw:
        fail("logo.svg: must use currentColor")

    # equal stroke weights: every cut stroke in a mark is width 4
    if name in ("logo.svg", "logo-dark.svg", "logo-mono.svg"):
        widths = {e.attrib["stroke-width"] for e in walk(root) if e.attrib.get("stroke-width")}
        if widths != {"4"}:
            fail(f"{name}: cut stroke widths {widths} != {{'4'}}")
        else:
            ok(f"{name}: single stroke weight 4 (equal weights)")


def texts(root: ET.Element) -> list[ET.Element]:
    return [e for e in walk(root) if local(e.tag) == "text"]


def check_banner(name: str, profile: dict) -> None:
    path = ASSETS / name
    if not path.is_file():
        fail(f"{name}: missing")
        return
    root = ET.parse(path).getroot()  # noqa: S314
    raw = path.read_text(encoding="utf-8")

    if not re.search(r'transform="translate\(64 112\) scale\(4\)"', raw):
        fail(f"{name}: mark not at translate(64 112) scale(4) (96px box, y=112)")
    if 'width="1280" height="320"' not in raw:
        fail(f"{name}: not 1280x320")

    # transparent: no full-canvas background rect
    for el in walk(root):
        if (
            local(el.tag) == "rect"
            and el.attrib.get("width") == "1280"
            and el.attrib.get("height") == "320"
            and "mask" not in el.attrib
        ):
            fail(f"{name}: has a full-canvas background (must be transparent)")

    by_size: dict[str, ET.Element] = {}
    for t in texts(root):
        by_size.setdefault(t.attrib.get("font-size", ""), t)
    word = by_size.get("64")
    tag = by_size.get("22")
    url = by_size.get("16")
    if word is None or (word.text or "").strip() != profile["wordmark"]:
        fail(f"{name}: wordmark wrong or missing")
    else:
        if word.attrib.get("x") != "184" or word.attrib.get("y") != "160":
            fail(f"{name}: wordmark must sit at x=184 baseline y=160 (mark center)")
        if word.attrib.get("font-weight") != "700" or word.attrib.get("letter-spacing") != "-1":
            fail(f"{name}: wordmark must be weight 700, letter-spacing -1")
        ok(f"{name}: wordmark grid (x=184, baseline=160, 700/-1)")
    if tag is None or (tag.text or "").strip() != profile["tagline"]:
        fail(f"{name}: tagline wrong or missing")
    else:
        if tag.attrib.get("x") != "184" or tag.attrib.get("y") != "200":
            fail(f"{name}: tagline must sit at x=184 baseline y=200")
        ok(f"{name}: tagline baseline y=200 (no overlap)")
    if url is None or (url.text or "").strip() != profile["url"]:
        fail(f"{name}: URL wrong or missing")
    else:
        if (
            url.attrib.get("x") != "1216"
            or url.attrib.get("y") != "256"
            or url.attrib.get("text-anchor") != "end"
        ):
            fail(f"{name}: URL must be end-anchored at x=1216 baseline y=256")
        if url.attrib.get("fill") != "#94A3B8":
            fail(f"{name}: URL fill must be #94A3B8 (readable, not faded)")
        ok(f"{name}: URL bottom-right, fill #94A3B8, 64px above bottom")

    for t in texts(root):
        fam = t.attrib.get("font-family", "")
        if not fam.endswith("sans-serif"):
            fail(f"{name}: text font-family must end with sans-serif")

    # tagline max width 800: estimated at 0.5em average glyph width
    est = len(profile["tagline"]) * 0.5 * 22
    if est > 800:
        fail(f"{name}: tagline estimated width {est:.0f} > 800")
    else:
        ok(f"{name}: tagline width ~{est:.0f}px <= 800")


def check_social(name: str, profile: dict) -> None:
    path = ASSETS / name
    if not path.is_file():
        fail(f"{name}: missing")
        return
    raw = path.read_text(encoding="utf-8")
    root = ET.parse(path).getroot()  # noqa: S314

    if not re.search(r'<rect width="1280" height="640" fill="#0F172A"/>', raw):
        fail(f"{name}: missing opaque #0F172A background")
    if not re.search(r'transform="translate\(580 96\) scale\(5\)"', raw):
        fail(f"{name}: mark not centered at translate(580 96) scale(5)")

    sizes = {t.attrib.get("font-size") for t in texts(root)}
    if not {"72", "26", "18"} <= sizes:
        fail(f"{name}: expected font sizes 72/26/18, got {sizes}")
    anchors = {t.attrib.get("text-anchor") for t in texts(root)}
    if anchors != {"middle"}:
        fail(f"{name}: all text must be centered, got {anchors}")
    baselines = {t.attrib.get("y") for t in texts(root)}
    if baselines != {"304", "352", "568"}:
        fail(f"{name}: baselines {baselines} != 304/352/568")
    ok(f"{name}: centered layout, baselines 304/352/568")


def check_pngs() -> None:
    specs = {
        "logo.png": ((512, 512), "RGBA"),
        "social-preview.png": ((1280, 640), "RGB"),
    }
    for name, (size, mode) in specs.items():
        path = ASSETS / name
        if not path.is_file():
            fail(f"{name}: missing")
            continue
        kb = path.stat().st_size / 1024
        with Image.open(path) as im:
            if im.size != size:
                fail(f"{name}: {im.size} != {size}")
            if im.mode != mode:
                fail(f"{name}: mode {im.mode} != {mode}")
        if kb >= 200:
            fail(f"{name}: {kb:.0f} KB >= 200 KB")
        else:
            ok(f"{name}: {size[0]}x{size[1]} {mode} {kb:.1f} KB < 200 KB")


def _lin(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(hex_a: str, hex_b: str) -> float:
    def lum(h: str) -> float:
        r, g, b = (int(h[i : i + 2], 16) for i in (1, 3, 5))
        return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

    la, lb = lum(hex_a), lum(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def check_contrast() -> None:
    pairs = [
        ("mark light #0F172A on #FFFFFF", "#0F172A", "#FFFFFF", 7.0),
        ("mark dark #F8FAFC on #0F172A", "#F8FAFC", "#0F172A", 7.0),
        ("logo.png #2563EB on #FFFFFF", "#2563EB", "#FFFFFF", 4.5),
        ("tagline #475569 on #FFFFFF", "#475569", "#FFFFFF", 4.5),
        ("tagline dark #94A3B8 on #0F172A", "#94A3B8", "#0F172A", 4.5),
        ("URL #94A3B8 on #0F172A", "#94A3B8", "#0F172A", 4.5),
        ("URL #94A3B8 on #FFFFFF (brief-mandated, informational)", "#94A3B8", "#FFFFFF", 0.0),
    ]
    print("  contrast ratios:")
    for label, a, b, threshold in pairs:
        ratio = contrast(a, b)
        flag = "ok  " if ratio >= threshold else "FAIL"
        if threshold == 0.0:
            flag = "info"
        print(f"    {flag} {label}: {ratio:.2f}:1")
        if threshold and ratio < threshold:
            fail(f"contrast {label}: {ratio:.2f} < {threshold}")


def main() -> int:
    banner = (ASSETS / "banner.svg").read_text(encoding="utf-8")
    profile = next((p for p in PROFILES.values() if p["wordmark"] in banner), None)
    if profile is None:
        print("FAIL: could not identify project profile from banner.svg")
        return 1
    print(f"validating {profile['wordmark']} assets in {ASSETS}")

    for name in SVG_FILES:
        check_svg(name, profile)
    for name in ("banner.svg", "banner-dark.svg"):
        check_banner(name, profile)
    check_social("social-preview.svg", profile)
    check_pngs()
    check_contrast()

    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall asset checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
