from pathlib import Path


class FileMarkdownExporter:
    def export(self, markdown_text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_text, encoding="utf-8")
        return output_path
