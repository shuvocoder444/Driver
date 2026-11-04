from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.drivers.models import Driver


class DriverDashboardTests(TestCase):
    def test_driver_without_profile_does_not_see_another_drivers_profile(self):
        fleet_owner = CustomUser.objects.create_user(
            email='fleet@example.com',
            password='valid-password-123',
            role=CustomUser.Role.COMPANY,
        )
        another_driver = CustomUser.objects.create_user(
            email='another-driver@example.com',
            password='valid-password-123',
            role=CustomUser.Role.DRIVER,
        )
        Driver.objects.create(
            user=another_driver,
            created_by=fleet_owner,
            first_name='Private',
            last_name='Driver',
            phone='555-0100',
            passport_number='PRIVATE-PASSPORT',
            personal_id='PRIVATE-ID',
        )
        unlinked_driver = CustomUser.objects.create_user(
            email='unlinked-driver@example.com',
            password='valid-password-123',
            role=CustomUser.Role.DRIVER,
        )
        self.client.force_login(unlinked_driver)

        response = self.client.get(reverse('dashboard:driver'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['driver'])
        self.assertNotContains(response, 'PRIVATE-PASSPORT')
