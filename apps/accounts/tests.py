from django.test import Client, TestCase
from django.urls import reverse

from .models import CustomUser


class AccountSecurityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='owner@example.com',
            password='valid-password-123',
            role=CustomUser.Role.COMPANY,
        )

    def test_login_rejects_post_without_csrf_cookie(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            reverse('accounts:login'),
            {
                'email': self.user.email,
                'password': 'valid-password-123',
                'csrfmiddlewaretoken': 'a' * 32,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_login_does_not_redirect_to_external_host(self):
        response = self.client.post(
            reverse('accounts:login'),
            {
                'email': self.user.email,
                'password': 'valid-password-123',
                'next': 'https://attacker.example/',
            },
        )

        self.assertRedirects(response, reverse('dashboard:admin'), fetch_redirect_response=False)

    def test_login_preserves_password_whitespace(self):
        spaced_user = CustomUser.objects.create_user(
            email='spaced@example.com',
            password=' password-with-spaces ',
            role=CustomUser.Role.COMPANY,
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'email': spaced_user.email, 'password': ' password-with-spaces '},
        )

        self.assertRedirects(response, reverse('dashboard:admin'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), spaced_user.pk)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        get_response = self.client.get(reverse('accounts:logout'))
        post_response = self.client.post(reverse('accounts:logout'))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse('landing_page'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_delete_requires_post(self):
        superuser = CustomUser.objects.create_superuser(
            email='root@example.com',
            password='valid-password-123',
        )
        self.client.force_login(superuser)

        response = self.client.get(reverse('accounts:user_delete', args=[self.user.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(CustomUser.objects.filter(pk=self.user.pk).exists())

    def test_registration_rejects_common_password(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'account_type': 'individual',
                'full_name': 'New Customer',
                'email': 'new@example.com',
                'password': 'password',
                'confirm_password': 'password',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='new@example.com').exists())

    def test_team_members_view_requires_authentication(self):
        response = Client().get(reverse('accounts:team'))

        self.assertRedirects(
            response,
            f'{reverse("accounts:login")}?next={reverse("accounts:team")}',
            fetch_redirect_response=False,
        )
