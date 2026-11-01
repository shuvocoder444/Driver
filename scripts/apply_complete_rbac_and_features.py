import re

# ================= 1. apps/dashboard/views.py =================
with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update superadmin_dashboard guard
old_super_guard = '''def superadmin_dashboard(request):
    """1. Super Admin Master Dashboard"""
    # Guard: If logged in as driver, redirect to driver dashboard
    if request.user.is_authenticated and getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
        request.session['active_dashboard_role'] = 'driver'
        return redirect('dashboard:driver')

    # Guard: If logged in as company, redirect to company admin
    if request.user.is_authenticated and not (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN):
        request.session['active_dashboard_role'] = 'admin'
        return redirect('dashboard:admin')

    request.session['active_dashboard_role'] = 'superadmin'
    request.session.modified = True
    display_user = request.user if request.user.is_authenticated else CustomUser.objects.filter(role=CustomUser.Role.SUPERADMIN).first()'''

new_super_guard = '''def superadmin_dashboard(request):
    """1. Super Admin Master Dashboard"""
    # Strict Guard: Must be authenticated and superadmin
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    if not (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN):
        if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
            return redirect('dashboard:driver')
        return redirect('dashboard:admin')

    request.session['active_dashboard_role'] = 'superadmin'
    request.session.modified = True
    display_user = request.user'''

assert old_super_guard in content, "old_super_guard not found"
content = content.replace(old_super_guard, new_super_guard)

# Update payments_received fallback
content = content.replace("or 2623.50", "or 0.00")

# Update admin_dashboard guard
old_admin_guard = '''def admin_dashboard(request):
    """2. Rental Company / Fleet Admin Dashboard (like Team JBDIT)"""
    # Guard: If logged in as driver, redirect to driver dashboard!
    if request.user.is_authenticated and getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
        request.session['active_dashboard_role'] = 'driver'
        return redirect('dashboard:driver')

    if not (request.user.is_authenticated and getattr(request.user, 'is_superadmin', False)):
        request.session['active_dashboard_role'] = 'admin'
        request.session.modified = True
    display_user = request.user if request.user.is_authenticated else CustomUser.objects.filter(role=CustomUser.Role.COMPANY).first()'''

new_admin_guard = '''def admin_dashboard(request):
    """2. Rental Company / Fleet Admin Dashboard (like Team JBDIT)"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    # Guard: If logged in as driver, redirect to driver dashboard!
    if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
        request.session['active_dashboard_role'] = 'driver'
        return redirect('dashboard:driver')

    if not (request.user.is_authenticated and getattr(request.user, 'is_superadmin', False)):
        request.session['active_dashboard_role'] = 'admin'
        request.session.modified = True
    display_user = request.user'''

assert old_admin_guard in content, "old_admin_guard not found"
content = content.replace(old_admin_guard, new_admin_guard)

# Update driver dashboard guard
old_driver_code = '''def get_current_driver(request):
    """Helper to retrieve current driver profile and display user for driver views."""
    if not (request.user.is_authenticated and getattr(request.user, 'is_superadmin', False)):
        request.session['active_dashboard_role'] = 'driver'
        request.session.modified = True
    display_user = request.user if request.user.is_authenticated else CustomUser.objects.filter(role=CustomUser.Role.DRIVER).first()'''

new_driver_code = '''def get_current_driver(request):
    """Helper to resolve driver instance for the active driver view."""
    if not request.user.is_authenticated:
        return None, None
    # Block company user from driver portal
    if not (request.user.is_superuser or getattr(request.user, 'role', '') in [CustomUser.Role.SUPERADMIN, CustomUser.Role.DRIVER]):
        return None, None
    if not getattr(request.user, 'is_superadmin', False):
        request.session['active_dashboard_role'] = 'driver'
        request.session.modified = True
    display_user = request.user'''

assert old_driver_code in content, "old_driver_code not found"
content = content.replace(old_driver_code, new_driver_code)

# Guard inside driver views if driver is None
driver_guard_snippet = '''def driver_dashboard(request):
    """3. Driver Dedicated Portal Dashboard - Profile & Performance"""
    display_user, driver = get_current_driver(request)
    if not display_user:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return redirect('dashboard:admin')'''

content = content.replace('''def driver_dashboard(request):
    """3. Driver Dedicated Portal Dashboard - Profile & Performance"""
    display_user, driver = get_current_driver(request)''', driver_guard_snippet)

driver_vehicle_snippet = '''def driver_vehicle_view(request):
    """Current Assigned Vehicle dedicated page for driver"""
    display_user, driver = get_current_driver(request)
    if not display_user:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return redirect('dashboard:admin')'''

content = content.replace('''def driver_vehicle_view(request):
    """Current Assigned Vehicle dedicated page for driver"""
    display_user, driver = get_current_driver(request)''', driver_vehicle_snippet)

driver_agreements_snippet = '''def driver_agreements_view(request):
    """Trip Contracts dedicated page for driver"""
    display_user, driver = get_current_driver(request)
    if not display_user:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return redirect('dashboard:admin')'''

content = content.replace('''def driver_agreements_view(request):
    """Trip Contracts dedicated page for driver"""
    display_user, driver = get_current_driver(request)''', driver_agreements_snippet)

driver_history_snippet = '''def driver_history_view(request):
    """Incident History & Driving Records dedicated page for driver"""
    display_user, driver = get_current_driver(request)
    if not display_user:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return redirect('dashboard:admin')'''

content = content.replace('''def driver_history_view(request):
    """Incident History & Driving Records dedicated page for driver"""
    display_user, driver = get_current_driver(request)''', driver_history_snippet)

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("apps/dashboard/views.py updated successfully!")
