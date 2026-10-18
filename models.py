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
                Insert INTO users (username, password_hash, role, full_name, is_active, date_created)
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


class Equipment:
    # Columns that are allowed to be used in ORDER BY. If the sort key 
    # the GUI sends through isn't one of these, we fall back to sorting 
    # by item name instead of putting an unknown column straight into
    # the SQL string
    SORTABLE_COLUMNS = ("item_id", "item_name", "category", "total_qty", "available_qty", "location")

    def __init__(self, row=None):
        if row is not None:
            self.item_id = row["item_id"]
            self.item_name = row["item_name"]
            self.category = row["category"]
            self.total_qty = row["total_qty"]
            self.available_qty = row["available_qty"]
            self.location = row["location"]
            self.condition_status = row["condition_status"]
            self.low_stock_threshold = row["low_stock_threshold"]
            if row["notes"]:
                self.notes = row["notes"]
            else:
                self.notes = ""
            self.date_added = row["date_added"]
        else:
            self.item_id = None
            self.item_name = ""
            self.category = ""
            self.total_qty = 0
            self.avaliable_qty = 0
            self.location = ""
            self.condition_status = ""
            self.low_stock_threshold = 2
            self.notes = ""
            self.date_added = str(date.today())

    def is_low_stock(self):
        return self.available_qty < self.low_stock_threshold

    def update_availability(self, action, quantity):
        if action == "borrow":
            self.available_qty -= quantity
        elif action == "return":
            self.available_qty += quantity
        connection = get_connection()
        connection.execute("UPDATE equipment SET available_qty = ? WHERE item_id = ?", (self.available_qty, self.item_id))
        connection.commit()
        connection.close()

    def validate(self):
        if self.item_name.strip() == "" or self.location.strip() == "":
            return False, "Item Name and Location cannot be empty."
        if self.category == "":
            return False, "Please select a category."
        if self.condition_status == "":
            return False, "Please select a conditon."
        try:
            self.total_qty = int(self.total_qty)
            if self.total_qty < 1:
                return False, "Total quantity must be at least 1."
            if self.total_qty > 500:
                return False, "Total quantity sees too high (max 500). Check the number."
        except ValueError:
            return False, "Total quantiy must be a whole number."
        try:
            self.low_stock_threshold = int(self.low_stock_threshold)
            if self.low_stock_threshold < 1:
                return False, "Threshold must be at least 1"
            if self.low_stock_threshold > 500:
                return False, "Threshold seems too high (max 500). Check the number."
        except ValueError:
            return False, "Low-stock threshold must be a number."
        return True, "Success"

    def save(self):
        is_valid, msg = self.validate()
        if not is_valid:
            return False, msg

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT item_id FROM equipment WHERE item_name=?", (self.item_name,))
        dup = cursor.fetchone()

        if dup is not None and dup["item_id"] != self.item_id:
            connection.close()
            return False, "An item with this name already exists."

        if self.item_id is not None:
            # if the qty gets chnaged while editing, shift available_qty
            # by the same amount so it doesn't get out of sync with total
            cursor.execute("SELECT total_qty , available_qty FROM equipment WHERE item_id=?", (self.item_id,))
            existing = cursor.fetchone()
            borrowed_out = existing["total qty"] - existing["available_qty"]
            new_available = self.total_qty - borrowed_out
            if new_available < 0:
                new_available = 0

            cursor.execute("""
                UPDATE equipment SET item_name=?, category=?, total_qty=?, available_qty=?, location=?,
                condition_status=?, low_stock_threshold=?, notes=? WHERE item_id=?
            """, (self.item_name, self.category, self.total_qty, new_available, self.location,
                  self.condtion_status, self.low_stock_threshold, self.notes, self.item_id))
            self.available_qty = new_available
        else:
            self.available_qty = self.total_qty
            cursor.execute("""
                INSERT INTO equipment (item_name, category, total_qty, available_qty, location, condition_status, low_stock_threshold, notes, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.item_name, self.category, self.total_qty, self.available_qty, self.location, self.condition_status, self.low_stock_threshold, self.notes, self.date_added))
            self.item_id = cursor.lastrowid
            connection.commit()
            connection.close()
            return True, "Saved"

    def delete(self):
        connection = get_connection()
        cursor = connection.cursor()
        # can't delete if it's on loan right now
        cursor.execute("SELECT COUNT(*) FROM borrow_records WHERE item_id=?", (self.item_id,))
        if cursor.fetchone()[0] > 0:
            connection.close()
            return False, "Cannot delete: item is currently borrowed."
        # also can't delete if it has old borrow records, otherwise the
        # database throws a foreign key error (found this out the hard way)
        cursor.execute("SELECT COUNT(*) FROM borrow_records WHERE item_id=?", (self.item_id,))
        if cursor.fetchone()[0] > 0:
            connection.close()
            return False, "Cannot delete: this item has past borrow history."
        cursor.execute("DELETE FROM equipment WHERE item_id=?", (self.item_id))
        connection.commit()
        connection.close()
        return True, "Deleted"

    def get_all(self, search_text="", sort_col="item_name", sort_asc=True):
        # search checks name, category AND item id (e.g. "3" or "E003"
        # both match item 3, since E003 is what shows on the screen)
        connection = get_connection()
        cursor = connection.cursor()

        if sort_asc:
            direction = "ASC"
        else:
            direction = "DESC"

        if sort_col not in self.SORTABLE_COLUMNS:
            sort_col = "item_name"

        text = search_text.strip()
        if text != "":
            # Accept both the raw item_id (e.g. "3") and the zero-padded
            # "E003" format shown in the Item ID column, by stripping the
            # leding "E" and any leading zeros before matching.
            if text[:1].lower() == "e":
                id_text = text[1:]
            else:
                id_text = text
            if id_text.isdigit():
                id_text = str(int(id_text))

            cursor.execute(
                f"""SELECT * FROM equipment
                    WHERE item_name LIKE ? OR category LIKE ? OR CAST(item_id AS TEXT) LIKE ?
                    ORDER BY {sort_col} {direction}""",
                (f"%{text}%", f"%{text}%", f"%{id_text}%")
            )
    
        else:
            cursor.execute(f"SELECT * FROM equipment ORDER BY {sort_col} {direction}")
        rows = cursor.fetchall()
        connection.close()

        items = []
        for row in rows:
            items.append(Equipment(row))
        return items
    
    def get_by_id(self, find_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM equipment WHERE item_id=?", (find_id,))
        row = cursor.fetchone()
        connection.close()
        if row:
            return Equipment(row)
        return None

    def get_summary(self):
        # numbers used by the report screen
        items = self.get_all()

        categories = []
        low_stock_items = []
        total_qty = 0
        total_available = 0

        for item in items:
            if item.category in categories:
                categories[item.category] += 1
            else:
                categories[item.categoty] = 1 

            total_qty += item.total_qty
            total_available += item.available_qty

            if item.is_low_stock():
                low_stock_items.append(item)

        total_borrowed = total_qty - total_available

        return {
            "total_items": len(items),
            "total_qty": total_qty,
            "total_available": total_available,
            "total_borrowed": total_borrowed,
            "categories": categories,
            "low_stock_items": low_stock_items,
        }


class BorrowRecord:
    def __init__(self, row=None):
        if row is not None:
            self.borrow_id = row["borrow_id"]
            self.item_id = row["item_id"]
            self.borrower_name = row["borrower_name"]
            self.qty_borrowed = row["qty_borrowed"]
            self.borrow_date = row["borrow_date"]
            self.expected_return = row["expected_return"]
            self.return_date = row["return_date"]
            self.status = row["status"]
            self.recorded_by = row["recorded_by"]
        else:
            self.borrow_id = None
            self.item_id = None
            self.borrower_name = ""
            self.qty_borrowed = 0 
            self.borrow_date = str(date.today())
            self.expected_return = ""
            self.return_date = None
            self.status = "Borrowed"
            self.recorded_by = ""

    def save(self):
        if self.borrower_name.strip() == "":
            return False, "Borrower name cannot be empty."
        if len(self.borrower_name.strip()) > 60:
            return False, "Borrower name is too long."
        item = Equipment().get_by_id(self.item_id)
        if item is None:
            return False, "Item not found."

        try:
            self.qty_borrowed = int(self.qty_borrowed)
            if self.qty_borrowed < 1:
                return False, "Quantity must be at least 1."
        except ValueError:
            return False, "Quantiy must be a number."

        if self.qty_borrowed > item.available_qty:
            return False, "Cannot exceed available stock."

        connection = get_connection() 
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO borrow_records (item_id, borrower_name, qty_borrowed, borrow_date, expected_return, status, recorded_by)
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (self.item_id, self.borrower_name, self.qty_borrowed, self.borrow_date, self.expected_return, "Borrowed", self.recorded_by))
        self.borrow_id = cursor.lastrowid
        connection.commit()
        connection.close()
        item.update_availability("borrow", self.qty_borrowed)
        return True, "Saved" 

    def complete_return(self, return_date):
        connection = get_connection()
        connection.execute("UPDATE borrow_records SET return_date=?, status='Returned' WHERE borrow_id=?", (return_date, self.borrow_id))
        connection.commit()
        connection.close()
        self.return_date = return_date
        self.status = 'Returned'
        Equipment().get_by_id(self.item_id).update_availability("return", self.qty_borrowed)
        return True, "Returned"

    def get_active_for_item(self, item_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM borrow_records WHERE item_id=? AND status= 'Borrowed'", (item_id,))
        rows = cursor.fetchall()
        connection.close()

        records = []
        for row in rows:
            records.append(BorrowRecord(row))
        return records

    def get_all_active(self):
        # everything currently out on loan, across every item, not just 
        # one - joins with equipment so we get the item name too
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT b.*, e.item_name AS item_name
            FROM borrow_records b
            JOIN equipment e ON e.item_id = b.item_id
            WHERE b.status = 'Borrowed'
            ORDER BY b.borrow_date DESC, b.borrow_id DESC
            """)
        rows = cursor.fetchall()
        connection.close()

        records = []
        for row in rows:
            rec = BorrowRecord(row)
            rec.item_name = row["item_name"]
            records.append(rec)
        return records

    def get_history(self, search_text=""):
        # same idea as get_all_active but includes returned items too
        connection = get_connection()
        cursor = connection.cursor()
        text = search_text.strip()
        if text != "":
            cursor.execute("""
                SELECT b.*, e.item_name AS item_name
                FROM borrow_records b
                JOIN equipment e ON e.item_id = b.item_id
                WHERE b.borrower_name LIKE ? OR e.item_name LIKE ?
                ORDER BY b.borrow_date DESC, b.borrow_id DESC
            """, (f"%{text}%", f"%{text}%"))
        else:
            cursor.execute("""
                SELECT b.*, e.item_name AS item_name
                FROM borrow_records b
                JOIN equipment e ON e.item_id = b.item_id
                ORDER BY b.borrow_date DESC, b.borrow_id DESC
            """)
        rows = cursor.fetchall()
        connection.close()

        records = []
        for row in rows:
            rec = BorrowRecord(row)
            rec.item_name = row["item_name"]
            records.append(rec)
        return records
   