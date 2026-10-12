"""FastAPI server exposing the same checks over HTTP.

``GET /health``  - liveness and version
``GET /doctor``  - findings + score for ``?path=<repo>``
``GET /report``  - markdown health report for ``?path=<repo>``
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException

from forgefix import __version__
from forgefix.core.report import render_markdown
from forgefix.core.scanner import scan


def _resolve(path: str) -> Path:
    base = Path.cwd().resolve()
    root = (base / path).expanduser().resolve()
    try:
        root.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="path escapes allowed root") from exc
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"not a directory: {path}")
    return root


def create_app() -> FastAPI:
    """Build the FastAPI application (used by ``forgefix serve`` and uvicorn)."""
    api = FastAPI(
        title="ForgeFix",
        version=__version__,
        description="One command to set up, health-check, and repair any open-source project.",
    )

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @api.get("/doctor")
    def doctor(path: str = ".") -> dict[str, object]:
        root = _resolve(path)
        result = scan(root)
        return {
            "path": str(result.root),
            "score": asdict(result.score),
            "findings": [asdict(finding) for finding in result.findings],
            "plugins": result.plugins,
        }

    @api.get("/report")
    def report(path: str = ".") -> dict[str, object]:
        root = _resolve(path)
        result = scan(root)
        return {
            "path": str(result.root),
            "score": result.score.total,
            "markdown": render_markdown(result),
        }

    return api


app = create_app()
