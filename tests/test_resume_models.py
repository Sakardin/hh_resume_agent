import unittest

from resume.exceptions import ResumeValidationError
from resume.models import MatchScore, ResumeAdaptationResult


class MatchScoreTest(unittest.TestCase):
    def test_create_from_valid_mapping(self) -> None:
        match_score = MatchScore.from_mapping(
            {
                "score": "82",
                "strong_matches": ["Python", "Playwright"],
                "gaps": [""],
                "reason": "Relevant QA background",
            }
        )

        self.assertEqual(match_score.score, 82)
        self.assertEqual(match_score.strong_matches, ["Python", "Playwright"])
        self.assertEqual(match_score.gaps, [])
        self.assertEqual(match_score.reason, "Relevant QA background")

    def test_reject_out_of_range_score(self) -> None:
        with self.assertRaises(ResumeValidationError):
            MatchScore.from_mapping({"score": 101})

    def test_reject_non_list_fields(self) -> None:
        with self.assertRaises(ResumeValidationError):
            MatchScore.from_mapping({"score": 80, "strong_matches": "Python"})

    def test_render_output_markdown_includes_target_language(self) -> None:
        result = ResumeAdaptationResult(
            target_language="Russian",
            recruiter_review="review",
            interview_review="interview",
            vacancy_comments="vacancy",
            final_resume_markdown="# Resume\n\ncontent",
        )

        output = result.render_output_markdown()

        self.assertIn("# Adapted Resume (Russian)", output)
        self.assertIn("## Комментарии рекрутера", output)
        self.assertIn("## Комментарии по вакансии", output)


if __name__ == "__main__":
    unittest.main()
