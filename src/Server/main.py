from DatabaseService import DatabaseService
from NetworkService import NetworkService
import GameServer
import threading
import sys
import os
import logging

if getattr(sys, 'frozen', False):
    print(f'Running in Productive (PROD) Environment (.exe)')
    program_directory = os.path.dirname(os.path.abspath(sys.executable))
    ENV = "PROD"
    logging.basicConfig(filename=f'server.log', filemode='a', format='%(name)s - %(levelname)s - %(funcName)20s() - %(message)s', level=logging.DEBUG, force=True)
else:
    print(f'Running in Development (DEV) Environment (.py)')
    program_directory = os.path.dirname(os.path.abspath(__file__))
    ENV = "DEV"
    logging.basicConfig(stream=sys.stdout, format='%(name)s - %(levelname)s - %(funcName)20s() - %(message)s', level=logging.DEBUG, force=True)
os.chdir(program_directory)

if ENV == "PROD":
    DatabaseService.PATH_TO_YOUR_CONNECTION_STRING_FILE = r"connection_string.txt"
    env = DatabaseService.get_sillyorm_environment(use_postgres=False)
else:
    ENV == "DEV"

# Initialisiere GameService
GameServer.init_game_service(env)

# XMLRPC Thread
NetService = NetworkService()
xmlrpc_thread = threading.Thread(target=NetService.start, daemon=True)
xmlrpc_thread.start()

print("✅ XMLRPC Server gestartet auf Port 8000")
print("🚀 Starte GameService auf Port 5000...")

# Starte GameService
GameServer.game_service.start()  # ← Über Modul zugreifen