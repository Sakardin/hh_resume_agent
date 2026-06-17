class BrowserError(Exception):
    """Base error for browser automation failures."""


class EmptyPageError(BrowserError):
    """Raised when Playwright opens a page with no meaningful body content."""


class PageOpenError(BrowserError):
    """Raised when a page cannot be opened after configured retries."""
