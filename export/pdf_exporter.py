from pathlib import Path

import markdown
from weasyprint import HTML


class WeasyPrintPdfExporter:
    def export(self, markdown_text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html_body = markdown.markdown(markdown_text)
        html = self._build_html(html_body)
        HTML(string=html).write_pdf(str(output_path))
        return output_path

    @staticmethod
    def _build_html(html_body: str) -> str:
        return f"""
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: Arial, sans-serif;
      font-size: 12px;
      line-height: 1.45;
      color: #222;
      max-width: 800px;
      margin: 40px auto;
    }}
    h1 {{
      font-size: 24px;
    }}
    h2 {{
      font-size: 18px;
      border-bottom: 1px solid #ddd;
      padding-bottom: 4px;
    }}
    h3 {{
      font-size: 15px;
    }}
    li {{
      margin-bottom: 4px;
    }}
  </style>
</head>
<body>
  {html_body}
</body>
</html>
"""
