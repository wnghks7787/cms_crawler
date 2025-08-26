from playwright.sync_api import sync_playwright, Page
from typing import Optional

class PlaywrightManager:
    def __init__(self, headless: bool=True, viewport: Optional[dict]=None):
        self.headless = headless
        self.viewport = viewport or {'width': 1920, 'height': 1000}
        self.playwright = None
        self.browser = None
    
    def __enter__(self) -> Page:
        print("⚙️ Playwright 브라우저를 설정합니다...")
        self.playwright = sync_playwright().start()

        browser_args = ['--no-sandbox', '--disable-dev-shm-usage']

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args,
            slow_mo=50
        )

        context = self.browser.new_context(viewport=self.viewport)
        page = context.new_page()
        print("    -> 브라우저 설정 완료")
        return page
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("\n🧹 Playwright 브라우저를 정리합니다...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("    -> 정리 완료")

def version_splitter(ver):
    splitted_ver = ver.split(".")

    return splitted_ver