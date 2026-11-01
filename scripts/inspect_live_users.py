import requests

base_url = 'http://rus.velohoster.com'

def inspect_user(email, password, role_label):
    print(f"\n=======================================================")
    print(f"INSPECTING LIVE: {role_label} ({email})")
    print(f"=======================================================")
    s = requests.Session()
    
    # 1. Login
    r = s.get(f'{base_url}/accounts/login/')
    csrf = s.cookies.get('csrftoken')
    r_post = s.post(f'{base_url}/accounts/login/', data={'email': email, 'password': password, 'csrfmiddlewaretoken': csrf}, allow_redirects=True)
    print(f"1. Login -> {r_post.url} (Status: {r_post.status_code})")
    
    # 2. Extract brand badge (under Topd logo)
    html = r_post.text
    brand_sub = ""
    if 'Sidebar Brand Header' in html:
        brand_chunk = html.split('Sidebar Brand Header')[1].split('Sidebar Navigation Menu')[0]
        for line in brand_chunk.splitlines():
            if 'uppercase tracking-widest' in line:
                brand_sub = line.strip()
            elif brand_sub and line.strip() and not line.strip().startswith('<'):
                brand_sub += " -> " + line.strip()
    print(f"2. Brand subtitle in sidebar: {brand_sub}")
    
    # 3. Extract top navbar badge / title
    header_chunk = ""
    if '<header' in html and '</header>' in html:
        header_chunk = html.split('<header')[1].split('</header>')[0]
        # find badges
        lines = [l.strip() for l in header_chunk.splitlines() if l.strip() and ('<span' in l or 'fa-building' in l or 'fa-crown' in l or 'fa-id-badge' in l)]
        print(f"3. Top navbar badges/icons: {lines[:4]}")
        
    # 4. Check user profile footer in sidebar
    footer_chunk = ""
    if 'Sidebar Footer' in html:
        footer_chunk = html.split('Sidebar Footer')[1].split('</aside>')[0]
        p_lines = [l.strip() for l in footer_chunk.splitlines() if '<p ' in l or 'text-xs font-bold' in l or 'capitalize' in l]
        print(f"4. Sidebar footer user card: {p_lines}")
        
    # 5. Check clicking /vehicles/
    r_veh = s.get(f'{base_url}/vehicles/')
    veh_html = r_veh.text
    is_super_side = 'SUPER ADMIN SIDEBAR' in veh_html
    is_comp_side = 'FLEET COMPANY ADMIN SIDEBAR' in veh_html
    is_driver_side = 'DRIVER SIDEBAR' in veh_html
    print(f"5. On /vehicles/ -> SuperAdminSidebar: {is_super_side}, CompanySidebar: {is_comp_side}, DriverSidebar: {is_driver_side}")

inspect_user('admin@topd.kg', 'admin123', 'Super Admin')
inspect_user('company@topd.kg', 'company123', 'Rental Agency')
inspect_user('driver@topd.kg', 'driver123', 'Driver')

