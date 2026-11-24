import os
import math
from contextlib import contextmanager
from datetime import datetime

import psycopg2
import psycopg2.extras
import psycopg2.errors
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")
app.secret_key = SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

@contextmanager
def db_cursor():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                surname TEXT NOT NULL,
                middle_name TEXT,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                type TEXT NOT NULL,
                amount NUMERIC(14, 2) NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)

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

        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters")

        hashed = generate_password_hash(password)

        try:
            with db_cursor() as cur:
                cur.execute(
                    "INSERT INTO users (surname, middle_name, last_name, email, password_hash) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (surname, middle_name, last_name, email, hashed),
                )
        except psycopg2.errors.UniqueViolation:
            return render_template("signup.html", error="Email already registered")

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        with db_cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

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

    with db_cursor() as cur:
        cur.execute(
            "SELECT id, type, amount, description, date FROM transactions "
            "WHERE user_id = %s ORDER BY id DESC",
            (user_id,),
        )
        transactions = cur.fetchall()

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
        amount = round(float(request.form["amount"]), 2)
    except ValueError:
        return redirect(url_for("dashboard"))

    if (
        transaction_type not in ("income", "expense")
        or not math.isfinite(amount)
        or amount <= 0
        or amount > 999_999_999
        or description == ""
    ):
        return redirect(url_for("dashboard"))

    today = datetime.now().strftime("%Y-%m-%d")

    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO transactions (user_id, type, amount, description, date) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, transaction_type, amount, description, today),
        )

    return redirect(url_for("dashboard"))

@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))

    with db_cursor() as cur:
        cur.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)