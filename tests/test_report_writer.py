import json
import tempfile
import unittest
from pathlib import Path

from reports.html_report_writer import HtmlReportWriter
from reports.markdown_preview_writer import MarkdownPreviewWriter
from reports.models import VacancyReportItem
from reports.report_writer import JsonReportWriter


class JsonReportWriterTest(unittest.TestCase):
    def test_write_report_items(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "report.json"
            item = VacancyReportItem(
                score=91,
                title="QA Engineer",
                company="Example",
                url="https://hh.ru/vacancy/1",
                markdown=Path("output/resume.md"),
                pdf=Path("output/resume.pdf"),
                generate_resume_script=Path("output/generate.command"),
                strong_matches=["QA"],
                gaps=[],
                reason="Good match",
            )

            JsonReportWriter().write([item], output_path)

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["score"], 91)
            self.assertEqual(payload[0]["markdown"], "output/resume.md")
            self.assertEqual(payload[0]["pdf"], "output/resume.pdf")
            self.assertEqual(payload[0]["generate_resume_script"], "output/generate.command")

    def test_write_html_report_items(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "report.html"
            json_path = Path(directory) / "report.json"
            markdown_path = Path(directory) / "resume.md"
            script_path = Path(directory) / "generate.command"
            markdown_path.write_text("# Resume\n\ncontent", encoding="utf-8")
            script_path.write_text("echo", encoding="utf-8")
            MarkdownPreviewWriter().write(markdown_path)
            item = VacancyReportItem(
                score=91,
                title="QA Engineer",
                company="Example",
                url="https://hh.ru/vacancy/1",
                markdown=markdown_path,
                pdf=Path(directory) / "resume.pdf",
                generate_resume_script=script_path,
                strong_matches=["QA"],
                gaps=["No mobile testing"],
                reason="Good match",
            )

            HtmlReportWriter().write([item], output_path, json_path)

            payload = output_path.read_text(encoding="utf-8")
            self.assertIn("QA Engineer", payload)
            self.assertIn("https://hh.ru/vacancy/1", payload)
            self.assertIn("report.json", payload)
            self.assertIn("resume.md", payload)
            self.assertIn("resume.resume.html", payload)
            self.assertIn("Regenerate Resume", payload)


if __name__ == "__main__":
    unittest.main()
