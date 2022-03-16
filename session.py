from playwright.sync_api import Playwright, sync_playwright
from prob import check_stop


class TradeSession:
    def __init__(self):
        self.mtng = 0.01
        self.init_stake = 0.35
        self.stake = 0.35
        self.stop_loss = 2
        self.stop_profit = 2
        self.ldp = 0
        self.loop = False

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()


    def login(self, email, psword):
        # Go to https://smarttrader.deriv.com/
        self.page.goto("https://smarttrader.deriv.com/")

        # Click text=Log in
        lg_btn = self.page.locator("#btn__login") or self.page.locator("text=Log in")
        lg_btn.click()

        self.page.wait_for_timeout(9000)

        # Click [placeholder="example\@email\.com"]
        email_input = self.page.locator('#txtEmail') or self.page.locator("[placeholder=\"example\\@email\\.com\"]")
        email_input.fill(email)

        self.page.wait_for_timeout(3000)

        psword_input = self.page.locator('#txtPass') or self.page.locator("input[name=\"password\"]")

        # Fill input[name="password"]
        psword_input.fill(psword)

        self.page.wait_for_timeout(2000)
        # Click button:has-text("Log in")
        # with page.expect_navigation(url="https://smarttrader.deriv.com/en/trading.html"):
        with self.page.expect_navigation():
            submit_btn = self.page.locator('button.button.secondary') or self.page.locator('input[name="login"]')
            submit_btn.click()
            #page.locator("button:has-text(\"Log in\")").click()



    def pause(self):
        self.loop = False


    def stop(self):
        self.loop = False


    def exit(self):
        '''
        Executed when the user closes (X)
        the GUI application window
        '''

        self.browser.close()
        self.playwright.stop()
        return
