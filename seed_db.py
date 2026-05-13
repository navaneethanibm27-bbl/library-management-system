"""
Seed script to create admin and test user accounts
Run this once to populate the database with initial accounts
"""

import sqlite3
from werkzeug.security import generate_password_hash

def connect_db():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

def seed_users():
    conn = connect_db()
    cur = conn.cursor()

    # Check if admin exists
    cur.execute("SELECT * FROM users WHERE email=?", ('admin@library.com',))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users(name, email, password, role) VALUES(?, ?, ?, ?)",
            ('Admin User', 'admin@library.com', generate_password_hash('admin123'), 'admin')
        )
        print("✓ Admin account created: admin@library.com / admin123")
    else:
        print("✗ Admin account already exists")

    # Check if test user exists
    cur.execute("SELECT * FROM users WHERE email=?", ('user@library.com',))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users(name, email, password, role) VALUES(?, ?, ?, ?)",
            ('Test User', 'user@library.com', generate_password_hash('user123'), 'user')
        )
        print("✓ Test user account created: user@library.com / user123")
    else:
        print("✗ Test user account already exists")

    # Add sample books (check for duplicates)
    books = [
        ('Python Programming', 'Guido van Rossum', 15),
        ('Data Science Handbook', 'Jake VanderPlas', 10),
        ('Web Development with Flask', 'Miguel Grinberg', 8),
        ('Clean Code', 'Robert C. Martin', 12),
        ('Design Patterns', 'Gang of Four', 6),
    ]
    
    added = 0
    for book_name, author, quantity in books:
        cur.execute("SELECT * FROM books WHERE book_name=? AND author=?", (book_name, author))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO books(book_name, author, quantity) VALUES(?, ?, ?)",
                (book_name, author, quantity)
            )
            added += 1
    
    if added > 0:
        print(f"✓ Added {added} sample books to the library")
    else:
        print("✗ Sample books already exist")

    conn.commit()
    conn.close()
    print("\n✓ Database seeding complete!")

if __name__ == "__main__":
    seed_users()
