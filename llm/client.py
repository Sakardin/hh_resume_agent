import logging
import re
from typing import Protocol

from openai import OpenAI

from llm.exceptions import LlmError

logger = logging.getLogger(__name__)
WHITESPACE_PATTERN = re.compile(r"\s+")


class LlmClient(Protocol):
    def ask(self, prompt: str) -> str:
        ...


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "ollama",
        temperature: float = 0.2,
        debug: bool = False,
        log_preview_chars: int = 800,
    ) -> None:
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._debug = debug
        self._log_preview_chars = log_preview_chars

    def ask(self, prompt: str) -> str:
        if self._debug:
            logger.info(
                "LLM request model=%s prompt_chars=%s prompt_preview=%r",
                self._model,
                len(prompt),
                self._preview_text(prompt),
            )

        result = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты опытный рекрутер и карьерный консультант. "
                        "Пиши точно. Не выдумывай опыт."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=self._temperature,
        )

        content = result.choices[0].message.content
        if not content:
            raise LlmError("LLM returned an empty response")

        if self._debug:
            logger.info(
                "LLM response model=%s response_chars=%s response_preview=%r",
                self._model,
                len(content),
                self._preview_text(content),
            )

        return content

    def _preview_text(self, text: str) -> str:
        normalized = WHITESPACE_PATTERN.sub(" ", text).strip()
        if len(normalized) <= self._log_preview_chars:
            return normalized
        return normalized[: self._log_preview_chars] + "..."
