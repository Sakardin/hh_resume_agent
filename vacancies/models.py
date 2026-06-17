from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class VacancySummary:
    title: str
    url: str


@dataclass(frozen=True)
class VacancyDetails:
    title: str
    company: str
    url: str
    description: str
    key_skills: List[str]

    def to_prompt_text(self) -> str:
        skills = ", ".join(self.key_skills)
        return (
            f"Название: {self.title}\n"
            f"Компания: {self.company}\n"
            f"Ссылка: {self.url}\n"
            f"Ключевые навыки: {skills}\n"
            f"Описание:\n{self.description}\n"
        )

    def to_language_detection_text(self) -> str:
        skills = ", ".join(self.key_skills)
        return "\n".join(
            part for part in (self.title, self.company, skills, self.description) if part
        )
