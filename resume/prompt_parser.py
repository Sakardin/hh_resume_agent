import re
from dataclasses import dataclass
from typing import Dict, Optional

from resume.exceptions import ResumeValidationError

PROMPT_PATTERN = re.compile(
    r"(?:^|\n)\s*#*\s*ПРОМПТ\s*(\d+)\s*:\s*(.+?)\n+(.*?)(?=\n\s*#*\s*ПРОМПТ\s*\d+\s*:|\Z)",
    re.DOTALL,
)


@dataclass(frozen=True)
class PromptSequence:
    recruiter_review_prompt: str
    rewrite_prompt: str
    interview_review_prompt: str
    vacancy_adaptation_prompt: Optional[str]


class PromptSequenceParser:
    def parse(self, raw_text: str) -> PromptSequence:
        prompts_by_number: Dict[int, str] = {}

        for match in PROMPT_PATTERN.finditer(raw_text):
            prompt_number = int(match.group(1))
            prompt_title = self._normalize_text(match.group(2))
            prompt_body = self._normalize_text(match.group(3))
            prompts_by_number[prompt_number] = f"{prompt_title}\n\n{prompt_body}".strip()

        missing = [number for number in (1, 2, 3) if number not in prompts_by_number]
        if missing:
            raise ResumeValidationError(
                f"Missing prompts in prompts file: {', '.join(str(number) for number in missing)}"
            )

        return PromptSequence(
            recruiter_review_prompt=prompts_by_number[1],
            rewrite_prompt=prompts_by_number[2],
            interview_review_prompt=prompts_by_number[3],
            vacancy_adaptation_prompt=prompts_by_number.get(4),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = text.replace("\uFFFC", "").replace("￼", "")
        cleaned = cleaned.replace("«", '"').replace("»", '"')
        return cleaned.strip()
