import unittest

from llm.exceptions import LlmJsonError
from llm.json_parser import JsonResponseParser


class JsonResponseParserTest(unittest.TestCase):
    def test_parse_object_from_noisy_response(self) -> None:
        parser = JsonResponseParser()

        data = parser.parse_object('text before {"score": 75, "reason": "ok"} text after')

        self.assertEqual(data["score"], 75)
        self.assertEqual(data["reason"], "ok")

    def test_raise_for_missing_json_object(self) -> None:
        parser = JsonResponseParser()

        with self.assertRaises(LlmJsonError):
            parser.parse_object("score: 75")


if __name__ == "__main__":
    unittest.main()
