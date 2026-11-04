import tempfile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import CustomUser
from apps.agreements.models import Agreement, AgreementDocument
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle


class AgreementCreationTests(TestCase):
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
        self.vehicle = Vehicle.objects.create(
            created_by=self.owner,
            title='Rental car',
            brand='Test',
            model='Car',
            year=2025,
            color='Blue',
            registration_number='OWN-001',
        )
        self.driver = Driver.objects.create(
            created_by=self.owner,
            first_name='Fleet',
            last_name='Driver',
            phone='555-0100',
            passport_number='OWN-PASS',
            personal_id='OWN-ID',
        )
        self.foreign_driver = Driver.objects.create(
            created_by=self.other_owner,
            first_name='Other',
            last_name='Driver',
            phone='555-0101',
            passport_number='OTHER-PASS',
            personal_id='OTHER-ID',
        )
        self.client.force_login(self.owner)

    def test_agreement_cannot_assign_a_driver_from_another_fleet(self):
        response = self.client.post(
            reverse('agreements:create'),
            {
                'client_name': 'Client',
                'vehicle_id': self.vehicle.pk,
                'driver_id': self.foreign_driver.pk,
                'terms_agree': 'on',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Agreement.objects.exists())
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.AVAILABLE)

    def test_agreement_creation_updates_vehicle_and_driver_atomically(self):
        response = self.client.post(
            reverse('agreements:create'),
            {
                'client_name': 'Client',
                'vehicle_id': self.vehicle.pk,
                'driver_id': self.driver.pk,
                'terms_agree': 'on',
            },
        )

        self.assertRedirects(response, reverse('agreements:list'), fetch_redirect_response=False)
        agreement = Agreement.objects.get()
        self.assertEqual(agreement.created_by, self.owner)
        self.vehicle.refresh_from_db()
        self.driver.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.RENTED)
        self.assertEqual(self.driver.status, Driver.Status.BUSY)

    def test_uploaded_pdf_is_saved_with_the_agreement(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        settings_override = override_settings(MEDIA_ROOT=temp_dir.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        response = self.client.post(
            reverse('agreements:create'),
            {
                'client_name': 'Client',
                'vehicle_id': self.vehicle.pk,
                'driver_id': self.driver.pk,
                'terms_agree': 'on',
                'agreement_document': SimpleUploadedFile(
                    'agreement.pdf',
                    b'%PDF-1.4 test document',
                    content_type='application/pdf',
                ),
            },
        )

        self.assertRedirects(response, reverse('agreements:list'), fetch_redirect_response=False)
        self.assertEqual(AgreementDocument.objects.count(), 1)

    def test_invalid_upload_does_not_create_an_agreement(self):
        response = self.client.post(
            reverse('agreements:create'),
            {
                'client_name': 'Client',
                'vehicle_id': self.vehicle.pk,
                'driver_id': self.driver.pk,
                'terms_agree': 'on',
                'agreement_document': SimpleUploadedFile(
                    'not-a-pdf.pdf',
                    b'not a PDF',
                    content_type='application/pdf',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Agreement.objects.exists())
