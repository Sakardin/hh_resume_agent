import unittest
from pathlib import Path

from resume.prompt_parser import PromptSequenceParser


class PromptSequenceParserTest(unittest.TestCase):
    def test_parse_current_prompts_file(self) -> None:
        raw_text = Path("data/prompts.md").read_text(encoding="utf-8")

        parsed = PromptSequenceParser().parse(raw_text)

        self.assertIn("Включи режим рекрутера", parsed.recruiter_review_prompt)
        self.assertIn("Перевод с языка кандидата на язык HR", parsed.rewrite_prompt)
        self.assertIn("Проверка на", parsed.interview_review_prompt)
        self.assertIsNotNone(parsed.vacancy_adaptation_prompt)


if __name__ == "__main__":
    unittest.main()
