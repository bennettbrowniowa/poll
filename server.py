import os, json, secrets, sqlite3
from flask import Flask, render_template, request, jsonify, abort, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DB = os.environ.get("DATABASE_PATH", "polls.db")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_current INTEGER DEFAULT 1
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER NOT NULL,
        station_id TEXT NOT NULL,
        choice INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    return conn

def current_poll(conn):
    row = conn.execute("SELECT * FROM polls WHERE is_current=1 ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        cur = conn.execute("INSERT INTO polls (is_current) VALUES (1)")
        conn.commit()
        return conn.execute("SELECT * FROM polls WHERE id=?", (cur.lastrowid,)).fetchone()
    return row

def counts(conn, poll_id):
    rows = conn.execute(
        "SELECT choice, COUNT(*) n FROM votes WHERE poll_id=? GROUP BY choice",
        (poll_id,)
    ).fetchall()
    d = {str(i): 0 for i in range(1, 6)}
    for r in rows:
        d[str(r["choice"])] = r["n"]
    return d

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def state():
    conn = db()
    poll = current_poll(conn)
    c = counts(conn, poll["id"])
    conn.close()
    return jsonify({"poll_id": poll["id"], "counts": c, "total": sum(c.values())})

@app.route("/api/history")
def history():
    conn = db()
    rows = conn.execute(
        "SELECT id, created_at FROM polls ORDER BY id ASC"
    ).fetchall()
    result = []
    for r in rows:
        c = counts(conn, r["id"])
        result.append({"id": r["id"], "created_at": r["created_at"],
                       "counts": c, "total": sum(c.values())})
    conn.close()
    return jsonify(result)

@app.route("/api/new", methods=["POST"])
def new_poll():
    conn = db()
    conn.execute("UPDATE polls SET is_current=0 WHERE is_current=1")
    cur = conn.execute("INSERT INTO polls (is_current) VALUES (1)")
    conn.commit()
    conn.close()
    return jsonify({"poll_id": cur.lastrowid})

@app.route("/api/vote", methods=["POST"])
def vote():
    data = request.get_json(silent=True) or {}
    try:
        choice = int(data.get("choice"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid choice"}), 400
    if choice not in range(1, 6):
        return jsonify({"error": "Invalid choice"}), 400

    # A persistent browser-generated station ID identifies the tablet.
    # It is deliberately not exposed as a station label.
    station = session.get("station_id")
    if not station:
        station = secrets.token_urlsafe(16)
        session["station_id"] = station

    conn = db()
    poll = current_poll(conn)

    # One tap = one vote. A station can vote repeatedly, once per student.
    conn.execute(
        "INSERT INTO votes (poll_id, station_id, choice) VALUES (?, ?, ?)",
        (poll["id"], station, choice)
    )
    conn.commit()
    c = counts(conn, poll["id"])
    conn.close()
    return jsonify({"ok": True, "counts": c, "total": sum(c.values())})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    db() .close()
    app.run(host="0.0.0.0", port=port)
