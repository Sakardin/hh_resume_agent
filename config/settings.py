import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Union

from dotenv import load_dotenv


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path


def _get_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw_value = env.get(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from error


def _get_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw_value = env.get(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(f"{name} must be a boolean, got {raw_value!r}")


@dataclass(frozen=True)
class AppConfig:
    ollama_model: str
    ollama_base_url: str
    llm_debug: bool
    llm_log_preview_chars: int
    hh_area: int
    min_match_score: int
    max_results_per_keyword: int
    headless: bool
    browser_profile_dir: Path
    output_dir: Path
    seen_vacancies_path: Path
    resume_path: Path
    prompts_path: Path
    keywords_path: Path
    page_timeout_ms: int
    retry_attempts: int
    retry_delay_ms: int
    generate_pdf: bool

    @classmethod
    def from_env(
        cls,
        env_path: Optional[Union[str, Path]] = ".env",
        base_dir: Optional[Union[str, Path]] = None,
    ) -> "AppConfig":
        if env_path is not None:
            load_dotenv(dotenv_path=env_path)

        root_dir = Path(base_dir) if base_dir is not None else Path.cwd()
        env = os.environ

        return cls(
            ollama_model=env.get("OLLAMA_MODEL", "qwen3:8b"),
            ollama_base_url=env.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            llm_debug=_get_bool(env, "LLM_DEBUG", False),
            llm_log_preview_chars=max(100, _get_int(env, "LLM_LOG_PREVIEW_CHARS", 800)),
            hh_area=_get_int(env, "HH_AREA", 1002),
            min_match_score=_get_int(env, "MIN_MATCH_SCORE", 70),
            max_results_per_keyword=_get_int(env, "MAX_RESULTS_PER_KEYWORD", 10),
            headless=_get_bool(env, "HH_HEADLESS", False),
            browser_profile_dir=_resolve_path(
                root_dir,
                env.get("BROWSER_PROFILE_DIR", "browser_profile"),
            ),
            output_dir=_resolve_path(root_dir, env.get("OUTPUT_DIR", "output")),
            seen_vacancies_path=_resolve_path(
                root_dir,
                env.get("SEEN_VACANCIES_PATH", "output/seen_vacancies.json"),
            ),
            resume_path=_resolve_path(
                root_dir,
                env.get("RESUME_PATH", "data/resume_master.md"),
            ),
            prompts_path=_resolve_path(
                root_dir,
                env.get("PROMPTS_PATH", "data/prompts.md"),
            ),
            keywords_path=_resolve_path(
                root_dir,
                env.get("KEYWORDS_PATH", "data/keywords.txt"),
            ),
            page_timeout_ms=_get_int(env, "PAGE_TIMEOUT_MS", 60000),
            retry_attempts=max(1, _get_int(env, "BROWSER_RETRY_ATTEMPTS", 2)),
            retry_delay_ms=max(0, _get_int(env, "BROWSER_RETRY_DELAY_MS", 1000)),
            generate_pdf=_get_bool(env, "GENERATE_PDF", True),
        )
