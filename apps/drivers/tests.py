from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser
from .models import Driver


class DriverAccessTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            email='owner@example.com',
            password='valid-password-123',
            role=CustomUser.Role.COMPANY,
        )
        self.other_owner = CustomUser.objects.create_user(
            email='other@example.com',
            password='valid-password-123',
            role=CustomUser.Role.COMPANY,
        )
        self.own_driver = self.create_driver(self.owner, 'Owner', 'OWN-PASS')
        self.other_driver = self.create_driver(self.other_owner, 'Other', 'OTHER-PASS')

    @staticmethod
    def create_driver(owner, first_name, passport_number):
        return Driver.objects.create(
            created_by=owner,
            first_name=first_name,
            last_name='Driver',
            phone='555-0100',
            passport_number=passport_number,
            personal_id=f'ID-{passport_number}',
        )

    def test_company_sees_only_its_drivers(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('drivers:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_driver.passport_number)
        self.assertNotContains(response, self.other_driver.passport_number)
        self.assertEqual(response.context['total_count'], 1)

    def test_company_cannot_open_another_fleets_driver(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('drivers:detail', args=[self.other_driver.pk]))

        self.assertEqual(response.status_code, 404)
