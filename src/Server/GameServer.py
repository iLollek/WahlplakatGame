from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
from typing import Dict, List, Optional
from DatabaseService import DatabaseService
import secrets
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


class GameLobby:
    """Zentrale Spiel-Lobby - alle Spieler spielen zusammen"""
    
    def __init__(self, db_env):
        self.db_env = db_env
        self.players: Dict[str, dict] = {}  # session_token -> {user_id, nickname, sid, answered, points}
        self.sid_to_token: Dict[str, str] = {}  # sid -> session_token für Disconnect-Handling
        self.current_wahlspruch = None
        self.current_quelle = None
        self.current_answers: Dict[str, str] = {}  # session_token -> partei
        self.round_timer = None
        self.round_active = False
        self.round_number = 0
        self.lock = threading.Lock()
        
    def add_player(self, session_token: str, user_id: int, nickname: str, sid: str, points: int):
        """Fügt einen Spieler zur Lobby hinzu"""
        with self.lock:
            self.players[session_token] = {
                'user_id': user_id,
                'nickname': nickname,
                'sid': sid,
                'answered': False,
                'points': points,
                'can_answer': True  # Kann diese Runde antworten
            }
            self.sid_to_token[sid] = session_token
            
            # Wenn Spieler während einer aktiven Runde beitritt, kann er diese Runde nicht antworten
            if self.round_active:
                self.players[session_token]['can_answer'] = False
        
    def remove_player(self, session_token: str = None, sid: str = None) -> Optional[dict]:
        """
        Entfernt einen Spieler aus der Lobby.
        Kann entweder per session_token oder sid erfolgen.
        
        Returns:
            Dict mit Spieler-Info falls gefunden, sonst None
        """
        with self.lock:
            # Finde Token falls nur SID gegeben
            if sid and not session_token:
                session_token = self.sid_to_token.get(sid)
            
            if not session_token:
                return None
            
            # Entferne Spieler
            player_info = None
            if session_token in self.players:
                player_info = self.players[session_token].copy()
                del self.players[session_token]
                
                # Cleanup sid_to_token mapping
                if player_info['sid'] in self.sid_to_token:
                    del self.sid_to_token[player_info['sid']]
                
                # Cleanup Antworten
                if session_token in self.current_answers:
                    del self.current_answers[session_token]
            
            return player_info
    
    def get_player_list(self) -> List[dict]:
        """Gibt Liste aller Spieler zurück"""
        with self.lock:
            return [
                {
                    'nickname': p['nickname'],
                    'points': p['points'],
                    'answered': p['answered'],
                    'can_answer': p['can_answer']
                }
                for p in self.players.values()
            ]
    
    def start_new_round(self):
        """Startet eine neue Runde"""
        with self.lock:
            self.round_number += 1
            self.round_active = True
            self.current_answers = {}
            
            # Reset answered status und ermögliche allen das Antworten
            for player in self.players.values():
                player['answered'] = False
                player['can_answer'] = True
            
            # Wähle zufälligen Wahlspruch
            self.current_wahlspruch = DatabaseService.get_random_wahlspruch(self.db_env)
            
            if not self.current_wahlspruch:
                self.round_active = False
                return None
            
            self.current_quelle = self.current_wahlspruch.quelle
            
            # Starte 15-Sekunden Timer
            if self.round_timer:
                self.round_timer.cancel()
            self.round_timer = threading.Timer(15.0, self.end_round)
            self.round_timer.start()
            
            return {
                'round_number': self.round_number,
                'wahlspruch': self.current_wahlspruch.spruch,
                'wahlspruch_id': self.current_wahlspruch.id
            }
    
    def submit_answer(self, session_token: str, partei: str) -> tuple[bool, str]:
        """
        Registriert eine Antwort
        Returns: (success, message)
        """
        with self.lock:
            if not self.round_active:
                return False, "Keine aktive Runde"
            
            if session_token not in self.players:
                return False, "Nicht in der Lobby"
            
            player = self.players[session_token]
            
            if not player['can_answer']:
                return False, "Du bist während der laufenden Runde beigetreten"
            
            if player['answered']:
                return False, "Du hast bereits geantwortet"
            
            self.current_answers[session_token] = partei
            player['answered'] = True
            
            # Prüfe ob alle Spieler die antworten können, geantwortet haben
            players_who_can_answer = [p for p in self.players.values() if p['can_answer']]
            all_answered = all(p['answered'] for p in players_who_can_answer)
            
            if all_answered and len(players_who_can_answer) > 0:
                if self.round_timer:
                    self.round_timer.cancel()
                threading.Thread(target=self.end_round).start()
            
            return True, "Antwort registriert"
    
    def end_round(self):
        """Beendet die Runde und verteilt Punkte"""
        with self.lock:
            if not self.round_active:
                return
            
            self.round_active = False
            
            if not self.current_wahlspruch:
                return
            
            correct_partei = self.current_wahlspruch.partei
            results = []
            
            # Berechne Ergebnisse und update Punkte
            for session_token, player in self.players.items():
                answered_partei = self.current_answers.get(session_token, None)
                
                # Nur bewerten wenn Spieler antworten konnte
                if player['can_answer']:
                    is_correct = answered_partei == correct_partei if answered_partei else False
                    points_earned = 1 if is_correct else 0
                    
                    if is_correct:
                        # Update Punkte in DB
                        new_points = player['points'] + points_earned
                        DatabaseService.update_user_points(self.db_env, player['user_id'], new_points)
                        player['points'] = new_points
                else:
                    is_correct = None  # Konnte nicht antworten
                    points_earned = 0
                
                results.append({
                    'nickname': player['nickname'],
                    'answered': answered_partei,
                    'correct': is_correct,
                    'points_earned': points_earned,
                    'total_points': player['points'],
                    'could_answer': player['can_answer']
                })
        
        # Sende Ergebnisse an alle Clients (außerhalb des Locks)
        socketio.emit('round_end', {
            'correct_partei': correct_partei,
            'results': results,
            'quelle': self.current_quelle
        })
        
        # Starte nach 5 Sekunden neue Runde
        threading.Timer(5.0, self._auto_start_next_round).start()
    
    def _auto_start_next_round(self):
        """Startet automatisch die nächste Runde"""
        if len(self.players) > 0:  # Nur wenn noch Spieler in der Lobby sind
            round_data = self.start_new_round()
            if round_data:
                socketio.emit('new_round', round_data)
    
    def get_current_quelle(self, session_token: str) -> Optional[str]:
        """Gibt die Quelle zurück wenn Spieler geantwortet hat"""
        with self.lock:
            if session_token in self.players and self.players[session_token]['answered']:
                return self.current_quelle
            return None


