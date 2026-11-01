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
    print("1. Login as Super Admin...")
    driver.get('http://rus.velohoster.com/accounts/login/')
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "password").send_keys("admin123")
    email_input.send_keys("admin@topd.kg")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    print("Logged in. Current URL:", driver.current_url)

    print("\n2. Now navigating to Website Landing Page (http://rus.velohoster.com/)...")
    driver.get('http://rus.velohoster.com/')
    time.sleep(2)
    print("Landing Page Title:", driver.title)
    driver.save_screenshot("scratch/landing_while_logged_in.png")

    # Check navbar buttons on landing page
    nav = driver.find_element(By.TAG_NAME, "nav")
    print("Landing page nav buttons:", nav.text.replace("\n", " | "))

    # Check if the user is still logged in or logged out
    cookies = driver.get_cookies()
    session_cookie = [c for c in cookies if c['name'] == 'sessionid']
    print("Session cookie exists on landing page:", len(session_cookie) > 0)

    # Click Dashboard button on landing page if exists
    try:
        dash_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Dashboard') or contains(text(), 'Панель')]")
        print("Found Dashboard button on landing page! Link:", dash_btn.get_attribute("href"))
        dash_btn.click()
        time.sleep(2)
        print("After clicking Dashboard from landing page:", driver.current_url)
    except Exception as e:
        print("Dashboard button not found or error:", e)

finally:
    driver.quit()
    print("Done test.")

