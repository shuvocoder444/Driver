from apps.site_settings.context_processors import get_active_dashboard_role
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .models import CustomUser, ActivityLog
from .utils import log_activity


def _password_validation_error(password, email, first_name=''):
    try:
        validate_password(password, user=CustomUser(email=email, first_name=first_name))
    except ValidationError as error:
        return ' '.join(error.messages)
    return None


def clear_messages(request):
    """Clears any stale or accumulated unread messages from session/cookie storage."""
    try:
        from django.contrib.messages import get_messages
        storage = get_messages(request)
        if hasattr(storage, '_queued_messages'):
            storage._queued_messages.clear()
        for s in getattr(storage, 'storages', []):
            if hasattr(s, '_queued_messages'):
                s._queued_messages.clear()
            if hasattr(s, '_loaded_data'):
                s._loaded_data = []
    except Exception:
        pass


def login_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
            return redirect('dashboard:driver')
        elif getattr(request.user, 'role', '') in [CustomUser.Role.COMPANY, CustomUser.Role.ADMIN, CustomUser.Role.INDIVIDUAL]:
            return redirect('dashboard:admin')
        return redirect('dashboard:superadmin')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                clear_messages(request)
                auth_login(request, user)

                # Route strictly according to authenticated user's role
                if getattr(user, 'role', '') == CustomUser.Role.DRIVER:
                    request.session['active_dashboard_role'] = 'driver'
                    request.session.modified = True
                    log_activity(
                        request,
                        ActivityLog.ActionType.LOGIN,
                        ActivityLog.Module.AUTH,
                        f"Driver logged into dedicated portal",
                        company=user.get_company_account()
                    )
                    messages.success(request, f'Welcome back, {user.first_name or user.email}!')
                    return redirect('dashboard:driver')

                elif getattr(user, 'role', '') in [CustomUser.Role.COMPANY, CustomUser.Role.ADMIN, CustomUser.Role.INDIVIDUAL]:
                    request.session['active_dashboard_role'] = 'admin'
                    request.session.modified = True
                    log_activity(
                        request,
                        ActivityLog.ActionType.LOGIN,
                        ActivityLog.Module.AUTH,
                        f"Logged into company portal",
                        company=user.get_company_account()
                    )
                    messages.success(request, f'Welcome back, {user.first_name or user.email}!')
                    if (
                        next_url
                        and url_has_allowed_host_and_scheme(
                            next_url,
                            allowed_hosts={request.get_host()},
                            require_https=request.is_secure(),
                        )
                        and not any(bad in next_url for bad in ['/driver/', '/superadmin/', '/dashboard/'])
                    ):
                        return redirect(next_url)
                    return redirect('dashboard:admin')

                else:
                    request.session['active_dashboard_role'] = 'superadmin'
                    request.session.modified = True
                    log_activity(
                        request,
                        ActivityLog.ActionType.LOGIN,
                        ActivityLog.Module.AUTH,
                        f"Superadmin logged into system",
                        company=user.get_company_account()
                    )
                    messages.success(request, f'Welcome back, {user.first_name or user.email}!')
                    if (
                        next_url
                        and url_has_allowed_host_and_scheme(
                            next_url,
                            allowed_hosts={request.get_host()},
                            require_https=request.is_secure(),
                        )
                        and next_url not in ['/dashboard/', '/dashboard/admin/', '/dashboard/company/', '/dashboard/driver/']
                    ):
                        return redirect(next_url)
                    return redirect('dashboard:superadmin')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')

    context = {
        'next': next_url,
    }
    return render(request, 'users/login.html', context)


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        log_activity(
            request,
            ActivityLog.ActionType.LOGIN,
            ActivityLog.Module.AUTH,
            f"Logged out of system",
            company=request.user.get_company_account()
        )
    # Wipe any accumulated messages from previous dashboard actions
    clear_messages(request)

    auth_logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('landing_page')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        account_type = request.POST.get('account_type', 'individual').strip()
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        password_error = _password_validation_error(password, email, full_name)

        # Company-specific fields
        company_name = request.POST.get('company_name', '').strip()
        business_type = request.POST.get('business_type', '').strip()
        business_registration_number = request.POST.get('business_registration_number', '').strip()

        if not email or not password or not full_name:
            messages.error(request, 'Full Name, Email and Password are required.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        elif password_error:
            messages.error(request, password_error)
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
        else:
            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''

            role = CustomUser.Role.COMPANY if account_type == 'company' else CustomUser.Role.INDIVIDUAL

            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                company_name=company_name if account_type == 'company' else '',
                business_type=business_type if account_type == 'company' else '',
                business_registration_number=business_registration_number if account_type == 'company' else '',
                role=role,
                status=CustomUser.Status.VERIFIED,
                member_role='Owner'
            )
            auth_login(request, user)
            request.session['active_dashboard_role'] = 'admin'

            log_activity(
                request,
                ActivityLog.ActionType.CREATE,
                ActivityLog.Module.AUTH,
                f"Registered new {account_type.upper()} account ({full_name})",
                company=user
            )

            messages.success(request, f'Welcome, {full_name}! Your account has been created successfully.')
            return redirect('billing:purchase')

    return render(request, 'users/register.html')


