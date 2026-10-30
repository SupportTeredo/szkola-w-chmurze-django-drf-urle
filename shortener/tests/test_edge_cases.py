from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from shortener.hashing import CODE_LENGTH, hash_url
from shortener.models import ShortURL

URL = 'https://example.com/very/long/path'


class HashCollisionTests(TestCase):
    def setUp(self):
        self.url = reverse('shortener:shorten')

    def test_collision_extends_code(self):
        digest = hash_url(URL)
        ShortURL.objects.create(
            original_url='https://other.example.com/taken',
            code=digest[:CODE_LENGTH],
        )

        response = self.client.post(self.url, {'url': URL})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['code'], digest[:CODE_LENGTH + 1])

    def test_collision_extends_code_until_free(self):
        digest = hash_url(URL)
        for length in range(CODE_LENGTH, CODE_LENGTH + 3):
            ShortURL.objects.create(
                original_url=f'https://other.example.com/taken-{length}',
                code=digest[:length],
            )

        response = self.client.post(self.url, {'url': URL})

        self.assertEqual(response.json()['code'], digest[:CODE_LENGTH + 3])

    def test_collision_does_not_affect_other_urls(self):
        digest = hash_url(URL)
        ShortURL.objects.create(
            original_url='https://other.example.com/taken',
            code=digest[:CODE_LENGTH],
        )

        self.client.post(self.url, {'url': URL})

        self.assertEqual(ShortURL.objects.count(), 2)
        self.assertEqual(
            ShortURL.objects.get(original_url='https://other.example.com/taken').code,
            digest[:CODE_LENGTH],
        )


class UniquenessConstraintTests(TestCase):
    def test_original_url_must_be_unique(self):
        ShortURL.objects.create(original_url=URL, code='aaaaaaaaaa')

        with self.assertRaises(IntegrityError):
            ShortURL.objects.create(original_url=URL, code='bbbbbbbbbb')

    def test_code_must_be_unique(self):
        ShortURL.objects.create(original_url=URL, code='aaaaaaaaaa')

        with self.assertRaises(IntegrityError):
            ShortURL.objects.create(
                original_url='https://other.example.com',
                code='aaaaaaaaaa',
            )


class RepeatedShorteningTests(TestCase):
    def setUp(self):
        self.url = reverse('shortener:shorten')

    def test_returns_same_record(self):
        first = self.client.post(self.url, {'url': URL}).json()
        second = self.client.post(self.url, {'url': URL}).json()

        self.assertEqual(first['code'], second['code'])
        self.assertEqual(ShortURL.objects.count(), 1)

    def test_returns_existing_record_after_integrity_error(self):
        existing = ShortURL.objects.create(
            original_url=URL,
            code=hash_url(URL)[:CODE_LENGTH],
        )
        real_filter = ShortURL.objects.filter
        calls = {'count': 0}

        def filter_side_effect(*args, **kwargs):
            calls['count'] += 1
            if calls['count'] == 1:
                # Pierwsze sprawdzenie nie widzi jeszcze rekordu (wyścig).
                return ShortURL.objects.none()
            return real_filter(*args, **kwargs)

        with mock.patch.object(
            ShortURL.objects, 'filter', side_effect=filter_side_effect
        ), mock.patch.object(
            ShortURL.objects, 'create', side_effect=IntegrityError('race')
        ):
            response = self.client.post(self.url, {'url': URL})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], existing.code)
        self.assertEqual(ShortURL.objects.count(), 1)

    def test_no_url_normalization(self):
        self.client.post(self.url, {'url': URL})
        self.client.post(self.url, {'url': URL + '/'})

        self.assertEqual(ShortURL.objects.count(), 2)


class UrlValidationTests(TestCase):
    def setUp(self):
        self.url = reverse('shortener:shorten')

    def test_rejects_empty_string(self):
        self.assertEqual(self.client.post(self.url, {'url': ''}).status_code, 400)

    def test_rejects_whitespace_only(self):
        self.assertEqual(self.client.post(self.url, {'url': '   '}).status_code, 400)

    def test_rejects_url_without_host(self):
        self.assertEqual(
            self.client.post(self.url, {'url': 'http://'}).status_code, 400
        )

    def test_rejects_url_exceeding_max_length(self):
        long_url = 'https://example.com/' + 'a' * 2100
        self.assertEqual(
            self.client.post(self.url, {'url': long_url}).status_code, 400
        )

    def test_accepts_url_with_query_and_port(self):
        url = 'https://example.com:8443/path?query=1&other=2#fragment'
        response = self.client.post(self.url, {'url': url})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['original_url'], url)