class GameService:
    """Verwaltet die zentrale Spiel-Lobby"""
    
    def __init__(self, db_env, host: str = "0.0.0.0", port: int = 5000):
        self.db_env = db_env
        self.host = host
        self.port = port
        self.lobby = GameLobby(db_env)
        self.session_to_sid: Dict[str, str] = {}  # session_token -> socket_id
    
    def start(self):
        """Startet den GameService Server"""
        logging.info(f"🎮 GameService läuft auf {self.host}:{self.port}")
        socketio.run(app, host=self.host, port=self.port, debug=False, allow_unsafe_werkzeug=True)


# Globale GameService Instanz
game_service: Optional[GameService] = None


def init_game_service(db_env):
    """Initialisiert den GameService"""
    global game_service
    game_service = GameService(db_env)


# ==================== SOCKETIO EVENT HANDLERS ====================

@socketio.on('connect')
def handle_connect():
    """Client verbindet sich"""
    logging.info(f"🔌 Client verbunden: {request.sid}")
    emit('connected', {'message': 'Verbindung erfolgreich'})


@socketio.on('disconnect')
def handle_disconnect():
    """Client trennt Verbindung - automatische Erkennung"""
    logging.info(f"🔌 Client getrennt: {request.sid}")
    
    if not game_service:
        return
    
    # Finde und entferne Spieler anhand der Socket-ID
    player_info = game_service.lobby.remove_player(sid=request.sid)
    
    if player_info:
        nickname = player_info['nickname']
        
        # Benachrichtige andere Spieler über Disconnect
        emit('player_left', {
            'nickname': nickname,
            'reason': 'disconnect'
        }, broadcast=True)
        
        # Update Spielerliste
        player_list = game_service.lobby.get_player_list()
        emit('player_list_update', {'players': player_list}, broadcast=True)
        
        logging.info(f"👋 {nickname} wurde automatisch aus der Lobby entfernt (Disconnect)")


