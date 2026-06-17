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
    markdown: Path
    pdf: Optional[Path]
    strong_matches: List[str]
    gaps: List[str]
    reason: str

    @classmethod
    def from_result(
        cls,
        vacancy: VacancyDetails,
        match_score: MatchScore,
        markdown_path: Path,
        pdf_path: Optional[Path],
    ) -> "VacancyReportItem":
        return cls(
            score=match_score.score,
            title=vacancy.title,
            company=vacancy.company,
            url=vacancy.url,
            markdown=markdown_path,
            pdf=pdf_path,
            strong_matches=match_score.strong_matches,
            gaps=match_score.gaps,
            reason=match_score.reason,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "pdf": str(self.pdf) if self.pdf is not None else None,
            "markdown": str(self.markdown),
            "strong_matches": self.strong_matches,
            "gaps": self.gaps,
            "reason": self.reason,
        }
