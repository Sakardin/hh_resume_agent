from dataclasses import asdict
from typing import Dict, List

from browser import PlaywrightBrowserSession
from config import AppConfig
from vacancies import HhVacancyRepository


def _create_browser_session(config: AppConfig) -> PlaywrightBrowserSession:
    return PlaywrightBrowserSession(
        headless=config.headless,
        profile_dir=config.browser_profile_dir,
        timeout_ms=config.page_timeout_ms,
        retry_attempts=config.retry_attempts,
        retry_delay_ms=config.retry_delay_ms,
    )


def search_hh_vacancies(
    keyword: str,
    area: int = 1002,
    max_results: int = 10,
) -> List[Dict[str, str]]:
    config = AppConfig.from_env()
    browser_session = _create_browser_session(config)

    with HhVacancyRepository(browser_session, area=area, max_results=max_results) as repository:
        return [asdict(vacancy) for vacancy in repository.search(keyword)]


def get_hh_vacancy_details(url: str) -> Dict[str, object]:
    config = AppConfig.from_env()
    browser_session = _create_browser_session(config)

    with HhVacancyRepository(
        browser_session,
        area=config.hh_area,
        max_results=config.max_results_per_keyword,
    ) as repository:
        return asdict(repository.get_details(url))
