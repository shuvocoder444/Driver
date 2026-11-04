from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser
from .models import ManualPayment, Plan, Subscription


class SubscriptionFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='customer@example.com',
            password='valid-password-123',
            role=CustomUser.Role.INDIVIDUAL,
        )
        self.admin = CustomUser.objects.create_superuser(
            email='root@example.com',
            password='valid-password-123',
        )
        self.plan = Plan.objects.create(
            name='Monthly',
            slug='monthly-test',
            price=Decimal('29.99'),
            currency='USD',
            interval=Plan.Interval.MONTHLY,
            status=Plan.Status.ACTIVE,
        )

    def test_guest_cannot_submit_payment(self):
        response = self.client.post(
            reverse('billing:purchase'),
            {'plan_id': self.plan.pk, 'transaction_info': 'TX-123'},
        )

        self.assertRedirects(
            response,
            f'{reverse("accounts:login")}?next={reverse("billing:purchase")}',
            fetch_redirect_response=False,
        )
        self.assertFalse(ManualPayment.objects.exists())

    def test_payment_uses_plan_amount_and_currency_not_form_values(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('billing:purchase'),
            {
                'plan_id': self.plan.pk,
                'payment_method': ManualPayment.PaymentMethod.BANK_TRANSFER,
                'transaction_info': 'TX-123',
                'amount': '0.01',
                'currency': 'FAKE',
            },
        )

        self.assertRedirects(response, reverse('billing:subscriptions'), fetch_redirect_response=False)
        payment = ManualPayment.objects.get()
        self.assertEqual(payment.amount, self.plan.price)
        self.assertEqual(payment.currency, self.plan.currency)
        self.assertEqual(payment.user, self.user)
        self.assertEqual(Subscription.objects.get().status, Subscription.Status.PENDING)

    def test_inactive_plan_cannot_be_purchased(self):
        self.client.force_login(self.user)
        self.plan.status = Plan.Status.INACTIVE
        self.plan.save(update_fields=['status'])

        response = self.client.post(
            reverse('billing:purchase'),
            {
                'plan_id': self.plan.pk,
                'transaction_info': 'TX-123',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(ManualPayment.objects.exists())

    def test_payment_review_requires_post_and_approval_is_idempotent(self):
        payment = ManualPayment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=self.plan.price,
            currency=self.plan.currency,
            transaction_info='TX-456',
            status=ManualPayment.Status.PENDING,
        )
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            status=Subscription.Status.PENDING,
        )
        self.client.force_login(self.admin)
        approve_url = reverse('billing:approve_payment', args=[payment.pk])

        get_response = self.client.get(approve_url)
        first_post = self.client.post(approve_url)
        second_post = self.client.post(approve_url)

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(first_post, reverse('billing:manual_payments'), fetch_redirect_response=False)
        self.assertRedirects(second_post, reverse('billing:manual_payments'), fetch_redirect_response=False)
        payment.refresh_from_db()
        subscription.refresh_from_db()
        self.assertEqual(payment.status, ManualPayment.Status.APPROVED)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(
            Subscription.objects.filter(
                user=self.user,
                plan=self.plan,
                status=Subscription.Status.ACTIVE,
            ).count(),
            1,
        )
