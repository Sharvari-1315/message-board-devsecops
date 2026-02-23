from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import time

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@db:5432/messages")

def get_conn():
    """Try to connect to Postgres with retries."""
    for i in range(5):
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError:
            print("Database not ready, retrying...")
            time.sleep(3)
    raise Exception("Could not connect to database after retries")

def init_db():
    """Create messages table if it doesn't exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    text TEXT NOT NULL
                )
            """)
            conn.commit()

@app.route("/api/messages", methods=["GET"])
def get_messages():
    """Fetch all messages in ascending order, including ID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, text FROM messages ORDER BY id ASC;")
            rows = cur.fetchall()
    messages = [{"id": r[0], "user": r[1], "text": r[2]} for r in rows]
    return jsonify(messages)

@app.route("/api/messages", methods=["POST"])
def add_message():
    """Insert a new message into the database."""
    data = request.get_json()
    if "user" in data and "text" in data:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (username, text) VALUES (%s, %s) RETURNING id;",
                    (data["user"], data["text"])
                )
                new_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({"id": new_id, "user": data["user"], "text": data["text"]}), 201
    return jsonify({"error": "Invalid payload"}), 400

@app.route("/api/messages/<int:msg_id>", methods=["DELETE"])
def delete_message(msg_id):
    """Delete a message by ID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE id = %s RETURNING id;", (msg_id,))
            deleted = cur.fetchone()
            conn.commit()
    if deleted:
        return jsonify({"status": "deleted", "id": msg_id}), 200
    else:
        return jsonify({"error": "Message not found"}), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

