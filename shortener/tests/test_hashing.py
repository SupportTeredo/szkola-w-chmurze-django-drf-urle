from django.test import SimpleTestCase

from shortener.hashing import CODE_LENGTH, generate_code, hash_url


class HashUrlTests(SimpleTestCase):
    def test_hash_is_deterministic(self):
        url = 'https://example.com/very/long/path'
        self.assertEqual(hash_url(url), hash_url(url))

    def test_hash_differs_for_different_urls(self):
        self.assertNotEqual(
            hash_url('https://example.com/a'),
            hash_url('https://example.com/b'),
        )

    def test_hash_is_sha256_hex(self):
        digest = hash_url('https://example.com')
        self.assertEqual(len(digest), 64)
        int(digest, 16)  # rzuca ValueError, jeśli to nie hex


class GenerateCodeTests(SimpleTestCase):
    def test_code_is_deterministic(self):
        url = 'https://example.com/test'
        self.assertEqual(generate_code(url, lambda code: False),
                         generate_code(url, lambda code: False))

    def test_code_has_default_length(self):
        code = generate_code('https://example.com/test', lambda code: False)
        self.assertEqual(len(code), CODE_LENGTH)

    def test_code_is_prefix_of_hash(self):
        url = 'https://example.com/test'
        self.assertEqual(generate_code(url, lambda code: False),
                         hash_url(url)[:CODE_LENGTH])

    def test_code_extends_on_collision(self):
        url = 'https://example.com/test'
        digest = hash_url(url)
        taken = {digest[:CODE_LENGTH]}

        code = generate_code(url, lambda candidate: candidate in taken)

        self.assertEqual(code, digest[:CODE_LENGTH + 1])
        self.assertEqual(len(code), CODE_LENGTH + 1)

    def test_raises_when_all_lengths_taken(self):
        with self.assertRaises(ValueError):
            generate_code('https://example.com/test', lambda code: True)

