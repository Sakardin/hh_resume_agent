import argparse
from pathlib import Path
from typing import Optional, Sequence

from config import AppConfig
from pipeline import create_pipeline


def run_cli(argv: Optional[Sequence[str]] = None) -> Path:
    args = _build_parser().parse_args(argv)
    config = AppConfig.from_env()
    pipeline = create_pipeline(config)

    if args.command == "generate":
        return pipeline.generate_resume_for_report_item(
            report_dir=Path(args.report_dir),
            vacancy_url=args.vacancy_url,
        )

    return pipeline.run()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hh-resume-agent")
    subparsers = parser.add_subparsers(dest="command")

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--report-dir", required=True)
    generate_parser.add_argument("--vacancy-url", required=True)

    return parser
