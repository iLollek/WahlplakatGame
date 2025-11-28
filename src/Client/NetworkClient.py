import xmlrpc.client
from typing import Dict, List, Optional
import socket
import threading


class NetworkClient:
    """
    Singleton RPC Client für das WahlplakatGame.
    Kommuniziert mit dem NetworkService Server.
    
    Verwendung:
        # Einmalig verbinden (z.B. in main.py)
        client = NetworkClient.get_instance()
        client.connect()
        
        # Überall im Code verwenden
        client = NetworkClient.get_instance()
        if client.is_connected():
            client.login(...)
    """
    
    _instance = None
    _lock = threading.Lock()  # Für Thread-Sicherheit
    _initialized = False
    
    def __new__(cls):
        """Verhindert direkte Instanziierung"""
        if cls._instance is None:
            cls._instance = super(NetworkClient, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls, host: str = "localhost", port: int = 8000) -> 'NetworkClient':
        """
        Gibt die Singleton-Instanz zurück.
        
        Args:
            host: Server hostname oder IP (nur beim ersten Aufruf relevant)
            port: Server port (nur beim ersten Aufruf relevant)
            
        Returns:
            Die NetworkClient Singleton-Instanz
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._instance._initialize(host, port)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """
        Setzt die Singleton-Instanz zurück.
        Nützlich für Tests oder wenn eine neue Verbindung aufgebaut werden soll.
        """
        with cls._lock:
            if cls._instance:
                try:
                    cls._instance.disconnect()
                except:
                    pass
            cls._instance = None
            cls._initialized = False
    
    def _initialize(self, host: str = "localhost", port: int = 8000):
        """
        Initialisiert den NetworkClient (nur beim ersten Mal).
        
        Args:
            host: Server hostname oder IP
            port: Server port
        """
        if NetworkClient._initialized:
            return
            
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.proxy = None
        self.session_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.nickname: Optional[str] = None
        self.points: int = 0
        NetworkClient._initialized = True
    
    def connect(self) -> bool:
        """
        Verbindet mit dem Server.
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            self.proxy = xmlrpc.client.ServerProxy(self.server_url, allow_none=True)
            # Test connection
            response = self.proxy.get_server_info()
            if response.get("success"):
                print(f"✅ Verbunden mit Server {self.host}:{self.port}")
                return True
            return False
        except Exception as e:
            print(f"❌ Verbindung zum Server fehlgeschlagen: {e}")
            return False
    
    def disconnect(self):
        """Trennt die Verbindung zum Server"""
        if self.session_token:
            self.logout()
        self.proxy = None
    
    def _ensure_connected(self) -> bool:
        """Stellt sicher, dass eine Verbindung besteht"""
        if not self.proxy:
            print("❌ Nicht mit dem Server verbunden. Bitte zuerst connect() aufrufen.")
            return False
        return True
    
    def _ensure_authenticated(self) -> bool:
        """Stellt sicher, dass der Benutzer authentifiziert ist"""
        if not self.session_token:
            print("❌ Nicht angemeldet. Bitte zuerst login() oder register_account() aufrufen.")
            return False
        return True
    
    # ==================== AUTHENTICATION ====================
    
    def register_account(self, nickname: str, password: str) -> Dict:
        """
        Erstellt ein neues Benutzerkonto.
        
        Args:
            nickname: Benutzername (max 18 Zeichen)
            password: Passwort (min 6 Zeichen)
            
        Returns:
            Response dictionary mit success, message, etc.
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Nicht mit Server verbunden"}
        
        try:
            response = self.proxy.register_account(nickname, password)
            if response["success"]:
                print(f"✅ {response['message']}")
            else:
                print(f"❌ {response['message']}")
            return response
        except Exception as e:
            error_msg = f"Fehler bei der Registrierung: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def login(self, nickname: str, password: str) -> Dict:
        """
        Meldet einen Benutzer an.
        
        Args:
            nickname: Benutzername
            password: Passwort
            
        Returns:
            Response dictionary mit success, message, token, etc.
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Nicht mit Server verbunden"}
        
        try:
            # Get local IP address
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "unknown"
            
            response = self.proxy.login(nickname, password, ip_address)
            
            if response["success"]:
                self.session_token = response.get("token")
                self.user_id = response.get("user_id")
                self.nickname = response.get("nickname")
                self.points = response.get("points", 0)
                print(f"✅ {response['message']}")
                print(f"👤 Angemeldet als: {self.nickname} (Punkte: {self.points})")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Login: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def logout(self) -> Dict:
        """
        Meldet den aktuellen Benutzer ab.
        
        Returns:
            Response dictionary mit success, message
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.logout(self.session_token)
            
            if response["success"]:
                print(f"✅ {response['message']}")
                self.session_token = None
                self.user_id = None
                self.nickname = None
                self.points = 0
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Logout: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def validate_token(self) -> Dict:
        """
        Validiert den aktuellen Session-Token.
        
        Returns:
            Response dictionary mit valid, user_id, nickname
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"valid": False}
        
        try:
            response = self.proxy.validate_token(self.session_token)
            
            if response.get("valid"):
                print(f"✅ Token gültig für Benutzer: {response.get('nickname')}")
            else:
                print(f"❌ Token ungültig")
                self.session_token = None
                self.user_id = None
                self.nickname = None
                self.points = 0
            
            return response
        except Exception as e:
            print(f"❌ Fehler bei Token-Validierung: {e}")
            return {"valid": False, "error": str(e)}
    
    def check_username_available(self, nickname: str) -> Dict:
        """Prüft ob ein Benutzername verfügbar ist."""
        response = self.proxy.check_username_available(nickname)
        return response
    
    # ==================== MESSAGING ====================
    
    def send_message(self, message: str) -> Dict:
        """
        Sendet eine Nachricht an alle Spieler im aktuellen Raum.
        
        Args:
            message: Nachrichtentext
            
        Returns:
            Response dictionary mit success, message, timestamp
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.send_message(self.session_token, message)
            
            if response["success"]:
                print(f"✅ Nachricht gesendet: {message}")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Senden der Nachricht: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    # ==================== LEADERBOARD ====================
    
    def get_leaderboard(self, limit: int = 10) -> Dict:
        """
        Gibt die Bestenliste zurück.
        
        Args:
            limit: Anzahl der Top-Spieler (Standard: 10)
            
        Returns:
            Response dictionary mit success, leaderboard
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Nicht mit Server verbunden"}
        
        try:
            response = self.proxy.get_leaderboard(limit)
            
            if response["success"]:
                leaderboard = response.get("leaderboard", [])
                print(f"\n🏆 BESTENLISTE (Top {limit})")
                print("=" * 50)
                for entry in leaderboard:
                    rank = entry["rank"]
                    nickname = entry["nickname"]
                    points = entry["points"]
                    
                    # Medal for top 3
                    medal = ""
                    if rank == 1:
                        medal = "🥇"
                    elif rank == 2:
                        medal = "🥈"
                    elif rank == 3:
                        medal = "🥉"
                    
                    print(f"{medal} {rank:2d}. {nickname:18s} {points:6d} Punkte")
                print("=" * 50 + "\n")
            else:
                print(f"❌ {response.get('message', 'Fehler beim Abrufen der Bestenliste')}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Abrufen der Bestenliste: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_user_stats(self) -> Dict:
        """
        Gibt die Statistiken des aktuellen Benutzers zurück.
        
        Returns:
            Response dictionary mit success, stats
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.get_user_stats(self.session_token)
            
            if response["success"]:
                stats = response.get("stats", {})
                print(f"\n📊 DEINE STATISTIKEN")
                print("=" * 50)
                print(f"Nickname:        {stats.get('nickname')}")
                print(f"Punkte:          {stats.get('points')}")
                print(f"Rang:            #{stats.get('rank', 'N/A')}")
                print(f"Registriert am:  {stats.get('registered_at', 'N/A')}")
                print("=" * 50 + "\n")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Abrufen der Statistiken: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    # ==================== UTILITY ====================
    
    def get_server_info(self) -> Dict:
        """
        Gibt Informationen über den Server zurück.
        
        Returns:
            Response dictionary mit success, info
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Nicht mit Server verbunden"}
        
        try:
            response = self.proxy.get_server_info()
            
            if response["success"]:
                info = response.get("info", {})
                print(f"\n📡 SERVER INFORMATIONEN")
                print("=" * 50)
                print(f"Registrierte Benutzer:  {info.get('total_users', 0)}")
                print(f"Gesamt Räume:           {info.get('total_rooms', 0)}")
                print(f"Offene Räume:           {info.get('open_rooms', 0)}")
                print(f"Wahlsprüche:            {info.get('total_wahlsprueche', 0)}")
                print(f"Aktive Sessions:        {info.get('active_sessions', 0)}")
                print("=" * 50 + "\n")
            else:
                print(f"❌ {response.get('message', 'Fehler beim Abrufen der Server-Informationen')}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Abrufen der Server-Informationen: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    # ==================== STATUS CHECKS ====================
    
    def get_alle_parteien(self, token: str) -> list[str]:
        """
        Holt alle Parteien vom Server die aktuell in der Datenbank gelistet sind
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}

        try:
            response = self.proxy.get_alle_parteien(self.session_token)
            
            if response["success"]:
                return response["parteien"]
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Abrufen der Partien: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}

    def is_connected(self) -> bool:
        """Prüft ob eine Verbindung zum Server besteht"""
        return self.proxy is not None
    
    def is_authenticated(self) -> bool:
        """Prüft ob der Benutzer authentifiziert ist"""
        return self.session_token is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Gibt Informationen über den aktuell angemeldeten Benutzer zurück.
        
        Returns:
            Dictionary mit user_id, nickname, points oder None
        """
        if not self.is_authenticated():
            return None
        
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "points": self.points
        }


# ==================== CONVENIENCE FUNCTIONS ====================

def get_client() -> NetworkClient:
    """
    Convenience-Funktion für schnellen Zugriff auf den Client.
    
    Returns:
        Die NetworkClient Singleton-Instanz
    """
    return NetworkClient.get_instance()


# ==================== EXAMPLE USAGE ====================

def example_usage():
    """Beispiel für die Verwendung des Singleton NetworkClient"""
    
    print("=== BEISPIEL: Singleton NetworkClient ===\n")
    
    # 1. Erste Instanz erstellen und verbinden
    print("1. Client-Instanz holen und verbinden...")
    client = NetworkClient.get_instance(host="localhost", port=8000)
    
    if not client.connect():
        print("Verbindung fehlgeschlagen!")
        return
    
    # 2. Server-Info abrufen
    print("\n2. Server-Informationen abrufen...")
    client.get_server_info()
    
    # 3. Registrierung
    print("\n3. Neuen Account registrieren...")
    client.register_account("TestUser123", "password123")
    
    # 4. Login
    print("\n4. Login...")
    client.login("TestUser123", "password123")
    
    # 5. Zeige, dass die Instanz überall verfügbar ist
    print("\n5. Demonstriere Singleton-Verhalten...")
    
    # Hole Instanz "erneut" (ist die gleiche)
    client2 = NetworkClient.get_instance()
    
    print(f"client == client2: {client is client2}")  # True
    print(f"Angemeldet als: {client2.nickname}")
    print(f"User ID: {client2.user_id}")
    
    # 6. Verwende die Instanz in einer "anderen Funktion"
    print("\n6. Verwende Client in einer anderen Funktion...")
    other_function_example()
    
    # 7. Logout
    print("\n7. Logout...")
    client.logout()
    
    print("\n✅ Beispiel abgeschlossen!")


def other_function_example():
    """
    Beispiel-Funktion die zeigt, dass der Client überall verfügbar ist.
    Simuliert z.B. eine GUI-Klasse die den Client verwendet.
    """
    # Kein Import nötig, Client ist bereits initialisiert
    client = NetworkClient.get_instance()
    
    if client.is_authenticated():
        print(f"   ✓ In other_function_example(): User '{client.nickname}' ist angemeldet")
        print(f"   ✓ Kann direkt Funktionen aufrufen!")
        
        # Beispiel: Leaderboard abrufen
        client.get_leaderboard(limit=3)
    else:
        print("   ✗ Nicht angemeldet")


if __name__ == "__main__":
    example_usage()