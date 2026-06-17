import tempfile
import unittest
from pathlib import Path

from reports.seen_vacancies import SeenVacancyStore


class SeenVacancyStoreTest(unittest.TestCase):
    def test_save_and_load_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seen_vacancies.json"
            store = SeenVacancyStore(path)

            store.save(
                [
                    "https://hh.ru/vacancy/2",
                    "https://hh.ru/vacancy/1",
                    "https://hh.ru/vacancy/1",
                ]
            )

            self.assertEqual(
                store.load(),
                {"https://hh.ru/vacancy/1", "https://hh.ru/vacancy/2"},
            )


if __name__ == "__main__":
    unittest.main()
