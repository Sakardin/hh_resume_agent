import re
from pathlib import Path
from typing import List

INVALID_FILENAME_CHARS = re.compile(r"[^a-zA-Zа-яА-Я0-9_-]+")


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_keywords(path: Path) -> List[str]:
    return [
        line.strip()
        for line in load_text_file(path).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(text: str, max_length: int = 80, default: str = "vacancy") -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", text).strip("_")
    if not cleaned:
        return default
    return cleaned[:max_length].rstrip("_") or default
