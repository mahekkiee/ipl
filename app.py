import os
import logging
from flask import Flask, jsonify, request, send_file
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ipl-auction")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    logger.info("Connecting to database")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def setup_database():
    try:
        conn = get_db()
        cur = conn.cursor()

        logger.info("Creating table if not exists")

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

        cur.execute("SELECT COUNT(*) FROM players")
        count = cur.fetchone()["count"]

        if count == 0:
            logger.info("Inserting seed players")

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

        logger.info("Database ready")

    except Exception as e:
        logger.exception("Database setup failed")


@app.route("/")
def index():
    return send_file("app.html")


@app.route("/script.js")
def script():
    return send_file("script.js")


@app.route("/players")
def players():
    try:
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

        cur.close()
        conn.close()

        return jsonify(rows)

    except Exception as e:
        logger.exception("Players endpoint failed")
        return jsonify({"error": str(e)}), 500


@app.route("/bid", methods=["POST"])
def bid():
    try:
        data = request.json
        player_id = data["player_id"]
        bid_amount = int(data["bid"])

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT current_bid FROM players WHERE id=%s", (player_id,))
        current = cur.fetchone()["current_bid"]

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

    except Exception as e:
        logger.exception("Bid endpoint failed")
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Check if server and database are working."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()

        return jsonify({
            "status": "ok",
            "database": "connected",
            "database_url_set": bool(DATABASE_URL)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "database": "failed",
            "error": str(e),
            "database_url_set": bool(DATABASE_URL)
        }), 500


@app.route("/debug")
def debug():
    """Return environment info for debugging."""
    return jsonify({
        "DATABASE_URL_exists": bool(DATABASE_URL),
        "DATABASE_URL_preview": DATABASE_URL[:30] + "..." if DATABASE_URL else None,
        "working_directory": os.getcwd(),
        "files": os.listdir(".")
    })


setup_database()

if __name__ == "__main__":
    app.run(debug=True)
