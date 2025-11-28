import sillyorm
from Models import User, Wahlspruch
from datetime import date, datetime

class DatabaseService:
    PATH_TO_YOUR_CONNECTION_STRING_FILE = r"C:\Users\loris\Desktop\Coding\WahlplakatGame\Docs\connection_string.txt"
    
    @staticmethod
    def get_sillyorm_environment(use_postgres: bool = False) -> sillyorm.Environment:
        """
        Gets your SillyORM Database Environment. If you want to use the productive environment (PostgreSQL) then set argument `use_postgres` to True.
        """
        if use_postgres:
            # Read the connection parameters from file
            conn_params = open(DatabaseService.PATH_TO_YOUR_CONNECTION_STRING_FILE, "r").read().strip()
            
            # Parse the connection string
            params = {}
            for param in conn_params.split():
                key, value = param.split('=', 1)
                params[key] = value
            
            # Build PostgreSQL URI: postgresql://user:password@host:port/dbname
            connection_string = f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['dbname']}"
            
            registry = sillyorm.Registry(connection_string)
        else:
            registry = sillyorm.Registry("sqlite:///wahlplakatgame.db")
        
        registry.register_model(User)
        registry.register_model(Wahlspruch)
        registry.resolve_tables()
        registry.init_db_tables()
        
        env = registry.get_environment(autocommit=True)
        return env
    
    @staticmethod
    def create_new_wahlspruch(env: sillyorm.Environment, text: str, partei: str, wahl: str|None = None, datum: date|None = None, quelle: str|None = None) -> bool:
        """
        Creates a new Wahlspruch in the Database. Returns `True` if created, `False` if the Wahlspruch already existed and raises Exception if something goes wrong.
        """
        try:
            # Check if Wahlspruch already exists
            existing = env["wahlspruch"].search([("spruch", "=", text)])
            if existing:
                return False
            
            # Create new Wahlspruch
            wahlspruch_data = {
                "spruch": text,
                "partei": partei,
                "wahl": wahl,
                "datum": datum,
                "quelle": quelle
            }
            env["wahlspruch"].create(wahlspruch_data)
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def get_all_wahlsprueche(env: sillyorm.Environment):
        """
        Returns all Wahlsprüche from the database.
        """
        return env["wahlspruch"].search([])
    
    @staticmethod
    def get_alle_parteien(env: sillyorm.Environment) -> list[str]:
        """
        Returns a list with all unique Parteien currently in the Database
        """
        wahlsprueche = env["wahlspruch"].search([])
        parteien = set()
        
        for wahlspruch in wahlsprueche:
            if wahlspruch.partei:
                parteien.add(wahlspruch.partei)
        
        return sorted(list(parteien))


    @staticmethod
    def get_wahlspruch_by_id(env: sillyorm.Environment, wahlspruch_id: int):
        """
        Returns a Wahlspruch by its ID or empty recordset if not found.
        """
        return env["wahlspruch"].search([("id", "=", wahlspruch_id)])
    
    @staticmethod
    def get_random_wahlspruch(env: sillyorm.Environment):
        """
        Returns a random Wahlspruch from the database.
        """
        import random
        wahlsprueche = env["wahlspruch"].search([])
        if wahlsprueche:
            return random.choice(list(wahlsprueche))
        return None
    
    @staticmethod
    def search_wahlsprueche_by_partei(env: sillyorm.Environment, partei: str):
        """
        Returns all Wahlsprüche from a specific party.
        """
        return env["wahlspruch"].search([("partei", "=", partei)])
    
    @staticmethod
    def search_wahlsprueche_by_wahl(env: sillyorm.Environment, wahl: str):
        """
        Returns all Wahlsprüche from a specific election.
        """
        return env["wahlspruch"].search([("wahl", "=", wahl)])
    
    @staticmethod
    def count_wahlsprueche(env: sillyorm.Environment) -> int:
        """
        Returns the total count of Wahlsprüche in the database.
        """
        return env["wahlspruch"].search_count([])
    
    @staticmethod
    def create_new_user(env: sillyorm.Environment, nickname: str, password: str) -> bool:
        """
        Creates a new User in the Database. Returns `True` if created, `False` if the User already existed.
        """
        try:
            # Check if user already exists
            existing = env["user"].search([("nickname", "=", nickname)])
            if existing:
                return False
            
            # Create new User
            user_data = {
                "nickname": nickname,
                "password": password,
                "points": 0,
                "registered_at": datetime.now()
            }
            env["user"].create(user_data)
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def get_user_by_nickname(env: sillyorm.Environment, nickname: str):
        """
        Returns a User by nickname or empty recordset if not found.
        """
        return env["user"].search([("nickname", "=", nickname)])
    
    @staticmethod
    def get_user_by_id(env: sillyorm.Environment, user_id: int):
        """
        Returns a User by ID or empty recordset if not found.
        """
        return env["user"].search([("id", "=", user_id)])
    
    @staticmethod
    def get_user_by_session_token(env: sillyorm.Environment, session_token: str):
        """
        Returns a User by session token or empty recordset if not found.
        """
        return env["user"].search([("session_token", "=", session_token)])
    
    @staticmethod
    def update_user_points(env: sillyorm.Environment, user_id: int, new_points: int) -> bool:
        """
        Updates a user's points. Returns True if successful, False if user not found.
        """
        try:
            user = env["user"].search([("id", "=", user_id)])
            if not user:
                return False
            
            user.write({"points": new_points})
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def update_user_session(env: sillyorm.Environment, user_id: int, session_token: str, ip_address: str) -> bool:
        """
        Updates a user's session token and last login IP. Returns True if successful, False if user not found.
        """
        try:
            user = env["user"].search([("id", "=", user_id)])
            if not user:
                return False
            
            user.write({
                "session_token": session_token,
                "last_login_ip": ip_address,
                "last_login_time": datetime.now()
            })
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def get_top_users(env: sillyorm.Environment, limit: int = 10):
        """
        Returns the top users by points.
        """
        return env["user"].search([], order_by="points", order_asc=False, limit=limit)
    
    @staticmethod
    def delete_wahlspruch(env: sillyorm.Environment, wahlspruch_id: int) -> bool:
        """
        Deletes a Wahlspruch by ID. Returns True if successful, False if not found.
        """
        try:
            wahlspruch = env["wahlspruch"].search([("id", "=", wahlspruch_id)])
            if not wahlspruch:
                return False
            
            wahlspruch.unlink()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_user(env: sillyorm.Environment, user_id: int) -> bool:
        """
        Deletes a User by ID. Returns True if successful, False if not found.
        """
        try:
            user = env["user"].search([("id", "=", user_id)])
            if not user:
                return False
            
            user.unlink()
            return True
        except Exception as e:
            raise e

    @staticmethod
    def create_new_room(env: sillyorm.Environment, room_code: str, created_by_user_id: int) -> bool:
        """
        Creates a new Room in the Database. Returns `True` if created, `False` if the room_code already exists.
        """
        try:
            # Check if room with this code already exists
            existing = env["room"].search([("room_code", "=", room_code)])
            if existing:
                return False
            
            # Create new Room
            room_data = {
                "room_code": room_code,
                "room_created_by": created_by_user_id,
                "room_created_at": datetime.now(),
                "room_closed_at": None
            }
            env["room"].create(room_data)
            return True
        except Exception as e:
            raise e

    @staticmethod
    def get_room_by_code(env: sillyorm.Environment, room_code: str):
        """
        Returns a Room by its room_code or empty recordset if not found.
        """
        return env["room"].search([("room_code", "=", room_code)])

    @staticmethod
    def get_room_by_id(env: sillyorm.Environment, room_id: int):
        """
        Returns a Room by its ID or empty recordset if not found.
        """
        return env["room"].search([("id", "=", room_id)])

    @staticmethod
    def get_all_open_rooms(env: sillyorm.Environment):
        """
        Returns all rooms that are still open (room_closed_at is None).
        """
        return env["room"].search([("room_closed_at", "=", None)])

    @staticmethod
    def close_room(env: sillyorm.Environment, room_id: int) -> bool:
        """
        Closes a room by setting room_closed_at timestamp. Returns True if successful, False if room not found.
        """
        try:
            room = env["room"].search([("id", "=", room_id)])
            if not room:
                return False
            
            room.write({"room_closed_at": datetime.now()})
            return True
        except Exception as e:
            raise e

    @staticmethod
    def get_rooms_created_by_user(env: sillyorm.Environment, user_id: int):
        """
        Returns all rooms created by a specific user.
        """
        return env["room"].search([("room_created_by", "=", user_id)])

    @staticmethod
    def delete_room(env: sillyorm.Environment, room_id: int) -> bool:
        """
        Deletes a Room by ID. Returns True if successful, False if not found.
        """
        try:
            room = env["room"].search([("id", "=", room_id)])
            if not room:
                return False
            
            room.unlink()
            return True
        except Exception as e:
            raise e

    @staticmethod
    def count_rooms(env: sillyorm.Environment) -> int:
        """
        Returns the total count of rooms in the database.
        """
        return env["room"].search_count([])

    @staticmethod
    def count_open_rooms(env: sillyorm.Environment) -> int:
        """
        Returns the count of open rooms (room_closed_at is None).
        """
        return env["room"].search_count([("room_closed_at", "=", None)])