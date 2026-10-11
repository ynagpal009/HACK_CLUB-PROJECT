'''
database.py
Sets up the SQLite database and handles password hashing.
Every other file goes through get_connection() instead of touching sqlite3 directly, 
so the schema only lives in one place.
'''
import sqlite3
import hashlib
import os
import secrets
from datetime import date

db_path = os.path.join(os.path.dirname(__file__), "inventory.db")


def get_connection():
    # row factory lets us do row["item_name"] instead of row[1], row[2] etc
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def hash_password(password, salt=None):
    # adds a random salt so the same password doesn't always hash to the
    # same string, found this out after finding out plain sha256 alone
    #isn't great practice for storing passwords
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(password, stored_hash):
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    return hashlib.sha256((salt + password).encode()).hexdigest() == digest


def intialise_database():
    # runs every time the app starts, but CREATE TABLE IF NOT EXISTS means
    # it only actually does anything the very first time
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOL NULL CHECK(role IN ('Admin', 'Staff')),
            full_name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            date_created TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            total_qty INTEGER NOT NULL,
            available_qty INTEGER NOT NULL,
            location TEXT NOT NULL,
            condition_status TEXT NOT NULL,
            low_stock_threshold INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            date_added TEXT NOT NULL
        )
    """) 

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrow_records (
            borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES equipment(item_id),
            borrower_name TEXT NOT NULL,
            qty_borrowed INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            expected_return TEXT,
            return_date TEXT DEAFULT NULL,
            status TEXT NOT NULL DEFAULT 'Borrowed',
            recorded_by TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
            today_date = str(date.today())
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, date_created)
                VALUES (?,?, 'Admin', 'Mr Smith', ?)
            """, ("admin", hash_password("admin123"), today_date))

    connection.commit()
    connection.close()






