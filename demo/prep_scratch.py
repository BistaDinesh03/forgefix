"""Prepare a scratch copy of the broken fixture for demo recordings.

Used by demo/demo.tape so recordings exercise the real CLI without mutating
the committed fixture. Works on Windows, macOS, and Linux (no shell quoting).
"""

from __future__ import annotations

import shutil
from pathlib import Path

SOURCE = Path("tests/fixtures/broken_repo")
TARGET = Path("demo-scratch")


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"run from the repository root: {SOURCE} not found")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)
    print(f"scratch copy ready: {TARGET}")


if __name__ == "__main__":
    main()
