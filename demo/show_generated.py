"""Print the generated setup files for the demo recording."""

from pathlib import Path


def main() -> None:
    for name in ("SECURITY.md", "Dockerfile"):
        path = Path(name)
        print(f"--- {name} ---")
        print(path.read_text(encoding="utf-8").rstrip())


if __name__ == "__main__":
    main()
