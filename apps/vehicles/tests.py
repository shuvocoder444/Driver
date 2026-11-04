from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser
from .models import Vehicle


class VehicleAccessTests(TestCase):
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
        self.own_vehicle = self.create_vehicle(self.owner, 'Owner car', 'OWN-001')
        self.other_vehicle = self.create_vehicle(self.other_owner, 'Other car', 'OTHER-001')

    @staticmethod
    def create_vehicle(owner, title, registration_number):
        return Vehicle.objects.create(
            created_by=owner,
            title=title,
            brand='Test',
            model='Car',
            year=2025,
            color='Blue',
            registration_number=registration_number,
        )

    def test_guest_must_log_in_to_view_fleet(self):
        response = self.client.get(reverse('vehicles:list'))

        self.assertRedirects(
            response,
            f'{reverse("accounts:login")}?next={reverse("vehicles:list")}',
            fetch_redirect_response=False,
        )

    def test_company_sees_only_its_vehicles(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('vehicles:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_vehicle.title)
        self.assertNotContains(response, self.other_vehicle.title)
        self.assertEqual(response.context['total_count'], 1)

    def test_company_cannot_open_another_fleets_vehicle(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('vehicles:detail', args=[self.other_vehicle.pk]))

        self.assertEqual(response.status_code, 404)
