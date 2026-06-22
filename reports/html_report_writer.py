import html
from pathlib import Path
from typing import Iterable, Optional

from reports.models import VacancyReportItem


class HtmlReportWriter:
    def write(
        self,
        items: Iterable[VacancyReportItem],
        output_path: Path,
        report_json_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html_text = self._render_page(list(items), report_json_path)
        output_path.write_text(html_text, encoding="utf-8")
        return output_path

    def _render_page(self, items: list[VacancyReportItem], report_json_path: Path) -> str:
        rows = "\n".join(self._render_item(item) for item in items)
        if not rows:
            rows = '<div class="empty">Подходящие вакансии не найдены. Проверьте <a href="{0}">report.json</a>.</div>'.format(
                self._file_href(report_json_path)
            )

        return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HH Resume Agent Report</title>
  <style>
    :root {{
      --bg: #f4efe5;
      --card: #fffdf8;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #d6c8b4;
      --accent: #0f766e;
      --accent-soft: #d9f3ef;
      --warn: #92400e;
      --warn-soft: #fef3c7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #fff8eb 0, transparent 35%),
        linear-gradient(180deg, #f6f1e7 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(146,64,14,0.08));
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(30px, 5vw, 52px);
      line-height: 1;
    }}
    .lead {{
      margin: 0;
      color: var(--muted);
      font-size: 18px;
    }}
    .toolbar {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .link {{
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      text-decoration: none;
      color: var(--accent);
      background: var(--accent-soft);
      border: 1px solid rgba(15,118,110,0.15);
      font-weight: 600;
    }}
    .grid {{
      display: grid;
      gap: 16px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(31, 41, 55, 0.05);
    }}
    .head {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }}
    .title {{
      margin: 0 0 4px;
      font-size: 24px;
    }}
    .company {{
      color: var(--muted);
    }}
    .score {{
      min-width: 92px;
      text-align: center;
      padding: 10px 12px;
      border-radius: 16px;
      background: var(--warn-soft);
      color: var(--warn);
      font-weight: 700;
      font-size: 22px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
    }}
    .meta a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid rgba(15,118,110,0.16);
      background: #f5fbfa;
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }}
    .chip:hover {{
      background: #e8f6f3;
    }}
    .chip-muted {{
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid rgba(107,114,128,0.16);
      background: #f3f4f6;
      color: var(--muted);
      font-weight: 600;
    }}
    .title-link {{
      color: inherit;
      text-decoration: none;
      border-bottom: 2px solid rgba(15,118,110,0.2);
    }}
    .title-link:hover {{
      color: var(--accent);
      border-bottom-color: rgba(15,118,110,0.5);
    }}
    .section {{
      margin-top: 16px;
    }}
    .section h2 {{
      margin: 0 0 8px;
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    .reason {{
      white-space: pre-wrap;
      line-height: 1.55;
    }}
    .empty {{
      background: var(--card);
      border: 1px dashed var(--line);
      border-radius: 20px;
      padding: 24px;
      color: var(--muted);
    }}
    @media (max-width: 640px) {{
      main {{ padding: 18px 14px 32px; }}
      .card, .hero {{ border-radius: 18px; }}
      .score {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>HH Resume Agent Report</h1>
      <p class="lead">Сводка по найденным вакансиям, score и кнопкам для генерации резюме по запросу.</p>
      <div class="toolbar">
        <a class="link" href="{self._file_href(report_json_path)}">Открыть report.json</a>
      </div>
    </section>
    <section class="grid">
      {rows}
    </section>
  </main>
</body>
</html>
"""

    def _render_item(self, item: VacancyReportItem) -> str:
        strong_matches = self._render_list(item.strong_matches, "Совпадения не выделены.")
        gaps = self._render_list(item.gaps, "Пробелы не указаны.")
        pdf_link = self._optional_file_link(item.pdf, "PDF")
        resume_link = self._resume_link(item.markdown)
        markdown_raw_link = self._optional_file_link(item.markdown, "Markdown")
        generate_link = self._generate_resume_link(item.generate_resume_script, item.markdown)

        return f"""<article class="card">
  <div class="head">
    <div>
      <h2 class="title"><a class="title-link" href="{html.escape(item.url, quote=True)}">{html.escape(item.title)}</a></h2>
      <div class="company">{html.escape(item.company)}</div>
    </div>
    <div class="score">{item.score}%</div>
  </div>
  <div class="meta">
    <a class="chip" href="{html.escape(item.url, quote=True)}">Vacancy HH</a>
    {generate_link}
    {resume_link}
    {markdown_raw_link}
    {pdf_link}
  </div>
  <div class="section">
    <h2>Reason</h2>
    <div class="reason">{html.escape(item.reason)}</div>
  </div>
  <div class="section">
    <h2>Strong Matches</h2>
    {strong_matches}
  </div>
  <div class="section">
    <h2>Gaps</h2>
    {gaps}
  </div>
</article>"""

    @staticmethod
    def _render_list(values: list[str], empty_message: str) -> str:
        if not values:
            return f"<p>{html.escape(empty_message)}</p>"
        items = "".join(f"<li>{html.escape(value)}</li>" for value in values)
        return f"<ul>{items}</ul>"

    def _optional_file_link(self, path: Optional[Path], label: str) -> str:
        if path is None:
            return f'<span class="chip-muted">{html.escape(label)}: not generated</span>'
        if not path.exists():
            return f'<span class="chip-muted">{html.escape(label)}: missing file</span>'
        return f'<a class="chip" href="{self._file_href(path)}">{html.escape(label)}</a>'

    def _resume_link(self, markdown_path: Optional[Path]) -> str:
        if markdown_path is None:
            return '<span class="chip-muted">Resume: not generated</span>'
        if not markdown_path.exists():
            return '<span class="chip-muted">Resume: missing file</span>'

        preview_path = markdown_path.with_suffix(".resume.html")
        if preview_path.exists():
            return f'<a class="chip" href="{self._file_href(preview_path)}">Resume</a>'
        return f'<a class="chip" href="{self._file_href(markdown_path)}">Resume</a>'

    def _generate_resume_link(
        self,
        script_path: Optional[Path],
        markdown_path: Optional[Path],
    ) -> str:
        if script_path is None or not script_path.exists():
            return '<span class="chip-muted">Generate Resume: unavailable</span>'

        label = "Regenerate Resume" if markdown_path is not None else "Generate Resume"
        return f'<a class="chip" href="{self._file_href(script_path)}">{html.escape(label)}</a>'

    @staticmethod
    def _file_href(path: Path) -> str:
        return html.escape(path.resolve().as_uri(), quote=True)
