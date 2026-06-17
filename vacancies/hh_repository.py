import logging
from typing import List, Optional, Sequence, Set
from urllib.parse import quote_plus

from playwright.sync_api import Error as PlaywrightError, Locator, Page

from browser.playwright_session import PlaywrightBrowserSession
from vacancies.exceptions import VacancyParsingError
from vacancies.models import VacancyDetails, VacancySummary

logger = logging.getLogger(__name__)


class HhVacancyRepository:
    SEARCH_TITLE_SELECTORS = (
        '[data-qa="serp-item__title"]',
        'a[href*="/vacancy/"]',
    )
    TITLE_SELECTORS = (
        '[data-qa="vacancy-title"]',
        "h1",
    )
    COMPANY_SELECTORS = (
        '[data-qa="vacancy-company-name"]',
        'a[href*="/employer/"]',
    )
    DESCRIPTION_SELECTORS = (
        '[data-qa="vacancy-description"]',
        '[class*="vacancy-description"]',
    )
    SKILL_SELECTORS = (
        '[data-qa="bloko-tag__text"]',
        '[data-qa="skills-element"]',
    )

    def __init__(
        self,
        browser_session: PlaywrightBrowserSession,
        area: int,
        max_results: int,
    ) -> None:
        self._browser_session = browser_session
        self._area = area
        self._max_results = max_results

    def __enter__(self) -> "HhVacancyRepository":
        self._browser_session.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._browser_session.close()

    def search(self, keyword: str) -> List[VacancySummary]:
        search_url = (
            "https://hh.ru/search/vacancy"
            f"?text={quote_plus(keyword)}"
            f"&area={self._area}"
            "&search_field=name"
        )

        page = self._browser_session.open_page(search_url)
        try:
            cards = self._first_locator_with_items(page, self.SEARCH_TITLE_SELECTORS)
            if cards is None:
                logger.warning("No vacancy cards found for keyword %s", keyword)
                return []

            return self._parse_search_cards(cards)
        finally:
            self._browser_session.close_page(page)

    def get_details(self, url: str) -> VacancyDetails:
        page = self._browser_session.open_page(url)
        try:
            title = self._first_text(page, self.TITLE_SELECTORS)
            if not title:
                raise VacancyParsingError(f"Vacancy title was not found: {url}")

            company = self._first_text(page, self.COMPANY_SELECTORS) or ""
            description = self._first_text(page, self.DESCRIPTION_SELECTORS) or ""
            key_skills = self._all_texts(page, self.SKILL_SELECTORS)

            return VacancyDetails(
                title=title,
                company=company,
                url=url,
                description=description,
                key_skills=key_skills,
            )
        finally:
            self._browser_session.close_page(page)

    def _parse_search_cards(self, cards: Locator) -> List[VacancySummary]:
        vacancies: List[VacancySummary] = []
        seen_urls: Set[str] = set()
        count = min(cards.count(), self._max_results)

        for index in range(count):
            card = cards.nth(index)
            title = self._safe_inner_text(card)
            url = self._safe_attribute(card, "href")

            if not title or not url or url in seen_urls:
                continue

            seen_urls.add(url)
            vacancies.append(VacancySummary(title=title, url=url))

        return vacancies

    @staticmethod
    def _first_locator_with_items(
        page: Page,
        selectors: Sequence[str],
    ) -> Optional[Locator]:
        for selector in selectors:
            locator = page.locator(selector)
            try:
                if locator.count() > 0:
                    return locator
            except PlaywrightError:
                continue
        return None

    @classmethod
    def _first_text(cls, page: Page, selectors: Sequence[str]) -> Optional[str]:
        for selector in selectors:
            locator = page.locator(selector).first
            text = cls._safe_inner_text(locator)
            if text:
                return text
        return None

    @classmethod
    def _all_texts(cls, page: Page, selectors: Sequence[str]) -> List[str]:
        values: List[str] = []
        seen: Set[str] = set()

        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = locator.count()
            except PlaywrightError:
                continue

            for index in range(count):
                text = cls._safe_inner_text(locator.nth(index))
                if text and text not in seen:
                    seen.add(text)
                    values.append(text)

        return values

    @staticmethod
    def _safe_inner_text(locator: Locator) -> str:
        try:
            return locator.inner_text(timeout=3000).strip()
        except PlaywrightError:
            return ""

    @staticmethod
    def _safe_attribute(locator: Locator, name: str) -> str:
        try:
            return (locator.get_attribute(name, timeout=3000) or "").strip()
        except PlaywrightError:
            return ""
