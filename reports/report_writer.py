import json
from pathlib import Path
from typing import Iterable

from reports.models import VacancyReportItem


class JsonReportWriter:
    def write(self, items: Iterable[VacancyReportItem], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in items]
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
