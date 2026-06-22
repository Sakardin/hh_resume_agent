import tempfile
import unittest
from pathlib import Path

from reports.seen_vacancies import SeenVacancyStore, normalize_vacancy_url


class SeenVacancyStoreTest(unittest.TestCase):
    def test_normalize_vacancy_url_ignores_query_and_fragment(self) -> None:
        self.assertEqual(
            normalize_vacancy_url(
                "https://hh.ru/vacancy/123456?query=QA&hhtmFrom=vacancy_search_list#details"
            ),
            "https://hh.ru/vacancy/123456",
        )

    def test_save_and_load_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seen_vacancies.json"
            store = SeenVacancyStore(path)

            store.save(
                [
                    "https://hh.ru/vacancy/2?query=AQA",
                    "https://hh.ru/vacancy/1?hhtmFrom=vacancy_search_list",
                    "https://hh.ru/vacancy/1",
                ]
            )

            self.assertEqual(
                store.load(),
                {"https://hh.ru/vacancy/1", "https://hh.ru/vacancy/2"},
            )


if __name__ == "__main__":
    unittest.main()
