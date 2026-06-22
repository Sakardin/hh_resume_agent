from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from resume.models import MatchScore
from vacancies.models import VacancyDetails


@dataclass(frozen=True)
class VacancyReportItem:
    score: int
    title: str
    company: str
    url: str
    markdown: Optional[Path]
    pdf: Optional[Path]
    generate_resume_script: Optional[Path]
    strong_matches: List[str]
    gaps: List[str]
    reason: str

    @classmethod
    def from_result(
        cls,
        vacancy: VacancyDetails,
        match_score: MatchScore,
        markdown_path: Optional[Path],
        pdf_path: Optional[Path],
        generate_resume_script_path: Optional[Path] = None,
    ) -> "VacancyReportItem":
        return cls(
            score=match_score.score,
            title=vacancy.title,
            company=vacancy.company,
            url=vacancy.url,
            markdown=markdown_path,
            pdf=pdf_path,
            generate_resume_script=generate_resume_script_path,
            strong_matches=match_score.strong_matches,
            gaps=match_score.gaps,
            reason=match_score.reason,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VacancyReportItem":
        return cls(
            score=int(data["score"]),
            title=str(data["title"]),
            company=str(data.get("company", "")),
            url=str(data["url"]),
            markdown=_optional_path(data.get("markdown")),
            pdf=_optional_path(data.get("pdf")),
            generate_resume_script=_optional_path(data.get("generate_resume_script")),
            strong_matches=[str(item).strip() for item in data.get("strong_matches", [])],
            gaps=[str(item).strip() for item in data.get("gaps", [])],
            reason=str(data.get("reason", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "pdf": str(self.pdf) if self.pdf is not None else None,
            "markdown": str(self.markdown) if self.markdown is not None else None,
            "generate_resume_script": (
                str(self.generate_resume_script)
                if self.generate_resume_script is not None
                else None
            ),
            "strong_matches": self.strong_matches,
            "gaps": self.gaps,
            "reason": self.reason,
        }


def _optional_path(value: Any) -> Optional[Path]:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return Path(normalized)
