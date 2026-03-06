from flask import Flask, send_file, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("players.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return send_file("app.html")


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

    players = []
    for r in rows:
        players.append(dict(r))

    return jsonify(players)


@app.route("/bid", methods=["POST"])
def bid():

    data = request.json
    player_id = data["player_id"]
    bid_amount = int(data["bid"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT current_bid FROM players WHERE id=?", (player_id,))
    current = cur.fetchone()[0]

    if bid_amount <= current:
        return jsonify({"error":"Bid must be higher"}),400

    cur.execute(
        "UPDATE players SET current_bid=? WHERE id=?",
        (bid_amount, player_id)
    )

    conn.commit()

    return jsonify({"success":True})


if __name__ == "__main__":

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    team TEXT,
    nationality TEXT,
    strike_rate REAL,
    base_price INTEGER,
    current_bid INTEGER
    )
    """)

    cur.execute("SELECT COUNT(*) FROM players")
    if cur.fetchone()[0] == 0:

        players = [
        ("Virat Kohli","RCB","Indian",138.5,50000,50000),
        ("Rohit Sharma","MI","Indian",130.1,50000,50000),
        ("Jos Buttler","RR","Overseas",149.3,50000,50000),
        ("David Warner","DC","Overseas",142.0,50000,50000)
        ]

        cur.executemany(
        "INSERT INTO players(name,team,nationality,strike_rate,base_price,current_bid) VALUES (?,?,?,?,?,?)",
        players
        )

        conn.commit()

    app.run(debug=True)