import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

DATABASE = "pivotspend.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            surname TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        surname = request.form["surname"].strip()
        middle_name = request.form.get("middle_name", "").strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing:
            conn.close()
            return render_template("signup.html", error="Email already registered")

        hashed = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (surname, middle_name, last_name, email, password_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (surname, middle_name, last_name, email, hashed),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Wrong email or password")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))

    conn = get_db()
    transactions = conn.execute(
        "SELECT id, type, amount, description, date FROM transactions "
        "WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expense

    return render_template(
        "index.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
    )

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))

    transaction_type = request.form["type"]
    description = request.form["description"].strip()

    try:
        amount = float(request.form["amount"])
    except ValueError:
        return redirect(url_for("dashboard"))

    if transaction_type not in ("income", "expense") or amount <= 0 or description == "":
        return redirect(url_for("dashboard"))

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    conn.execute(
        "INSERT INTO transactions (user_id, type, amount, description, date) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, transaction_type, amount, description, today),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
    