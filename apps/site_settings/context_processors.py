from .models import WebsiteSetting, Currency
from .translations import get_translation
from django.db.models import Q


def get_active_dashboard_role(request):
    """
    Returns the persistent active dashboard role ('superadmin', 'admin', 'driver').
    Guarantees that:
    1. Driver user ALWAYS gets 'driver'.
    2. Company user ALWAYS gets 'admin'.
    3. Superadmin can preview superadmin, admin, or driver.
    4. Unauthenticated guest preview respects selected tab or defaults to 'admin'.
    """
    user = getattr(request, 'user', None)
    path = getattr(request, 'path', '')
    role_param = request.GET.get('role', '').strip().lower()

    # 1. Authenticated users with dedicated roles
    if user and user.is_authenticated:
        if getattr(user, 'role', '') == 'driver':
            request.session['active_dashboard_role'] = 'driver'
            return 'driver'
        elif getattr(user, 'role', '') in ['company', 'admin', 'individual']:
            request.session['active_dashboard_role'] = 'admin'
            return 'admin'
        elif getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'superadmin':
            if role_param in ['superadmin', 'admin', 'driver']:
                request.session['active_dashboard_role'] = role_param
                return role_param
            if path.startswith('/dashboard/driver/'):
                return 'driver'
            elif path.startswith('/dashboard/admin/') or path.startswith('/dashboard/company/'):
                return 'admin'
            elif path.startswith('/dashboard/superadmin/'):
                request.session['active_dashboard_role'] = 'superadmin'
                return 'superadmin'
            # When superadmin navigates across operational menus (agreements, vehicles, drivers, billing, settings, users),
            # superadmin MUST strictly remain in the superadmin master dashboard!
            request.session['active_dashboard_role'] = 'superadmin'
            return 'superadmin'

    # 2. Unauthenticated / guest preview
    if role_param in ['superadmin', 'admin', 'company', 'driver']:
        if role_param == 'company':
            role_param = 'admin'
        request.session['active_dashboard_role'] = role_param
        return role_param

    if '/dashboard/superadmin/' in path:
        request.session['active_dashboard_role'] = 'superadmin'
        return 'superadmin'
    elif '/dashboard/driver/' in path:
        request.session['active_dashboard_role'] = 'driver'
        return 'driver'
    elif '/dashboard/admin/' in path or '/dashboard/company/' in path:
        request.session['active_dashboard_role'] = 'admin'
        return 'admin'

    return request.session.get('active_dashboard_role', 'admin')


