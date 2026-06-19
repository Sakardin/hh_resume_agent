import json
from pathlib import Path
from typing import Iterable, Set
from urllib.parse import urlsplit, urlunsplit


def normalize_vacancy_url(url: str) -> str:
    stripped = url.strip()
    if not stripped:
        return ""

    parts = urlsplit(stripped)
    if not parts.scheme or not parts.netloc:
        return stripped

    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


class SeenVacancyStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Set[str]:
        if not self._path.exists():
            return set()

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return {
                normalized
                for item in payload
                if (normalized := normalize_vacancy_url(str(item)))
            }

        if isinstance(payload, dict):
            raw_urls = payload.get("urls", [])
            if isinstance(raw_urls, list):
                return {
                    normalized
                    for item in raw_urls
                    if (normalized := normalize_vacancy_url(str(item)))
                }

        raise ValueError(f"Invalid seen vacancies payload in {self._path}")

    def save(self, urls: Iterable[str]) -> Path:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        normalized_urls = sorted(
            {normalized for url in urls if (normalized := normalize_vacancy_url(url))}
        )
        self._path.write_text(
            json.dumps({"urls": normalized_urls}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._path
