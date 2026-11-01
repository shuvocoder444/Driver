# 1. Update apps/site_settings/views.py
with open('apps/site_settings/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_guard = '''    if not request.user.is_authenticated:
        admin_user = CustomUser.objects.filter(role='superadmin').first() or CustomUser.objects.filter(is_superuser=True).first() or CustomUser.objects.first()
        if admin_user:
            request.user = admin_user'''

new_guard = '''    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')'''

assert old_guard in content, "old_guard not found in site_settings/views.py"
content = content.replace(old_guard, new_guard)

with open('apps/site_settings/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("apps/site_settings/views.py updated successfully!")

# 2. Update apps/billing/views.py
with open('apps/billing/views.py', 'r', encoding='utf-8') as f:
    b_content = f.read()

# Add CustomUser import if needed
if "from apps.accounts.models import CustomUser" not in b_content:
    b_content = "from apps.accounts.models import CustomUser\n" + b_content

old_manual = '''def manual_payments_list(request):
    status_filter = request.GET.get('status', '').strip()'''

new_manual = '''def manual_payments_list(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    status_filter = request.GET.get('status', '').strip()'''

assert old_manual in b_content, "old_manual not found in billing/views.py"
b_content = b_content.replace(old_manual, new_manual)

# Update approve_payment and reject_payment guards
b_content = b_content.replace(
    '''def approve_payment(request, pk):
    payment = get_object_or_404(ManualPayment, pk=pk)''',
    '''def approve_payment(request, pk):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('dashboard:index')
    payment = get_object_or_404(ManualPayment, pk=pk)'''
)

b_content = b_content.replace(
    '''def reject_payment(request, pk):
    payment = get_object_or_404(ManualPayment, pk=pk)''',
    '''def reject_payment(request, pk):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('dashboard:index')
    payment = get_object_or_404(ManualPayment, pk=pk)'''
)

# Update plan_create, plan_edit, plan_delete
b_content = b_content.replace(
    '''def plan_create(request):
    form = PlanForm(request.POST or None)''',
    '''def plan_create(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('billing:plans')
    form = PlanForm(request.POST or None)'''
)

b_content = b_content.replace(
    '''def plan_edit(request, pk):
    plan = get_object_or_404(Plan, pk=pk)''',
    '''def plan_edit(request, pk):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('billing:plans')
    plan = get_object_or_404(Plan, pk=pk)'''
)

b_content = b_content.replace(
    '''def plan_delete(request, pk):
    plan = get_object_or_404(Plan, pk=pk)''',
    '''def plan_delete(request, pk):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('billing:plans')
    plan = get_object_or_404(Plan, pk=pk)'''
)

with open('apps/billing/views.py', 'w', encoding='utf-8') as f:
    f.write(b_content)
print("apps/billing/views.py updated successfully!")

