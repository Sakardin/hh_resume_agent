import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from config import AppConfig
from pipeline import ResumePipeline
from reports import HtmlReportWriter, JsonReportWriter, MarkdownPreviewWriter, SeenVacancyStore
from reports.resume_generation_script_writer import ResumeGenerationScriptWriter
from resume.models import MatchScore, ResumeAdaptationResult
from vacancies.models import VacancyDetails, VacancySummary


class _DummyRepository:
    def __init__(self, vacancies, details_by_url) -> None:
        self._vacancies = vacancies
        self._details_by_url = details_by_url
        self.requested_urls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def search(self, keyword: str):
        return self._vacancies

    def get_details(self, url: str) -> VacancyDetails:
        self.requested_urls.append(url)
        return self._details_by_url[url]


class _DummyResumeService:
    def __init__(self) -> None:
        self.target_languages = []

    def score_vacancy(self, resume_text: str, vacancy_text: str) -> MatchScore:
        return MatchScore(score=90, strong_matches=["QA"], gaps=[], reason="ok")

    def adapt_resume_with_comments(
        self,
        resume_text: str,
        vacancy_text: str,
        user_prompt: str,
        target_language: str,
    ) -> ResumeAdaptationResult:
        self.target_languages.append(target_language)
        return ResumeAdaptationResult(
            target_language=target_language,
            recruiter_review="review",
            interview_review="interview",
            vacancy_comments="vacancy",
            final_resume_markdown="# Resume\n\ncontent",
        )


class _DummyMarkdownExporter:
    def export(self, markdown_text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_text, encoding="utf-8")
        return output_path


