class VacancyError(Exception):
    """Base error for vacancy search and parsing failures."""


class VacancyParsingError(VacancyError):
    """Raised when a vacancy page cannot be parsed into required fields."""
