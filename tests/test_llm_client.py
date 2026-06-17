import unittest

from llm.client import OllamaClient


class OllamaClientTest(unittest.TestCase):
    def test_preview_text_normalizes_whitespace_and_truncates(self) -> None:
        client = OllamaClient(
            base_url="http://localhost:11434/v1",
            model="test-model",
            debug=True,
            log_preview_chars=10,
        )

        preview = client._preview_text("line 1\n\nline\t\t2 and more")

        self.assertEqual(preview, "line 1 lin...")


if __name__ == "__main__":
    unittest.main()
