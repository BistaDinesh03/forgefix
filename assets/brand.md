# ForgeFix visual identity

Single source of truth for colors, type, and asset usage. Keep every surface
(README, docs, demo, social) consistent with this file.

## Color palette

| Token | Hex | Use |
| --- | --- | --- |
| Primary (slate-900) | `#0F172A` | Text on light surfaces, banner background, terminal margin |
| Accent (blue-600) | `#2563EB` | Links, calls to action, `logo.png` mark |
| Success (green-600) | `#16A34A` | Passing checks, score improvement, checkmark accent |
| Warn (amber-600) | `#D97706` | Warning states in docs examples |
| Fail (red-600) | `#DC2626` | Failing states in docs examples |
| BG light | `#FFFFFF` | Page background |
| BG subtle | `#F8FAFC` | Cards, table stripes, code-block chrome |
| Slate-200 | `#E2E8F0` | Mark on dark surfaces (`logo-dark.svg`, banner) |
| Slate-400 | `#94A3B8` | Secondary text on dark surfaces (tagline) |

Rules: flat fills only; no multi-stop gradients on the mark; at most one accent
color per surface.

## Typography

Use GitHub's rendered defaults everywhere (system sans stack for prose,
GitHub's monospace for code). Do not embed custom web fonts — they break
rendering and add weight. Hierarchy comes from spacing, weight, and size.

Demo terminal: **Catppuccin Mocha** (`demo/demo.tape`), JetBrains Mono 18.
Dracula is the accepted alternate theme.

## Assets

| File | Size | Purpose |
| --- | --- | --- |
| `logo.svg` | 24x24 viewBox | Primary mark, uses `currentColor` (dark on light) |
| `logo-dark.svg` | 24x24 viewBox | Mark for dark surfaces (slate-200) |
| `logo.png` | 512x512 | Raster mark (accent blue, transparent background) |
| `banner.svg` | 1280x320 | README hero: mark + wordmark + tagline |
| `social-preview.png` | 1280x640 | GitHub social preview / link card |
| `badge-score.svg` | 1280x640 slot | Static "health: 42 -> 91" badge |

The mark is a pointy-top hexagon (radius 10, centered at 12,12 in a 24-unit
viewbox) with a monoline "F" (stem 2 units wide, round caps). It reads at
24 px and at 200 px because every proportion is relative to the viewbox.

Rasters are generated from these coordinates by `assets/render_rasters.py`
(Pillow). Regenerate with:

```bash
python assets/render_rasters.py
```

## Licensing

All assets in this directory are original work, MIT licensed with the rest of
the repository (see `LICENSE`). No third-party icon sets are embedded.
