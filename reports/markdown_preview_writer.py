from pathlib import Path

import markdown


class MarkdownPreviewWriter:
    def write(self, markdown_path: Path) -> Path:
        html_path = markdown_path.with_suffix(".resume.html")
        markdown_text = markdown_path.read_text(encoding="utf-8")
        body_html = markdown.markdown(markdown_text, extensions=["extra", "nl2br", "tables"])
        html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{markdown_path.stem}</title>
  <style>
    :root {{
      --bg: #f6f1e7;
      --paper: #fffdfa;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #ded4c4;
      --accent: #0f766e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #fff8eb 0, transparent 35%),
        linear-gradient(180deg, #f8f3ea 0%, var(--bg) 100%);
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }}
    .toolbar {{
      margin-bottom: 16px;
    }}
    .toolbar a {{
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid rgba(15,118,110,0.16);
      background: #f5fbfa;
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }}
    article {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 10px 30px rgba(31, 41, 55, 0.05);
      line-height: 1.65;
    }}
    h1, h2, h3 {{
      line-height: 1.2;
    }}
    pre, code {{
      white-space: pre-wrap;
      word-break: break-word;
    }}
    @media (max-width: 640px) {{
      article {{
        padding: 20px;
        border-radius: 18px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="toolbar">
      <a href="{markdown_path.resolve().as_uri()}">Open raw Markdown</a>
    </div>
    <article>
      {body_html}
    </article>
  </main>
</body>
</html>
"""
        html_path.write_text(html_text, encoding="utf-8")
        return html_path