@socketio.on('join_game')
def handle_join_game(data):
    """Spieler tritt dem Spiel bei"""
    try:
        session_token = data.get('token')
        
        if not game_service:
            emit('error', {'message': 'GameService nicht initialisiert'})
            return
        
        # Validiere Session Token über DatabaseService
        user = DatabaseService.get_user_by_session_token(game_service.db_env, session_token)
        
        if not user:
            emit('error', {'message': 'Ungültige Session'})
            return
        
        user = user[0]
        
        # Entferne Spieler falls schon in Lobby (reconnect)
        game_service.lobby.remove_player(session_token)
        
        # Füge zur Lobby hinzu
        game_service.lobby.add_player(session_token, user.id, user.nickname, request.sid, user.points)
        game_service.session_to_sid[session_token] = request.sid
        
        # Sende aktuelle Spielerliste an alle
        player_list = game_service.lobby.get_player_list()
        emit('player_list_update', {'players': player_list}, broadcast=True)
        
        # Benachrichtige andere über neuen Spieler
        emit('player_joined', {
            'nickname': user.nickname,
            'points': user.points
        }, broadcast=True, include_self=False)
        
        # Sende Success an Spieler mit aktueller Rundeinfo
        emit('join_success', {
            'players': player_list,
            'your_nickname': user.nickname,
            'round_active': game_service.lobby.round_active,
            'round_number': game_service.lobby.round_number
        })
        
        # Wenn aktive Runde läuft, sende aktuellen Wahlspruch
        if game_service.lobby.round_active and game_service.lobby.current_wahlspruch:
            emit('new_round', {
                'round_number': game_service.lobby.round_number,
                'wahlspruch': game_service.lobby.current_wahlspruch.spruch,
                'wahlspruch_id': game_service.lobby.current_wahlspruch.id
            })
        
        # Starte erste Runde wenn erster Spieler
        if len(game_service.lobby.players) == 1 and not game_service.lobby.round_active:
            round_data = game_service.lobby.start_new_round()
            if round_data:
                socketio.emit('new_round', round_data)
        
        logging.info(f"✅ {user.nickname} ist der Lobby beigetreten")
        
    except Exception as e:
        logging.exception(f"❌ Fehler bei join_game: {e}")
        emit('error', {'message': str(e)})


@socketio.on('leave_game')
def handle_leave_game(data):
    """Spieler verlässt das Spiel bewusst"""
    try:
        session_token = data.get('token')
        reason = data.get('reason', 'request')  # 'request' oder 'crash'
        
        if not game_service:
            return
        
        player_info = game_service.lobby.remove_player(session_token)
        
        if player_info:
            nickname = player_info['nickname']
            
            if session_token in game_service.session_to_sid:
                del game_service.session_to_sid[session_token]
            
            # Benachrichtige andere
            emit('player_left', {
                'nickname': nickname,
                'reason': reason
            }, broadcast=True)
            
            # Update Spielerliste
            player_list = game_service.lobby.get_player_list()
            emit('player_list_update', {'players': player_list}, broadcast=True)
            
            if reason == 'crash':
                logging.warning(f"👋 {nickname} hat die Lobby verlassen (Crash)")
            else:
                logging.info(f"👋 {nickname} hat die Lobby verlassen (auf Anfrage)")
        
    except Exception as e:
        logging.exception(f"❌ Fehler bei leave_game: {e}")


@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Spieler gibt Antwort ab"""
    try:
        session_token = data.get('token')
        partei = data.get('partei')
        
        if not game_service:
            emit('error', {'message': 'GameService nicht initialisiert'})
            return
        
        # Registriere Antwort
        success, message = game_service.lobby.submit_answer(session_token, partei)
        
        if success:
            player = game_service.lobby.players[session_token]
            
            # Bestätige Antwort an Spieler
            emit('answer_accepted', {'partei': partei})
            
            # Benachrichtige andere Spieler
            emit('player_answered', {
                'nickname': player['nickname']
            }, broadcast=True, include_self=False)
            
            # Update Spielerliste
            player_list = game_service.lobby.get_player_list()
            emit('player_list_update', {'players': player_list}, broadcast=True)
            
            logging.info(f"✓ {player['nickname']} hat geantwortet: {partei}")
        else:
            emit('error', {'message': message})
        
    except Exception as e:
        logging.exception(f"❌ Fehler bei submit_answer: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_quelle')
def handle_request_quelle(data):
    """Spieler fordert Quelle an (nach eigener Antwort)"""
    try:
        session_token = data.get('token')
        
        if not game_service:
            emit('error', {'message': 'GameService nicht initialisiert'})
            return
        
        quelle = game_service.lobby.get_current_quelle(session_token)
        
        if quelle is not None:
            emit('quelle_response', {'quelle': quelle})
        else:
            emit('error', {'message': 'Quelle nicht verfügbar - hast du geantwortet?'})
        
    except Exception as e:
        logging.exception(f"❌ Fehler bei request_quelle: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_leaderboard')
def handle_request_leaderboard():
    """Client fordert Leaderboard an"""
    try:
        if not game_service:
            emit('error', {'message': 'GameService nicht initialisiert'})
            return
        
        top_users = DatabaseService.get_top_users(game_service.db_env, limit=10)
        
        leaderboard = []
        for i, user in enumerate(top_users, 1):
            leaderboard.append({
                'rank': i,
                'nickname': user.nickname,
                'points': user.points
            })
        
        emit('leaderboard_update', {'leaderboard': leaderboard})
        
    except Exception as e:
        logging.exception(f"❌ Fehler bei request_leaderboard: {e}")
        emit('error', {'message': str(e)})


if __name__ == "__main__":
    # Test
    from DatabaseService import DatabaseService
    env = DatabaseService.get_sillyorm_environment(use_postgres=False)
    init_game_service(env)
    game_service.start()