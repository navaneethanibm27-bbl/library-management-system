# app.py

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "library_secret"

# ---------------- DATABASE ---------------- #

def connect_db():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    # Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    # Books Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_name TEXT,
        author TEXT,
        quantity INTEGER
    )
    """)

    # Issue Books Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS issued_books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        return_date TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
    )
    """)

    conn.commit()
    conn.close()

create_tables()

# ---------------- HOME ---------------- #

@app.route('/')
def home():
    return render_template("index_new.html")

# ---------------- REGISTER ---------------- #

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password), 'user')
            )
            conn.commit()
            return redirect('/login/user')

        except:
            return "Email already exists!"

    return render_template("register_new.html")

# ---------------- LOGIN ---------------- #

@app.route('/login')
def login_choice():
    return render_template("login_choice.html")

# User Login
@app.route('/login/user', methods=['GET', 'POST'])
def login_user():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND role=?",
            (email, 'user')
        )

        user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['name']
            session['user_id'] = user['id']
            session['role'] = 'user'
            return redirect('/dashboard')
        else:
            return "Invalid Email or Password"

    return render_template("login_user.html")

# Admin Login
@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND role=?",
            (email, 'admin')
        )

        user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['name']
            session['user_id'] = user['id']
            session['role'] = 'admin'
            return redirect('/admin-dashboard')
        else:
            return "Invalid Admin Credentials"

    return render_template("login_admin.html")

# ---------------- DASHBOARD ---------------- #

@app.route('/dashboard')
def dashboard():

    if 'user' not in session or session.get('role') != 'user':
        return redirect('/login/user')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books")
    books = cur.fetchall()

    # Get issued books for this user
    cur.execute(
        "SELECT * FROM issued_books WHERE student_name=?",
        (session['user'],)
    )
    issued = cur.fetchall()

    return render_template(
        "dashboard_user.html",
        books=books,
        issued=issued,
        user=session['user']
    )

# Admin Dashboard
@app.route('/admin-dashboard')
def admin_dashboard():

    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/login/admin')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books")
    books = cur.fetchall()

    cur.execute("SELECT COUNT(*) as count FROM issued_books")
    issued_count = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) as count FROM users WHERE role='user'")
    user_count = cur.fetchone()['count']

    return render_template(
        "admin_dashboard.html",
        books=books,
        issued_count=issued_count,
        user_count=user_count,
        admin=session['user']
    )

# ---------------- ADD BOOK ---------------- #

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():

    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/login/admin')

    if request.method == 'POST':
        book_name = request.form['book_name']
        author = request.form['author']
        quantity = request.form['quantity']

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO books(book_name,author,quantity) VALUES(?,?,?)",
            (book_name, author, quantity)
        )

        conn.commit()

        return redirect('/admin-dashboard')

    return render_template("add_book_new.html")

# ---------------- ISSUE BOOK ---------------- #

@app.route('/issue_book/<int:id>')
def issue_book(id):

    if 'user' not in session or session.get('role') != 'user':
        return redirect('/login/user')

    conn = connect_db()
    cur = conn.cursor()

    # Get Book
    cur.execute("SELECT * FROM books WHERE id=?", (id,))
    book = cur.fetchone()

    if not book:
        return redirect('/dashboard')

    if int(book['quantity'] or 0) > 0:

        # Save issue record
        cur.execute(
            "INSERT INTO issued_books(student_name,book_name) VALUES(?,?)",
            (session['user'], book['book_name'])
        )

        # Reduce quantity
        new_quantity = int(book['quantity']) - 1

        cur.execute(
            "UPDATE books SET quantity=? WHERE id=?",
            (new_quantity, id)
        )

        conn.commit()

    return redirect('/dashboard')

# ---------------- LOGOUT ---------------- #

@app.route('/logout')
def logout():
    role = session.get('role', 'user')
    session.clear()
    if role == 'admin':
        return redirect('/login/admin')
    return redirect('/login/user')

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)