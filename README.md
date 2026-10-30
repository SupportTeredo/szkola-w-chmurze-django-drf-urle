# URL Shortener API

Minimalne API skracania adresów URL zbudowane w Django + Django REST Framework.
Kod skrótu jest deterministycznie wyprowadzany z adresu URL (SHA-256), a baza danych
egzekwuje unikalność adresów i kodów.

## Wymagania

- Python 3.12+
- SQLite (wbudowana w Django, bez dodatkowej konfiguracji)

## Instalacja

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

## Uruchomienie serwera

```bash
python manage.py runserver
```

Serwer dostępny jest pod `http://localhost:8000/`.

## Testy

```bash
python manage.py test shortener
```

Testy obejmują:

| Plik | Zakres |
| --- | --- |
| `shortener/tests/test_hashing.py` | deterministyczność hasha, długość kodu, kolizje |
| `shortener/tests/test_api.py` | endpointy API, walidacja, 404, przekierowanie |
| `shortener/tests/test_edge_cases.py` | kolizje, ograniczenia unikalności, wyścig requestów |
| `shortener/tests/test_e2e.py` | pełny przepływ HTTP przez `LiveServerTestCase` |

## API

### Skrócenie adresu

```bash
curl -i -X POST http://localhost:8000/api/urls/ \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/very/long/path"}'
```

Odpowiedź `201 Created` dla nowego adresu, `200 OK` gdy adres już istnieje:

```json
{
  "code": "a3f8b91c20",
  "original_url": "https://example.com/very/long/path",
  "short_url": "http://localhost:8000/shrt/a3f8b91c20/"
}
```

Niepoprawny adres zwraca `400 Bad Request`.

### Odczyt oryginalnego adresu (JSON)

```bash
curl http://localhost:8000/api/urls/a3f8b91c20/
```

```json
{"url": "https://example.com/very/long/path"}
```

Nieistniejący kod zwraca `404 Not Found`.

### Przekierowanie

```bash
curl -i http://localhost:8000/shrt/a3f8b91c20/
```

Odpowiedź `302 Found` z nagłówkiem `Location` wskazującym oryginalny adres.
Nieistniejący kod zwraca `404 Not Found`.

## Jak działa generowanie kodu

1. Adres URL jest hashowany funkcją SHA-256.
2. Kod to pierwsze 10 znaków zapisu szesnastkowego hasha.
3. Jeśli kod jest już zajęty przez inny adres, prefiks jest wydłużany o jeden znak
   (maksymalnie 32 znaki), aż kod będzie wolny.
4. Ponowne skrócenie tego samego adresu zwraca istniejący rekord — adresy nie są
   duplikowane.

Adresy porównywane są dokładnie, bez normalizacji: `https://example.com` i
`https://example.com/` to dwa różne adresy.

## Struktura projektu

```
config/          # konfiguracja Django (settings, urls, wsgi, asgi)
shortener/
  hashing.py     # generowanie kodu z hasha URL
  models.py      # model ShortURL
  serializers.py # walidacja i reprezentacja API
  views.py       # endpointy skracania, odczytu i przekierowania
  urls.py        # routing aplikacji
  tests/         # testy jednostkowe, integracyjne i E2E
manage.py
requirements.txt
```

