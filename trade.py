import asyncio
import secrets
import traceback
import PySimpleGUI as sg
from session import TradeSession


def btn(name, key=secrets.token_urlsafe()):
    '''
    # a PySimpleGUI "User Defined Element" (see PySimpleGUI docs)
    '''
    return sg.Button(name, key=key, size=(8, 1), pad=(2, 2))



async def bg(window, trade_session):
    '''
    Run all blocking tasks here
    '''

    await trade_session.setup(window)
    while True:
        await asyncio.sleep(0)
        event, values = window.read(timeout=10)

        if event == sg.WIN_CLOSED or event == 'Exit':
            await trade_session.exit()
            asyncio.get_running_loop().stop()
            break

        if event == '_LOGIN_':
            if values['_EMAIL_'] and values['_PWORD_']:
                await trade_session.login(values['_EMAIL_'], values['_PWORD_'], window)
            else:
                window['_MESSAGE_'].update(
                        'Please provide Email and Password'
                    )

        if event == '_BUTTON_PLAY_':
            await trade_session.play(
                    window, values
                )

        await asyncio.sleep(0)


async def ui(window, trade_session):
    '''
    Run all non-blocking, main GUI tasks here

    '''
    while True:  # PysimpleGUI Event Loop
        await asyncio.sleep(0)
        event, values = window.read(timeout=10)

        if event == sg.WIN_CLOSED or event == 'Exit':
            await trade_session.exit()
            asyncio.get_running_loop().stop()
            break

        if event == '_BUTTON_PAUSE_':
            trade_session.pause(window)

        if event == '_BUTTON_STOP_':
            trade_session.stop(window)

        if trade_session.loop:
            bl = await trade_session.page.locator("#header__acc-balance").inner_text()
            if bl:
                cur_balance = float(bl.split()[0].replace(',',''))

                stop_est = cur_balance - trade_session.start_balance

                if stop_est > float(trade_session.stop_profit) or abs(stop_est) > float(trade_session.stop_loss):
                    trade_session.loop = False
                    window['_PLAY_STATUS_'].update('AUTO STOPPED!')

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
    sg.theme('BluePurple')

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
        asyncio.run(main(window, trade_session))
    except Exception as e:
        #print(traceback.format_exc())
        print('The program has been halted!')
