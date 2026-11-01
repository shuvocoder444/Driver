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

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    email_input.clear()
    email_input.send_keys("admin@topd.kg")
    password_input.clear()
    password_input.send_keys("admin123")
    submit_btn.click()
    time.sleep(3)
    print("Initial URL after login:", driver.current_url)

    # List all link texts in sidebar
    sidebar = wait.until(EC.presence_of_element_located((By.TAG_NAME, "aside")))
    nav_links = sidebar.find_elements(By.CSS_SELECTOR, "nav a")
    link_texts = [a.text.split("\n")[0].strip() for a in nav_links if a.text.strip()]
    print("Sidebar links found:", link_texts)

    for text in link_texts:
        print(f"\n---> Clicking sidebar link: '{text}'")
        # Re-fetch sidebar and find element by partial text
        aside = driver.find_element(By.TAG_NAME, "aside")
        links = aside.find_elements(By.CSS_SELECTOR, "nav a")
        target_link = None
        for l in links:
            if text in l.text:
                target_link = l
                break
        
        if not target_link:
            print(f"Could not find link '{text}'!")
            continue

        target_href = target_link.get_attribute("href")
        print(f"Target href: {target_href}")
        target_link.click()
        time.sleep(2)

        print(f"Landed on URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")

        # Check what the header looks like
        try:
            hdr = driver.find_element(By.TAG_NAME, "header")
            print(f"Header: {hdr.text.replace(chr(10), ' | ')}")
        except Exception as e:
            print(f"Header not found: {e}")

        # Check what sidebar top item says
        try:
            aside = driver.find_element(By.TAG_NAME, "aside")
            first_a = aside.find_element(By.CSS_SELECTOR, "nav a")
            print(f"Sidebar top nav item: '{first_a.text.replace(chr(10), ' ').strip()}'")
        except Exception as e:
            print(f"Sidebar first item error: {e}")

        if "admin/" in driver.current_url and "superadmin" not in driver.current_url:
            print(f"⚠️ ALERT! Reached Company Dashboard URL on clicking '{text}'!")

finally:
    driver.quit()
    print("\nClick test finished.")

