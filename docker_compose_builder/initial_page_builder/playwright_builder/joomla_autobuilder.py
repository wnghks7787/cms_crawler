from playwright.sync_api import sync_playwright, Page, expect
from playwright_tools import PlaywrightManager
import playwright_tools as pw_tools

import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--portnum', required=True)
parser.add_argument('--version', required=True)

args = parser.parse_args()

ACCESSING_CMS = f'Joomla-{args.version}'


def step1(page):
    print(f'Step1 Start: {ACCESSING_CMS}')

    page.locator('#jform_site_name').fill('test')

    page.locator('#step1').click()
    
    print(f'Step1 End: {ACCESSING_CMS}')

def step2(page):
    print(f'Step2 Start: {ACCESSING_CMS}')

    page.locator('#jform_admin_user').fill('admin')
    page.locator('#jform_admin_username').fill('admin')
    page.locator('#jform_admin_password').fill('password12345678')
    page.locator('#jform_admin_email').fill('wnghks7787@unist.ac.kr')

    page.locator('#step2').click()

    print(f'Step2 End: {ACCESSING_CMS}')

def step3(page):
    print(f'Step3 Start: {ACCESSING_CMS}')

    page.locator('#jform_db_host').fill(f'joomla-{args.version}-db')
    page.locator('#jform_db_user').fill('user')
    page.locator('#jform_db_pass').fill('password_user')
    page.locator('#jform_db_name').fill(f'db-joomla-{args.version}')

    page.locator('#setupButton').click()

    print(f'Step3 End: {ACCESSING_CMS}')

def step4(page):
    print(f'Step4 Start: {ACCESSING_CMS}')

    page.get_by_role('button', name='Open Site').click()

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
            
            success_message_locator = page.get_by_text('Congratulations! Your Joomla site is ready.')
            expect(success_message_locator).to_be_visible(timeout=120000)
            
            step4(page)
            
    except Exception as e:
        print(f'❌ \n{ACCESSING_CMS}: 스크립트 실행 중 알 수 없는 오류 발생: {e}')



