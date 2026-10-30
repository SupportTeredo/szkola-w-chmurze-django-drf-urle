"""Deterministyczne generowanie krótkich kodów na podstawie adresu URL."""

import hashlib

CODE_LENGTH = 10
MAX_CODE_LENGTH = 32


def hash_url(url: str) -> str:
    """Zwraca hex SHA-256 dla podanego adresu URL."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def generate_code(url: str, is_taken) -> str:
    """Zwraca kod wyprowadzony z hasha URL.

    Zaczynamy od CODE_LENGTH znaków. Jeśli kod jest już zajęty przez inny
    adres, wydłużamy prefiks hasha o jeden znak, aż znajdziemy wolny kod.
    Dzięki temu wynik jest deterministyczny dla danego stanu bazy.
    """
    digest = hash_url(url)
    for length in range(CODE_LENGTH, MAX_CODE_LENGTH + 1):
        code = digest[:length]
        if not is_taken(code):
            return code
    raise ValueError('Nie udało się wygenerować unikalnego kodu.')

