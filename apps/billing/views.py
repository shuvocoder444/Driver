from apps.site_settings.context_processors import get_active_dashboard_role
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from .models import ManualPayment, Subscription, Plan
from apps.accounts.models import CustomUser


def manual_payments_list(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    status_filter = request.GET.get('status', '').strip()
    payments = ManualPayment.objects.all().select_related('user', 'plan')
    if status_filter:
        payments = payments.filter(status=status_filter)

    payment_counts = ManualPayment.objects.aggregate(
        pending=Count('pk', filter=Q(status=ManualPayment.Status.PENDING)),
        approved=Count('pk', filter=Q(status=ManualPayment.Status.APPROVED)),
        cancelled=Count('pk', filter=Q(status=ManualPayment.Status.CANCELLED)),
    )

    context = {
        'payments': payments,
        'status_filter': status_filter,
        'pending_count': payment_counts['pending'],
        'approved_count': payment_counts['approved'],
        'cancelled_count': payment_counts['cancelled'],
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'billing/manual_payments.html', context)


def approve_payment(request, pk):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('dashboard:index')
    payment = get_object_or_404(ManualPayment, pk=pk)
    payment.status = ManualPayment.Status.APPROVED
    payment.reviewed_at = timezone.now()
    if request.user.is_authenticated:
        payment.reviewed_by = request.user
    payment.save()

    # Determine duration based on interval
    days = 30
    if payment.plan.interval == Plan.Interval.YEARLY:
        days = 365
    elif payment.plan.interval == Plan.Interval.ONCE:
        days = 365

    # Check if there is an existing pending subscription for this user and plan
    sub = Subscription.objects.filter(
        user=payment.user,
        plan=payment.plan,
        status=Subscription.Status.PENDING
    ).first()

    if sub:
        sub.status = Subscription.Status.ACTIVE
        sub.start_date = timezone.now()
        sub.end_date = timezone.now() + timezone.timedelta(days=days)
        sub.save()
    else:
        Subscription.objects.create(
            user=payment.user,
            plan=payment.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=days),
            status=Subscription.Status.ACTIVE
        )

    messages.success(request, f'Payment #{payment.id} approved and subscription activated for {payment.user.email}!')
    return redirect('billing:manual_payments')


def reject_payment(request, pk):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('dashboard:index')
    payment = get_object_or_404(ManualPayment, pk=pk)
    payment.status = ManualPayment.Status.CANCELLED
    payment.reviewed_at = timezone.now()
    if request.user.is_authenticated:
        payment.reviewed_by = request.user
    payment.save()

    # Cancel pending subscription if any
    Subscription.objects.filter(
        user=payment.user,
        plan=payment.plan,
        status=Subscription.Status.PENDING
    ).update(status=Subscription.Status.CANCELLED)

    messages.warning(request, f'Payment #{payment.id} marked as rejected.')
    return redirect('billing:manual_payments')


def purchase_subscription(request, plan_id=None):
    """Allows user to manually purchase a subscription via bank transfer / cash / mobile money."""
    if not request.user.is_authenticated:
        fallback_user = CustomUser.objects.filter(role=CustomUser.Role.COMPANY).first() or CustomUser.objects.filter(role=CustomUser.Role.SUPERADMIN).first() or CustomUser.objects.first()
        if fallback_user:
            request.user = fallback_user

    plans = Plan.objects.filter(status=Plan.Status.ACTIVE).order_by('price')
    
    selected_plan = None
    target_id = plan_id or request.GET.get('plan')
    if target_id:
        selected_plan = Plan.objects.filter(pk=target_id, status=Plan.Status.ACTIVE).first()
    if not selected_plan and plans.exists():
        selected_plan = plans.first()

    if request.method == 'POST':
        submitted_plan_id = request.POST.get('plan_id')
        payment_method = request.POST.get('payment_method', ManualPayment.PaymentMethod.BANK_TRANSFER)
        transaction_info = request.POST.get('transaction_info', '').strip()
        custom_amount = request.POST.get('amount', '').strip()
        currency = request.POST.get('currency', 'USD').strip()

        plan = get_object_or_404(Plan, pk=submitted_plan_id)
        amount = custom_amount if custom_amount else plan.price

        if not transaction_info:
            messages.error(request, 'Please provide the transaction reference / TrxID or receipt details.')
            selected_plan = plan
        else:
            # 1. Create ManualPayment record
            payment = ManualPayment.objects.create(
                user=request.user,
                plan=plan,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                transaction_date=timezone.now(),
                transaction_info=transaction_info,
                status=ManualPayment.Status.PENDING
            )

            # 2. Record Pending Subscription
            Subscription.objects.create(
                user=request.user,
                plan=plan,
                start_date=timezone.now(),
                status=Subscription.Status.PENDING
            )

            messages.success(
                request,
                f'Success! Your manual payment for "{plan.name}" (Reference #{payment.id}) has been submitted. Our team will verify and activate your subscription shortly.'
            )
            return redirect('billing:subscriptions')

    context = {
        'plans': plans,
        'selected_plan': selected_plan,
        'payment_methods': ManualPayment.PaymentMethod.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'billing/purchase.html', context)


