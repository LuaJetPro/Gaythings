from flask import Flask, request, jsonify
import sqlite3
import time

app = Flask(__name__)

# Initialize DB (runs once)
def init_db():
    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys
                 (key TEXT PRIMARY KEY, expires INTEGER)''')
    conn.commit()
    conn.close()

# Generate new key (for you only)
@app.route('/generate', methods=['POST'])
def generate_key():
    import random, string
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    expires = int(time.time()) + (36 * 60 * 60)  # 36 hours from now

    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, expires) VALUES (?, ?)", (key, expires))
    conn.commit()
    conn.close()

    return jsonify({'key': key, 'expires_in_hours': 36})

# Verify key
@app.route('/verify', methods=['GET'])
def verify_key():
    # Check Referer header
    referer = request.headers.get('Referer')
    if referer is None or not referer.startswith("https://work.ink/"):
        return jsonify({'valid': False, 'reason': 'Bypass detected: Invalid Referer'})
    
    user_key = request.args.get('key')
    if not user_key:
        return jsonify({'valid': False, 'reason': 'No key provided'})

    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute("SELECT expires FROM keys WHERE key=?", (user_key,))
    result = c.fetchone()
    conn.close()

    if not result:
        return jsonify({'valid': False, 'reason': 'Key not found'})

    expires = result[0]
    if int(time.time()) > expires:
        return jsonify({'valid': False, 'reason': 'Key expired'})
    else:
        return jsonify({'valid': True})

init_db()
app.run(host="0.0.0.0", port=8080)
