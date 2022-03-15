def check_stop(session, start_balance, stake):
    ''' Compute new stake value
    #Martingale should round off to 2 Decimal points {Formulae= (Stake*Martingale) + Stake
	#Stop Loss= When total losses of stakes add up to the value or more
	#Stop Profit= When profit reaches this value or more (using the account balance before start)
    '''

    stake = float(stake)

    cur_balance = session.page.locator(
            "#header__acc-balance"
        ).inner_text().split()[0].replace(',','')

    stop_est = float(cur_balance) - float(start_balance.replace(',',''))

    if stop_est > float(session.stop_profit) or abs(stop_est) > float(session.stop_loss):
        return None, stop_est

    return (stake*float(session.mtng)) + stake, stop_est
