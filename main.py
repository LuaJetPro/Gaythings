from flask import Flask, request, jsonify
import sqlite3, time, os

app = Flask(__name__)

# Initialize DB (runs once)
def init_db():
    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys
                 (key TEXT PRIMARY KEY, expires INTEGER)''')
    conn.commit()
    conn.close()

# Root route to verify service is up
@app.route('/')
def index():
    return "KeySystemBackend is running!"

# Generate new key (for admin use)
@app.route('/generate', methods=['POST'])
def generate_key():
    import random, string
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    expires = int(time.time()) + (36 * 60 * 60)  # 36h

    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, expires) VALUES (?, ?)", (key, expires))
    conn.commit()
    conn.close()

    return jsonify({'key': key, 'expires_in_hours': 36})

# Verify key (called by your Roblox script)
@app.route('/verify', methods=['GET'])
def verify_key():
    # Optional: Referer check for bypass detection
    referer = request.headers.get('Referer','')
    if not referer.startswith("https://work.ink/"):
        return jsonify({'valid': False, 'reason': 'Bypass detected'}), 403

    user_key = request.args.get('key')
    if not user_key:
        return jsonify({'valid': False, 'reason': 'No key provided'})

    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute("SELECT expires FROM keys WHERE key=?", (user_key,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({'valid': False, 'reason': 'Key not found'})
    if int(time.time()) > row[0]:
        return jsonify({'valid': False, 'reason': 'Key expired'})
    return jsonify({'valid': True})

# Fire it up on the right port
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
