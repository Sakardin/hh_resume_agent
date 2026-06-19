import unittest

from llm.json_parser import JsonResponseParser
from resume.service import ResumeService


class _SequentialLlmClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.prompts = []

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._responses:
            raise AssertionError("Unexpected LLM call")
        return self._responses.pop(0)


class ResumeServiceTest(unittest.TestCase):
    def test_adapt_resume_with_comments_runs_prompt_chain(self) -> None:
        resume_text = "Original resume"
        vacancy_text = "Vacancy text"
        llm_client = _SequentialLlmClient(
            [
                "Weak wording in summary",
                "# Rewritten Resume\n\nBetter content",
                "Strong QA profile",
                "# Comments\n\nBetter aligned with the vacancy\n# Resume\n\n# Final Resume\n\nTailored content",
            ]
        )
        service = ResumeService(
            llm_client=llm_client,
            json_parser=JsonResponseParser(),
        )

        result = service.adapt_resume_with_comments(
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            user_prompt="""
ПРОМПТ 1: Review
Review body

ПРОМПТ 2: Rewrite
Rewrite body

ПРОМПТ 3: Interview
Interview body

ПРОМПТ 4: Vacancy
Vacancy body
""",
            target_language="English",
        )

        self.assertEqual(result.recruiter_review, "Weak wording in summary")
        self.assertEqual(result.interview_review, "Strong QA profile")
        self.assertEqual(result.vacancy_comments, "Better aligned with the vacancy")
        self.assertEqual(result.final_resume_markdown, "# Final Resume\n\nTailored content")
        self.assertIn("## Комментарии рекрутера", result.render_output_markdown())
        self.assertIn("русском языке", llm_client.prompts[0])
        self.assertIn("русском языке", llm_client.prompts[2])
        self.assertIn("Comments должна быть полностью на русском языке", llm_client.prompts[3])
        self.assertIn("Resume должна быть полностью на языке: English", llm_client.prompts[3])
        self.assertIn(resume_text, llm_client.prompts[0])
        self.assertIn(resume_text, llm_client.prompts[1])
        self.assertIn(vacancy_text, llm_client.prompts[3])

    def test_score_vacancy_includes_resume_and_vacancy_text_in_prompt(self) -> None:
        resume_text = "Resume body with QA automation"
        vacancy_text = "Vacancy body with Python and Playwright"
        llm_client = _SequentialLlmClient(
            [
                '{"score": 80, "strong_matches": ["QA"], "gaps": [], "reason": "Relevant"}',
            ]
        )
        service = ResumeService(
            llm_client=llm_client,
            json_parser=JsonResponseParser(),
        )

        result = service.score_vacancy(resume_text=resume_text, vacancy_text=vacancy_text)

        self.assertEqual(result.score, 80)
        self.assertEqual(len(llm_client.prompts), 1)
        self.assertIn(resume_text, llm_client.prompts[0])
        self.assertIn(vacancy_text, llm_client.prompts[0])


if __name__ == "__main__":
    unittest.main()
