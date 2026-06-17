import re

CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")


def detect_text_language(text: str) -> str:
    cyrillic_count = len(CYRILLIC_PATTERN.findall(text))
    latin_count = len(LATIN_PATTERN.findall(text))

    if cyrillic_count == 0 and latin_count == 0:
        return "English"

    if cyrillic_count >= latin_count:
        return "Russian"

    return "English"
