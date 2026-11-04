from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect

from .models import ActivityLog, CustomUser


def fleet_user_ids(user):
    """Return the users whose fleet records are visible to this account."""
    if user.is_superadmin:
        return CustomUser.objects.values('pk')

    company = user.get_company_account()
    return CustomUser.objects.filter(Q(pk=company.pk) | Q(company=company)).values('pk')


def fleet_access_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = request.user
        allowed_roles = {
            CustomUser.Role.COMPANY,
            CustomUser.Role.ADMIN,
            CustomUser.Role.INDIVIDUAL,
        }
        if not (user.is_superadmin or user.role in allowed_roles):
            messages.error(request, 'Access denied. Fleet account privileges required.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)

    return wrapped


def log_activity(request, action_type, module, description, company=None):
    """
    Records an activity audit log for the current company and team member.
    """
    user = getattr(request, 'user', None)

    if not user or not user.is_authenticated:
        if not company:
            company = CustomUser.objects.filter(role=CustomUser.Role.COMPANY).first()
        actor_name = "Bakyt (Company Owner)"
        actor_email = "bakyt@bishkekwheels.kg"
        actor_role = "Owner"
        actor_obj = company
    else:
        if not company:
            company = user.get_company_account()
        actor_name = user.get_full_name() or user.email
        actor_email = user.email
        actor_role = getattr(user, 'member_role', 'Owner') or 'Owner'
        actor_obj = user

    # Retrieve client IP
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    if company:
        return ActivityLog.objects.create(
            company=company,
            actor=actor_obj,
            actor_name=actor_name,
            actor_email=actor_email,
            actor_role=actor_role,
            action_type=action_type,
            module=module,
            description=description,
            ip_address=ip or '127.0.0.1'
        )
    return None