def subscriptions_list(request):
    status_filter = request.GET.get('status', '').strip()
    
    # If superadmin, show all; otherwise show user's own subscriptions
    is_super = request.user.is_superuser or getattr(request.user, 'role', '') == 'superadmin'
    if is_super:
        subscriptions = Subscription.objects.all().select_related('user', 'plan')
        my_payments = None
    else:
        subscriptions = Subscription.objects.filter(user=request.user).select_related('user', 'plan') if request.user.is_authenticated else Subscription.objects.none()
        my_payments = ManualPayment.objects.filter(user=request.user).select_related('plan') if request.user.is_authenticated else ManualPayment.objects.none()

    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)

    total_count = subscriptions.count()
    active_count = subscriptions.filter(status=Subscription.Status.ACTIVE).count()
    pending_count = subscriptions.filter(status=Subscription.Status.PENDING).count()

    context = {
        'subscriptions': subscriptions,
        'my_payments': my_payments,
        'status_filter': status_filter,
        'total_count': total_count,
        'active_count': active_count,
        'pending_count': pending_count,
        'is_super': is_super,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'billing/subscriptions.html', context)


def plans_list(request):
    plans = Plan.objects.all().order_by('price')
    is_admin = request.user.is_authenticated and (
        request.user.is_superuser or getattr(request.user, 'role', '') in ['superadmin', 'admin']
    )
    context = {
        'plans': plans,
        'is_admin': is_admin,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'billing/plans.html', context)


def plan_create(request):
    from django.utils.text import slugify

    is_admin = request.user.is_authenticated and (
        request.user.is_superuser or getattr(request.user, 'role', '') in ['superadmin', 'admin']
    )
    if not is_admin:
        messages.error(request, 'Access restricted to administrators.')
        return redirect('billing:plans')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or slugify(name)
        price = request.POST.get('price', '').strip()
        currency = request.POST.get('currency', 'USD').strip().upper()
        interval = request.POST.get('interval', Plan.Interval.MONTHLY)
        status = request.POST.get('status', Plan.Status.ACTIVE)
        description = request.POST.get('description', '').strip()
        highlight = request.POST.get('highlight', '').strip()

        if not name or not price:
            messages.error(request, 'Please provide package name and price.')
        else:
            base_slug = slug or 'plan'
            candidate_slug = base_slug
            counter = 1
            while Plan.objects.filter(slug=candidate_slug).exists():
                candidate_slug = f"{base_slug}-{counter}"
                counter += 1

            plan = Plan.objects.create(
                name=name,
                slug=candidate_slug,
                price=price,
                currency=currency,
                interval=interval,
                status=status,
                description=description,
                highlight=highlight,
            )
            messages.success(request, f"Package '{plan.name}' created successfully!")
            return redirect('billing:plans')

    context = {
        'plan': None,
        'intervals': Plan.Interval.choices,
        'statuses': Plan.Status.choices,
        'is_edit': False,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'billing/plan_form.html', context)


def plan_edit(request, pk):
    from django.utils.text import slugify

    is_admin = request.user.is_authenticated and (
        request.user.is_superuser or getattr(request.user, 'role', '') in ['superadmin', 'admin']
    )
    if not is_admin:
        messages.error(request, 'Access restricted to administrators.')
        return redirect('billing:plans')

    plan = get_object_or_404(Plan, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or slugify(name)
        price = request.POST.get('price', '').strip()
        currency = request.POST.get('currency', 'USD').strip().upper()
        interval = request.POST.get('interval', Plan.Interval.MONTHLY)
        status = request.POST.get('status', Plan.Status.ACTIVE)
        description = request.POST.get('description', '').strip()
        highlight = request.POST.get('highlight', '').strip()

        if not name or not price:
            messages.error(request, 'Please provide package name and price.')
        else:
            base_slug = slug or 'plan'
            candidate_slug = base_slug
            counter = 1
            while Plan.objects.filter(slug=candidate_slug).exclude(pk=plan.pk).exists():
                candidate_slug = f"{base_slug}-{counter}"
                counter += 1

            plan.name = name
            plan.slug = candidate_slug
            plan.price = price
            plan.currency = currency
            plan.interval = interval
            plan.status = status
            plan.description = description
            plan.highlight = highlight
            plan.save()

            messages.success(request, f"Package '{plan.name}' updated successfully!")
            return redirect('billing:plans')

    context = {
        'plan': plan,
        'intervals': Plan.Interval.choices,
        'statuses': Plan.Status.choices,
        'is_edit': True,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'billing/plan_form.html', context)


def plan_delete(request, pk):
    is_admin = request.user.is_authenticated and (
        request.user.is_superuser or getattr(request.user, 'role', '') in ['superadmin', 'admin']
    )
    if not is_admin:
        messages.error(request, 'Access restricted to administrators.')
        return redirect('billing:plans')

    plan = get_object_or_404(Plan, pk=pk)

    if request.method == 'POST':
        plan_name = plan.name
        if plan.subscriptions.exists():
            plan.status = Plan.Status.INACTIVE
            plan.save()
            messages.warning(
                request,
                f"Package '{plan_name}' has existing subscriptions, so its status was changed to INACTIVE instead of permanent deletion."
            )
        else:
            plan.delete()
            messages.success(request, f"Package '{plan_name}' deleted successfully!")
    
    return redirect('billing:plans')

