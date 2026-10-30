from django.test import TestCase
from django.urls import reverse

from shortener.hashing import hash_url
from shortener.models import ShortURL

URL = 'https://example.com/very/long/path'


class ShortenEndpointTests(TestCase):
    def setUp(self):
        self.url = reverse('shortener:shorten')

    def test_creates_short_url(self):
        response = self.client.post(self.url, {'url': URL})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['original_url'], URL)
        self.assertEqual(ShortURL.objects.count(), 1)

    def test_code_is_derived_from_hash(self):
        code = self.client.post(self.url, {'url': URL}).json()['code']
        self.assertEqual(code, hash_url(URL)[:10])

    def test_response_contains_short_url(self):
        short_url = self.client.post(self.url, {'url': URL}).json()['short_url']
        self.assertTrue(short_url.endswith(f'/shrt/{hash_url(URL)[:10]}/'))

    def test_repeated_request_returns_existing_code(self):
        first = self.client.post(self.url, {'url': URL})
        second = self.client.post(self.url, {'url': URL})

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['code'], second.json()['code'])
        self.assertEqual(ShortURL.objects.count(), 1)

    def test_rejects_invalid_url(self):
        response = self.client.post(self.url, {'url': 'not-a-url'})
        self.assertEqual(response.status_code, 400)

    def test_rejects_non_http_scheme(self):
        response = self.client.post(self.url, {'url': 'ftp://example.com/file'})
        self.assertEqual(response.status_code, 400)

    def test_rejects_missing_url(self):
        self.assertEqual(self.client.post(self.url, {}).status_code, 400)

    def test_rejects_get_method(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class ResolveEndpointTests(TestCase):
    def setUp(self):
        self.short_url = ShortURL.objects.create(
            original_url=URL,
            code=hash_url(URL)[:10],
        )

    def test_returns_original_url(self):
        response = self.client.get(
            reverse('shortener:resolve', args=[self.short_url.code])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'url': URL})

    def test_unknown_code_returns_404(self):
        response = self.client.get(reverse('shortener:resolve', args=['deadbeef00']))
        self.assertEqual(response.status_code, 404)

    def test_rejects_post_method(self):
        response = self.client.post(
            reverse('shortener:resolve', args=[self.short_url.code])
        )
        self.assertEqual(response.status_code, 405)