class _DummyHtmlReportWriter:
    def write(self, items, output_path: Path, report_json_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("report html", encoding="utf-8")
        return output_path


class _DummyMarkdownPreviewWriter:
    def write(self, markdown_path: Path) -> Path:
        html_path = markdown_path.with_suffix(".resume.html")
        html_path.write_text("preview", encoding="utf-8")
        return html_path


class _DummyResumeGenerationScriptWriter:
    def write(
        self,
        output_path: Path,
        project_root: Path,
        report_dir: Path,
        vacancy_url: str,
    ) -> Path:
        output_path.write_text(vacancy_url, encoding="utf-8")
        return output_path


class _DummyReportOpener:
    def __init__(self) -> None:
        self.opened_paths = []

    def open(self, path: Path) -> None:
        self.opened_paths.append(path)


class _LowScoreResumeService:
    def __init__(self) -> None:
        self.adapt_calls = 0

    def score_vacancy(self, resume_text: str, vacancy_text: str) -> MatchScore:
        return MatchScore(score=60, strong_matches=[], gaps=["gap"], reason="low score")

    def adapt_resume_with_comments(
        self,
        resume_text: str,
        vacancy_text: str,
        user_prompt: str,
        target_language: str,
    ) -> ResumeAdaptationResult:
        self.adapt_calls += 1
        return ResumeAdaptationResult(
            target_language=target_language,
            recruiter_review="review",
            interview_review="interview",
            vacancy_comments="vacancy",
            final_resume_markdown="# Resume\n\ncontent",
        )


class ResumePipelineTest(unittest.TestCase):
    def test_create_run_output_dir_uses_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base_output_dir = Path(directory) / "output"
            base_output_dir.mkdir(parents=True, exist_ok=True)

            run_output_dir = ResumePipeline._create_run_output_dir(
                base_output_dir,
                now=datetime(2026, 6, 17, 10, 45, 30),
            )

            self.assertEqual(run_output_dir.name, "2026-06-17_10-45-30")
            self.assertTrue(run_output_dir.exists())

    def test_create_run_output_dir_adds_suffix_on_collision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base_output_dir = Path(directory) / "output"
            existing = base_output_dir / "2026-06-17_10-45-30"
            existing.mkdir(parents=True, exist_ok=True)

            run_output_dir = ResumePipeline._create_run_output_dir(
                base_output_dir,
                now=datetime(2026, 6, 17, 10, 45, 30),
            )

            self.assertEqual(run_output_dir.name, "2026-06-17_10-45-30_2")
            self.assertTrue(run_output_dir.exists())

    def test_run_skips_previously_viewed_vacancies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "output"
            seen_path = output_dir / "seen_vacancies.json"
            seen_store = SeenVacancyStore(seen_path)
            seen_store.save(["https://hh.ru/vacancy/1"])

            resume_path = root / "resume.md"
            prompts_path = root / "prompts.md"
            keywords_path = root / "keywords.txt"
            resume_path.write_text("resume", encoding="utf-8")
            prompts_path.write_text("prompt", encoding="utf-8")
            keywords_path.write_text("qa", encoding="utf-8")

            config = AppConfig(
                ollama_model="model",
                ollama_base_url="http://localhost",
                llm_debug=False,
                llm_log_preview_chars=800,
                hh_area=None,
                min_match_score=70,
                max_results_per_keyword=10,
                search_pages_per_keyword=5,
                headless=True,
                browser_profile_dir=root / "browser_profile",
                output_dir=output_dir,
                seen_vacancies_path=seen_path,
                resume_path=resume_path,
                prompts_path=prompts_path,
                keywords_path=keywords_path,
                page_timeout_ms=1000,
                retry_attempts=1,
                retry_delay_ms=0,
                generate_pdf=False,
                generate_resume_on_match=False,
                open_report_in_browser=True,
            )
            repository = _DummyRepository(
                vacancies=[
                    VacancySummary(title="Seen vacancy", url="https://hh.ru/vacancy/1"),
                    VacancySummary(
                        title="New vacancy",
                        url="https://hh.ru/vacancy/2?query=qa&hhtmFrom=vacancy_search_list",
                    ),
                ],
                details_by_url={
                    "https://hh.ru/vacancy/2?query=qa&hhtmFrom=vacancy_search_list": VacancyDetails(
                        title="New vacancy",
                        company="Example",
                        url="https://hh.ru/vacancy/2?query=qa&hhtmFrom=vacancy_search_list",
                        description="desc",
                        key_skills=["QA"],
                    )
                },
            )

            resume_service = _DummyResumeService()
            report_opener = _DummyReportOpener()

            pipeline = ResumePipeline(
                config=config,
                vacancy_repository=repository,
                resume_service=resume_service,
                markdown_exporter=_DummyMarkdownExporter(),
                pdf_exporter=None,
                report_writer=JsonReportWriter(),
                html_report_writer=_DummyHtmlReportWriter(),
                markdown_preview_writer=_DummyMarkdownPreviewWriter(),
                resume_generation_script_writer=_DummyResumeGenerationScriptWriter(),
                seen_vacancy_store=seen_store,
                report_opener=report_opener,
                project_root=root,
            )

            report_html_path = pipeline.run()
            saved_urls = seen_store.load()
            report_json = (report_html_path.parent / "report.json").read_text(encoding="utf-8")

            self.assertEqual(
                repository.requested_urls,
                ["https://hh.ru/vacancy/2?query=qa&hhtmFrom=vacancy_search_list"],
            )
            self.assertEqual(
                saved_urls,
                {"https://hh.ru/vacancy/1", "https://hh.ru/vacancy/2"},
            )
            self.assertEqual(resume_service.target_languages, [])
            self.assertTrue(report_path.exists())
            self.assertTrue(html_report_path.exists())
            self.assertTrue(resume_preview_path.exists())
            self.assertEqual(report_opener.opened_paths, [html_report_path])

    def test_run_skips_low_score_vacancy_without_marking_it_as_seen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "output"
            seen_path = output_dir / "seen_vacancies.json"
            seen_store = SeenVacancyStore(seen_path)

            resume_path = root / "resume.md"
            prompts_path = root / "prompts.md"
            keywords_path = root / "keywords.txt"
            resume_path.write_text("resume", encoding="utf-8")
            prompts_path.write_text("prompt", encoding="utf-8")
            keywords_path.write_text("qa", encoding="utf-8")

            config = AppConfig(
                ollama_model="model",
                ollama_base_url="http://localhost",
                llm_debug=False,
                llm_log_preview_chars=800,
                hh_area=None,
                min_match_score=70,
                max_results_per_keyword=10,
                search_pages_per_keyword=5,
                headless=True,
                browser_profile_dir=root / "browser_profile",
                output_dir=output_dir,
                seen_vacancies_path=seen_path,
                resume_path=resume_path,
                prompts_path=prompts_path,
                keywords_path=keywords_path,
                page_timeout_ms=1000,
                retry_attempts=1,
                retry_delay_ms=0,
                generate_pdf=False,
                generate_resume_on_match=False,
                open_report_in_browser=True,
            )
            repository = _DummyRepository(
                vacancies=[VacancySummary(title="Low score vacancy", url="https://hh.ru/vacancy/3")],
                details_by_url={
                    "https://hh.ru/vacancy/3": VacancyDetails(
                        title="Low score vacancy",
                        company="Example",
                        url="https://hh.ru/vacancy/3",
                        description="desc",
                        key_skills=["QA"],
                    )
                },
            )
            resume_service = _LowScoreResumeService()

            pipeline = ResumePipeline(
                config=config,
                vacancy_repository=repository,
                resume_service=resume_service,
                markdown_exporter=_DummyMarkdownExporter(),
                pdf_exporter=None,
                report_writer=JsonReportWriter(),
                html_report_writer=_DummyHtmlReportWriter(),
                markdown_preview_writer=_DummyMarkdownPreviewWriter(),
                resume_generation_script_writer=_DummyResumeGenerationScriptWriter(),
                seen_vacancy_store=seen_store,
                report_opener=None,
                project_root=root,
            )

            report_html_path = pipeline.run()
            saved_urls = seen_store.load()
            report_payload = (report_html_path.parent / "report.json").read_text(encoding="utf-8")

            self.assertEqual(saved_urls, set())
            self.assertEqual(resume_service.adapt_calls, 0)
            self.assertEqual(report_payload.strip(), "[]")

    def test_generate_resume_for_report_item_updates_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "output"
            seen_path = output_dir / "seen_vacancies.json"
            seen_store = SeenVacancyStore(seen_path)

            resume_path = root / "resume.md"
            prompts_path = root / "prompts.md"
            keywords_path = root / "keywords.txt"
            resume_path.write_text("resume", encoding="utf-8")
            prompts_path.write_text("prompt", encoding="utf-8")
            keywords_path.write_text("qa", encoding="utf-8")

            config = AppConfig(
                ollama_model="model",
                ollama_base_url="http://localhost",
                llm_debug=False,
                llm_log_preview_chars=800,
                hh_area=None,
                min_match_score=70,
                max_results_per_keyword=10,
                search_pages_per_keyword=5,
                headless=True,
                browser_profile_dir=root / "browser_profile",
                output_dir=output_dir,
                seen_vacancies_path=seen_path,
                resume_path=resume_path,
                prompts_path=prompts_path,
                keywords_path=keywords_path,
                page_timeout_ms=1000,
                retry_attempts=1,
                retry_delay_ms=0,
                generate_pdf=False,
                generate_resume_on_match=False,
                open_report_in_browser=False,
            )
            repository = _DummyRepository(
                vacancies=[VacancySummary(title="QA vacancy", url="https://hh.ru/vacancy/4")],
                details_by_url={
                    "https://hh.ru/vacancy/4": VacancyDetails(
                        title="QA vacancy",
                        company="Example",
                        url="https://hh.ru/vacancy/4",
                        description="desc",
                        key_skills=["QA"],
                    )
                },
            )
            resume_service = _DummyResumeService()

            pipeline = ResumePipeline(
                config=config,
                vacancy_repository=repository,
                resume_service=resume_service,
                markdown_exporter=_DummyMarkdownExporter(),
                pdf_exporter=None,
                report_writer=JsonReportWriter(),
                html_report_writer=HtmlReportWriter(),
                markdown_preview_writer=MarkdownPreviewWriter(),
                resume_generation_script_writer=ResumeGenerationScriptWriter(),
                seen_vacancy_store=seen_store,
                report_opener=None,
                project_root=root,
            )

            report_html_path = pipeline.run()
            report_dir = report_html_path.parent

            generated_markdown = pipeline.generate_resume_for_report_item(
                report_dir=report_dir,
                vacancy_url="https://hh.ru/vacancy/4",
            )

            self.assertTrue(generated_markdown.exists())
            self.assertTrue(generated_markdown.with_suffix(".resume.html").exists())
            report_payload = (report_dir / "report.json").read_text(encoding="utf-8")
            self.assertIn(str(generated_markdown), report_payload)
            self.assertEqual(resume_service.target_languages, ["English"])

    def test_generate_resume_for_report_item_updates_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "output"
            seen_path = output_dir / "seen_vacancies.json"
            seen_store = SeenVacancyStore(seen_path)

            resume_path = root / "resume.md"
            prompts_path = root / "prompts.md"
            keywords_path = root / "keywords.txt"
            resume_path.write_text("resume", encoding="utf-8")
            prompts_path.write_text("prompt", encoding="utf-8")
            keywords_path.write_text("qa", encoding="utf-8")

            config = AppConfig(
                ollama_model="model",
                ollama_base_url="http://localhost",
                llm_debug=False,
                llm_log_preview_chars=800,
                hh_area=1002,
                min_match_score=70,
                max_results_per_keyword=10,
                headless=True,
                browser_profile_dir=root / "browser_profile",
                output_dir=output_dir,
                seen_vacancies_path=seen_path,
                resume_path=resume_path,
                prompts_path=prompts_path,
                keywords_path=keywords_path,
                page_timeout_ms=1000,
                retry_attempts=1,
                retry_delay_ms=0,
                generate_pdf=False,
                generate_resume_on_match=False,
            )
            repository = _DummyRepository(
                vacancies=[VacancySummary(title="QA vacancy", url="https://hh.ru/vacancy/4")],
                details_by_url={
                    "https://hh.ru/vacancy/4": VacancyDetails(
                        title="QA vacancy",
                        company="Example",
                        url="https://hh.ru/vacancy/4",
                        description="desc",
                        key_skills=["QA"],
                    )
                },
            )
            resume_service = _DummyResumeService()

            pipeline = ResumePipeline(
                config=config,
                vacancy_repository=repository,
                resume_service=resume_service,
                markdown_exporter=_DummyMarkdownExporter(),
                pdf_exporter=None,
                report_writer=JsonReportWriter(),
                html_report_writer=HtmlReportWriter(),
                markdown_preview_writer=MarkdownPreviewWriter(),
                resume_generation_script_writer=ResumeGenerationScriptWriter(),
                seen_vacancy_store=seen_store,
                project_root=root,
            )

            report_html_path = pipeline.run()
            report_dir = report_html_path.parent

            generated_markdown = pipeline.generate_resume_for_report_item(
                report_dir=report_dir,
                vacancy_url="https://hh.ru/vacancy/4",
            )

            self.assertTrue(generated_markdown.exists())
            self.assertTrue(generated_markdown.with_suffix(".resume.html").exists())
            report_payload = (report_dir / "report.json").read_text(encoding="utf-8")
            self.assertIn(str(generated_markdown), report_payload)
            self.assertEqual(resume_service.target_languages, ["English"])

    def test_log_llm_inputs_writes_resume_and_vacancy_previews(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = AppConfig(
                ollama_model="model",
                ollama_base_url="http://localhost",
                llm_debug=True,
                llm_log_preview_chars=200,
                hh_area=None,
                min_match_score=70,
                max_results_per_keyword=10,
                search_pages_per_keyword=5,
                headless=True,
                browser_profile_dir=root / "browser_profile",
                output_dir=root / "output",
                seen_vacancies_path=root / "output" / "seen_vacancies.json",
                resume_path=root / "resume.md",
                prompts_path=root / "prompts.md",
                keywords_path=root / "keywords.txt",
                page_timeout_ms=1000,
                retry_attempts=1,
                retry_delay_ms=0,
                generate_pdf=False,
                generate_resume_on_match=False,
            )
            pipeline = ResumePipeline(
                config=config,
                vacancy_repository=_DummyRepository(vacancies=[], details_by_url={}),
                resume_service=_DummyResumeService(),
                markdown_exporter=_DummyMarkdownExporter(),
                pdf_exporter=None,
                report_writer=JsonReportWriter(),
                html_report_writer=_DummyHtmlReportWriter(),
                markdown_preview_writer=_DummyMarkdownPreviewWriter(),
                resume_generation_script_writer=_DummyResumeGenerationScriptWriter(),
                seen_vacancy_store=SeenVacancyStore(config.seen_vacancies_path),
                project_root=root,
            )
            vacancy = VacancyDetails(
                title="QA Engineer",
                company="Example",
                url="https://hh.ru/vacancy/1",
                description="Playwright and API testing",
                key_skills=["QA", "Playwright"],
            )

            with self.assertLogs("pipeline", level="INFO") as captured:
                pipeline._log_llm_inputs(
                    stage="score_vacancy",
                    resume_text="Manual QA and API testing",
                    vacancy_text=vacancy.to_prompt_text(),
                    vacancy=vacancy,
                )

            joined_logs = "\n".join(captured.output)
            self.assertIn("Вот моё резюме:", joined_logs)
            self.assertIn("Вот описание вакансии:", joined_logs)
            self.assertIn("QA Engineer", joined_logs)


if __name__ == "__main__":
    unittest.main()
