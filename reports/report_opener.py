import logging
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)


class BrowserReportOpener:
    def open(self, path: Path) -> None:
        opened = webbrowser.open(path.resolve().as_uri(), new=2)
        if opened:
            logger.info("Opened report in browser: %s", path)
        else:
            logger.warning("Could not open report in browser automatically: %s", path)
