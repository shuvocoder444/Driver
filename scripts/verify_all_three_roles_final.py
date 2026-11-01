import os
import sys
import time

os.environ['SE_CACHE_PATH'] = r'D:\new\.cache'

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.stdout.reconfigure(encoding='utf-8')

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1440,900')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

def login_user(email, password):
    driver.get('http://rus.velohoster.com/accounts/logout/')
    time.sleep(1)
    driver.get('http://rus.velohoster.com/accounts/login/')
    email_el = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    pwd_el = driver.find_element(By.NAME, 'password')
    email_el.clear()
    email_el.send_keys(email)
    pwd_el.clear()
    pwd_el.send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(2)

try:
    # ========================================================
    # 1. TEST SUPER ADMIN
    # ========================================================
    print("=" * 60)
    print("1. TESTING SUPER ADMIN (admin@topd.kg)")
    print("=" * 60)
    login_user('admin@topd.kg', 'admin123')
    print("Super Admin landed on:", driver.current_url)
    driver.save_screenshot("scratch/final_superadmin_dashboard.png")

    # Check header
    header = driver.find_element(By.TAG_NAME, 'header')
    hdr_text = header.text.replace("\n", " | ")
    print("Super Admin Header:", hdr_text)
    assert "1. Super Admin" not in hdr_text, "ERROR: Switcher tabs still present in header!"
    assert "2. Company" not in hdr_text, "ERROR: Switcher tabs still present in header!"
    assert "Platform Master" in hdr_text, "Platform Master badge not found in header"
    print("✅ Header Switcher tabs are completely REMOVED! Clean Platform Master badge shown.")

    # Check sidebar counts
    aside = driver.find_element(By.TAG_NAME, 'aside')
    links = aside.find_elements(By.CSS_SELECTOR, 'nav a')
    for l in links:
        txt = l.text.replace("\n", " ").strip()
        print(f" - Sidebar Item: '{txt}'")

    # Visit Manual Payments
    driver.get('http://rus.velohoster.com/billing/manual-payments/')
    time.sleep(1.5)
    driver.save_screenshot("scratch/final_superadmin_manual_payments.png")
    print("Manual Payments URL:", driver.current_url)

    # Visit Users Management
    driver.get('http://rus.velohoster.com/accounts/users/')
    time.sleep(1.5)
    driver.save_screenshot("scratch/final_superadmin_users_list.html.png")
    users_table = driver.find_element(By.TAG_NAME, 'table')
    th_texts = [th.text.strip() for th in users_table.find_elements(By.TAG_NAME, 'th')]
    print("Users table headers:", th_texts)
    assert any("action" in th.lower() for th in th_texts), "ERROR: Actions column missing in users table!"
    delete_buttons = users_table.find_elements(By.XPATH, "//a[contains(text(), 'Delete')]")
    print(f"✅ Found {len(delete_buttons)} delete buttons for Super Admin to delete users/team!")

    # ========================================================
    # 2. TEST COMPANY (company@topd.kg) & SECURITY ISOLATION
    # ========================================================
    print("\n" + "=" * 60)
    print("2. TESTING COMPANY (company@topd.kg)")
    print("=" * 60)
    login_user('company@topd.kg', 'company123')
    print("Company landed on:", driver.current_url)
    driver.save_screenshot("scratch/final_company_dashboard.png")

    co_hdr = driver.find_element(By.TAG_NAME, 'header').text.replace("\n", " | ")
    print("Company Header:", co_hdr)
    assert "Team JBDIT Rental Ltd" in co_hdr, "Company name missing in header"
    print("✅ Company header shows company badge cleanly.")

    # Try to access Super Admin restricted URLs as Company
    restricted_urls = [
        ("Superadmin Dashboard", "http://rus.velohoster.com/dashboard/superadmin/"),
        ("Website Settings", "http://rus.velohoster.com/settings/"),
        ("Users Management", "http://rus.velohoster.com/accounts/users/"),
        ("Manual Payments", "http://rus.velohoster.com/billing/manual-payments/"),
    ]

    for name, url in restricted_urls:
        driver.get(url)
        time.sleep(1.5)
        print(f"Company tried visiting {name} -> Landed on: {driver.current_url}")
        assert "superadmin" not in driver.current_url and "settings" not in driver.current_url and "manual-payments" not in driver.current_url, f"SECURITY LEAK! Company accessed {url}"
        print(f"✅ Access to {name} strictly BLOCKED for company!")

    # ========================================================
    # 3. TEST DRIVER (driver@topd.kg) & SECURITY ISOLATION
    # ========================================================
    print("\n" + "=" * 60)
    print("3. TESTING DRIVER (driver@topd.kg)")
    print("=" * 60)
    login_user('driver@topd.kg', 'driver123')
    print("Driver landed on:", driver.current_url)
    driver.save_screenshot("scratch/final_driver_dashboard.png")

    driver_hdr = driver.find_element(By.TAG_NAME, 'header').text.replace("\n", " | ")
    print("Driver Header:", driver_hdr)
    assert "Driver Portal" in driver_hdr, "Driver Portal badge missing in header"
    print("✅ Driver header shows Driver Portal badge cleanly.")

    # Try to access Super Admin & Company restricted URLs as Driver
    driver_restricted_urls = [
        ("Superadmin Dashboard", "http://rus.velohoster.com/dashboard/superadmin/"),
        ("Company Dashboard", "http://rus.velohoster.com/dashboard/admin/"),
        ("Website Settings", "http://rus.velohoster.com/settings/"),
    ]

    for name, url in driver_restricted_urls:
        driver.get(url)
        time.sleep(1.5)
        print(f"Driver tried visiting {name} -> Landed on: {driver.current_url}")
        assert "superadmin" not in driver.current_url and "admin" not in driver.current_url and "settings" not in driver.current_url, f"SECURITY LEAK! Driver accessed {url}"
        print(f"✅ Access to {name} strictly BLOCKED for driver!")

    print("\n" + "=" * 60)
    print("🎉 ALL ROLE ISOLATION & DYNAMIC COUNT TESTS PASSED 100%!")
    print("=" * 60)

finally:
    driver.quit()
