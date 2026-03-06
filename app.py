import os
import logging
from flask import Flask, jsonify, request, send_file, session
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY","auction-secret")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ipl-auction")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def setup_database():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        name TEXT,
        team TEXT,
        nationality TEXT,
        strike_rate FLOAT,
        base_price INT,
        current_bid INT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bids(
        id SERIAL PRIMARY KEY,
        user_id INT,
        player_id INT,
        amount INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("SELECT COUNT(*) FROM players")
    if cur.fetchone()["count"] == 0:
        cur.execute("""
        INSERT INTO players(name,team,nationality,strike_rate,base_price,current_bid)
        VALUES
        ('Virat Kohli','RCB','Indian',138.5,50000,50000),
        ('Rohit Sharma','MI','Indian',130.2,50000,50000),
        ('Jos Buttler','RR','Overseas',149.1,50000,50000),
        ('David Warner','DC','Overseas',142.3,50000,50000)
        """)

    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def home():
    if "user_id" not in session:
        return send_file("login.html")
    return send_file("app.html")


@app.route("/script.js")
def js():
    return send_file("script.js")


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    password = generate_password_hash(data["password"])

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (username,password)
        )
        conn.commit()
    except:
        return jsonify({"error":"User exists"}),400

    return jsonify({"success":True})


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=%s",
        (data["username"],)
    )

    user = cur.fetchone()

    if not user or not check_password_hash(user["password"],data["password"]):
        return jsonify({"error":"Invalid login"}),401

    session["user_id"] = user["id"]

    return jsonify({"success":True})

@app.route("/login-page")
def login_page():
    return send_file("login.html")


@app.route("/register-page")
def register_page():
    return send_file("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success":True})


@app.route("/players")
def players():

    nationality = request.args.get("type")

    conn = get_db()
    cur = conn.cursor()

    if nationality == "Indian":
        cur.execute("SELECT * FROM players WHERE nationality='Indian'")
    elif nationality == "Overseas":
        cur.execute("SELECT * FROM players WHERE nationality='Overseas'")
    else:
        cur.execute("SELECT * FROM players")

    rows = cur.fetchall()

    return jsonify(rows)


@app.route("/bid", methods=["POST"])
def bid():

    if "user_id" not in session:
        return jsonify({"error":"Login required"}),401

    data = request.json
    player_id = data["player_id"]
    bid_amount = int(data["bid"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT current_bid FROM players WHERE id=%s",
        (player_id,)
    )

    current = cur.fetchone()["current_bid"]

    if bid_amount <= current:
        return jsonify({"error":"Bid must be higher"}),400

    cur.execute(
        "UPDATE players SET current_bid=%s WHERE id=%s",
        (bid_amount,player_id)
    )

    cur.execute(
        "INSERT INTO bids(user_id,player_id,amount) VALUES(%s,%s,%s)",
        (session["user_id"],player_id,bid_amount)
    )

    conn.commit()

    return jsonify({"success":True})


@app.route("/health")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","error":str(e)})


setup_database()

if __name__ == "__main__":
    app.run(debug=True)


