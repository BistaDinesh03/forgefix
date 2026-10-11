"""Prepare a scratch copy of the broken fixture for demo recordings.

Used by demo/demo.tape so recordings exercise the real CLI without mutating
the committed fixture. Works on Windows, macOS, and Linux (no shell quoting).

Prints the copied file list so the demo can show what the repository contains
without relying on platform-specific `ls`/`dir`. Also warms the pip download
cache (setuptools + pytest are what ``forgefix up`` installs into the scratch
venv) so the on-camera bring-up does not spend the shot downloading.
"""

from __future__ import annotations

import shutil
import subprocess  # noqa: S404 - list-argv, shell=False only # nosec B404
import sys
import tempfile
from pathlib import Path

SOURCE = Path("tests/fixtures/broken_repo")
TARGET = Path("demo-scratch")


def _warm_pip_cache() -> None:
    """Populate the shared pip cache so the recorded install runs fast."""
    with tempfile.TemporaryDirectory(prefix="forgefix-pipwarm-") as tmp:
        subprocess.run(  # noqa: S603 # nosec B603 - sanitized list argv, no shell
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--quiet",
                "--no-deps",
                "--dest",
                tmp,
                "setuptools",
                "pytest",
            ],
            shell=False,  # noqa: S602 - explicitly never a shell
            check=False,
            capture_output=True,
        )


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"run from the repository root: {SOURCE} not found")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)
    _warm_pip_cache()
    entries = sorted(
        path.relative_to(TARGET).as_posix()
        for path in TARGET.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    print(f"scratch copy ready: {TARGET}")
    for entry in entries:
        print(f"  {entry}")


if __name__ == "__main__":
    main()
