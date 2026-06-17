import json
from pathlib import Path
from typing import Iterable, Set


class SeenVacancyStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Set[str]:
        if not self._path.exists():
            return set()

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return {str(item).strip() for item in payload if str(item).strip()}

        if isinstance(payload, dict):
            raw_urls = payload.get("urls", [])
            if isinstance(raw_urls, list):
                return {str(item).strip() for item in raw_urls if str(item).strip()}

        raise ValueError(f"Invalid seen vacancies payload in {self._path}")

    def save(self, urls: Iterable[str]) -> Path:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        normalized_urls = sorted({url.strip() for url in urls if url.strip()})
        self._path.write_text(
            json.dumps({"urls": normalized_urls}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._path
