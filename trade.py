import asyncio
import secrets
import traceback
import logging

import uvloop
import PySimpleGUI as sg
from session import TradeSession


def btn(name, key=secrets.token_urlsafe()):
    '''
    # a PySimpleGUI "User Defined Element" (see PySimpleGUI docs)
    '''
    return sg.Button(name, key=key, size=(8, 1), pad=(2, 2))


async def event_listeners(event, values, window, trade_session):
    '''
    Both bg and ui tasks should be listening on all click events,
    except the play event which must run only on 1 coroutine,
    to avoid race conditions on pause and play scenarios.
    There should be no visible delay to the user on pause, stop clicks
    '''

    if event == sg.WIN_CLOSED or event == 'Exit':
        await trade_session.exit()
        asyncio.get_running_loop().stop()
        return 'BR'

    if event == '_LOGIN_':
        if values['_EMAIL_'] and values['_PWORD_']:
            await trade_session.login(values['_EMAIL_'], values['_PWORD_'], window)
        else:
            window['_MESSAGE_'].update(
                    'Please provide Email and Password'
                )
    if event == '_BUTTON_PAUSE_':
        trade_session.pause(window)

    if event == '_BUTTON_STOP_':
        trade_session.stop(window)



async def bg(window, trade_session):
    '''
    Run all blocking tasks here
    '''

    await trade_session.setup(window)

    while True:
        await asyncio.sleep(0)
        event, values = window.read(timeout=0)

        action = await event_listeners(event, values, window, trade_session)
        if action == 'BR':
            break

        await asyncio.sleep(0)
    window.close()


async def ui(window, trade_session):
    '''
    Run all non-blocking, main GUI tasks here

    '''
    while True:  # PysimpleGUI Event Loop
        await asyncio.sleep(0)
        event, values = window.read(timeout=0)

        if event == '_BUTTON_PLAY_':
            await trade_session.play(
                    window, values
                )

        action = await event_listeners(event, values, window, trade_session)
        if action == 'BR':
            break

        await asyncio.sleep(0)
    window.close()



async def main(window, trade_session):
    '''
    Async Functions Main entry

    '''
    try:
        #can be asyncio.wait([ui(), bg()] without return value
        res = await asyncio.gather(
                ui(window, trade_session), bg(window, trade_session)
            )
    except Exception as e:
        raise e


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    sg.theme('DarkAmber')

    layout = [
        [sg.Text(size=(30,1), key='_MESSAGE_')],

        [sg.Text('Email'), sg.Input(size=(24,1), k='_EMAIL_'),
            sg.Text(size=(7,1)), sg.Text('Password'), sg.Input(size=(24,1), k='_PWORD_')],

        [btn('Login', '_LOGIN_')],

        [sg.Text(size=(15,2))], #This is just for margin top bottom
        #[sg.Column([], pad=(10,  5))],

        #[sg.Text('Start Balance:'), sg.Text('0.00 USD', size=(8,1), key='_START_BAL_'),
        #    sg.Text('Current Balance:'), sg.Text('0.00 USD', size=(12,1), key='_CURRENT_BAL_'),
        #        sg.Text('Current Loss/Profit:'), sg.Text('0.00', size=(12,1), key='_STOP_EST_')],

        [sg.Text('Stop Loss:'), sg.Input(size=(7,1), k='_SL_'),
            sg.Text('Stop Profit:'), sg.Input(size=(7,1), k='_SP_'),
                sg.Text('Stake:'), sg.Input(size=(7,1), k='_SK_'),
                    sg.Text('Martingale:'), sg.Input(size=(7,1), k='_MG_'),
                        sg.Text('LDP:'), sg.Input(size=(7,1), k='_LDP_')],

        [sg.Text(size=(15,2))], #This is just for margin top bottom


        [sg.Text('STATUS: '), sg.Text('NOT PLAYING!', size=(20,1), key='_PLAY_STATUS_')],

        [btn('Play ▶️', '_BUTTON_PLAY_'),
            btn('Pause ⏸️', '_BUTTON_PAUSE_'), btn('Stop ⏹️', '_BUTTON_STOP_')],

    ]

    window = sg.Window(
                'Deriv SmartTrader Bot',
                layout,
                keep_on_top=True,
                element_justification='center',
                finalize=True, resizable=True
            )

    #Use it in different coros in the async loop
    trade_session = TradeSession()

    try:
        uvloop.install()
        asyncio.run(main(window, trade_session))
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.info('The program has been halted!')
