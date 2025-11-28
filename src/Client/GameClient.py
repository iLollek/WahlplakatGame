import socketio
import threading
from typing import Callable, Optional, Dict
import logging


class GameClient:
    """
    Singleton WebSocket Client für das WahlplakatGame.
    Verbindet sich mit dem GameService Server für Echtzeit-Spiel-Events.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        """Verhindert direkte Instanziierung"""
        if cls._instance is None:
            cls._instance = super(GameClient, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls, host: str = "localhost", port: int = 5000) -> 'GameClient':
        """
        Gibt die Singleton-Instanz zurück.
        
        Args:
            host: Server hostname oder IP
            port: Server port
            
        Returns:
            Die GameClient Singleton-Instanz
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._instance._initialize(host, port)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Setzt die Singleton-Instanz zurück"""
        with cls._lock:
            if cls._instance:
                try:
                    cls._instance.disconnect()
                except:
                    pass
            cls._instance = None
            cls._initialized = False
    
    def _initialize(self, host: str = "localhost", port: int = 5000):
        """
        Initialisiert den GameClient.
        
        Args:
            host: Server hostname oder IP
            port: Server port
        """
        if GameClient._initialized:
            return
        
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.connected = False
        self.session_token: Optional[str] = None
        
        # Event Callbacks
        self.callbacks: Dict[str, list] = {
            'connected': [],
            'new_round': [],
            'player_answered': [],
            'round_end': [],
            'player_joined': [],
            'player_left': [],
            'player_list_update': [],
            'answer_accepted': [],
            'leaderboard_update': [],
            'quelle_response': [],
            'join_success': [],
            'error': []
        }
        
        self._register_socketio_handlers()
        GameClient._initialized = True
    
    def _register_socketio_handlers(self):
        """Registriert SocketIO Event Handler"""
        
        @self.sio.on('connect')
        def on_connect():
            self.connected = True
            print("✅ WebSocket verbunden")
            self._trigger_callbacks('connected', {})
        
        @self.sio.on('disconnect')
        def on_disconnect():
            self.connected = False
            print("🔌 WebSocket getrennt")
        
        @self.sio.on('connected')
        def on_server_connected(data):
            print(f"📡 Server: {data.get('message', '')}")
        
        @self.sio.on('new_round')
        def on_new_round(data):
            print(f"🎮 Neue Runde #{data.get('round_number')}: {data.get('wahlspruch', '')[:50]}...")
            self._trigger_callbacks('new_round', data)
        
        @self.sio.on('player_answered')
        def on_player_answered(data):
            print(f"✓ {data.get('nickname')} hat geantwortet")
            self._trigger_callbacks('player_answered', data)
        
        @self.sio.on('round_end')
        def on_round_end(data):
            print(f"🏁 Runde beendet - Richtige Partei: {data.get('correct_partei')}")
            self._trigger_callbacks('round_end', data)
        
        @self.sio.on('player_joined')
        def on_player_joined(data):
            print(f"👋 {data.get('nickname')} ist beigetreten")
            self._trigger_callbacks('player_joined', data)
        
        @self.sio.on('player_left')
        def on_player_left(data):
            print(f"👋 {data.get('nickname')} hat verlassen")
            self._trigger_callbacks('player_left', data)
        
        @self.sio.on('player_list_update')
        def on_player_list_update(data):
            self._trigger_callbacks('player_list_update', data)
        
        @self.sio.on('answer_accepted')
        def on_answer_accepted(data):
            print(f"✅ Antwort akzeptiert: {data.get('partei')}")
            self._trigger_callbacks('answer_accepted', data)
        
        @self.sio.on('leaderboard_update')
        def on_leaderboard_update(data):
            self._trigger_callbacks('leaderboard_update', data)
        
        @self.sio.on('quelle_response')
        def on_quelle_response(data):
            self._trigger_callbacks('quelle_response', data)
        
        @self.sio.on('join_success')
        def on_join_success(data):
            print(f"🎉 Erfolgreich der Lobby beigetreten")
            self._trigger_callbacks('join_success', data)
        
        @self.sio.on('error')
        def on_error(data):
            print(f"❌ Fehler: {data.get('message')}")
            self._trigger_callbacks('error', data)
    
    def _trigger_callbacks(self, event: str, data: Dict):
        """Ruft alle registrierten Callbacks für ein Event auf"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"❌ Fehler in Callback für {event}: {e}")
    
    # ==================== PUBLIC API ====================
    
    def connect(self) -> bool:
        """
        Verbindet mit dem GameService Server.
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            if not self.connected:
                self.sio.connect(self.server_url)
                return True
            return True
        except Exception as e:
            print(f"❌ Verbindung zum GameService fehlgeschlagen: {e}")
            return False
    
    def disconnect(self):
        """Trennt die Verbindung zum GameService"""
        try:
            if self.connected:
                if self.session_token:
                    self.leave_game()
                self.sio.disconnect()
        except Exception as e:
            print(f"❌ Fehler beim Trennen: {e}")
    
    def join_game(self, session_token: str) -> bool:
        """
        Tritt dem Spiel bei.
        
        Args:
            session_token: Session-Token vom Login
            
        Returns:
            True wenn erfolgreich
        """
        try:
            self.session_token = session_token
            self.sio.emit('join_game', {'token': session_token})
            return True
        except Exception as e:
            print(f"❌ Fehler beim Beitreten: {e}")
            return False
    
    def leave_game(self):
        """Verlässt das Spiel"""
        try:
            if self.session_token:
                self.sio.emit('leave_game', {'token': self.session_token})
                self.session_token = None
        except Exception as e:
            print(f"❌ Fehler beim Verlassen: {e}")
    
    def submit_answer(self, partei: str) -> bool:
        """
        Sendet eine Antwort.
        
        Args:
            partei: Die gewählte Partei
            
        Returns:
            True wenn erfolgreich gesendet
        """
        try:
            if not self.session_token:
                print("❌ Nicht im Spiel")
                return False
            
            self.sio.emit('submit_answer', {
                'token': self.session_token,
                'partei': partei
            })
            return True
        except Exception as e:
            print(f"❌ Fehler beim Senden der Antwort: {e}")
            return False
    
    def request_quelle(self):
        """Fordert die Quelle des aktuellen Wahlspruchs an"""
        try:
            if not self.session_token:
                print("❌ Nicht im Spiel")
                return
            
            self.sio.emit('request_quelle', {'token': self.session_token})
        except Exception as e:
            print(f"❌ Fehler beim Anfordern der Quelle: {e}")
    
    def request_leaderboard(self):
        """Fordert das Leaderboard an"""
        try:
            self.sio.emit('request_leaderboard', {})
        except Exception as e:
            print(f"❌ Fehler beim Anfordern des Leaderboards: {e}")
    
    # ==================== EVENT REGISTRATION ====================
    
    def on(self, event: str, callback: Callable):
        """
        Registriert einen Callback für ein Event.
        
        Args:
            event: Event-Name ('new_round', 'player_answered', 'round_end', etc.)
            callback: Callback-Funktion die aufgerufen wird
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
        else:
            print(f"⚠️ Unbekanntes Event: {event}")
    
    def remove_callback(self, event: str, callback: Callable):
        """Entfernt einen Callback für ein Event"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
    
    def is_connected(self) -> bool:
        """Prüft ob verbunden"""
        return self.connected


# ==================== CONVENIENCE FUNCTIONS ====================

def get_game_client() -> GameClient:
    """
    Convenience-Funktion für schnellen Zugriff auf den GameClient.
    
    Returns:
        Die GameClient Singleton-Instanz
    """
    return GameClient.get_instance()


if __name__ == "__main__":
    # Test
    client = GameClient.get_instance(host="localhost", port=5000)
    
    # Register callbacks
    def on_new_round(data):
        print(f"Callback: Neue Runde - {data}")
    
    client.on('new_round', on_new_round)
    
    # Connect
    if client.connect():
        print("Verbunden!")
        # Würde normalerweise ein Token vom XMLRPC Login bekommen
        # client.join_game("test_token")