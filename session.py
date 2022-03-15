from playwright.sync_api import Playwright, sync_playwright
from prob import check_stop


class TradeSession:
    def __init__(self):
        self.mtng = 0.01
        self.init_stake = 0.35
        self.stop_loss = 2
        self.stop_profit = 2
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

        self.page.wait_for_timeout(11000)

        psword_input = self.page.locator('#txtPass') or self.page.locator("input[name=\"password\"]")

        # Fill input[name="password"]
        psword_input.fill(psword)

        self.page.wait_for_timeout(9000)
        # Click button:has-text("Log in")
        # with page.expect_navigation(url="https://smarttrader.deriv.com/en/trading.html"):
        with self.page.expect_navigation():
            submit_btn = self.page.locator('button.button.secondary') or self.page.locator('input[name="login"]')
            submit_btn.click()
            #page.locator("button:has-text(\"Log in\")").click()
        # assert page.url == "https://smarttrader.deriv.com/en/logged_inws.html?acct1=VRTC5668415&token1=a1-5YB08Egh7wehF3DMq5ihyFDSRNnZK&cur1=USD&state="


    def play(self, window, values):
        '''
        Runs the smarttrader session with Volatility 100
        in the Match/Differ settings
        '''
        if not values['_SK_'] or not values['_MG_'] or not values['_LDP_']:
            window['_MESSAGE_'].update('Please provide LDP, Stake and initial Martingale')
            return

        self.loop = True
        self.mtng = values['_MG_']
        self.stop_loss = values['_SL_']
        self.stop_profit = values['_SP_']
        stake = values['_SK_']
        ldp = values['_LDP_']

        start_balance = self.page.locator("#header__acc-balance").inner_text().split()[0]
        window['_START_BAL_'].update(start_balance)

        while self.loop:
            self.page.wait_for_timeout(8000)
            self.page.goto(
                f"https://smarttrader.deriv.com/en/trading.html?currency=USD&market=synthetic_index&underlying=R_100&formname=matchdiff&date_start=now&duration_amount=1&duration_units=t&amount={stake}&amount_type=stake&expiry_type=duration&prediction={ldp}"
            )

            self.page.wait_for_timeout(13000)
            #10,001.83 USD
            balance = self.page.locator("#header__acc-balance").inner_text().split()[0]
            window['_CURRENT_BAL_'].update(balance)

            # Click #purchase_button_top
            self.page.locator("#purchase_button_top").click()

            self.page.wait_for_timeout(21000)
            # Click text=This contract lost
            result_str = self.page.locator("#contract_purchase_heading").inner_text()
            print(result_str)

            win = True
            if result_str == "This contract lost":
                win = False

            self.page.wait_for_timeout(7000)
            # Click #close_confirmation_container
            self.page.locator("#close_confirmation_container").click()

            martingale, stop_est = check_stop(self, start_balance, stake)
            window['_STOP_EST_'].update(stop_est)

            if not martingale:
                self.loop = False
                break

            if win:
                stake = self.init_stake
            else:
                stake = round(stake+martingale, 2)


    def pause(self):
        self.loop = False


    def stop(self):
        self.loop = False


    def exit(self):
        self.browser.close()
        self.playwright.stop()
        return
