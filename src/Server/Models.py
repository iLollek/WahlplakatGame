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

