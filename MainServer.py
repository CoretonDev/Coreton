from flask import Flask, request, jsonify
import sqlite3
import bcrypt
import os

app = Flask(__name__)

# This creates the database in the exact same folder as this script
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Users Table (Accounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password BLOB NOT NULL,
        name TEXT, age TEXT, email TEXT
    )""")
    
    # 2. Friends Table (Relationships)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1 TEXT NOT NULL,
        user2 TEXT NOT NULL,
        UNIQUE(user1, user2)
    )""")
    
    # 3. Messages Table (Global Chat History)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    
    conn.commit()
    conn.close()
    print(f"\n[DEBUG] Server Database is ready and located at: {DB_FILE}")

# ------------------- ACCOUNT ROUTES -------------------

@app.route('/register', methods=['POST'])
def register():
    print(f"\n[DEBUG] REGISTRATION DATA: {request.json}")
    data = request.json
    
    u = data.get('username')
    p = data.get('password')
    
    if not u or not p:
        return jsonify({"error": "Username and Password required"}), 400

    hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt())
    
    conn = sqlite3.connect(DB_FILE); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password, name, age, email) VALUES (?, ?, ?, ?, ?)", 
                   (u, hashed, data.get('name', ''), data.get('age', ''), data.get('email', '')))
        conn.commit()
        print(f"[DEBUG] SUCCESS: User '{u}' registered.")
        return jsonify({"status": "Success"}), 200
    except sqlite3.IntegrityError:
        print(f"[DEBUG] ERROR: Registration failed. '{u}' already exists.")
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    print(f"\n[DEBUG] LOGIN ATTEMPT: {request.json}")
    data = request.json
    u = data.get('username')
    
    if not u: 
        return jsonify({"error": "Missing username"}), 400
    
    conn = sqlite3.connect(DB_FILE); cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (u,))
    row = cur.fetchone(); conn.close()
    
    if row:
        pw = row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]
        print(f"[DEBUG] SUCCESS: '{u}' found. Sending verification data.")
        return jsonify({"password": pw}), 200
        
    print(f"[DEBUG] ERROR: '{u}' not found.")
    return jsonify({"error": "User not found"}), 404

# ------------------- SYNC ROUTES (NEW) -------------------

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    s = data.get('sender')
    r = data.get('receiver')
    m = data.get('message')
    
    print(f"[DEBUG] MESSAGE SENT: {s} -> {r}: {m}")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (s, r, m))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "Sent"}), 200

@app.route('/get_messages/<u1>/<u2>', methods=['GET'])
def get_messages(u1, u2):
    conn = sqlite3.connect(DB_FILE); cur = conn.cursor()
    # Grabs the conversation between these two specific users in chronological order
    cur.execute("""
        SELECT sender, message FROM messages 
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) 
        ORDER BY timestamp ASC
    """, (u1, u2, u2, u1))
    
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/get_friends/<username>', methods=['GET'])
def get_friends(username):
    conn = sqlite3.connect(DB_FILE); cur = conn.cursor()
    # Looks for any relationship where the user is either user1 or user2
    cur.execute("""
        SELECT user2 FROM friends WHERE user1 = ? 
        UNION 
        SELECT user1 FROM friends WHERE user2 = ?
    """, (username, username))
    
    res = [r[0] for r in cur.fetchall()]
    conn.close()
    return jsonify(res)

@app.route('/add_friend', methods=['POST'])
def add_friend():
    data = request.json
    u1 = data.get('user1')
    u2 = data.get('user2')
    
    print(f"[DEBUG] ADD FRIEND: {u1} added {u2}")
    
    conn = sqlite3.connect(DB_FILE); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO friends (user1, user2) VALUES (?, ?)", (u1, u2))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "Added"}), 200

# ------------------- SERVER STARTUP -------------------

if __name__ == '__main__':
    init_db()
    print("\n[DEBUG] Server is online and listening on Port 5000!")
    app.run(host='0.0.0.0', port=5000)
