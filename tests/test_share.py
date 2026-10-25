"""Tests for the shareable score text."""

from pathlib import Path

from forgefix.core.share import SHARE_TEXT, build_share_text, find_demo_gif


def test_share_text_contains_required_sentence() -> None:
    text = build_share_text(
        96,
        "https://github.com/acme/demo",
        "https://github.com/acme/demo/blob/main/demo/demo.gif",
    )
    assert text.startswith("My repo just scored a 96/100 on Setup Health with ForgeFix!")
    assert "🛠️" in text
    assert "pip install forgefix" in text
    assert "Repo: https://github.com/acme/demo" in text
    assert "Demo: https://github.com/acme/demo/blob/main/demo/demo.gif" in text


def test_share_text_without_links() -> None:
    assert build_share_text(42) == SHARE_TEXT.format(score=42)


def test_find_demo_gif_prefers_root(tmp_path: Path) -> None:
    root_gif = tmp_path / "root.gif"
    root_gif.write_bytes(b"GIF89a")
    demo = tmp_path / "demo"
    demo.mkdir()
    (demo / "demo.gif").write_bytes(b"GIF89a")
    assert find_demo_gif(tmp_path) == root_gif


def test_find_demo_gif_falls_back_to_demo_dir(tmp_path: Path) -> None:
    (tmp_path / "demo").mkdir()
    gif = tmp_path / "demo" / "demo.gif"
    gif.write_bytes(b"GIF89a")
    assert find_demo_gif(tmp_path) == gif


def test_find_demo_gif_returns_none(tmp_path: Path) -> None:
    assert find_demo_gif(tmp_path) is None
