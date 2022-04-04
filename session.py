import os
import asyncio
import traceback
import logging
from time import sleep
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
        self.purchase_handle = self.close_btn_handle = None
        self.playwright = self.browser = self.context = self.page = None


    async def setup(self, window):
        '''
        This was supposed to go to init method
        but a quick way to avoid a return on the init
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
            self.page = await self.context.new_page()
        else:
            window['_MESSAGE_'].update('Please Login First!')
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

        try:
            await self.page.goto("https://smarttrader.deriv.com/")
        except PWTimeoutError as e:
            logging.info('The page is taking long to load please wait')
            await asyncio.sleep(10)


    async def login(self, email, psword, window):
        '''
        Login if not logged in and then store the context into state.json

        '''
        #Best way to go about this is to check if state.json exists in path
        #if yes then return here, and notify the user via message key

        #if os.path.isfile("state.json"): #This doesn't guarantee logged in
            #window['_MESSAGE_'].update('Logged in already!')
            #return

        # Click text=Log in
        try:
            lg_btn = self.page.locator("#btn__login") or self.page.locator("text=Log in")
            await lg_btn.click()
            # Click [placeholder="example\@email\.com"]
            email_input = self.page.locator('#txtEmail') or self.page.locator(
                        "[placeholder=\"example\\@email\\.com\"]"
                    )
            await email_input.fill(email)

            await asyncio.sleep(3)

            psword_input = self.page.locator('#txtPass') or self.page.locator(
                        "input[name=\"password\"]"
                    )

            # Fill input[name="password"]
            await psword_input.fill(psword)

        except Exception as e:
            logging.info(e)
            window['_MESSAGE_'].update('Playwright Cannot Login!')

        await asyncio.sleep(7)

        await asyncio.sleep(3)
        # Click button:has-text("Log in")
        # with page.expect_navigation(url="https://smarttrader.deriv.com/en/trading.html"):
        async with self.page.expect_navigation():
            submit_btn = self.page.locator(
                    'button.button.secondary'
                ) or self.page.locator('input[name="login"]')
            await submit_btn.click()
            #page.locator("button:has-text(\"Log in\")").click()

        window['_MESSAGE_'].update('Logged in already!')
        await asyncio.sleep(3)
        # Save storage state into the file.
        storage = await self.context.storage_state(path="state.json")


    async def tight_play(self, spot_balance_span, stake_input):
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

        bid_spot = prev_spot = ''
        self.loop = True

        xbtn_visible = await self.close_btn_handle.is_visible()
        if xbtn_visible:
            try:
                await self.close_btn_handle.click(timeout=3000)
            except PWTimeoutError:
                pass

        while self.loop:
            bid_spot = await spot_balance_span.inner_text()

            while prev_spot == bid_spot:
                bid_spot = await spot_balance_span.inner_text()

            if int(bid_spot[-1]) is self.ldp: #Play Check
                #Once LDP is correct, purchase immediately,
                #Deriv will schedule for the next price spot
                try:
                    await self.page.locator("#purchase_button_top").click(timeout=100)

                    sleep(0.6)
                    bid_spot_purchase = await spot_balance_span.inner_text()

                    next_price = await spot_balance_span.inner_text()
                    #If the price spot didn't change yet
                    #try again to read the next_price
                    while next_price == bid_spot_purchase:
                        next_price = await spot_balance_span.inner_text()

                    logging.info(f"**PRICES: {bid_spot}, {bid_spot_purchase}, {next_price}, **")

                    if bid_spot == bid_spot_purchase:
                        if int(next_price[-1]) is self.ldp:
                            logging.info('--FAST WON--')
                            self.stake = self.init_stake
                        else:
                            logging.info('FAST LOST!!!')
                            self.stake = round(self.stake * self.mtng + self.stake, 2)
                    else:
                        #This sleep is to wait for the results,
                        #don't give control back to the event loop
                        sleep(0.5)
                        result_str = await self.page.locator(
                                "#contract_purchase_heading"
                            ).inner_text()

                        while result_str == 'Contract Confirmation':
                            result_str = await self.page.locator(
                                    "#contract_purchase_heading"
                                ).inner_text()

                        logging.info(result_str)
                        if result_str == "This contract won":
                            logging.info('--WON--')
                            self.stake = self.init_stake
                        elif result_str == "This contract lost":
                            logging.info('LOST!!!')
                            self.stake = round(self.stake * self.mtng + self.stake, 2)
                        else:
                            logging.info('@@The bot could not update stake@@')

                    logging.info(f'The stake is updated to: {self.stake}')
                    await stake_input.fill(str(self.stake))

                    pbtn_visible = await self.purchase_handle.is_visible()
                    if not pbtn_visible:
                        await self.close_btn_handle.click()
                    prev_spot = next_price

                except PWTimeoutError as e:
                    logging.error(e)
                    logging.info('Purchase btn is disabled by Deriv, waiting for activation...')
                    await asyncio.sleep(5)
                    return await self.tight_play(spot_balance_span, stake_input)

            else:
                #Wait for the price tick to move forward
                #Check for stopping profit/loss while waiting for the tick
                bl = await self.page.locator("#header__acc-balance").inner_text()
                cur_balance = float(bl.split()[0].replace(',',''))

                stop_est = cur_balance - self.start_balance
                if stop_est > float(self.stop_profit) or abs(stop_est) > float(self.stop_loss):
                    self.loop = False
                    return 'AS'

                prev_spot = bid_spot


    async def play(self, window, values):
        '''
        Runs the smarttrader session with Volatility 100,
        Match/Differ option and Tick = 1
        '''

        window['_PLAY_STATUS_'].update('PLAYING...')

        if not values['_SK_'] or not values['_MG_'] or not values['_LDP_']:
            window['_MESSAGE_'].update(
                    'Please provide LDP, Stake and initial Martingale'
                )
            return

        if self.paused:
            self.paused = False
            xbtn_visible = await self.close_btn_handle.is_visible()
            if xbtn_visible:
                try:
                    await self.close_btn_handle.click(timeout=2000)
                except PWTimeoutError as e:
                    pass
        else:
            #New Play session, take stake value from the user input
            self.stake = self.init_stake = float(values['_SK_'])

        self.mtng = float(values['_MG_'])
        self.stop_loss = float(values['_SL_'])
        self.stop_profit = float(values['_SP_'])
        self.ldp = int(values['_LDP_'])

        spot_balance_span = self.page.locator("#spot")
        stake_input = self.page.locator("#amount")

        self.purchase_handle = self.page.locator(
                    '#purchase_button_top'
                )
        self.close_btn_handle = self.page.locator(
                    "#close_confirmation_container"
                )

        sblnc = await self.page.locator("#header__acc-balance").inner_text()
        if sblnc:
            self.start_balance = float(sblnc.split()[0].replace(',',''))
        else:
            logging.info('Sorry the Start Balance was never retrieved!')
            logging.info('PLEASE STOP THE PLAY MANUALLY!')

        try:
            await self.page.goto(
                f"https://smarttrader.deriv.com/en/trading.html?currency=USD&market=synthetic_index&underlying=R_100&formname=matchdiff&date_start=now&duration_amount=1&duration_units=t&amount={self.stake}&amount_type=stake&expiry_type=duration&prediction={self.ldp}"
            )
        except PWTimeoutError as e:
            #traceback.format_exc()
            logging.info('The page is taking long to load please wait')
            await asyncio.sleep(8)

        await asyncio.sleep(4)
        status = await self.tight_play(spot_balance_span, stake_input)
        if status == 'AS':
            window['_PLAY_STATUS_'].update('STOPPED!')

        elif status == 'BK':
            window['_PLAY_STATUS_'].update('PURCHASE BLOCKED!')

        xbtn_visible = await self.close_btn_handle.is_visible()
        if xbtn_visible:
            try:
                await self.close_btn_handle.click(timeout=2000)
            except PWTimeoutError as e:
                pass


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
