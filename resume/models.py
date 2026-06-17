from dataclasses import dataclass
from typing import Any, Dict, List, Mapping

from resume.exceptions import ResumeValidationError


@dataclass(frozen=True)
class MatchScore:
    score: int
    strong_matches: List[str]
    gaps: List[str]
    reason: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "MatchScore":
        raw_score = data.get("score")
        try:
            score = int(raw_score)
        except (TypeError, ValueError) as error:
            raise ResumeValidationError(f"Invalid score value: {raw_score!r}") from error

        if score < 0 or score > 100:
            raise ResumeValidationError(f"Score must be between 0 and 100, got {score}")

        return cls(
            score=score,
            strong_matches=_string_list(data.get("strong_matches", []), "strong_matches"),
            gaps=_string_list(data.get("gaps", []), "gaps"),
            reason=str(data.get("reason", "")).strip(),
        )

    def to_report_fields(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "strong_matches": self.strong_matches,
            "gaps": self.gaps,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ResumePreparationResult:
    recruiter_review: str
    rewritten_resume_markdown: str
    interview_review: str


@dataclass(frozen=True)
class ResumeAdaptationResult:
    target_language: str
    recruiter_review: str
    interview_review: str
    vacancy_comments: str
    final_resume_markdown: str

    def render_output_markdown(self) -> str:
        parts = [
            f"# Adapted Resume ({self.target_language})",
            "",
            self.final_resume_markdown,
            "",
            "---",
            "",
            "# Комментарии",
            "",
            "## Комментарии рекрутера",
            "",
            self.recruiter_review,
            "",
            "## Проверка на интервью",
            "",
            self.interview_review,
        ]

        if self.vacancy_comments.strip():
            parts.extend(
                [
                    "",
                    "## Комментарии по вакансии",
                    "",
                    self.vacancy_comments,
                ]
            )

        return "\n".join(parts).strip() + "\n"


def _string_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ResumeValidationError(f"{field_name} must be a list")

    return [str(item).strip() for item in value if str(item).strip()]