@login_required
def team_members_view(request):
    """Manage company team members (Owner + up to 2 staff = 3 seats maximum)."""
    user = request.user
    company = user.get_company_account()

    if user.role not in [CustomUser.Role.COMPANY, CustomUser.Role.ADMIN, CustomUser.Role.INDIVIDUAL] and not user.is_superadmin:
        messages.error(request, 'Access denied. Company account privileges required.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        if not company:
            messages.error(request, 'No active company found.')
            return redirect('accounts:team')

        if company.role != CustomUser.Role.COMPANY:
            messages.error(request, 'Personal / Individual accounts are limited to 1 user seat. Upgrade to a Company account to add team members.')
            return redirect('accounts:team')

        if company.team_seat_count >= company.max_allowed_seats:
            messages.error(request, f'Maximum seat limit reached ({company.max_allowed_seats} seats max for Company accounts). Remove an existing member to free up a seat.')
            return redirect('accounts:team')

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        member_role = request.POST.get('member_role', 'Manager').strip()
        phone = request.POST.get('phone', '').strip()

        if not email or not password or not first_name:
            messages.error(request, 'First Name, Email, and Password are required.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        elif password_error := _password_validation_error(password, email, first_name):
            messages.error(request, password_error)
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email address already exists.')
        else:
            member = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=CustomUser.Role.COMPANY,
                company=company,
                member_role=member_role,
                status=CustomUser.Status.VERIFIED
            )
            log_activity(
                request,
                ActivityLog.ActionType.CREATE,
                ActivityLog.Module.TEAM,
                f"Added new team member: {member.get_full_name()} ({member.email}) as {member.member_role}",
                company=company
            )
            messages.success(request, f'Team member {member.get_full_name()} added successfully ({company.team_seat_count}/{company.max_allowed_seats} seats used)!')
            return redirect('accounts:team')

    team_members = company.team_members.all().order_by('-date_joined') if company else CustomUser.objects.none()

    context = {
        'company': company,
        'team_members': team_members,
        'team_seat_count': company.team_seat_count if company else 1,
        'max_allowed_seats': company.max_allowed_seats if company else 3,
        'seats_available': company.seats_available if company else 2,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'users/team_members.html', context)


@require_POST
def team_member_delete(request, pk):
    """Remove a team member to free up a company seat (Company or Super Admin)."""
    user = request.user
    if not user.is_authenticated:
        return redirect('accounts:login')

    if user.is_superuser or getattr(user, 'role', '') == CustomUser.Role.SUPERADMIN:
        member = get_object_or_404(CustomUser, pk=pk, company__isnull=False)
        company = member.company
    else:
        company = user.get_company_account()
        member = get_object_or_404(CustomUser, pk=pk, company=company)

    member_name = member.get_full_name() or member.email
    member.delete()

    log_activity(
        request,
        ActivityLog.ActionType.DELETE,
        ActivityLog.Module.TEAM,
        f"Removed team member: {member_name}",
        company=company
    )
    messages.success(request, f'Team member {member_name} has been removed successfully.')
    return redirect('accounts:team')


@login_required
def activity_log_view(request):
    """Audit Trail / Activity Log showing who did what across all 3 company members."""
    user = request.user
    company = user.get_company_account()

    module_filter = request.GET.get('module', '').strip()
    actor_filter = request.GET.get('actor', '').strip()
    query = request.GET.get('q', '').strip()

    logs = ActivityLog.objects.filter(company=company) if company else ActivityLog.objects.none()

    if module_filter:
        logs = logs.filter(module=module_filter)
    if actor_filter:
        logs = logs.filter(actor_id=actor_filter)
    if query:
        logs = logs.filter(
            Q(description__icontains=query) |
            Q(actor_name__icontains=query) |
            Q(actor_email__icontains=query)
        )

    actors = list(company.team_members.all()) + [company] if company else []

    context = {
        'company': company,
        'logs': logs[:100],
        'total_logs_count': logs.count(),
        'actors': actors,
        'modules': ActivityLog.Module.choices,
        'current_module': module_filter,
        'current_actor': actor_filter,
        'query': query,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'users/activity_log.html', context)


def users_list(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    users = CustomUser.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(phone__icontains=query)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    total_count = CustomUser.objects.count()
    superadmin_count = CustomUser.objects.filter(role=CustomUser.Role.SUPERADMIN).count()
    company_count = CustomUser.objects.filter(role__in=[CustomUser.Role.ADMIN, CustomUser.Role.COMPANY]).count()
    driver_count = CustomUser.objects.filter(role=CustomUser.Role.DRIVER).count()

    context = {
        'users': users,
        'query': query,
        'role_filter': role_filter,
        'total_count': total_count,
        'superadmin_count': superadmin_count,
        'company_count': company_count,
        'driver_count': driver_count,
        'role_choices': CustomUser.Role.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'users/list.html', context)


@login_required
@require_POST
def user_delete(request, pk):
    """Permanently delete a user or team member account (Super Admin only)."""
    if not (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('dashboard:index')

    user_to_delete = get_object_or_404(CustomUser, pk=pk)
    if user_to_delete == request.user:
        messages.error(request, 'You cannot delete your own Super Admin account.')
        return redirect('accounts:users')

    target_email = user_to_delete.email
    user_to_delete.delete()
    messages.success(request, f'User {target_email} has been permanently deleted.')
    return redirect('accounts:users')
