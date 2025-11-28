from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import hashlib
import secrets
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from DatabaseService import DatabaseService
import sillyorm


class RequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler for logging"""
    rpc_paths = ('/RPC2',)


class NetworkService:
    """
    RPC Service für das WahlplakatGame.
    Behandelt synchrone Operationen wie Authentication, Room Management, etc.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000, use_postgres: bool = False):
        self.host = host
        self.port = port
        self.use_postgres = use_postgres
        self.env = DatabaseService.get_sillyorm_environment(use_postgres=use_postgres)
        self.server = None
        
        # Active sessions cache (token -> user_id)
        self.active_sessions: Dict[str, int] = {}
        
        # Room state cache (room_code -> list of user_ids)
        self.room_players: Dict[str, List[int]] = {}
        
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _generate_session_token(self) -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)
    
    def _generate_room_code(self) -> str:
        """Generate a unique 4-character room code"""
        while True:
            code = secrets.token_hex(2).upper()  # 4 characters
            if not DatabaseService.get_room_by_code(self.env, code):
                return code
    
    def _validate_session(self, token: str) -> Optional[int]:
        """
        Validate a session token and return user_id if valid.
        Returns None if invalid.
        """
        if token in self.active_sessions:
            return self.active_sessions[token]
        
        # Check database
        user = DatabaseService.get_user_by_session_token(self.env, token)
        if user:
            user_id = user[0].id
            self.active_sessions[token] = user_id
            return user_id
        
        return None
    
    # ==================== AUTHENTICATION ====================
    
    def register_account(self, nickname: str, password: str) -> Dict:
        """
        Erstellt ein neues Benutzerkonto.
        
        Returns:
            {"success": bool, "message": str, "user_id": int (optional)}
        """
        try:
            # Validate input
            if not nickname or len(nickname) > 18:
                return {
                    "success": False,
                    "message": "Nickname muss zwischen 1 und 18 Zeichen lang sein."
                }
            
            if not password or len(password) < 6:
                return {
                    "success": False,
                    "message": "Passwort muss mindestens 6 Zeichen lang sein."
                }
            
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Create user
            success = DatabaseService.create_new_user(self.env, nickname, hashed_password)
            
            if success:
                user = DatabaseService.get_user_by_nickname(self.env, nickname)
                return {
                    "success": True,
                    "message": "Konto erfolgreich erstellt!",
                    "user_id": user[0].id
                }
            else:
                return {
                    "success": False,
                    "message": "Nickname bereits vergeben."
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Erstellen des Kontos: {str(e)}"
            }
    
    def login(self, nickname: str, password: str, ip_address: str = "unknown") -> Dict:
        """
        Meldet einen Benutzer an und gibt einen Session-Token zurück.
        
        Returns:
            {"success": bool, "message": str, "token": str (optional), "user_id": int (optional)}
        """
        try:
            # Get user from database
            user = DatabaseService.get_user_by_nickname(self.env, nickname)
            
            if not user:
                return {
                    "success": False,
                    "message": "Ungültiger Nickname oder Passwort."
                }
            
            user = user[0]
            
            # Verify password
            hashed_password = self._hash_password(password)
            if user.password != hashed_password:
                return {
                    "success": False,
                    "message": "Ungültiger Nickname oder Passwort."
                }
            
            # Generate session token
            token = self._generate_session_token()
            
            # Update user session
            DatabaseService.update_user_session(self.env, user.id, token, ip_address)
            
            # Cache session
            self.active_sessions[token] = user.id
            
            return {
                "success": True,
                "message": "Erfolgreich angemeldet!",
                "token": token,
                "user_id": user.id,
                "nickname": user.nickname,
                "points": user.points,
                "last_login_ip": user.last_login_ip
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Login: {str(e)}"
            }
    
    def logout(self, token: str) -> Dict:
        """
        Meldet einen Benutzer ab und invalidiert den Session-Token.
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session."
                }
            
            # Remove from active sessions
            if token in self.active_sessions:
                del self.active_sessions[token]
            
            # Clear session token in database
            DatabaseService.update_user_session(self.env, user_id, "", "")
            
            return {
                "success": True,
                "message": "Erfolgreich abgemeldet."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Logout: {str(e)}"
            }
    
    def validate_token(self, token: str) -> Dict:
        """
        Validiert einen Session-Token.
        
        Returns:
            {"valid": bool, "user_id": int (optional), "nickname": str (optional)}
        """
        try:
            user_id = self._validate_session(token)
            
            if user_id:
                user = DatabaseService.get_user_by_id(self.env, user_id)
                if user:
                    return {
                        "valid": True,
                        "user_id": user[0].id,
                        "nickname": user[0].nickname,
                        "points": user[0].points
                    }
            
            return {"valid": False}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def check_username_available(self, nickname: str) -> Dict:
        """
        Prüft ob ein Benutzername verfügbar ist.
        
        Args:
            nickname: Zu prüfender Benutzername
            
        Returns:
            {"available": bool, "message": str}
        """
        try:
            # Validate input length
            if not nickname or len(nickname) > 18:
                return {
                    "available": False,
                    "message": "Nickname muss zwischen 1 und 18 Zeichen lang sein."
                }
            
            # Check if user already exists
            existing = DatabaseService.get_user_by_nickname(self.env, nickname)
            
            if existing:
                return {
                    "available": False,
                    "message": "Nickname bereits vergeben."
                }
            else:
                return {
                    "available": True,
                    "message": "Nickname verfügbar!"
                }
                
        except Exception as e:
            return {
                "available": False,
                "message": f"Fehler beim Prüfen des Nicknames: {str(e)}"
            }
    
    # ==================== ROOM MANAGEMENT ====================
    
    def create_room(self, token: str) -> Dict:
        """
        Erstellt einen neuen Raum und fügt den Benutzer hinzu.
        
        Returns:
            {"success": bool, "message": str, "room_code": str (optional)}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session. Bitte neu anmelden."
                }
            
            # Generate room code
            room_code = self._generate_room_code()
            
            # Create room in database
            success = DatabaseService.create_new_room(self.env, room_code, user_id)
            
            if not success:
                return {
                    "success": False,
                    "message": "Fehler beim Erstellen des Raums."
                }
            
            # Initialize room player list
            self.room_players[room_code] = [user_id]
            
            # Update user's current room
            user = DatabaseService.get_user_by_id(self.env, user_id)
            room = DatabaseService.get_room_by_code(self.env, room_code)
            if user and room:
                user[0].write({"current_room": room[0].id})
            
            return {
                "success": True,
                "message": "Raum erfolgreich erstellt!",
                "room_code": room_code
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Erstellen des Raums: {str(e)}"
            }
    
    def join_room(self, token: str, room_code: str) -> Dict:
        """
        Tritt einem existierenden Raum bei.
        
        Returns:
            {"success": bool, "message": str, "players": list (optional)}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session. Bitte neu anmelden."
                }
            
            # Check if room exists
            room = DatabaseService.get_room_by_code(self.env, room_code.upper())
            
            if not room:
                return {
                    "success": False,
                    "message": "Raum nicht gefunden."
                }
            
            room = room[0]
            
            # Check if room is closed
            if room.room_closed_at:
                return {
                    "success": False,
                    "message": "Dieser Raum ist bereits geschlossen."
                }
            
            # Initialize room player list if not exists
            if room_code not in self.room_players:
                self.room_players[room_code] = []
            
            # Check if user is already in room
            if user_id in self.room_players[room_code]:
                return {
                    "success": False,
                    "message": "Du bist bereits in diesem Raum."
                }
            
            # Add user to room
            self.room_players[room_code].append(user_id)
            
            # Update user's current room
            user = DatabaseService.get_user_by_id(self.env, user_id)
            if user:
                user[0].write({"current_room": room.id})
            
            # Get player list
            players = self._get_room_players_info(room_code)
            
            return {
                "success": True,
                "message": "Raum erfolgreich beigetreten!",
                "room_code": room_code.upper(),
                "players": players
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Beitreten des Raums: {str(e)}"
            }
    
    def leave_room(self, token: str) -> Dict:
        """
        Verlässt den aktuellen Raum.
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session. Bitte neu anmelden."
                }
            
            # Get user's current room
            user = DatabaseService.get_user_by_id(self.env, user_id)
            if not user or not user[0].current_room:
                return {
                    "success": False,
                    "message": "Du bist in keinem Raum."
                }
            
            room = DatabaseService.get_room_by_id(self.env, user[0].current_room)
            if not room:
                return {
                    "success": False,
                    "message": "Raum nicht gefunden."
                }
            
            room_code = room[0].room_code
            
            # Remove user from room player list
            if room_code in self.room_players and user_id in self.room_players[room_code]:
                self.room_players[room_code].remove(user_id)
                
                # Close room if empty
                if len(self.room_players[room_code]) == 0:
                    DatabaseService.close_room(self.env, room[0].id)
                    del self.room_players[room_code]
            
            # Clear user's current room
            user[0].write({"current_room": None})
            
            return {
                "success": True,
                "message": "Raum erfolgreich verlassen."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Verlassen des Raums: {str(e)}"
            }
    
    def get_room_players(self, token: str) -> Dict:
        """
        Gibt die Liste der Spieler im aktuellen Raum zurück.
        
        Returns:
            {"success": bool, "players": list (optional), "message": str (optional)}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session. Bitte neu anmelden."
                }
            
            # Get user's current room
            user = DatabaseService.get_user_by_id(self.env, user_id)
            if not user or not user[0].current_room:
                return {
                    "success": False,
                    "message": "Du bist in keinem Raum."
                }
            
            room = DatabaseService.get_room_by_id(self.env, user[0].current_room)
            if not room:
                return {
                    "success": False,
                    "message": "Raum nicht gefunden."
                }
            
            room_code = room[0].room_code
            players = self._get_room_players_info(room_code)
            
            return {
                "success": True,
                "room_code": room_code,
                "players": players
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Abrufen der Spielerliste: {str(e)}"
            }
    
    def _get_room_players_info(self, room_code: str) -> List[Dict]:
        """Helper method to get detailed player information for a room"""
        if room_code not in self.room_players:
            return []
        
        players = []
        for user_id in self.room_players[room_code]:
            user = DatabaseService.get_user_by_id(self.env, user_id)
            if user:
                players.append({
                    "user_id": user[0].id,
                    "nickname": user[0].nickname,
                    "points": user[0].points
                })
        
        return players
    
    # ==================== MESSAGING ====================
    
    def send_message(self, token: str, message: str) -> Dict:
        """
        Sendet eine Nachricht an alle Spieler im aktuellen Raum.
        (Für Chat-Funktionalität)
        
        Returns:
            {"success": bool, "message": str, "timestamp": str (optional)}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session. Bitte neu anmelden."
                }
            
            # Get user info
            user = DatabaseService.get_user_by_id(self.env, user_id)
            if not user:
                return {
                    "success": False,
                    "message": "Benutzer nicht gefunden."
                }
            
            # Check if user is in a room
            if not user[0].current_room:
                return {
                    "success": False,
                    "message": "Du bist in keinem Raum."
                }
            
            timestamp = datetime.now().isoformat()
            
            # Note: Actual message broadcasting would be handled by a separate
            # streaming/event system. This just validates the operation.
            
            return {
                "success": True,
                "message": "Nachricht gesendet.",
                "timestamp": timestamp,
                "sender": user[0].nickname
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Senden der Nachricht: {str(e)}"
            }
    
    # ==================== LEADERBOARD ====================
    
    def get_leaderboard(self, limit: int = 10) -> Dict:
        """
        Gibt die Bestenliste zurück.
        
        Returns:
            {"success": bool, "leaderboard": list}
        """
        try:
            top_users = DatabaseService.get_top_users(self.env, limit=limit)
            
            leaderboard = []
            for i, user in enumerate(top_users, 1):
                leaderboard.append({
                    "rank": i,
                    "nickname": user.nickname,
                    "points": user.points
                })
            
            return {
                "success": True,
                "leaderboard": leaderboard
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Abrufen der Bestenliste: {str(e)}",
                "leaderboard": []
            }
    
    def get_user_stats(self, token: str) -> Dict:
        """
        Gibt die Statistiken des aktuellen Benutzers zurück.
        
        Returns:
            {"success": bool, "stats": dict}
        """
        try:
            user_id = self._validate_session(token)
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Ungültige Session. Bitte neu anmelden."
                }
            
            user = DatabaseService.get_user_by_id(self.env, user_id)
            if not user:
                return {
                    "success": False,
                    "message": "Benutzer nicht gefunden."
                }
            
            user = user[0]
            
            # Get user's rank
            all_users = DatabaseService.get_top_users(self.env, limit=1000)
            rank = None
            for i, u in enumerate(all_users, 1):
                if u.id == user_id:
                    rank = i
                    break
            
            return {
                "success": True,
                "stats": {
                    "nickname": user.nickname,
                    "points": user.points,
                    "rank": rank,
                    "registered_at": user.registered_at.isoformat() if user.registered_at else None
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Abrufen der Statistiken: {str(e)}"
            }
    
    # ==================== UTILITY ====================
    
    def get_server_info(self) -> Dict:
        """
        Gibt Informationen über den Server zurück.
        
        Returns:
            {"success": bool, "info": dict}
        """
        try:
            total_users = self.env["user"].search_count([])
            total_rooms = DatabaseService.count_rooms(self.env)
            open_rooms = DatabaseService.count_open_rooms(self.env)
            total_wahlsprueche = DatabaseService.count_wahlsprueche(self.env)
            
            return {
                "success": True,
                "info": {
                    "total_users": total_users,
                    "total_rooms": total_rooms,
                    "open_rooms": open_rooms,
                    "total_wahlsprueche": total_wahlsprueche,
                    "active_sessions": len(self.active_sessions)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler beim Abrufen der Server-Informationen: {str(e)}"
            }
    
    # ==================== SERVER CONTROL ====================
    
    def start(self):
        """Startet den RPC Server"""
        try:
            self.server = SimpleXMLRPCServer(
                (self.host, self.port),
                requestHandler=RequestHandler,
                allow_none=True
            )
            
            # Register all public methods
            self.server.register_instance(self)
            
            print(f"🚀 NetworkService läuft auf {self.host}:{self.port}")
            print(f"📊 Database: {'PostgreSQL' if self.use_postgres else 'SQLite'}")
            print("="*60)
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n⚠️  Server wird heruntergefahren...")
            self.stop()
        except Exception as e:
            print(f"❌ Fehler beim Starten des Servers: {e}")
    
    def stop(self):
        """Stoppt den RPC Server"""
        if self.server:
            self.server.shutdown()
            print("✅ Server erfolgreich beendet.")


if __name__ == "__main__":
    # Beispiel: Server starten
    service = NetworkService(host="localhost", port=8000, use_postgres=False)
    service.start()