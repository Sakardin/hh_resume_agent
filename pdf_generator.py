from pathlib import Path
from typing import Union

def markdown_to_pdf(markdown_text: str, output_path: Union[str, Path]) -> Path:
    from export.pdf_exporter import WeasyPrintPdfExporter

    return WeasyPrintPdfExporter().export(markdown_text, Path(output_path))
