import os
import sys
import logging
import signal
import atexit


from NetworkClient import NetworkClient

from PopupViews import *

from GUI import MainGUI

NetClient = NetworkClient.get_instance()

def cleanup_on_exit():
    """Cleanup-Funktion die beim Beenden aufgerufen wird"""
    logging.info('Führe Cleanup beim Beenden durch...')
    
    # Import GameClient hier, um zirkuläre Imports zu vermeiden
    try:
        from GameClient import GameClient
        game_client = GameClient.get_instance()
        
        if game_client.is_connected():
            logging.info('Trenne GameClient...')
            game_client.disconnect(by_request=False)  # by_request=False da es ein Crash/Schließen ist
    except Exception as e:
        logging.error(f'Fehler beim Trennen des GameClients: {e}')
    
    # Logout über NetClient
    try:
        if NetClient.is_authenticated():
            logging.info('Melde vom Server ab...')
            NetClient.logout()
    except Exception as e:
        logging.error(f'Fehler beim Logout: {e}')

def closing_protocol():
    """Closes WahlplakatGame and executes some last saving lines of Code."""
    logging.info(f'Closing WahlplakatGame')
    cleanup_on_exit()
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

# Registriere Cleanup-Funktion für verschiedene Exit-Szenarien
atexit.register(cleanup_on_exit)

# Signal Handler für SIGTERM und SIGINT
def signal_handler(signum, frame):
    logging.info(f'Signal {signum} empfangen, führe Cleanup durch...')
    cleanup_on_exit()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    logging.info(f'Started WahlplakatGame (Online)')
    try:
        if NetClient.connect():
            logging.info(f'Verbindung zum Server per NetClient erfolgreich hergestellt!')
        else:
            show_error_box(f'Kritischer Fehler', f'Es konnte keine Verbindung zum WahlplakatGame-Server hergestellt werden. Das Spiel kann nicht gestartet werden. :(')
            closing_protocol()
    except Exception as e:
        show_error_box(f'Kritischer Fehler', f'Es konnte keine Verbindung zum WahlplakatGame-Server hergestellt werden. Das Spiel kann nicht gestartet werden. {e} :(')
        closing_protocol()

    try:
        gui = MainGUI()
        gui.mainloop()
    except KeyboardInterrupt:
        logging.info('KeyboardInterrupt empfangen')
        cleanup_on_exit()
    except Exception as e:
        logging.error(f'Unerwarteter Fehler in main loop: {e}')
        cleanup_on_exit()
        raise
    finally:
        logging.info('Programm wird beendet')
        cleanup_on_exit()