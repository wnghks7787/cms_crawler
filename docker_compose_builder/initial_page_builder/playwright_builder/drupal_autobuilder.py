from playwright.sync_api import sync_playwright, Page, expect
from playwright_tools import PlaywrightManager
import playwright_tools as pw_tools

import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--portnum', required=True)
parser.add_argument('--version', required=True)

args = parser.parse_args()

ACCESSING_CMS = f'Drupal-{args.version}'

def step1(page):
    print(f'Step1 Start: {ACCESSING_CMS}')

    page.locator('#edit-submit').click()

    print(f'Step1 End: {ACCESSING_CMS}')

def step2(page):
    print(f'Step2 Start: {ACCESSING_CMS}')

    page.locator('#edit-submit').click()

    print(f'Step2 End: {ACCESSING_CMS}')

def step3(page):
    print(f'Step3 Start: {ACCESSING_CMS}')

    page.get_by_role('button', name='Advanced options').click()

    if int(pw_tools.version_splitter(args.version)[0]) > 9:
        page.locator('#edit-drupalmysqldriverdatabasemysql-database').fill(f'db-drupal-{args.version}')
        page.locator('#edit-drupalmysqldriverdatabasemysql-username').fill('user')
        page.locator('#edit-drupalmysqldriverdatabasemysql-password').fill('password_user')
        page.locator('#edit-drupalmysqldriverdatabasemysql-host').fill(f'drupal-{args.version}-db')
    else:
        page.locator('#edit-mysql-database').fill(f'db-drupal-{args.version}')
        page.locator('#edit-mysql-username').fill('user')
        page.locator('#edit-mysql-password').fill('password_user')
        page.locator('#edit-mysql-host').fill(f'drupal-{args.version}-db')

    page.locator('#edit-save').click()

    print(f'Step3 End: {ACCESSING_CMS}')

def step4(page):
    print(f'Step4 Start: {ACCESSING_CMS}')

    page.locator('#edit-site-name').fill('test')
    page.locator('#edit-site-mail').fill('wnghks7787@unist.ac.kr')
    page.locator('#edit-account-name').fill('admin')
    page.locator('#edit-account-pass-pass1').fill('password')
    page.locator('#edit-account-pass-pass2').fill('password')

    page.locator('#edit-enable-update-status-module').click()

    page.locator('#edit-submit').click()

    print(f'Step4 End: {ACCESSING_CMS}')


if __name__ == '__main__':
    PORT = args.portnum

    try:
        with PlaywrightManager(headless=False, viewport={'width':1400, 'height':1500}) as page:
            page.goto(f'http://localhost:{PORT}')
            print('✅ Page 오픈 성공')

            step1(page)
            step2(page)
            step3(page)
            
            success_message_locator = page.get_by_text('Site name')
            expect(success_message_locator).to_be_visible(timeout=120000)

            step4(page)
            
    except Exception as e:
        print(f'\n❌ {ACCESSING_CMS}: 스크립트 실행 중 알 수 없는 오류 발생: {e}')


