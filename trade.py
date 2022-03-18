import asyncio
import secrets
import PySimpleGUI as sg
from session import TradeSession



#Use it in different coros in the async loop
window = None
trade_session = TradeSession()
print(trade_session.loop)


def btn(name, key=secrets.token_urlsafe()):
    '''
    # a PySimpleGUI "User Defined Element" (see PySimpleGUI docs)
    '''
    return sg.Button(name, key=key, size=(8, 1), pad=(2, 2))



async def background():
    '''
    Run all blocking tasks here
    '''

    await trade_session.setup(window)
    while True:
        event, values = window.read()

        if event == '_LOGIN_':
            if values['_EMAIL_'] and values['_PWORD_']:
                await trade_session.login(values['_EMAIL_'], values['_PWORD_'])
            else:
                window['_MESSAGE_'].update(
                        'Please provide Email and Password'
                    )

        if event == '_BUTTON_PLAY_':
            await trade_session.play(
                    window, values
                )

        print('background task run')
        await asyncio.sleep(0)


async def ui():
    '''
    Run all non-blocking, main GUI tasks here

    '''
    #list_player = inst.media_list_player_new()
    #media_list = inst.media_list_new([])
    #list_player.set_media_list(media_list)
    #player = list_player.get_media_player()

    while True:  # PysimpleGUI Event Loop
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Exit':
            await trade_session.exit()
            break

        if event == '_BUTTON_PAUSE_':
            trade_session.pause()

        if event == '_BUTTON_STOP_':
            trade_session.stop()

        await asyncio.sleep(0)
    window.close()



async def main():
    try:
        #can be asyncio.wait([ui(), bg()] without return value
        res = await asyncio.gather(
                ui(), background()
            )
    except Exception as e:
        raise e
    print(res)


if __name__ == '__main__':
    sg.theme('BluePurple')

    layout = [
        [sg.Text(size=(15,1), key='_MESSAGE_')],

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

        [btn('Play ▶️', '_BUTTON_PLAY_'), btn('Pause ⏸️', '_BUTTON_PAUSE_'), btn('Stop ⏹️', '_BUTTON_STOP_')],

    ]

    window = sg.Window(
                'Deriv SmartTrader Bot',
                layout,
                keep_on_top=True,
                element_justification='center',
                finalize=True, resizable=True
            )
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
