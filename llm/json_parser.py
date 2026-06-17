import json
from typing import Any, Dict

from llm.exceptions import LlmJsonError


class JsonResponseParser:
    def parse_object(self, raw_response: str) -> Dict[str, Any]:
        start = raw_response.find("{")
        end = raw_response.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise LlmJsonError("LLM response does not contain a JSON object")

        json_payload = raw_response[start : end + 1]

        try:
            data = json.loads(json_payload)
        except json.JSONDecodeError as error:
            raise LlmJsonError(f"LLM returned invalid JSON: {error}") from error

        if not isinstance(data, dict):
            raise LlmJsonError("LLM JSON response must be an object")

        return data
