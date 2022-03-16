import asyncio
import multiprocessing as mp
import PySimpleGUI as sg


def prog_meter(gui_queue, session, window, values, loop):
    proc = mp.Process(target=_prog_meter, args=(gui_queue, session, window, values, loop))
    proc.start()

    return proc

def _prog_meter(gui_queue, session, window, values, loop):
    '''
    Runs the smarttrader session with Volatility 100
    in the Match/Differ settings
    '''

    #sg.popup_animated(
    #        sg.DEFAULT_BASE64_LOADING_GIF,
    #        'Loading',
    #        text_color='black',
    #        transparent_color='blue', background_color='blue', time_between_frames=100
    #    )

    asyncio.set_event_loop(loop)
    #currently if this loop is rerun playwright compains it's already running
    #if it doesn't run it also complains no running loop
    #loop.run_forever()

    print(gui_queue)

    #session.play(window, values)

    if not values['_SK_'] or not values['_MG_'] or not values['_LDP_']:
        window['_MESSAGE_'].update('Please provide LDP, Stake and initial Martingale')
        return

    session.mtng = values['_MG_']
    session.stop_loss = values['_SL_']
    session.stop_profit = values['_SP_']
    session.ldp = int(values['_LDP_'])
    session.init_stake = session.stake = float(values['_SK_'])

    start_balance = session.page.locator("#header__acc-balance").inner_text().split()[0]
    #window['_START_BAL_'].update(start_balance)
    #window['_STOP_EST_'].update('0.00')

    session.loop = True
    while session.loop:
        session.page.goto(
            f"https://smarttrader.deriv.com/en/trading.html?currency=USD&market=synthetic_index&underlying=R_100&formname=matchdiff&date_start=now&duration_amount=1&duration_units=t&amount={session.stake}&amount_type=stake&expiry_type=duration&prediction={session.ldp}"
        )
        session.page.wait_for_timeout(13000)

        # Click #purchase_button_top
        session.page.locator("#purchase_button_top").click()

        session.page.wait_for_timeout(5000)
        # Click text=This contract lost
        result_str = session.page.locator("#contract_purchase_heading").inner_text()

        win = False
        if result_str == "This contract won":
            win = True
        elif result_str == "This contract lost":
            win = False

        try:
            message = gui_queue.get_nowait()    # see if something has been posted to Queue
        except Exception as e:                     # get_nowait() will get exception when Queue is empty
            message = None                      # nothing in queue so do nothing
        if message:
            print(f'Got a queue message {message}!!!')
            break




        session.page.wait_for_timeout(7000)
        # Click #close_confirmation_container
        session.page.locator("#close_confirmation_container").click()

        martingale, stop_est = check_stop(session, start_balance, session.stake)
        balance = session.page.locator("#header__acc-balance").inner_text().split()[0]
        #window['_CURRENT_BAL_'].update(balance)
        #window['_STOP_EST_'].update(round(stop_est, 2))

        if not martingale: #martingale is float eg 0.80239999999999 or None
            session.loop = False
            break

        if win:
            session.stake = session.init_stake
        else:
            session.stake = round(float(session.stake)+martingale, 2)



def _long_func_thread(window, end_key, original_func):
    """
    Used to run long operations on the user's behalf. Called by the window object

    :param window:        The window that will get the event
    :type window:         (Window)
    :param end_key:       The event that will be sent when function returns
    :type end_key:        (Any)
    :param original_func: The user's function that is called. Can be a function with no arguments or a lambda experession
    :type original_func:  (Any)
    """

    return_value = original_func()
    window.write_event_value(end_key, return_value)


def perform_long_operation(window, func, end_key):
    """
    This function is taken from sg library internals
    Call your function that will take a long time to execute.  When it's complete, send an event
    specified by the end_key.

    NOTE: This uses Threads
    Threading doesn't work as greenlets can't switch to another Thread
    In the future this can be replaced with greenlets

    :param func:    A lambda or a function name with no parms
    :type func:     Any
    :param end_key: The key that will be generated when the function returns
    :type end_key:  (Any)
    :return:        The id of the thread
    :rtype:         threading.Thread
    """

    thread = threading.Thread(target=_long_func_thread, args=(window, end_key, func), daemon=True)
    thread.start()
    return thread
