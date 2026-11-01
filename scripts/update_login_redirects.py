with open('apps/accounts/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_code = """                elif getattr(user, 'role', '') in [CustomUser.Role.COMPANY, CustomUser.Role.ADMIN, CustomUser.Role.INDIVIDUAL]:
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
                    if next_url and '/driver/' not in next_url:
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
                    if next_url:
                        return redirect(next_url)
                    return redirect('dashboard:superadmin')"""

new_code = """                elif getattr(user, 'role', '') in [CustomUser.Role.COMPANY, CustomUser.Role.ADMIN, CustomUser.Role.INDIVIDUAL]:
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
                    if next_url and not any(bad in next_url for bad in ['/driver/', '/superadmin/', '/dashboard/']):
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
                    if next_url and next_url not in ['/dashboard/', '/dashboard/admin/', '/dashboard/company/', '/dashboard/driver/']:
                        return redirect(next_url)
                    return redirect('dashboard:superadmin')"""

text_norm = text.replace('\r\n', '\n')
old_norm = old_code.replace('\r\n', '\n')
new_norm = new_code.replace('\r\n', '\n')

assert old_norm in text_norm, "old_code not found in accounts/views.py"
text_norm = text_norm.replace(old_norm, new_norm, 1)

with open('apps/accounts/views.py', 'w', encoding='utf-8') as f:
    f.write(text_norm)

print("Successfully updated accounts/views.py login redirects")

