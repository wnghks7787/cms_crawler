from playwright.sync_api import sync_playwright, Page, expect
from playwright_tools import PlaywrightManager
import playwright_tools as pw_tools

import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--portnum', required=True)
parser.add_argument('--version', required=True)

args = parser.parse_args()

ACCESSING_CMS = f'Prestashop-{args.version}'

def step1(page):
    print(f'Step1 Start: {ACCESSING_CMS}')

    page.locator('#btNext').click()

    print(f'Step1 End: {ACCESSING_CMS}')

def step2(page):
    print(f'Step2 Start: {ACCESSING_CMS}')

    page.locator('#set_license').click()

    page.locator('#btNext').click()

    print(f'Step2 End: {ACCESSING_CMS}')

def step3(page):
    print(f'Step3 Start: {ACCESSING_CMS}')

    page.locator('#infosShop').fill('test')
    page.locator('#infosFirstname').fill('John')
    page.locator('#infosName').fill('Doe')
    page.locator('#infosEmail').fill('wnghks7787@unist.ac.kr')
    page.locator('#infosPassword').fill('adminpassword12345678')
    page.locator('#infosPasswordRepeat').fill('adminpassword12345678')

    country_dropdown_locator = page.locator('#infosCountry_chosen')
    clickable_area = country_dropdown_locator.locator('.chosen-single')
    clickable_area.click()
    page.get_by_role("listitem").filter(has_text="United States").click()

    page.locator('#btNext').click()

    print(f'Step3 End: {ACCESSING_CMS}')

def step4(page):
    print(f'Step4 Start: {ACCESSING_CMS}')

    next_button = page.locator('#btNext')
    next_button.focus()
    next_button.click()

    print(f'Step4 End: {ACCESSING_CMS}')

def step5(page):
    print(f'Step5 Start: {ACCESSING_CMS}')

    page.locator('#dbServer').fill(f'prestashop-{args.version}-db')
    page.locator('#dbName').fill(f'db-prestashop-{args.version}')
    page.locator('#dbLogin').fill('user')
    page.locator('#dbPassword').fill('password_user')
    
    page.locator('#btNext').click()

    print(f'Step5 End: {ACCESSING_CMS}')

if __name__ == '__main__':
    PORT = args.portnum

    try:
        with PlaywrightManager(headless=True, viewport={'width':1400, 'height':1500}) as page:
            page.goto(f'http://localhost:{PORT}')
            print('✅ Page 오픈 성공')

            step1(page)
            step2(page)
            step3(page)
            step4(page)
            step5(page)

            success_message_locator = page.get_by_text('Your installation is finished!')
            expect(success_message_locator).to_be_visible(timeout=600000)

    except Exception as e:
        print(f'\n❌ {ACCESSING_CMS}: 스크립트 실행 중 알 수 없는 오류 발생: {e}')