from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
import argparse

STEP_TIME = 1
INSTALL_TIME = 30

parser = argparse.ArgumentParser()
parser.add_argument('--portnum', required=True)
parser.add_argument('--version', required=True)

args = parser.parse_args()

options = webdriver.ChromeOptions()
options.add_argument("headless")

def driver_getter(port_num):
    driver = webdriver.Chrome()
    driver.get(f'http://localhost:{port_num}')

    return driver

# STEP1: 언어 선택
def step1(driver):
    step1_button = driver.find_element(By.NAME, 'submitNext')

    step1_button.click()

# STEP2: 라이선스 동의
def step2(driver):
    license_agreement = driver.find_element(By.NAME, 'licence_agrement')
    step2_button = driver.find_element(By.NAME, 'submitNext')

    license_agreement.click()
    step2_button.click()

# STEP3: 상점 정보
def step3(driver):
    shop_name = driver.find_element(By.NAME, 'shop_name')
    admin_firstname = driver.find_element(By.NAME, 'admin_firstname')
    admin_lastname = driver.find_element(By.NAME, 'admin_lastname')
    admin_email = driver.find_element(By.NAME, 'admin_email')
    admin_password = driver.find_element(By.NAME, 'admin_password')
    admin_password_confirm = driver.find_element(By.NAME, 'admin_password_confirm')

    step3_button = driver.find_element(By.NAME, 'submitNext')

    shop_name.send_keys('test')
    admin_firstname.send_keys('John')
    admin_lastname.send_keys('Doe')
    admin_email.send_keys('wnghks7787@naver.com')
    admin_password.send_keys('adminpassword12345678')
    admin_password_confirm.send_keys('adminpassword12345678')

    step3_button.click()

# STEP4: 설치 정보
def step4(driver):
    step4_button = driver.find_element(By.NAME, 'submitNext')

    step4_button.click()

# STEP5: DB 정보
def step5(driver):
    db_server = driver.find_element(By.NAME, 'dbServer')
    db_name = driver.find_element(By.NAME, 'dbName')
    db_user = driver.find_element(By.NAME, 'dbLogin')
    db_password = driver.find_element(By.NAME, 'dbPassword')

    step5_button = driver.find_element(By.NAME, 'submitNext')

    db_server.clear()
    db_name.clear()
    db_user.clear()

    db_server.send_keys(f'prestashop-{args.version}-db')
    db_name.send_keys(f'db-prestashop-{args.version}')
    db_user.send_keys('user')
    db_password.send_keys('password_user')

    step5_button.click()
    
def run():
    driver = driver_getter(args.portnum)

    step1(driver)
    time.sleep(STEP_TIME)

    step2(driver)
    time.sleep(STEP_TIME)

    step3(driver)
    time.sleep(STEP_TIME)

    step4(driver)
    time.sleep(STEP_TIME)

    step5(driver)

    try:
        wait = WebDriverWait(driver, 300)

        finish = wait.until(
            EC.visibility_of_element_located((By.ID, 'install_process_success'))
        )
    except TimeoutException:
        print("error with timeout")

    time.sleep(STEP_TIME)

if __name__ == '__main__':
    run()