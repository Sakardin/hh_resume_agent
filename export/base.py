from pathlib import Path
from typing import Protocol


class MarkdownExporter(Protocol):
    def export(self, markdown_text: str, output_path: Path) -> Path:
        ...


class PdfExporter(Protocol):
    def export(self, markdown_text: str, output_path: Path) -> Path:
        ...
