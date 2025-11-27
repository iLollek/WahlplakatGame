import sillyorm

class User(sillyorm.model.Model):
    """
    Ein User
    """
    _name = "user"

    nickname = sillyorm.fields.String(length=18, required=True)
    points = sillyorm.fields.Integer()
    password = sillyorm.fields.Text()

    last_login_ip = sillyorm.fields.String()
    session_token = sillyorm.fields.String()

    rooms = sillyorm.fields.One2many("room", "players")
    current_room = sillyorm.fields.Integer()

    registered_at = sillyorm.fields.Datetime(None)

class Wahlspruch(sillyorm.model.Model):
    """
    Ein Wahlspruch
    """

    _name = "wahlspruch"

    spruch = sillyorm.fields.Text(required=True)
    partei = sillyorm.fields.String(required=True)
    wahl = sillyorm.fields.String()
    datum = sillyorm.fields.Date()
    quelle = sillyorm.fields.Text()

    def __str__(self):
        return f"{self.spruch} ({self.partei})"

class Room(sillyorm.model.Model):
    """
    A WahlplakatGame Multiplayer Game Room
    """

    _name = "room"

    room_code = sillyorm.fields.String(length=4, required=True, unique=True)
    players = sillyorm.fields.One2many("user", "rooms")
    
    room_created_by = sillyorm.fields.Integer(required=True)
    room_created_at = sillyorm.fields.Datetime(None)
    room_closed_at = sillyorm.fields.Datetime(None)


