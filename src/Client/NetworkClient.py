import xmlrpc.client
from typing import Dict, List, Optional
import socket


class NetworkClient:
    """
    RPC Client für das WahlplakatGame.
    Kommuniziert mit dem NetworkService Server.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Initialisiert den NetworkClient.
        
        Args:
            host: Server hostname oder IP
            port: Server port
        """
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.proxy = None
        self.session_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.nickname: Optional[str] = None
        
    def connect(self) -> bool:
        """
        Verbindet mit dem Server.
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            self.proxy = xmlrpc.client.ServerProxy(self.server_url, allow_none=True)
            # Test connection
            self.proxy.get_server_info()
            return True
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
                print(f"✅ {response['message']}")
                print(f"👤 Angemeldet als: {self.nickname} (Punkte: {response.get('points', 0)})")
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
            
            return response
        except Exception as e:
            print(f"❌ Fehler bei Token-Validierung: {e}")
            return {"valid": False, "error": str(e)}
    
    # ==================== ROOM MANAGEMENT ====================
    
    def create_room(self) -> Dict:
        """
        Erstellt einen neuen Raum.
        
        Returns:
            Response dictionary mit success, message, room_code
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.create_room(self.session_token)
            
            if response["success"]:
                room_code = response.get("room_code")
                print(f"✅ {response['message']}")
                print(f"🎮 Raum-Code: {room_code}")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Erstellen des Raums: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def join_room(self, room_code: str) -> Dict:
        """
        Tritt einem Raum bei.
        
        Args:
            room_code: 4-stelliger Raum-Code
            
        Returns:
            Response dictionary mit success, message, players
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.join_room(self.session_token, room_code)
            
            if response["success"]:
                print(f"✅ {response['message']}")
                print(f"🎮 Raum-Code: {response.get('room_code')}")
                players = response.get("players", [])
                print(f"👥 Spieler im Raum ({len(players)}):")
                for player in players:
                    print(f"   - {player['nickname']} (Punkte: {player['points']})")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Beitreten des Raums: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def leave_room(self) -> Dict:
        """
        Verlässt den aktuellen Raum.
        
        Returns:
            Response dictionary mit success, message
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.leave_room(self.session_token)
            
            if response["success"]:
                print(f"✅ {response['message']}")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Verlassen des Raums: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_room_players(self) -> Dict:
        """
        Gibt die Liste der Spieler im aktuellen Raum zurück.
        
        Returns:
            Response dictionary mit success, players, room_code
        """
        if not self._ensure_connected() or not self._ensure_authenticated():
            return {"success": False, "message": "Nicht angemeldet"}
        
        try:
            response = self.proxy.get_room_players(self.session_token)
            
            if response["success"]:
                room_code = response.get("room_code")
                players = response.get("players", [])
                print(f"🎮 Raum: {room_code}")
                print(f"👥 Spieler im Raum ({len(players)}):")
                for player in players:
                    print(f"   - {player['nickname']} (Punkte: {player['points']})")
            else:
                print(f"❌ {response['message']}")
            
            return response
        except Exception as e:
            error_msg = f"Fehler beim Abrufen der Spielerliste: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
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
    
    # ==================== CONVENIENCE METHODS ====================
    
    def quick_start(self, nickname: str, password: str, create_new_room: bool = False, 
                   room_code: Optional[str] = None) -> bool:
        """
        Schnellstart: Verbindet, meldet an und tritt optional einem Raum bei.
        
        Args:
            nickname: Benutzername
            password: Passwort
            create_new_room: Erstellt einen neuen Raum wenn True
            room_code: Raum-Code zum Beitreten (ignoriert wenn create_new_room=True)
            
        Returns:
            True wenn erfolgreich, False sonst
        """
        # Connect
        if not self.connect():
            return False
        
        # Login
        login_response = self.login(nickname, password)
        if not login_response.get("success"):
            return False
        
        # Room handling
        if create_new_room:
            create_response = self.create_room()
            return create_response.get("success", False)
        elif room_code:
            join_response = self.join_room(room_code)
            return join_response.get("success", False)
        
        return True
    
    def is_connected(self) -> bool:
        """Prüft ob eine Verbindung zum Server besteht"""
        return self.proxy is not None
    
    def is_authenticated(self) -> bool:
        """Prüft ob der Benutzer authentifiziert ist"""
        return self.session_token is not None


# ==================== EXAMPLE USAGE ====================

def example_usage():
    """Beispiel für die Verwendung des NetworkClient"""
    
    # Create client
    client = NetworkClient(host="localhost", port=8000)
    
    # Connect to server
    print("Verbinde mit Server...")
    if not client.connect():
        return
    
    # Get server info
    client.get_server_info()
    
    # Register new account
    print("\n--- Registrierung ---")
    client.register_account("TestSpieler", "password123")
    
    # Login
    print("\n--- Login ---")
    client.login("TestSpieler", "password123")
    
    # Get user stats
    print("\n--- Benutzerstatistiken ---")
    client.get_user_stats()
    
    # Get leaderboard
    print("\n--- Bestenliste ---")
    client.get_leaderboard(limit=5)
    
    # Create room
    print("\n--- Raum erstellen ---")
    room_response = client.create_room()
    
    # Get room players
    if room_response.get("success"):
        print("\n--- Spielerliste ---")
        client.get_room_players()
    
    # Send message
    print("\n--- Nachricht senden ---")
    client.send_message("Hallo zusammen!")
    
    # Leave room
    print("\n--- Raum verlassen ---")
    client.leave_room()
    
    # Logout
    print("\n--- Logout ---")
    client.logout()
    
    # Disconnect
    client.disconnect()
    print("\n✅ Beispiel abgeschlossen!")


if __name__ == "__main__":
    example_usage()