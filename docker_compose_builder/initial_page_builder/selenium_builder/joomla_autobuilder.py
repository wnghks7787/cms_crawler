from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import tempfile
import shutil
import os

import time
import argparse

import selenium_tools

STEP_TIME = 1
INSTALL_TIME = 10

CHROME_DRIVER_PATH = '/home/wnghks7787/chromedriver-linux64/chromedriver'

parser = argparse.ArgumentParser()
parser.add_argument('--portnum', required=True)
parser.add_argument('--version', required=True)

args = parser.parse_args()

def driver_getter(port_num):
    user_data_dir = tempfile.mkdtemp()
    print(f"충돌 방지를 위해 생성된 임시 프로필 폴더: {user_data_dir}")

    # Option 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("window-size=1400,1500")
    options.add_argument("start-maximized")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    service = Service(executable_path=CHROME_DRIVER_PATH)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(f'http://localhost:{port_num}')

    return driver, user_data_dir

# STEP1: Select language and site name
def step1(driver):
    site_name = driver.find_element(By.NAME, 'jform[site_name]')
    step1_button = driver.find_element(By.ID, 'step1')

    site_name.send_keys("test")
    step1_button.click()

# STEP2: Setting Super User
def step2(driver):
    try:
        super_user_name = driver.find_element(By.NAME, 'jform[admin_user]')
        super_user_account = driver.find_element(By.NAME, 'jform[admin_username]')
        super_user_password = driver.find_element(By.NAME, 'jform[admin_password]')
        super_user_email = driver.find_element(By.NAME, 'jform[admin_email]')
        step2_button_locator = driver.find_element(By.ID, 'step2')

        super_user_name.send_keys("admin")
        super_user_account.send_keys("admin")
        super_user_password.send_keys("password12345678")
        super_user_email.send_keys("wnghks7787@naver.com")
        step2_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(step2_button_locator)
        )
        driver.execute_script("arguments[0].click()", step2_button)
    except TimeoutException:
        print("클릭할 수 없습니다.")
        raise

# STEP3: DB Setting
def step3(driver):
    db_type = driver.find_element(By.NAME, 'jform[db_type]')
    db_host_name = driver.find_element(By.NAME, 'jform[db_host]')
    db_user_name = driver.find_element(By.NAME, 'jform[db_user]')
    db_password = driver.find_element(By.NAME, 'jform[db_pass]')
    db_name = driver.find_element(By.NAME, 'jform[db_name]')
    step3_button = driver.find_element(By.ID, 'setupButton')

    db_host_name.clear()
    db_name.clear()

    db_host_name.send_keys(f'joomla-{args.version}-db')
    db_user_name.send_keys('user')
    db_password.send_keys('password_user')
    db_name.send_keys(f'db-joomla-{args.version}')

    driver.execute_script("arguments[0].click();", step3_button)

def step4(driver):
    open_button = driver.find_element(By.XPATH, '//*[@id="installRecommended"]/div/div/button[1]')

    driver.execute_script("arguments[0].click()", open_button)

def old_step1(driver):
    site_name = driver.find_element(By.NAME, 'jform[site_name]')
    
    super_user_email = driver.find_element(By.NAME, 'jform[admin_email]')
    super_user_name = driver.find_element(By.NAME, 'jform[admin_user]')
    super_user_password = driver.find_element(By.NAME, 'jform[admin_password]')
    super_user_password2 = driver.find_element(By.NAME, 'jform[admin_password2]')

    step1_button = driver.find_element(By.XPATH, '//*[@id="adminForm"]/div[3]/div/div/a')

    site_name.send_keys("test")

    super_user_email.send_keys("wnghks7787@naver.com")
    super_user_name.send_keys("admin")
    super_user_password.send_keys("admin")
    super_user_password2.send_keys("admin")

    step1_button.click()
    
def old_step2(driver):
    db_host_name = driver.find_element(By.NAME, 'jform[db_host]')
    db_user_name = driver.find_element(By.NAME, 'jform[db_user]')
    db_password = driver.find_element(By.NAME, 'jform[db_pass]')
    db_name = driver.find_element(By.NAME, 'jform[db_name]')
    step2_button = driver.find_element(By.XPATH, '//*[@id="adminForm"]/div[9]/div/div/a[2]')

    db_host_name.clear()

    db_host_name.send_keys(f'joomla-{args.version}-db')
    db_user_name.send_keys('user')
    db_password.send_keys('password_user')
    db_name.send_keys(f'db-joomla-{args.version}')

    driver.execute_script("arguments[0].click();", step2_button)

def old_step3(driver):
    step3_button = driver.find_element(By.XPATH, '//*[@id="adminForm"]/div[1]/div/a[2]')
    
    step3_button.click()

def old_step4(driver):
    step4_button = driver.find_element(By.NAME, 'instDefault')

    step4_button.click()

def run():
    driver = None
    user_data_dir_to_clean = None

    versions = selenium_tools.version_splitter(args.version)

    try:
        driver, user_data_dir_to_clean = driver_getter(args.portnum)

        if int(versions[0]) > 3:
            step1(driver)
            time.sleep(STEP_TIME)

            step2(driver)
            time.sleep(STEP_TIME)

            step3(driver)

            try:
                wait = WebDriverWait(driver, 300)

                finish = wait.until(
                    EC.visibility_of_element_located((By.ID, 'customInstallation'))
                )
            except TimeoutException:
                print("error with timeout")
            
            time.sleep(STEP_TIME)
            step4(driver)
            time.sleep(STEP_TIME)
        else:
            old_step1(driver)
            time.sleep(STEP_TIME)

            old_step2(driver)
            time.sleep(STEP_TIME)

            old_step3(driver)

            try:
                wait = WebDriverWait(driver, 300)

                finish = wait.until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="adminForm"]/div[2]'))
                )
            except TimeoutException:
                print("error with timeout")
            
            time.sleep(STEP_TIME)
            old_step4(driver)
            time.sleep(STEP_TIME)

        driver.quit()
    finally:
        if driver:
            driver.quit()
        time.sleep(STEP_TIME)
        
        if user_data_dir_to_clean:
            shutil.rmtree(user_data_dir_to_clean)

if __name__ == '__main__':
    run()
