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

    def validate(self, is_new, new_password):
        # checks the form fields before we bother touching the database
        if self.username.strip() == "":
            return False, "Username cannot be empty."
        if len(self.username.strip()) > 30:
               return False, "Username is too long (max 30 characters)."
        if self.full_name.strip() == "":
            return False, "Full name cannot be empty."
        if self.role not in ("Admin", "Staff"):
            return False, "Please select a role."
        if is_new and not new_password:
            return False, "A password is required for a new account."
        if new_password and len(new_password) < 4:
            return False, "Password must be at least 4 characters."
        return True, "Success"

    def save(self, new_password=None):
        # new_password only gets passed in when creating an account, or
        # when someone resets a password, leaving it blank on an edit
        # keeps whatever password was already there
        is_new = self.user_id is None
        is_valid, msg = self.validate(is_new, new_password)
        if not is_valid:
            return False, msg

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username=?", (self.username,))
        dup = cursor.fetchone()
        if dup is not None and dup["user_id"] != self.user_id:
            connection.close()
            return False, "A user with this username already exists."

        if is_new:
            password_hash = hash_password(new_password)
            cursor.execute("""
                Insert INTO users (username, password_hash, role, full_name, is_active, data_created)
                Values (?, ?, ?, ?, ?, ?)
            """, (self.username, password_hash, self.role, self.full_name, self.is_active, str(date.today())))
            self.user_id = cursor.lastrowid
        else:
            if new_password:
                password_hash = hash_password(new_password)
                cursor.execute("""
                    UPDATE users SET username=?, password_hash=?, role=?, full_name=?, is_active=?
                    WHERE user_id=?
                """, (self.username, password_hash, self.role, self.full_name, self.is_active, self.user_id))
            else:
                cursor.execute("""
                    UPDATE users SET username=?, role=?, full_name=?, is_active=?
                    WHERE user_id=?
                """, (self.username, self.role, self.full_name, self.is_active, self.user_id))

        connection.commit()
        connection.close()
        return True, "Saved"

    def set_active(self, is_active):
        # deactivating instead of deleting so their old borrow records
        # still make sense (who recorded what) even after they leave
        if is_active:
            self.is_active = 1
        else:
            self.is_active = 0
        connection = get_connection()
        connection.execute("UPDATE users SET is_active=? WHERE user_id=?", (self.is_active, self.user_id))
        connection.commit()
        connection.close()

    def get_all(self):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users ORDER BY is_active DESC, username ASC")
        rows = cursor.fetchall()
        connection.close()

        users = []
        for row in rows:
            users.append(User(row))
        return users
    
  

     

    
