with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update admin_dashboard
old_admin_sess = """    request.session['active_dashboard_role'] = 'admin'
    request.session.modified = True"""

new_admin_sess = """    if not (request.user.is_authenticated and getattr(request.user, 'is_superadmin', False)):
        request.session['active_dashboard_role'] = 'admin'
        request.session.modified = True"""

# 2. Update get_current_driver
old_driver_sess = """    request.session['active_dashboard_role'] = 'driver'
    request.session.modified = True"""

new_driver_sess = """    if not (request.user.is_authenticated and getattr(request.user, 'is_superadmin', False)):
        request.session['active_dashboard_role'] = 'driver'
        request.session.modified = True"""

text_norm = text.replace('\r\n', '\n')
old_admin_norm = old_admin_sess.replace('\r\n', '\n')
new_admin_norm = new_admin_sess.replace('\r\n', '\n')
old_driver_norm = old_driver_sess.replace('\r\n', '\n')
new_driver_norm = new_driver_sess.replace('\r\n', '\n')

assert old_admin_norm in text_norm
text_norm = text_norm.replace(old_admin_norm, new_admin_norm, 1)

assert old_driver_norm in text_norm
text_norm = text_norm.replace(old_driver_norm, new_driver_norm, 1)

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(text_norm)

print("Updated dashboard/views.py to preserve superadmin session role")

