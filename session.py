#from playwright.sync_api import Playwright, sync_playwright
import os
import asyncio
import traceback
from playwright.async_api import async_playwright
from playwright._impl._api_types import TimeoutError as PWTimeoutError
from prob import check_stop


class TradeSession:
    def __init__(self):
        self.stop_loss = 2
        self.stop_profit = 2
        self.mtng = self.start_balance = 0.1

        #self.ldp must always be an integer
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
        else:
            window['_MESSAGE_'].update('Please Login First!')
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

        try:
            await self.page.goto("https://smarttrader.deriv.com/")
        except PWTimeoutError as e:
            #traceback.format_exc()
            print('The page is taking long to load please wait')
            await asyncio.sleep(10)


    async def login(self, email, psword, window):
        '''
        Login if not logged in and then store the context into state.json

        '''
        #Best way to go about this is to check if state.json exists in path
        #if yes then return here, and notify the user via message key
        if os.path.isfile("state.json"):
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

        window['_MESSAGE_'].update('Logged in already!')
        await asyncio.sleep(3)
        # Save storage state into the file.
        storage = await self.context.storage_state(path="state.json")


    async def tight_play(self, spot_balance_span, stake_input, purchase_handle):
        '''
        Should run so fast, as fast as possible
        Noticeable compromises is the use of is for comparison of small ints
        Can also pull in uvloop for production operation

        #Wait for the price to change
        #Instead of sleeping, can more accurately register a MutationObserver
        #Also instead of returning in JS func, use a promise and resolve
        #See https://github.com/microsoft/playwright/issues/4051

        await self.page.evaluate("""() => {
              new window.MutationObserver((mutations) => {
                  if (mutation.addedNodes.length) {
                    return;
                  }
              }).observe(document.getElementById('spot'), { childList: true });
        }""")
        '''

        #The initial bid_ldp will be false in the play check if span.innerText was ''
        bid_ldp = prev_spot = None
        self.loop = True

        while self.loop:
            bid_spot = await spot_balance_span.inner_text()
            if bid_spot:
                while prev_spot == bid_spot:
                    bid_spot = await spot_balance_span.inner_text()

                bid_ldp = int(bid_spot[-1])

            if bid_ldp is self.ldp: #Play Check
                #Once LDP is correct, purchase immediately,
                #Deriv will schedule for the next price spot
                await self.page.locator("#purchase_button_top").click()

                #Sleep will facilitate Waiting for the price to change
                #Then we can move on to check if we won or fail
                await asyncio.sleep(1.75)

                next_price = await spot_balance_span.inner_text()
                #If the price spot didn't change yet
                #try again to read the next_price
                while next_price == bid_spot:
                    next_price = await spot_balance_span.inner_text()
                prev_spot = next_price

                if int(next_price[-1]) is bid_ldp:
                    self.stake = self.init_stake
                else:
                    self.stake = round(self.stake * self.mtng + self.stake, 2)

                await asyncio.sleep(1.75)
                await stake_input.fill(str(self.stake))

                pbtn_visible = await purchase_handle.is_visible()
                if not pbtn_visible:
                    await self.page.locator("#close_confirmation_container").click()

            else:
                #Wait for the tick spot price to change first
                #Before moving to the next loop round
                prev_spot = bid_spot
                await asyncio.sleep(1.77)

            await asyncio.sleep(0)


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

        self.mtng = float(values['_MG_'])
        self.stop_loss = float(values['_SL_'])
        self.stop_profit = float(values['_SP_'])
        self.ldp = int(values['_LDP_'])

        window['_PLAY_STATUS_'].update('PLAYING...')
        spot_balance_span = self.page.locator("#spot")
        stake_input = self.page.locator("#amount")

        #The use of handle is discouraged. But useful to check if element is_visible()

        purchase_handle = await self.page.wait_for_selector('#purchase_button_top')

        sblnc = await self.page.locator("#header__acc-balance").inner_text()
        if sblnc:
            self.start_balance = float(sblnc.split()[0].replace(',',''))
        else:
            print('Sorry the Start Balance was never retrieved!')
            print('PLEASE STOP THE PLAY MANUALLY!')

        try:
            await self.page.goto(
                f"https://smarttrader.deriv.com/en/trading.html?currency=USD&market=synthetic_index&underlying=R_100&formname=matchdiff&date_start=now&duration_amount=1&duration_units=t&amount={self.stake}&amount_type=stake&expiry_type=duration&prediction={self.ldp}"
            )
        except PWTimeoutError as e:
            #traceback.format_exc()
            print('The page is taking long to load please wait')
            await asyncio.sleep(8)

        await asyncio.sleep(4)
        await self.tight_play(spot_balance_span, stake_input, purchase_handle)


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

        self.mtng = 0.1
        self.stake = self.init_stake = 0.35
        self.stop_loss = 2
        self.stop_profit = 2

        window['_MG_'].update(self.mtng)
        window['_SL_'].update(self.stop_loss)
        window['_SP_'].update(self.stop_profit)
        window['_SK_'].update(self.init_stake)

        window['_LDP_'].update(self.ldp)



    async def exit(self):
        '''
        Executed when the user closes (X)
        the GUI application window
        '''

        if self.browser and self.playwright:
            await self.browser.close()
            await self.playwright.stop()
