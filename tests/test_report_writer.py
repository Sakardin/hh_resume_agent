import json
import tempfile
import unittest
from pathlib import Path

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
                strong_matches=["QA"],
                gaps=[],
                reason="Good match",
            )

            JsonReportWriter().write([item], output_path)

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["score"], 91)
            self.assertEqual(payload[0]["markdown"], "output/resume.md")
            self.assertEqual(payload[0]["pdf"], "output/resume.pdf")


if __name__ == "__main__":
    unittest.main()
