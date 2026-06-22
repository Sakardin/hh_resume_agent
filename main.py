from cli import run_cli
from utils import configure_logging


def main() -> None:
    configure_logging()
    run_cli()


if __name__ == "__main__":
    main()
