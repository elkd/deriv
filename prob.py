import asyncio


async def check_stop(session, start_balance, stake):
    '''
    Check wether to continue playing or not
    The rule for this function is that it shouldn't be run often
    Only when the Balance is approaching the stop loss/profit,
    Then this function should be called more often
    '''

    bl = await session.page.locator("#header__acc-balance").inner_text()
    if bl:
        cur_balance = float(bl.split()[0].replace(',',''))

        stop_est = cur_balance - session.start_balance

        if stop_est > float(session.stop_profit) or abs(stop_est) > float(session.stop_loss):
            session.loop = False
            return 'STOP'
