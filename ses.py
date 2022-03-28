#Fixing the session file:
#The ticking monitor
from time import sleep
from playwright.sync_api import sync_playwright

if __name__ == '__main__'
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)

    state = "state.json"
    context =  browser.new_context(storage_state=state)
    page =  context.new_page()

    try:
        page.goto(
            "https://smarttrader.deriv.com/en/trading.html?currency=USD&market=synthetic_index&underlying=R_100&formname=matchdiff&date_start=now&duration_amount=1&duration_units=t&amount=0.35&amount_type=stake&expiry_type=duration&prediction=8"
        )

    except PWTimeoutError as e:
        #traceback.format_exc()
        print('The page is taking long to load please wait')
        sleep(10)

    sleep(5)
    spot_balance_span = page.locator("#spot")
    stake_input = page.locator("#amount")

    #The use of handle is discouraged. But useful to check if element is_visible()
    purchase_handle = page.wait_for_selector('#purchase_button_top')


    while True:
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
            await asyncio.sleep(0.8)

            next_price = await spot_balance_span.inner_text()
            #If the price spot didn't change yet
            #try again to read the next_price
            while next_price == bid_spot:
                next_price = await spot_balance_span.inner_text()

            bl = await self.page.locator("#header__acc-balance").inner_text()
            if bl:
                cur_balance = float(bl.split()[0].replace(',',''))

                stop_est = cur_balance - self.start_balance

                if stop_est > float(self.stop_profit) or abs(stop_est) > float(self.stop_loss):
                    self.loop = False
                    return 'AS'

            print(bid_spot, next_price, next_price[-1])

            if int(next_price[-1]) is bid_ldp:
                print('--WON--')
                self.stake = self.init_stake
            else:
                print('LOST!!!')
                self.stake = round(self.stake * self.mtng + self.stake, 2)

            print(f'The stake is updated to: {self.stake}')
            await asyncio.sleep(0.8)
            await stake_input.fill(str(self.stake))

            pbtn_visible = await purchase_handle.is_visible()
            if not pbtn_visible:
                try:
                    await self.page.locator("#close_confirmation_container").click()
                except PWTimeoutError as e:
                    print('Purchase button is disabled by Deriv, waiting for activation to play...')
                    await asyncio.sleep(6)
                    return await self.tight_play(spot_balance_span, stake_input, purchase_handle)

            prev_spot = next_price
        else:
            #Wait for the tick spot price to change first
            #Before moving to the next loop round
            prev_spot = bid_spot
            await asyncio.sleep(0.8)

        #prev_spot = bid_spot
        await asyncio.sleep(0)

