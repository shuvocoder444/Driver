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

try:
    print("Navigating to login page...")
    driver.get('http://rus.velohoster.com/accounts/login/')
    print("Page Title:", driver.title)

    # Fill login form
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    email_input.clear()
    email_input.send_keys("admin@topd.kg")
    password_input.clear()
    password_input.send_keys("admin123")
    submit_btn.click()

    time.sleep(3)
    print("After Login URL:", driver.current_url)
    print("After Login Title:", driver.title)
    driver.save_screenshot("scratch/after_login.png")

    # Let's inspect the active sidebar links
    sidebar_links = driver.find_elements(By.CSS_SELECTOR, "aside a")
    print(f"Found {len(sidebar_links)} links in sidebar:")
    menu_urls = []
    for link in sidebar_links:
        href = link.get_attribute("href")
        text = link.text.replace("\n", " ").strip()
        if href and "javascript" not in href:
            print(f" - [{text}] -> {href}")
            menu_urls.append((text, href))

    # Also inspect the top header tabs/badges
    header = driver.find_element(By.TAG_NAME, "header")
    print("Header Text:", header.text.replace("\n", " | "))

    # Now let's visit each menu link or click them and inspect the result
    test_urls = [
        ("Agreements", "http://rus.velohoster.com/agreements/"),
        ("Drivers", "http://rus.velohoster.com/drivers/"),
        ("Check Driver", "http://rus.velohoster.com/drivers/check/"),
        ("Vehicles", "http://rus.velohoster.com/vehicles/"),
        ("Subscriptions", "http://rus.velohoster.com/billing/subscriptions/"),
        ("Buy Subscription", "http://rus.velohoster.com/billing/purchase/"),
        ("Users", "http://rus.velohoster.com/accounts/users/"),
        ("Settings", "http://rus.velohoster.com/settings/"),
    ]

    for name, target_url in test_urls:
        print(f"\n--- Testing Navigation to {name} ({target_url}) ---")
        driver.get(target_url)
        time.sleep(2)
        print(f"Final URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")
        
        # Check what tabs/badges exist in header
        try:
            hdr = driver.find_element(By.TAG_NAME, "header")
            print(f"Header: {hdr.text.replace(chr(10), ' | ')}")
        except Exception as e:
            print(f"Header not found: {e}")

        # Check if sidebar has Super Admin or Company Admin
        try:
            aside = driver.find_element(By.TAG_NAME, "aside")
            first_links = aside.find_elements(By.CSS_SELECTOR, "a")[:4]
            aside_texts = [a.text.replace("\n", " ").strip() for a in first_links]
            print(f"Sidebar top items: {aside_texts}")
        except Exception as e:
            print(f"Aside not found: {e}")

        clean_name = name.lower().replace(" ", "_")
        driver.save_screenshot(f"scratch/page_{clean_name}.png")

finally:
    driver.quit()
    print("\nBrowser test finished.")

