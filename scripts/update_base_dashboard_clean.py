with open('templates/dashboard/base_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Super Admin sidebar dynamic counts
old_agreements = '<span class="ml-2.5 flex-1">{{ t.menu_agreements }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full {% if \'/agreements/\' in request.path %}bg-red-100 text-red-700{% else %}bg-slate-100 text-slate-600{% endif %}">4</span>'
new_agreements = '<span class="ml-2.5 flex-1">{{ t.menu_agreements }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full {% if \'/agreements/\' in request.path %}bg-red-100 text-red-700{% else %}bg-slate-100 text-slate-600{% endif %}">{{ nav_counts.agreements }}</span>'
assert old_agreements in content, "old_agreements not found"
content = content.replace(old_agreements, new_agreements)

old_drivers = '<span class="ml-2.5 flex-1">{{ t.menu_drivers }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full {% if \'/drivers/\' in request.path and \'/check/\' not in request.path %}bg-red-100 text-red-700{% else %}bg-slate-100 text-slate-600{% endif %}">6</span>'
new_drivers = '<span class="ml-2.5 flex-1">{{ t.menu_drivers }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full {% if \'/drivers/\' in request.path and \'/check/\' not in request.path %}bg-red-100 text-red-700{% else %}bg-slate-100 text-slate-600{% endif %}">{{ nav_counts.drivers }}</span>'
assert old_drivers in content, "old_drivers not found"
content = content.replace(old_drivers, new_drivers)

old_vehicles = '<span class="ml-2.5 flex-1">{{ t.menu_vehicles_garage }}</span>\n                    </a>'
new_vehicles = '<span class="ml-2.5 flex-1">{{ t.menu_vehicles_garage }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">{{ nav_counts.vehicles }}</span>\n                    </a>'
assert old_vehicles in content, "old_vehicles not found"
content = content.replace(old_vehicles, new_vehicles, 1)

old_manual = '<span class="ml-2.5 flex-1">{{ t.menu_manual_payments }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600">1</span>'
new_manual = '<span class="ml-2.5 flex-1">{{ t.menu_manual_payments }}</span>\n                        {% if nav_counts.pending_payments > 0 %}\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600">{{ nav_counts.pending_payments }}</span>\n                        {% endif %}'
assert old_manual in content, "old_manual not found"
content = content.replace(old_manual, new_manual)

old_pages = '<span class="ml-2.5 flex-1">Manage Pages (CMS)</span>\n                        <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-red-100 text-red-600">7</span>'
new_pages = '<span class="ml-2.5 flex-1">Manage Pages (CMS)</span>\n                        <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-red-100 text-red-600">{{ nav_counts.pages }}</span>'
assert old_pages in content, "old_pages not found"
content = content.replace(old_pages, new_pages)

# 2. Company sidebar dynamic counts
old_co_vehicles = '<span class="ml-2.5 flex-1">{{ t.menu_my_vehicles }}</span>\n                    </a>'
new_co_vehicles = '<span class="ml-2.5 flex-1">{{ t.menu_my_vehicles }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">{{ nav_counts.vehicles }}</span>\n                    </a>'
assert old_co_vehicles in content, "old_co_vehicles not found"
content = content.replace(old_co_vehicles, new_co_vehicles, 1)

old_co_agreements = '<span class="ml-2.5 flex-1">{{ t.menu_rental_agreements }}</span>\n                    </a>'
new_co_agreements = '<span class="ml-2.5 flex-1">{{ t.menu_rental_agreements }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">{{ nav_counts.agreements }}</span>\n                    </a>'
assert old_co_agreements in content, "old_co_agreements not found"
content = content.replace(old_co_agreements, new_co_agreements, 1)

old_co_drivers = '<span class="ml-2.5 flex-1">{{ t.menu_agency_drivers }}</span>\n                    </a>'
new_co_drivers = '<span class="ml-2.5 flex-1">{{ t.menu_agency_drivers }}</span>\n                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">{{ nav_counts.drivers }}</span>\n                    </a>'
assert old_co_drivers in content, "old_co_drivers not found"
content = content.replace(old_co_drivers, new_co_drivers, 1)

old_seats = '<span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">3 Seats</span>'
new_seats = '<span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">{{ nav_counts.team_members }} Seats</span>'
assert old_seats in content, "old_seats not found"
content = content.replace(old_seats, new_seats)

old_co_sub = '<span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600">{{ t.badge_active }}</span>'
new_co_sub = '{% if nav_counts.active_subscriptions > 0 %}<span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600">{{ t.badge_active }}</span>{% else %}<span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-amber-50 text-amber-600">Inactive</span>{% endif %}'
assert old_co_sub in content, "old_co_sub not found"
content = content.replace(old_co_sub, new_co_sub)

# 3. Remove 3-switcher tabs from header and replace with clean role badge
import re
pattern = r'<!-- 3 DASHBOARD SWITCHER TABS.*?{% endif %}\s*</div>'
match = re.search(pattern, content, re.DOTALL)
assert match is not None, "Switcher tabs pattern not found"

clean_header_badge = '''<!-- Clean Role Status Badge (No Switcher Tabs) -->
                {% if request.user.is_authenticated and request.user.is_superadmin %}
                <div class="flex items-center space-x-2">
                    <span class="px-3 py-1.5 rounded-xl bg-red-50 text-red-600 border border-red-100 font-bold text-xs flex items-center space-x-1.5 shadow-xs">
                        <i class="fa-solid fa-crown text-[11px]"></i>
                        <span>Platform Master</span>
                    </span>
                </div>
                {% elif current_dashboard == 'admin' %}
                <div class="flex items-center space-x-2">
                    <span class="px-3 py-1.5 rounded-xl bg-red-50 text-red-600 border border-red-100 font-bold text-xs flex items-center space-x-1.5 shadow-xs">
                        <i class="fa-solid fa-building text-[11px]"></i>
                        <span>
                            {% if display_user.get_company_account.company_name %}
                                {{ display_user.get_company_account.company_name }}
                            {% elif display_user.company_name %}
                                {{ display_user.company_name }}
                            {% elif display_user.role == 'individual' %}
                                Personal
                            {% else %}
                                Company
                            {% endif %}
                        </span>
                    </span>
                </div>
                {% elif current_dashboard == 'driver' %}
                <div class="flex items-center space-x-2">
                    <span class="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-100 font-bold text-xs flex items-center space-x-1.5 shadow-xs">
                        <i class="fa-solid fa-id-badge text-[11px]"></i>
                        <span>Driver Portal</span>
                    </span>
                </div>
                {% else %}
                <div class="flex items-center space-x-2">
                    <span class="px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700 font-bold text-xs flex items-center space-x-1.5">
                        <i class="fa-solid fa-user text-[11px]"></i>
                        <span>Dashboard</span>
                    </span>
                </div>
                {% endif %}
            </div>'''

content = content[:match.start()] + clean_header_badge + content[match.end():]

with open('templates/dashboard/base_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("base_dashboard.html updated successfully!")

