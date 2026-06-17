from export.base import MarkdownExporter, PdfExporter
from export.markdown_exporter import FileMarkdownExporter

__all__ = [
    "FileMarkdownExporter",
    "MarkdownExporter",
    "PdfExporter",
    "WeasyPrintPdfExporter",
]


def __getattr__(name: str):
    if name == "WeasyPrintPdfExporter":
        from export.pdf_exporter import WeasyPrintPdfExporter

        return WeasyPrintPdfExporter

    raise AttributeError(f"module 'export' has no attribute {name!r}")
