"""Prepare a scratch project for the ForgeFix demo recording.

Creates a tiny, dependency-free Node project so the demo can show stack
detection, `.env.example` scanning (`process.env`), a generated Node
`Dockerfile`, and a real `npm test` run without spending time on installs.

The current demo GIF is copied into the scratch tree so ``forgefix share`` can
show the demo link at the end of the recording. The tape runs this script from
the repository root, then changes into ``demo-scratch``.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path

TARGET = Path("demo-scratch")
GIF = Path("demo/demo.gif")

PACKAGE = {
    "name": "forgefix-demo",
    "version": "1.0.0",
    "private": True,
    "scripts": {"test": "node -e \"console.log('tests pass')\""},
}

INDEX = """const token = process.env.APP_TOKEN;

console.log(token ? "APP_TOKEN is configured" : "Set APP_TOKEN to run");
"""

# A lockfile with no dependencies keeps `npm ci` fast and offline during the
# recording; the bring-up still runs the real install and test commands.
LOCK = {
    "name": "forgefix-demo",
    "version": "1.0.0",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {"": {"name": "forgefix-demo", "version": "1.0.0"}},
}


def _force_remove(func, path, exc_info):  # type: ignore[no-untyped-def]
    """Clear Windows read-only bits left by a previous recording, then retry."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        pass


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET, onerror=_force_remove)
    TARGET.mkdir()
    (TARGET / "package.json").write_text(json.dumps(PACKAGE, indent=2) + "\n", encoding="utf-8")
    (TARGET / "package-lock.json").write_text(json.dumps(LOCK, indent=2) + "\n", encoding="utf-8")
    (TARGET / "index.js").write_text(INDEX, encoding="utf-8")
    if GIF.is_file():
        (TARGET / "demo").mkdir()
        shutil.copy2(GIF, TARGET / "demo" / "demo.gif")
    print(f"scratch ready: {TARGET} (Node app + test)")


if __name__ == "__main__":
    main()
