from llm.client import LlmClient
from llm.json_parser import JsonResponseParser
from resume.exceptions import ResumeValidationError
from resume.models import MatchScore, ResumeAdaptationResult, ResumePreparationResult
from resume.prompt_parser import PromptSequence, PromptSequenceParser
from typing import Optional


class ResumeService:
    def __init__(self, llm_client: LlmClient, json_parser: JsonResponseParser) -> None:
        self._llm_client = llm_client
        self._json_parser = json_parser
        self._prompt_parser = PromptSequenceParser()

    def score_vacancy(self, resume_text: str, vacancy_text: str) -> MatchScore:
        prompt = f"""
Оцени, насколько резюме подходит под вакансию.

Ответь строго JSON без markdown:

{{
  "score": 0,
  "strong_matches": [],
  "gaps": [],
  "reason": ""
}}

Правила:
- score от 0 до 100
- не выдумывай опыт
- учитывай только то, что есть в резюме
- если вакансия не QA / AQA / QA Lead, score ниже 50

{self._vacancy_context(vacancy_text)}

{self._resume_context(resume_text)}
"""
        raw_response = self._llm_client.ask(prompt)
        data = self._json_parser.parse_object(raw_response)
        return MatchScore.from_mapping(data)

    def adapt_resume(
        self,
        resume_text: str,
        vacancy_text: str,
        user_prompt: str,
        target_language: str = "English",
    ) -> str:
        return self.adapt_resume_with_comments(
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            user_prompt=user_prompt,
            target_language=target_language,
        ).final_resume_markdown

    def adapt_resume_with_comments(
        self,
        resume_text: str,
        vacancy_text: str,
        user_prompt: str,
        target_language: str,
    ) -> ResumeAdaptationResult:
        prompt_sequence = self._prompt_parser.parse(user_prompt)
        preparation = self._prepare_resume(
            resume_text=resume_text,
            prompt_sequence=prompt_sequence,
            target_language=target_language,
        )
        vacancy_comments, final_resume = self._adapt_for_vacancy(
            preparation=preparation,
            source_resume_text=resume_text,
            vacancy_text=vacancy_text,
            vacancy_prompt=prompt_sequence.vacancy_adaptation_prompt,
            target_language=target_language,
        )
        return ResumeAdaptationResult(
            target_language=target_language,
            recruiter_review=preparation.recruiter_review,
            interview_review=preparation.interview_review,
            vacancy_comments=vacancy_comments,
            final_resume_markdown=final_resume,
        )

    def _prepare_resume(
        self,
        resume_text: str,
        prompt_sequence: PromptSequence,
        target_language: str,
    ) -> ResumePreparationResult:
        recruiter_review = self._ask_markdown(
            f"""
Используй инструкцию ниже как задание для честного рекрутерского разбора.

{prompt_sequence.recruiter_review_prompt}

{self._resume_context(resume_text)}

Правила ответа:
- не переписывай резюме
- дай только разбор в Markdown
- будь конкретен
- верни ответ полностью на русском языке
"""
        )

        rewritten_resume = self._ask_markdown(
            f"""
Используй инструкцию ниже как задание на переписывание резюме.

{prompt_sequence.rewrite_prompt}

{self._resume_context(resume_text)}

Разбор рекрутера:
{recruiter_review}

Правила ответа:
- верни только обновленное резюме в Markdown
- без дополнительных комментариев вокруг резюме
- не добавляй выдуманный опыт
- итоговое резюме должно быть полностью на языке: {target_language}
"""
        )

        interview_review = self._ask_markdown(
            f"""
Используй инструкцию ниже как финальную проверку резюме глазами рекрутера.

{prompt_sequence.interview_review_prompt}

Обновленное резюме:
{rewritten_resume}

Правила ответа:
- верни только комментарии в Markdown
- не переписывай заново резюме
- верни ответ полностью на русском языке
"""
        )

        return ResumePreparationResult(
            recruiter_review=recruiter_review,
            rewritten_resume_markdown=rewritten_resume,
            interview_review=interview_review,
        )

    def _adapt_for_vacancy(
        self,
        preparation: ResumePreparationResult,
        source_resume_text: str,
        vacancy_text: str,
        vacancy_prompt: Optional[str],
        target_language: str,
    ) -> tuple[str, str]:
        if not vacancy_prompt:
            return preparation.interview_review, preparation.rewritten_resume_markdown

        response = self._ask_markdown(
            f"""
Используй инструкцию ниже как задание на адаптацию резюме под вакансию.

{vacancy_prompt}

{self._vacancy_context(vacancy_text)}

{self._resume_context(source_resume_text)}

Подготовленное резюме после внутренней переработки:
{preparation.rewritten_resume_markdown}

Предыдущие комментарии рекрутера:
{preparation.recruiter_review}

Проверка на интервью:
{preparation.interview_review}

Правила ответа:
- ответь строго в Markdown
- используй две секции верхнего уровня:
# Comments
# Resume
- в секции Comments дай только комментарии по адаптации
- в секции Resume дай только итоговое резюме
- не добавляй выдуманный опыт
- не добавляй технологии, которых нет в исходном резюме
- секция Comments должна быть полностью на русском языке
- секция Resume должна быть полностью на языке: {target_language}
"""
        )

        comments, final_resume = self._split_comments_and_resume(response)
        return comments, final_resume

    @staticmethod
    def _vacancy_context(vacancy_text: str) -> str:
        return f"Вот описание вакансии:\n{vacancy_text}"

    @staticmethod
    def _resume_context(resume_text: str) -> str:
        return f"Вот моё резюме:\n{resume_text}"

    def _ask_markdown(self, prompt: str) -> str:
        response = self._strip_outer_markdown_fence(self._llm_client.ask(prompt))
        if not response:
            raise ResumeValidationError("LLM returned an empty response")
        return response

    @staticmethod
    def _split_comments_and_resume(markdown_text: str) -> tuple[str, str]:
        normalized = markdown_text.replace("\r\n", "\n").strip()
        marker = "\n# Resume"

        if not normalized.startswith("# Comments") or marker not in normalized:
            raise ResumeValidationError(
                "LLM must return '# Comments' and '# Resume' sections"
            )

        comments_part, resume_part = normalized.split(marker, 1)
        comments = comments_part[len("# Comments") :].strip()
        final_resume = resume_part.strip()

        if not final_resume:
            raise ResumeValidationError("LLM returned empty resume section")

        return comments, final_resume

    @staticmethod
    def _strip_outer_markdown_fence(text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```") or not stripped.endswith("```"):
            return stripped

        lines = stripped.splitlines()
        if len(lines) <= 2:
            return ""

        return "\n".join(lines[1:-1]).strip()
