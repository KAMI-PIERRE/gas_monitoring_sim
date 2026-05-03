from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import os
import sys

def find_templates_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"),
        os.path.join(os.getcwd(), "templates"),
        "/var/task/templates",
        os.path.join(os.path.dirname(__file__), "..", "templates"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]

def find_static_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
        os.path.join(os.getcwd(), "static"),
        "/var/task/static",
        os.path.join(os.path.dirname(__file__), "..", "static"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = find_templates_dir()
STATIC_DIR = find_static_dir()

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR, static_url_path="/static")

@app.errorhandler(Exception)
def handle_error(e):
    print(f"Error: {e}", file=sys.stderr)
    return jsonify({"error": str(e), "type": type(e).__name__}), 500

def init_db():
    try:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS gas_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        co2 INTEGER,
        o2 REAL,
        n2o INTEGER,
        bacteria INTEGER,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database init error: {e}")

def analyze(co2, o2, n2o, bacteria):
    messages = []
    if o2 < 19.5:
        return "CRITICAL", "Oxygen Level Dangerous - Hypoxia Risk!"
    elif o2 > 23.5:
        return "CRITICAL", "Oxygen Level Dangerous - Fire Risk!"
    if co2 > 1000:
        messages.append("High CO2 Level")
    elif co2 > 800:
        messages.append("Elevated CO2 - Check Ventilation")
    if n2o > 25:
        messages.append("N2O Exposure Risk - Staff Safety!")
    elif n2o > 15:
        messages.append("Elevated N2O - Monitor Exposure")
    if bacteria > 500:
        messages.append("HIGH BACTERIAL COUNT - Sterilization Required!")
    elif bacteria > 200:
        messages.append("Bacterial Detection - Clean Room")
    elif bacteria > 100:
        messages.append("Low Bacterial Levels Detected")
    if messages:
        return "WARNING", ", ".join(messages)
    else:
        return "NORMAL", "Safe Environment - All Systems Normal"

def save_data(co2, o2, n2o, bacteria, status):
    try:
        init_db()
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute('INSERT INTO gas_data (co2, o2, n2o, bacteria, status) VALUES (?, ?, ?, ?, ?)',
                    (co2, o2, n2o, bacteria, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save data error: {e}")

def get_recent_data(limit=12):
    try:
        init_db()
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute('SELECT timestamp, co2, o2, n2o, bacteria, status FROM gas_data ORDER BY id DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        conn.close()
        return list(reversed(rows)) if rows else []
    except Exception as e:
        print(f"Get data error: {e}")
        return []

@app.route('/')
def index():
    try:
        if not os.path.exists(TEMPLATE_DIR):
            return jsonify({
                "error": "Template directory not found",
                "template_dir": TEMPLATE_DIR,
                "cwd": os.getcwd(),
                "base_dir": BASE_DIR,
                "file": __file__
            }), 500
        return render_template('index.html')
    except Exception as e:
        print(f"Index route error: {e}", file=sys.stderr)
        return jsonify({"error": str(e), "template_dir": TEMPLATE_DIR, "cwd": os.getcwd()}), 500

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.json
        co2 = int(data.get('co2', 400))
        o2 = float(data.get('o2', 21))
        n2o = int(data.get('n2o', 0))
        bacteria = int(data.get('bacteria', 0))

        level, message = analyze(co2, o2, n2o, bacteria)
        save_data(co2, o2, n2o, bacteria, level)
        return jsonify({
            'level': level,
            'message': message
        })
    except Exception as e:
        print(f"Update error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    try:
        rows = get_recent_data(12)
        labels = [row[0] for row in rows] if rows else []
        co2 = [row[1] for row in rows] if rows else []
        o2 = [row[2] for row in rows] if rows else []
        n2o = [row[3] for row in rows] if rows else []
        bacteria = [row[4] for row in rows] if rows else []
        status_list = [row[5] for row in rows] if rows else []
        status_counts = {
            'NORMAL': status_list.count('NORMAL'),
            'WARNING': status_list.count('WARNING'),
            'CRITICAL': status_list.count('CRITICAL')
        }
        latest = {
            'co2': co2[-1] if co2 else 0,
            'o2': o2[-1] if o2 else 0,
            'n2o': n2o[-1] if n2o else 0,
            'bacteria': bacteria[-1] if bacteria else 0
        }
        return jsonify({
            'labels': labels,
            'co2': co2,
            'o2': o2,
            'n2o': n2o,
            'bacteria': bacteria,
            'statusCounts': status_counts,
            'latest': latest
        })
    except Exception as e:
        print(f"History error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        co2 = int(data.get('co2', random.randint(400, 1200)))
        o2 = float(data.get('o2', random.uniform(19, 24)))
        n2o = int(data.get('n2o', random.randint(0, 30)))
        bacteria = int(data.get('bacteria', random.randint(0, 600)))
        status, message = analyze(co2, o2, n2o, bacteria)
        return jsonify({
            'co2': co2,
            'o2': round(o2, 2),
            'n2o': n2o,
            'bacteria': bacteria,
            'level': status,
            'message': message
        })
    except Exception as e:
        print(f"Simulate error: {e}")
        return jsonify({'error': str(e)}), 500

init_db()

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "template_dir": TEMPLATE_DIR,
        "exists": os.path.exists(TEMPLATE_DIR),
        "cwd": os.getcwd()
    })

if __name__ == '__main__':
    app.run(debug=True)
