from DatabaseService import DatabaseService
from NetworkService import NetworkService
import GameServer  # ← Modul importieren, nicht die Variable
import threading

env = DatabaseService.get_sillyorm_environment(use_postgres=False)

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