from django.test import TestCase
from django.urls import reverse

from .models import Currency


class PublicPageSmokeTests(TestCase):
    def test_public_pages_render(self):
        names = [
            'landing_page',
            'about',
            'features',
            'pricing',
            'contact',
            'terms',
            'privacy',
            'accounts:login',
            'accounts:register',
            'billing:plans',
        ]

        for name in names:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_language_switch_never_redirects_to_an_external_host(self):
        response = self.client.get(
            reverse('switch_language', args=['ru']),
            HTTP_REFERER='https://attacker.example/',
        )

        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(response.cookies['django_language'].value, 'ru')

    def test_invalid_currency_does_not_set_a_currency_cookie(self):
        response = self.client.get(reverse('switch_currency', args=['INVALID']))

        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertNotIn('user_currency', response.cookies)

    def test_currency_switch_accepts_only_active_currency(self):
        Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate='1.0000',
            is_base=True,
            is_active=True,
        )

        response = self.client.get(reverse('switch_currency', args=['USD']))

        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(response.cookies['user_currency'].value, 'USD')
