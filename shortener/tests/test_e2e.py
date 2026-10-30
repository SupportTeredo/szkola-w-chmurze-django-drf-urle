"""Testy end-to-end: rzeczywisty serwer HTTP, SQLite i klient http.client."""

import http.client
import json
from urllib.parse import urlparse

from django.test import LiveServerTestCase

from shortener.hashing import CODE_LENGTH, hash_url
from shortener.models import ShortURL

URL = 'https://example.com/very/long/path'


class UrlShortenerE2ETests(LiveServerTestCase):
    def _request(self, method, path, payload=None):
        connection = http.client.HTTPConnection(
            urlparse(self.live_server_url).hostname,
            urlparse(self.live_server_url).port,
            timeout=5,
        )
        body = json.dumps(payload) if payload is not None else None
        headers = {'Content-Type': 'application/json'} if body else {}
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response, response.read()
        finally:
            connection.close()

    def test_full_shorten_and_redirect_flow(self):
        response, raw = self._request('POST', '/api/urls/', {'url': URL})

        self.assertEqual(response.status, 201)
        data = json.loads(raw)
        self.assertEqual(data['original_url'], URL)
        self.assertEqual(data['code'], hash_url(URL)[:CODE_LENGTH])
        self.assertEqual(ShortURL.objects.count(), 1)

        response, raw = self._request('GET', f'/api/urls/{data["code"]}/')

        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(raw), {'url': URL})

        response, _ = self._request('GET', f'/shrt/{data["code"]}/')

        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader('Location'), URL)

    def test_short_url_from_response_is_reachable(self):
        _, raw = self._request('POST', '/api/urls/', {'url': URL})
        short_url = json.loads(raw)['short_url']
        path = urlparse(short_url).path

        response, _ = self._request('GET', path)

        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader('Location'), URL)

    def test_repeated_shortening_returns_same_code(self):
        first, _ = self._request('POST', '/api/urls/', {'url': URL})
        second, raw = self._request('POST', '/api/urls/', {'url': URL})

        self.assertEqual(first.status, 201)
        self.assertEqual(second.status, 200)
        self.assertEqual(json.loads(raw)['code'], hash_url(URL)[:CODE_LENGTH])
        self.assertEqual(ShortURL.objects.count(), 1)

    def test_invalid_url_returns_400(self):
        response, _ = self._request('POST', '/api/urls/', {'url': 'not-a-url'})
        self.assertEqual(response.status, 400)

    def test_unknown_code_returns_404_for_api(self):
        response, _ = self._request('GET', '/api/urls/deadbeef00/')
        self.assertEqual(response.status, 404)

    def test_unknown_code_returns_404_for_redirect(self):
        response, _ = self._request('GET', '/shrt/deadbeef00/')
        self.assertEqual(response.status, 404)

