from apps.site_settings.context_processors import get_active_dashboard_role
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .models import WebsiteSetting, Currency, ContactMessage, FrontendPage
from apps.billing.models import Plan
from apps.accounts.models import CustomUser


def _safe_referrer(request):
    referrer = request.META.get('HTTP_REFERER', '/')
    if url_has_allowed_host_and_scheme(
        referrer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return referrer
    return '/'


def _frontend_page(slug, default_title):
    return FrontendPage.objects.filter(slug=slug).first() or FrontendPage(
        slug=slug,
        title=default_title,
    )


def landing_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('home', 'Home')
    plans = Plan.objects.filter(status=Plan.Status.ACTIVE).order_by('price')
    currencies = Currency.objects.filter(is_active=True)
    
    context = {
        'setting': setting,
        'page': page,
        'plans': plans,
        'currencies': currencies,
    }
    return render(request, 'landing/index.html', context)


def about_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('about', 'About Us')
    return render(request, 'landing/about.html', {'setting': setting, 'page': page})


def features_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('features', 'Platform Features')
    return render(request, 'landing/features.html', {'setting': setting, 'page': page})


def pricing_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('pricing', 'Pricing & Plans')
    plans = Plan.objects.filter(status=Plan.Status.ACTIVE).order_by('price')
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'landing/pricing.html', {
        'setting': setting,
        'page': page,
        'plans': plans,
        'currencies': currencies,
    })


def contact_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('contact', 'Contact Us')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        if name and email and message_text:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message_text
            )
            messages.success(request, 'Thank you! Your message has been sent successfully. Our team will contact you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'landing/contact.html', {'setting': setting, 'page': page})


def terms_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('terms', 'Terms & Conditions')
    return render(request, 'landing/terms.html', {'setting': setting, 'page': page})


def privacy_page(request):
    setting = WebsiteSetting.load()
    page = _frontend_page('privacy', 'Privacy Policy')
    return render(request, 'landing/privacy.html', {'setting': setting, 'page': page})


def switch_currency(request, code):
    code = code.upper()
    currency = Currency.objects.filter(code=code, is_active=True).first()
    if currency:
        request.session['currency'] = code
    response = redirect(_safe_referrer(request))
    if currency:
        response.set_cookie('user_currency', code, max_age=365*24*3600, path='/')
    return response


def switch_language(request, lang_code):
    valid_language = lang_code in ['en', 'ru']
    if valid_language:
        request.session['_language'] = lang_code
        request.session['django_language'] = lang_code
    response = redirect(_safe_referrer(request))
    if valid_language:
        response.set_cookie('django_language', lang_code, max_age=365*24*3600, path='/')
    return response


def settings_view(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    from decimal import Decimal
    setting = WebsiteSetting.load()
    usd_currency, _ = Currency.objects.get_or_create(
        code='USD',
        defaults={'name': 'US Dollar', 'symbol': '$', 'exchange_rate': Decimal('1.0000'), 'is_base': True, 'is_active': True}
    )
    kgs_currency, _ = Currency.objects.get_or_create(
        code='KGS',
        defaults={'name': 'Kyrgyzstani Som', 'symbol': 'сом', 'exchange_rate': Decimal('87.4500'), 'is_base': False, 'is_active': True}
    )

    if request.method == 'POST':
        setting.site_name = request.POST.get('site_name', 'Topd').strip()
        setting.contact_email = request.POST.get('contact_email', '').strip()
        setting.contact_phone = request.POST.get('contact_phone', '').strip()
        setting.address = request.POST.get('address', '').strip()
        setting.working_hours = request.POST.get('working_hours', '').strip()
        setting.facebook_url = request.POST.get('facebook_url', '').strip()
        setting.twitter_url = request.POST.get('twitter_url', '').strip()
        setting.instagram_url = request.POST.get('instagram_url', '').strip()
        setting.linkedin_url = request.POST.get('linkedin_url', '').strip()

        if request.FILES.get('logo'):
            setting.logo = request.FILES.get('logo')

        setting.save()

        # Currency & Exchange Rate Updates
        kgs_rate_raw = request.POST.get('kgs_exchange_rate', '').strip()
        kgs_symbol = request.POST.get('kgs_symbol', 'сом').strip()
        usd_symbol = request.POST.get('usd_symbol', '$').strip()

        if kgs_rate_raw:
            try:
                rate_decimal = Decimal(kgs_rate_raw)
                if rate_decimal > 0:
                    kgs_currency.exchange_rate = rate_decimal
                    kgs_currency.symbol = kgs_symbol or 'сом'
                    kgs_currency.save()
            except Exception as e:
                messages.warning(request, f'Invalid KGS exchange rate: {e}')

        if usd_symbol:
            usd_currency.symbol = usd_symbol
            usd_currency.save()

        messages.success(request, f'Website settings and Currency Exchange Rate (1 USD = {kgs_currency.exchange_rate} KGS) saved successfully!')
        return redirect('settings')

    context = {
        'setting': setting,
        'usd_currency': usd_currency,
        'kgs_currency': kgs_currency,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'settings/general.html', context)


# ========================================================
# FRONTEND PAGE MANAGEMENT (CMS)
# ========================================================

def pages_list_view(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    pages = FrontendPage.objects.all().order_by('slug')
    setting = WebsiteSetting.load()
    context = {
        'pages': pages,
        'setting': setting,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'settings/pages_list.html', context)


def page_edit_view(request, slug):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    page = get_object_or_404(FrontendPage, slug=slug)
    setting = WebsiteSetting.load()

    if request.method == 'POST':
        page.title = request.POST.get('title', '').strip() or page.title
        page.badge = request.POST.get('badge', '').strip()
        page.subtitle = request.POST.get('subtitle', '').strip()
        page.section_title = request.POST.get('section_title', '').strip()
        page.section_content = request.POST.get('section_content', '').strip()
        page.content = request.POST.get('content', '').strip()
        page.meta_title = request.POST.get('meta_title', '').strip()
        page.meta_description = request.POST.get('meta_description', '').strip()
        page.is_active = (request.POST.get('is_active') == 'on')

        if request.FILES.get('image'):
            page.image = request.FILES.get('image')

        page.save()
        messages.success(request, f"Page '{page.title}' updated successfully!")
        
        if 'save_and_continue' in request.POST:
            return redirect('page_edit', slug=page.slug)
        return redirect('pages_list')

    context = {
        'page': page,
        'setting': setting,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'settings/page_edit.html', context)
