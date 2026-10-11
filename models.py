"""
models.py
The User, Equipment and BorrowRecord classes. Each one matches a table
in the database and handles its own validation/SQL so the GUI files
don't need to write SQl themselves.
"""
from datetime import date
from database import get_connection, hash_password, verify_password


class User:
    def __init__(self, row=None):
        if row is not None:
            self.user_id = row["user_id"]
            self.username = row["username"]
            self.role = row["role"]
            self.full_name = row["full_name"]
            self.is_active = row["is_active"]
        else:
            self.user_id = None
            self.username = ""
            self.role = "Staff"
            self.full_name = ""
            self.is_active = 1

    def is_admin(self):
        return self.role == "Admin"

    def authenticate(self, entered_username, entered_password):
        # deactivated accounts get the same "wrong password" style error
        # as a username that doesn't exist, so it's less obvious why login failed
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND is_active=1", (entered_username,))
        row = cursor.fetchone()
        connection.close()

        if row is None:
            return None
        if verify_password(entered_password, row["password_hash"]):
            return User(row)
        return None
    