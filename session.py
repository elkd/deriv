#from playwright.sync_api import Playwright, sync_playwright
import os
import asyncio
from playwright.async_api import async_playwright
from prob import check_stop


class TradeSession:
    def __init__(self):
        self.stop_loss = 2
        self.stop_profit = 2
        self.mtng = 0.01
        self.ldp = 0
        self.stake = self.init_stake = 0.35

        self.loop = self.paused = False
        self.playwright = self.browser = None
        self.context = self.page = None


    async def setup(self, window):
        '''
        This was supposed to go to init method
        but a quick way to avoid awaiting on the initializer
        '''

        window['_MG_'].update(self.mtng)
        window['_SL_'].update(self.stop_loss)
        window['_SP_'].update(self.stop_profit)
        window['_SK_'].update(self.init_stake)

        #self.ldp is always 0 from the initialization of the trade session obj
        window['_LDP_'].update(self.ldp)


        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)

        state = "state.json"

        await asyncio.sleep(0)
        if os.path.isfile(state):
            # Create a new context with the saved storage state.
            self.context = await self.browser.new_context(storage_state=state)
            window['_MESSAGE_'].update('Logged in already!')
            self.page = await self.context.new_page()
            await self.page.goto("https://smarttrader.deriv.com/")
        else:
            window['_MESSAGE_'].update('Please Login First!')
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

        await self.page.goto("https://smarttrader.deriv.com/")


    async def login(self, email, psword):
        '''
        Login if not logged in and then store the context into state.json

        '''
        #Best way to go about this is to check if state.json exists in path
        #if yes then return here, and notify the user via message key
        if os.path.isfile(state):
            window['_MESSAGE_'].update('Logged in already!')
            return

        # Click text=Log in
        try:
            lg_btn = self.page.locator("#btn__login") or self.page.locator("text=Log in")
            await lg_btn.click()
            # Click [placeholder="example\@email\.com"]
            email_input = self.page.locator('#txtEmail') or self.page.locator("[placeholder=\"example\\@email\\.com\"]")
            await email_input.fill(email)

            await asyncio.sleep(3)

            psword_input = self.page.locator('#txtPass') or self.page.locator("input[name=\"password\"]")

            # Fill input[name="password"]
            await psword_input.fill(psword)

        except Exception as e:
            print(e)
            window['_MESSAGE_'].update('Playwright Cannot Login!')

        await asyncio.sleep(7)

        await asyncio.sleep(3)
        # Click button:has-text("Log in")
        # with page.expect_navigation(url="https://smarttrader.deriv.com/en/trading.html"):
        async with self.page.expect_navigation():
            submit_btn = self.page.locator('button.button.secondary') or self.page.locator('input[name="login"]')
            await submit_btn.click()
            #page.locator("button:has-text(\"Log in\")").click()

        await asyncio.sleep(3)
        # Save storage state into the file.
        storage = await self.context.storage_state(path="state.json")


    async def play(self, window, values):
        '''
        Runs the smarttrader session with Volatility 100
        in the Match/Differ settings
        '''
        if not values['_SK_'] or not values['_MG_'] or not values['_LDP_']:
            window['_MESSAGE_'].update('Please provide LDP, Stake and initial Martingale')
            return

        if self.paused:
            self.paused = False
        else:
            #New Play session, take stake value from the user input
            self.stake = self.init_stake = float(values['_SK_'])

        self.mtng = values['_MG_']
        self.stop_loss = values['_SL_']
        self.stop_profit = values['_SP_']
        ldp = int(values['_LDP_'])

        sblnc = await self.page.locator("#header__acc-balance").inner_text()
        start_balance = sblnc.split()[0]
        #window['_START_BAL_'].update(start_balance)
        #window['_STOP_EST_'].update('0.00')

        self.loop = True
        while self.loop:
            window['_PLAY_STATUS_'].update('PLAYING...')
            await self.page.goto(
                f"https://smarttrader.deriv.com/en/trading.html?currency=USD&market=synthetic_index&underlying=R_100&formname=matchdiff&date_start=now&duration_amount=1&duration_units=t&amount={self.stake}&amount_type=stake&expiry_type=duration&prediction={ldp}"
            )

            await asyncio.sleep(5)
            #self.page.wait_for_timeout(13000)

            # Click #purchase_button_top
            await self.page.locator("#purchase_button_top").click()

            # Click text=This contract lost
            await self.page.locator("#contract_purchase_heading").wait_for()

            result_str = await self.page.locator("#contract_purchase_heading").inner_text()

            win = False
            if result_str == "This contract won":
                win = True
            elif result_str == "This contract lost":
                win = False

            await asyncio.sleep(4)
            await self.page.locator("#close_confirmation_container").wait_for()

            # Click #close_confirmation_container
            await self.page.locator("#close_confirmation_container").click()

            martingale, stop_est = await check_stop(self, start_balance, self.stake)
            balance = await self.page.locator("#header__acc-balance").inner_text()
            balance = balance.split()[0]

            #window['_CURRENT_BAL_'].update(balance)
            #window['_STOP_EST_'].update(round(stop_est, 2))

            if not martingale: #martingale is float eg 0.80239999999999 or None
                window['_PLAY_STATUS_'].update('AUTO STOPPED!')
                self.loop = False
                break

            if win:
                self.stake = self.init_stake
            else:
                self.stake = round(float(self.stake)+martingale, 2)

            await asyncio.sleep(2)


    def pause(self, window):
        '''
        Pause the play loop
        '''

        window['_PLAY_STATUS_'].update('PAUSED...')

        self.loop = False
        self.paused = True


    def stop(self, window):
        '''
        Clear the current Play session values,
        restore the initial session values and break the play loop
        '''

        self.loop = False
        window['_PLAY_STATUS_'].update('STOPPED!')

        self.mtng = 0.01
        self.stake = self.init_stake = 0.35
        self.stop_loss = 2
        self.stop_profit = 2

        window['_MG_'].update(self.mtng)
        window['_SL_'].update(self.stop_loss)
        window['_SP_'].update(self.stop_profit)
        window['_SK_'].update(self.init_stake)

        #self.ldp is always 0 from the initialization of the trade session obj
        window['_LDP_'].update(self.ldp)



    async def exit(self):
        '''
        Executed when the user closes (X)
        the GUI application window
        '''

        if self.browser and self.playwright:
            await self.browser.close()
            await self.playwright.stop()
