import logging
import time
from pathlib import Path
from typing import Any, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from browser.exceptions import BrowserError, EmptyPageError, PageOpenError

logger = logging.getLogger(__name__)


class PlaywrightBrowserSession:
    def __init__(
        self,
        headless: bool,
        profile_dir: Optional[Path],
        timeout_ms: int,
        retry_attempts: int,
        retry_delay_ms: int,
    ) -> None:
        self._headless = headless
        self._profile_dir = profile_dir
        self._timeout_ms = timeout_ms
        self._retry_attempts = max(1, retry_attempts)
        self._retry_delay_ms = max(0, retry_delay_ms)
        self._playwright: Optional[Any] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def __enter__(self) -> "PlaywrightBrowserSession":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def start(self) -> None:
        if self._context is not None:
            return

        self._playwright = sync_playwright().start()

        if self._profile_dir is not None:
            self._profile_dir.mkdir(parents=True, exist_ok=True)
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self._profile_dir),
                headless=self._headless,
                viewport={"width": 1400, "height": 1000},
            )
        else:
            self._browser = self._playwright.chromium.launch(headless=self._headless)
            self._context = self._browser.new_context(
                viewport={"width": 1400, "height": 1000},
            )

        self._context.set_default_timeout(self._timeout_ms)
        self._context.set_default_navigation_timeout(self._timeout_ms)

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None

        if self._browser is not None:
            self._browser.close()
            self._browser = None

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def open_page(self, url: str) -> Page:
        if self._context is None:
            raise BrowserError("Browser session is not started")

        last_error: Optional[Exception] = None

        for attempt in range(1, self._retry_attempts + 1):
            page = self._context.new_page()
            page.set_default_timeout(self._timeout_ms)
            page.set_default_navigation_timeout(self._timeout_ms)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
                self._handle_retry_button(page)
                self._ensure_non_empty_page(page)
                return page
            except (PlaywrightError, PlaywrightTimeoutError, EmptyPageError) as error:
                last_error = error
                logger.warning(
                    "Failed to open %s on attempt %s/%s: %s",
                    url,
                    attempt,
                    self._retry_attempts,
                    error,
                )
                self.close_page(page)

                if attempt < self._retry_attempts and self._retry_delay_ms:
                    time.sleep(self._retry_delay_ms / 1000)

        raise PageOpenError(f"Cannot open page {url}: {last_error}") from last_error

    @staticmethod
    def close_page(page: Page) -> None:
        try:
            page.close()
        except PlaywrightError:
            logger.debug("Failed to close Playwright page", exc_info=True)

    def _handle_retry_button(self, page: Page) -> None:
        retry_selectors = (
            'button:has-text("Try again")',
            'button:has-text("Попробовать снова")',
            'text="Try again"',
            'text="Попробовать снова"',
        )

        for selector in retry_selectors:
            locator = page.locator(selector).first
            try:
                if locator.count() > 0 and locator.is_visible(timeout=1000):
                    locator.click(timeout=3000)
                    page.wait_for_load_state("domcontentloaded", timeout=self._timeout_ms)
                    page.wait_for_timeout(1000)
                    return
            except PlaywrightError:
                continue

    @staticmethod
    def _ensure_non_empty_page(page: Page) -> None:
        body_text = page.locator("body").inner_text(timeout=5000).strip()
        if not body_text:
            raise EmptyPageError("Page body is empty")
