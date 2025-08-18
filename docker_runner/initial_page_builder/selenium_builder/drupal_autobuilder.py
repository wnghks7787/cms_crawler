from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
import argparse

STEP_TIME = 1
INSTALL_TIME = 10

parser = argparse.ArgumentParser()
parser.add_argument('--portnum', required=True)
parser.add_argument('--version', required=True)

args = parser.parse_args()

# 드라이버 세팅
def driver_getter(port_num):
    driver = webdriver.Chrome()
    driver.get(f'http://localhost:{port_num}')

    return driver

# STEP1: 언어 설정
def step1(driver):
    step1_button = driver.find_element(By.NAME, 'op')
    step1_button.click()

# STEP2: 설치 프로필 설정 화면
def step2(driver):
    profile_button = driver.find_element(By.NAME, 'op')
    profile_button.click()

# STEP3: 데이터베이스 설정 화면
def step3(driver):
    db_name = driver.find_element(By.ID, 'edit-drupalmysqldriverdatabasemysql-database')
    db_id = driver.find_element(By.ID, 'edit-drupalmysqldriverdatabasemysql-username')
    db_pw = driver.find_element(By.ID, 'edit-drupalmysqldriverdatabasemysql-password')
    db_span = driver.find_element(By.XPATH, '//*[@id="edit-drupalmysqldriverdatabasemysql--2"]/summary')

    db_host_name = driver.find_element(By.ID, 'edit-drupalmysqldriverdatabasemysql-host')
    db_button = driver.find_element(By.NAME, 'op')

    db_span.click()
    db_host_name.clear()

    db_name.send_keys(f'db-drupal-{args.version}')
    db_id.send_keys('user')
    db_pw.send_keys('password_user')
    db_host_name.send_keys(f'drupal-{args.version}-db')
    db_button.click()

# STEP4: 사이트 정보 설정
def step4(driver):
    site_name = driver.find_element(By.NAME, 'site_name')
    site_email = driver.find_element(By.NAME, 'site_mail')
    site_username = driver.find_element(By.NAME, 'account[name]')
    site_password = driver.find_element(By.NAME, 'account[pass][pass1]')
    site_password2 = driver.find_element(By.NAME, 'account[pass][pass2]')
    site_email_addr = driver.find_element(By.NAME, 'account[mail]')
    site_auto_update = driver.find_element(By.NAME, 'enable_update_status_module')

    site_button = driver.find_element(By.NAME, 'op')

    site_name.send_keys('test')
    site_email.send_keys('wnghks7787@naver.com')
    site_username.send_keys('user')
    site_password.send_keys('password')
    site_password2.send_keys('password')
    site_email_addr.send_keys('wnghks7787@naver.com')

    site_auto_update.click()

    site_button.click()


def run():
    driver = driver_getter(args.portnum)

    step1(driver)
    time.sleep(STEP_TIME)

    step2(driver)
    time.sleep(STEP_TIME)

    step3(driver)

    try:
        wait = WebDriverWait(driver, 300)

        finish = wait.until(
            EC.visibility_of_element_located((By.NAME, 'site_name'))
        )
    except TimeoutException:
        print("error with timeout")

    step4(driver)
    time.sleep(STEP_TIME)

if __name__ == '__main__':
    run()