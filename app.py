import os
from flask import Flask, send_file, request, jsonify
import psycopg2

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@app.route("/")
def home():
    return send_file("app.html")


@app.route("/script.js")
def js():
    return send_file("script.js")


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
        players.append({
            "id": r[0],
            "name": r[1],
            "team": r[2],
            "nationality": r[3],
            "strike_rate": r[4],
            "base_price": r[5],
            "current_bid": r[6]
        })

    cur.close()
    conn.close()

    return jsonify(players)


@app.route("/bid", methods=["POST"])
def bid():

    data = request.json
    player_id = data["player_id"]
    bid_amount = int(data["bid"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT current_bid FROM players WHERE id=%s",
        (player_id,)
    )

    current = cur.fetchone()[0]

    if bid_amount <= current:
        return jsonify({"error": "Bid must be higher"}), 400

    cur.execute(
        "UPDATE players SET current_bid=%s WHERE id=%s",
        (bid_amount, player_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
