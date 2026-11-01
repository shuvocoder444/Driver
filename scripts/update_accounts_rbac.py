with open('apps/accounts/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update team_member_delete
old_team_delete = '''def team_member_delete(request, pk):
    """Remove a team member to free up a company seat."""
    user = request.user
    if user.is_authenticated:
        company = user.get_company_account()
    else:
        company = CustomUser.objects.filter(role=CustomUser.Role.COMPANY).first()

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
    messages.success(request, f'Team member {member_name} has been removed. A seat is now free.')
    return redirect('accounts:team')'''

new_team_delete = '''def team_member_delete(request, pk):
    """Remove a team member to free up a company seat (Company or Super Admin)."""
    user = request.user
    if not user.is_authenticated:
        return redirect('accounts:login')

    if user.is_superuser or getattr(user, 'role', '') == CustomUser.Role.SUPERADMIN:
        member = get_object_or_404(CustomUser, pk=pk)
        company = member.get_company_account() or member.company_account
    else:
        company = user.get_company_account()
        member = get_object_or_404(CustomUser, pk=pk, company_account=company)

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
    return redirect('accounts:team')'''

assert old_team_delete in content, "old_team_delete not found"
content = content.replace(old_team_delete, new_team_delete)

# Update users_list guard
old_users_list = '''def users_list(request):
    query = request.GET.get('q', '').strip()'''

new_users_list = '''def users_list(request):
    if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN)):
        messages.error(request, 'Access denied. Super Admin privileges required.')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
                return redirect('dashboard:driver')
            return redirect('dashboard:admin')
        return redirect('accounts:login')

    query = request.GET.get('q', '').strip()'''

assert old_users_list in content, "old_users_list not found"
content = content.replace(old_users_list, new_users_list)

# Add user_delete at bottom
user_delete_func = '''

@login_required
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
'''

content += user_delete_func

with open('apps/accounts/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("apps/accounts/views.py updated successfully!")

# Update apps/accounts/urls.py
with open('apps/accounts/urls.py', 'r', encoding='utf-8') as f:
    url_content = f.read()

old_url = "path('users/', views.users_list, name='users'),"
new_url = "path('users/', views.users_list, name='users'),\n    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),"

if "user_delete" not in url_content:
    assert old_url in url_content, "old_url not found in accounts/urls.py"
    url_content = url_content.replace(old_url, new_url)
    with open('apps/accounts/urls.py', 'w', encoding='utf-8') as f:
        f.write(url_content)
    print("apps/accounts/urls.py updated successfully!")

