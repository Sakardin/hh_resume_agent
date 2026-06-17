import tempfile
import unittest
from pathlib import Path

from utils.files import clean_filename, load_keywords
from utils.language import detect_text_language


class FileUtilsTest(unittest.TestCase):
    def test_clean_filename_keeps_letters_numbers_and_underscores(self) -> None:
        self.assertEqual(
            clean_filename("Senior QA / AQA Engineer: Java"),
            "Senior_QA_AQA_Engineer_Java",
        )

    def test_clean_filename_uses_default_for_empty_result(self) -> None:
        self.assertEqual(clean_filename("!!!"), "vacancy")

    def test_load_keywords_skips_empty_lines_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keywords.txt"
            path.write_text("QA\n\n# comment\nAQA\n", encoding="utf-8")

            self.assertEqual(load_keywords(path), ["QA", "AQA"])

    def test_detect_text_language_returns_russian_for_cyrillic_text(self) -> None:
        self.assertEqual(detect_text_language("Тестирование API и UI"), "Russian")

    def test_detect_text_language_returns_english_for_latin_text(self) -> None:
        self.assertEqual(detect_text_language("API and UI testing"), "English")


if __name__ == "__main__":
    unittest.main()
