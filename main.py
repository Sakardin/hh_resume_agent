from config import AppConfig
from pipeline import create_pipeline
from utils import configure_logging


def main() -> None:
    configure_logging()
    config = AppConfig.from_env()
    pipeline = create_pipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()
