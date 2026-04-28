"""Tests for romma robots_txt view."""

from django.test import TestCase


class RobotsTxtTests(TestCase):

    def test_returns_200(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_plain_text(self):
        response = self.client.get('/robots.txt')
        self.assertIn('text/plain', response['Content-Type'])

    def test_disallows_admin(self):
        response = self.client.get('/robots.txt')
        self.assertIn('Disallow: /admin/', response.content.decode())

    def test_contains_sitemap_url(self):
        response = self.client.get('/robots.txt')
        self.assertIn('Sitemap:', response.content.decode())
        self.assertIn('sitemap.xml', response.content.decode())
