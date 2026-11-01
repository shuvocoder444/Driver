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
    driver.get('http://rus.velohoster.com/accounts/login/')
    email_el = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    pwd_el = driver.find_element(By.NAME, 'password')
    email_el.clear()
    email_el.send_keys('driver@topd.kg')
    pwd_el.clear()
    pwd_el.send_keys('driver123')
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(3)

    print('Driver URL after login:', driver.current_url)
    print('Driver Page Title:', driver.title)
    driver.save_screenshot('scratch/driver_portal_clean.png')

    hdr = driver.find_element(By.TAG_NAME, 'header').text.replace('\n', ' | ')
    print('Driver Header:', hdr)

    # Test trying to access superadmin
    driver.get('http://rus.velohoster.com/dashboard/superadmin/')
    time.sleep(2)
    print('Driver after trying /dashboard/superadmin/:', driver.current_url)

    # Test trying to access company admin
    driver.get('http://rus.velohoster.com/dashboard/admin/')
    time.sleep(2)
    print('Driver after trying /dashboard/admin/:', driver.current_url)

finally:
    driver.quit()