def site_settings_processor(request):
    try:
        setting = WebsiteSetting.load()
        currencies = list(Currency.objects.filter(is_active=True).order_by('-is_base', 'code'))
        if not currencies:
            usd, _ = Currency.objects.get_or_create(code='USD', defaults={'name': 'US Dollar', 'symbol': '$', 'exchange_rate': 1.0, 'is_base': True, 'is_active': True})
            kgs, _ = Currency.objects.get_or_create(code='KGS', defaults={'name': 'Kyrgyzstani Som', 'symbol': 'сом', 'exchange_rate': 87.45, 'is_base': False, 'is_active': True})
            currencies = [usd, kgs]
    except Exception:
        setting = None
        currencies = []
    
    # 1. Determine active language (session -> cookie -> default 'en')
    current_lang = request.session.get('_language') or request.COOKIES.get('django_language') or 'en'
    if current_lang not in ['en', 'ru']:
        current_lang = 'en'

    # 2. Determine active currency (session -> cookie -> default 'USD')
    current_currency = request.session.get('currency') or request.COOKIES.get('user_currency') or 'USD'
    current_currency = current_currency.upper()

    active_currency = None
    for c in currencies:
        if c.code == current_currency:
            active_currency = c
            break
    if not active_currency and currencies:
        active_currency = currencies[0]
        current_currency = active_currency.code

    # 3. Determine current active dashboard role (Super Admin / Fleet Admin / Driver)
    current_dashboard = get_active_dashboard_role(request)
    user = getattr(request, 'user', None)

    # Display user object for avatars and names in dashboard
    display_user = user if (user and user.is_authenticated) else None
    if not display_user:
        try:
            from apps.accounts.models import CustomUser
            if current_dashboard == 'admin':
                display_user = CustomUser.objects.filter(role=CustomUser.Role.COMPANY).first() or CustomUser.objects.first()
            elif current_dashboard == 'driver':
                display_user = CustomUser.objects.filter(role=CustomUser.Role.DRIVER).first() or CustomUser.objects.first()
            else:
                display_user = CustomUser.objects.filter(role=CustomUser.Role.SUPERADMIN).first() or CustomUser.objects.first()
        except Exception:
            display_user = None

    # 4. Calculate dynamic navigation badge counts
    nav_counts = {
        'agreements': 0,
        'drivers': 0,
        'vehicles': 0,
        'pending_payments': 0,
        'active_subscriptions': 0,
        'pages': 0,
        'users': 0,
        'team_members': 0,
    }
    try:
        from apps.agreements.models import Agreement
        from apps.drivers.models import Driver
        from apps.vehicles.models import Vehicle
        from apps.billing.models import ManualPayment, Subscription
        from apps.site_settings.models import FrontendPage
        from apps.accounts.models import CustomUser

        is_super = user and user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == CustomUser.Role.SUPERADMIN)
        if is_super:
            nav_counts['agreements'] = Agreement.objects.count()
            nav_counts['drivers'] = Driver.objects.count()
            nav_counts['vehicles'] = Vehicle.objects.count()
            nav_counts['pending_payments'] = ManualPayment.objects.filter(status=ManualPayment.Status.PENDING).count()
            nav_counts['active_subscriptions'] = Subscription.objects.filter(status=Subscription.Status.ACTIVE).count()
            nav_counts['pages'] = FrontendPage.objects.count()
            nav_counts['users'] = CustomUser.objects.count()
        elif user and user.is_authenticated:
            company = user.get_company_account() if hasattr(user, 'get_company_account') else None
            if company:
                company_users = CustomUser.objects.filter(Q(pk=company.pk) | Q(company=company))
                nav_counts['agreements'] = Agreement.objects.filter(created_by__in=company_users).count()
                nav_counts['drivers'] = Driver.objects.filter(created_by__in=company_users).count()
                nav_counts['vehicles'] = Vehicle.objects.filter(created_by__in=company_users).count()
                nav_counts['team_members'] = company.team_members.filter(is_active=True).count() + 1
            else:
                nav_counts['agreements'] = Agreement.objects.count()
                nav_counts['drivers'] = Driver.objects.count()
                nav_counts['vehicles'] = Vehicle.objects.count()
                nav_counts['team_members'] = 1
            nav_counts['pending_payments'] = 0
            nav_counts['pages'] = 0
            nav_counts['active_subscriptions'] = 1 if Subscription.objects.filter(user=company or user, status=Subscription.Status.ACTIVE).exists() else 0
        else:
            nav_counts['agreements'] = Agreement.objects.count()
            nav_counts['drivers'] = Driver.objects.count()
            nav_counts['vehicles'] = Vehicle.objects.count()
            nav_counts['pending_payments'] = ManualPayment.objects.filter(status=ManualPayment.Status.PENDING).count()
            nav_counts['pages'] = FrontendPage.objects.count()
            nav_counts['users'] = CustomUser.objects.count()
    except Exception:
        pass

    return {
        'site_setting': setting,
        'currencies': currencies,
        'current_currency': current_currency,
        'active_currency': active_currency,
        'current_lang': current_lang,
        't': get_translation(current_lang),
        'current_dashboard': current_dashboard,
        'display_user': display_user,
        'nav_counts': nav_counts,
    }
