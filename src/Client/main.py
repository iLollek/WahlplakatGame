import os
import sys
import logging
import signal


from NetworkClient import NetworkClient

from PopupViews import *

from GUI import MainGUI

NetClient = NetworkClient.get_instance()

def closing_protocol():
    """Closes WahlplakatGame and executes some last saving lines of Code."""
    logging.info(f'Closing WahlplakatGame')
    os.kill(os.getpid(), signal.SIGTERM) # This is the last line that gets executed.

if getattr(sys, 'frozen', False):
    print(f'Running in Productive (PROD) Environment (.exe)')
    program_directory = os.path.dirname(os.path.abspath(sys.executable))
    ENV = "PROD"
    if os.path.exists(f'{os.getenv("APPDATA")}\\WahlplakatGame') == False:
        os.makedirs(f'{os.getenv("APPDATA")}\\WahlplakatGame')
    logging.basicConfig(filename=f'{os.getenv("APPDATA")}\\WahlplakatGame\\app.log', filemode='a', format='%(name)s - %(levelname)s - %(funcName)20s() - %(message)s', level=logging.DEBUG, force=True)
    try:
        import pyi_splash
    except Exception as e:
        logging.error(f'Unable to show Splash Screen: {e}')
        closing_protocol()
else:
    print(f'Running in Development (DEV) Environment (.py)')
    program_directory = os.path.dirname(os.path.abspath(__file__))
    ENV = "DEV"
    logging.basicConfig(stream=sys.stdout, format='%(name)s - %(levelname)s - %(funcName)20s() - %(message)s', level=logging.DEBUG, force=True)
os.chdir(program_directory)


if __name__ == "__main__":
    logging.info(f'Started WahlplakatGame (Online)')
    try:
        if NetClient.connect():
            logging.info(f'Verbindung zum Server per NetClient erfolgreich hergestellt!')
        else:
            show_error_box(f'Kritischer Fehler', f'Es konnte keine Verbindung zum WahlplakatGame-Server hergestellt werden. Das Spiel kann nicht gestartet werden. :(')
            closing_protocol()
    except Exception as e:
        show_error_box(f'Kritischer Fehler', f'Es konnte keine Verbindung zum WahlplakatGame-Server hergestellt werden. Das Spiel kann nicht gestartet werden. :(')
        closing_protocol()

    gui = MainGUI()
    gui.mainloop()

