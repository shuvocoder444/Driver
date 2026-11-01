with open('templates/users/list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update table header
old_th = '<th class="py-3.5 px-4">{{ t.date_joined }}</th>\n                    </tr>'
new_th = '<th class="py-3.5 px-4">{{ t.date_joined }}</th>\n                        <th class="py-3.5 px-4 text-right">Actions</th>\n                    </tr>'
assert old_th in content, "old_th not found"
content = content.replace(old_th, new_th)

# Update row actions
old_row = '''                        <td class="py-3 px-4 text-slate-500 text-[11px]">
                            {{ u.date_joined|date:"M d, Y" }}
                        </td>
                    </tr>'''

new_row = '''                        <td class="py-3 px-4 text-slate-500 text-[11px]">
                            {{ u.date_joined|date:"M d, Y" }}
                        </td>
                        <td class="py-3 px-4 text-right">
                            {% if u != request.user %}
                            <a href="{% url 'accounts:user_delete' u.id %}" 
                               onclick="return confirm('Are you sure you want to permanently delete user {{ u.email }}?')" 
                               class="inline-flex items-center px-2.5 py-1 text-xs font-semibold text-rose-600 hover:text-white hover:bg-rose-600 border border-rose-200 hover:border-rose-600 rounded-lg transition shadow-2xs">
                                <i class="fa-solid fa-trash-can mr-1.5 text-[10px]"></i> Delete
                            </a>
                            {% else %}
                            <span class="text-[10px] text-slate-400 font-semibold italic">Current Admin</span>
                            {% endif %}
                        </td>
                    </tr>'''

assert old_row in content, "old_row not found"
content = content.replace(old_row, new_row)

content = content.replace('<td colspan="5"', '<td colspan="6"')

with open('templates/users/list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("templates/users/list.html updated successfully!")

