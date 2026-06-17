from typing import Any, Dict

from config import AppConfig
from llm import JsonResponseParser, OllamaClient
from resume import ResumeService
from utils import detect_text_language


def _create_resume_service() -> ResumeService:
    config = AppConfig.from_env()
    llm_client = OllamaClient(
        base_url=config.ollama_base_url,
        model=config.ollama_model,
        debug=config.llm_debug,
        log_preview_chars=config.llm_log_preview_chars,
    )
    return ResumeService(llm_client=llm_client, json_parser=JsonResponseParser())


def ask_llm(prompt: str) -> str:
    config = AppConfig.from_env()
    llm_client = OllamaClient(
        base_url=config.ollama_base_url,
        model=config.ollama_model,
        debug=config.llm_debug,
        log_preview_chars=config.llm_log_preview_chars,
    )
    return llm_client.ask(prompt)


def score_vacancy(resume_text: str, vacancy_text: str) -> Dict[str, Any]:
    match_score = _create_resume_service().score_vacancy(resume_text, vacancy_text)
    return match_score.to_report_fields()


def adapt_resume(resume_text: str, vacancy_text: str, user_prompt: str) -> str:
    return _create_resume_service().adapt_resume(
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        user_prompt=user_prompt,
        target_language=detect_text_language(vacancy_text),
    )
