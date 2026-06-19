import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from browser import PlaywrightBrowserSession
from config import AppConfig
from export import FileMarkdownExporter, MarkdownExporter, PdfExporter
from llm import JsonResponseParser, OllamaClient
from reports import (
    BrowserReportOpener,
    HtmlReportWriter,
    JsonReportWriter,
    MarkdownPreviewWriter,
    SeenVacancyStore,
    VacancyReportItem,
    normalize_vacancy_url,
)
from resume import MatchScore, ResumeAdaptationResult, ResumeService
from utils import (
    clean_filename,
    detect_text_language,
    ensure_directory,
    load_keywords,
    load_text_file,
)
from vacancies import HhVacancyRepository, VacancyDetails

logger = logging.getLogger(__name__)
WHITESPACE_PATTERN = re.compile(r"\s+")


class ResumePipeline:
    def __init__(
        self,
        config: AppConfig,
        vacancy_repository: HhVacancyRepository,
        resume_service: ResumeService,
        markdown_exporter: MarkdownExporter,
        pdf_exporter: Optional[PdfExporter],
        report_writer: JsonReportWriter,
        html_report_writer: HtmlReportWriter,
        markdown_preview_writer: MarkdownPreviewWriter,
        seen_vacancy_store: SeenVacancyStore,
        report_opener: Optional[BrowserReportOpener],
    ) -> None:
        self._config = config
        self._vacancy_repository = vacancy_repository
        self._resume_service = resume_service
        self._markdown_exporter = markdown_exporter
        self._pdf_exporter = pdf_exporter
        self._report_writer = report_writer
        self._html_report_writer = html_report_writer
        self._markdown_preview_writer = markdown_preview_writer
        self._seen_vacancy_store = seen_vacancy_store
        self._report_opener = report_opener

    def run(self) -> Path:
        resume_text = load_text_file(self._config.resume_path)
        prompts_text = load_text_file(self._config.prompts_path)
        keywords = load_keywords(self._config.keywords_path)
        ensure_directory(self._config.output_dir)
        run_output_dir = self._create_run_output_dir(self._config.output_dir)
        persisted_seen_urls = self._seen_vacancy_store.load()

        report_items: List[VacancyReportItem] = []
        report_path = run_output_dir / "report.json"
        html_report_path = run_output_dir / "report.html"

        if not keywords:
            self._report_writer.write(report_items, report_path)
            self._html_report_writer.write(report_items, html_report_path, report_path)
            self._open_report(html_report_path)
            logger.info("No keywords found. Empty report written to %s", report_path)
            return report_path

        seen_urls: Set[str] = set()
        used_file_names: Set[str] = set()

        with self._vacancy_repository:
            for keyword in keywords:
                logger.info("Searching vacancies for keyword: %s", keyword)
                vacancies = self._vacancy_repository.search(keyword)

                for summary in vacancies:
                    normalized_summary_url = normalize_vacancy_url(summary.url)
                    if not normalized_summary_url:
                        continue

                    if normalized_summary_url in persisted_seen_urls:
                        logger.info("Skipping previously viewed vacancy: %s", summary.url)
                        continue

                    if normalized_summary_url in seen_urls:
                        continue

                    seen_urls.add(normalized_summary_url)
                    vacancy = self._load_vacancy(summary.url)
                    if vacancy is None:
                        continue

                    vacancy_text = vacancy.to_prompt_text()
                    match_score = self._score_vacancy(resume_text, vacancy_text, vacancy)
                    if match_score is None:
                        continue

                    logger.info(
                        "%s%% - %s - %s",
                        match_score.score,
                        vacancy.title,
                        vacancy.company,
                    )

                    if match_score.score < self._config.min_match_score:
                        continue

                    adaptation_result = self._adapt_resume(
                        resume_text,
                        vacancy_text,
                        prompts_text,
                        vacancy,
                    )
                    if adaptation_result is None:
                        continue

                    base_name = self._unique_output_name(vacancy.title, used_file_names)
                    markdown_path = run_output_dir / f"{base_name}.md"
                    output_markdown = adaptation_result.render_output_markdown()
                    self._markdown_exporter.export(output_markdown, markdown_path)
                    self._markdown_preview_writer.write(markdown_path)
                    pdf_path = self._export_pdf_path(run_output_dir, base_name, output_markdown)

                    report_items.append(
                        VacancyReportItem.from_result(
                            vacancy=vacancy,
                            match_score=match_score,
                            markdown_path=markdown_path,
                            pdf_path=pdf_path,
                        )
                    )
                    persisted_seen_urls.add(normalized_summary_url)

        self._report_writer.write(report_items, report_path)
        self._html_report_writer.write(report_items, html_report_path, report_path)
        self._seen_vacancy_store.save(persisted_seen_urls)
        self._open_report(html_report_path)
        logger.info("Done. Report written to %s", report_path)
        return report_path

    def _load_vacancy(self, url: str) -> Optional[VacancyDetails]:
        try:
            return self._vacancy_repository.get_details(url)
        except Exception as error:
            logger.warning("Could not open vacancy %s: %s", url, error)
            return None

    def _score_vacancy(
        self,
        resume_text: str,
        vacancy_text: str,
        vacancy: VacancyDetails,
    ) -> Optional[MatchScore]:
        try:
            self._log_llm_inputs(
                stage="score_vacancy",
                resume_text=resume_text,
                vacancy_text=vacancy_text,
                vacancy=vacancy,
            )
            return self._resume_service.score_vacancy(resume_text, vacancy_text)
        except Exception as error:
            logger.warning("Could not score vacancy %s: %s", vacancy.title, error)
            return None

    def _adapt_resume(
        self,
        resume_text: str,
        vacancy_text: str,
        prompts_text: str,
        vacancy: VacancyDetails,
    ) -> Optional[ResumeAdaptationResult]:
        try:
            self._log_llm_inputs(
                stage="adapt_resume",
                resume_text=resume_text,
                vacancy_text=vacancy_text,
                vacancy=vacancy,
            )
            target_language = detect_text_language(vacancy.to_language_detection_text())
            return self._resume_service.adapt_resume_with_comments(
                resume_text=resume_text,
                vacancy_text=vacancy_text,
                user_prompt=prompts_text,
                target_language=target_language,
            )
        except Exception as error:
            logger.warning("Could not adapt resume for %s: %s", vacancy.title, error)
            return None

    def _export_pdf_path(
        self,
        run_output_dir: Path,
        base_name: str,
        adapted_resume: str,
    ) -> Optional[Path]:
        if not self._config.generate_pdf or self._pdf_exporter is None:
            return None

        pdf_path = run_output_dir / f"{base_name}.pdf"
        try:
            self._pdf_exporter.export(adapted_resume, pdf_path)
            return pdf_path
        except Exception as error:
            logger.warning("Could not export PDF %s: %s", pdf_path, error)
            return None

    @staticmethod
    def _create_run_output_dir(base_output_dir: Path, now: Optional[datetime] = None) -> Path:
        timestamp = (now or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
        run_output_dir = base_output_dir / timestamp
        suffix = 2

        while run_output_dir.exists():
            run_output_dir = base_output_dir / f"{timestamp}_{suffix}"
            suffix += 1

        ensure_directory(run_output_dir)
        return run_output_dir

    @staticmethod
    def _unique_output_name(title: str, used_file_names: Set[str]) -> str:
        base_name = clean_filename(title)
        name = base_name
        counter = 2

        while name in used_file_names:
            name = f"{base_name}_{counter}"
            counter += 1

        used_file_names.add(name)
        return name

    def _log_llm_inputs(
        self,
        stage: str,
        resume_text: str,
        vacancy_text: str,
        vacancy: VacancyDetails,
    ) -> None:
        if not self._config.llm_debug:
            return

        logger.info(
            "LLM input stage=%s vacancy=%r resume_preview=%r vacancy_preview=%r",
            stage,
            vacancy.title,
            self._preview_text(f"Вот моё резюме:\n{resume_text}"),
            self._preview_text(f"Вот описание вакансии:\n{vacancy_text}"),
        )

    def _preview_text(self, text: str) -> str:
        normalized = WHITESPACE_PATTERN.sub(" ", text).strip()
        if len(normalized) <= self._config.llm_log_preview_chars:
            return normalized
        return normalized[: self._config.llm_log_preview_chars] + "..."

    def _open_report(self, html_report_path: Path) -> None:
        if not self._config.open_report_in_browser or self._report_opener is None:
            return

        try:
            self._report_opener.open(html_report_path)
        except Exception as error:
            logger.warning("Could not open HTML report %s: %s", html_report_path, error)


def create_pipeline(config: AppConfig) -> ResumePipeline:
    browser_session = PlaywrightBrowserSession(
        headless=config.headless,
        profile_dir=config.browser_profile_dir,
        timeout_ms=config.page_timeout_ms,
        retry_attempts=config.retry_attempts,
        retry_delay_ms=config.retry_delay_ms,
    )
    vacancy_repository = HhVacancyRepository(
        browser_session=browser_session,
        area=config.hh_area,
        max_results=config.max_results_per_keyword,
        search_pages=config.search_pages_per_keyword,
    )
    llm_client = OllamaClient(
        base_url=config.ollama_base_url,
        model=config.ollama_model,
        debug=config.llm_debug,
        log_preview_chars=config.llm_log_preview_chars,
    )
    resume_service = ResumeService(
        llm_client=llm_client,
        json_parser=JsonResponseParser(),
    )
    pdf_exporter = None
    if config.generate_pdf:
        try:
            from export.pdf_exporter import WeasyPrintPdfExporter

            pdf_exporter = WeasyPrintPdfExporter()
        except Exception as error:
            logger.warning("PDF exporter disabled: %s", error)

    return ResumePipeline(
        config=config,
        vacancy_repository=vacancy_repository,
        resume_service=resume_service,
        markdown_exporter=FileMarkdownExporter(),
        pdf_exporter=pdf_exporter,
        report_writer=JsonReportWriter(),
        html_report_writer=HtmlReportWriter(),
        markdown_preview_writer=MarkdownPreviewWriter(),
        seen_vacancy_store=SeenVacancyStore(config.seen_vacancies_path),
        report_opener=BrowserReportOpener() if config.open_report_in_browser else None,
    )
