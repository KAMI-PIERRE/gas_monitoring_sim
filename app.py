from flask import Flask, render_template, request, jsonify
import sqlite3
import random

app = Flask(__name__)

def init_db():
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
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO gas_data (co2,o2,n2o,bacteria,status) VALUES (?,?,?,?,?)",
    (co2, o2, n2o, bacteria, status))
    conn.commit()
    conn.close()


def get_recent_data(limit=12):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute('SELECT timestamp, co2, o2, n2o, bacteria, status FROM gas_data ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return list(reversed(rows))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/update", methods=["POST"])
def update():
    data = request.json
    co2 = int(data["co2"])
    o2 = float(data["o2"])
    n2o = int(data["n2o"])
    bacteria = int(data.get("bacteria", 0))
    level, message = analyze(co2, o2, n2o, bacteria)
    save_data(co2, o2, n2o, bacteria, level)
    return jsonify({"level": level, "message": message})

@app.route("/history")
def history():
    rows = get_recent_data(12)
    labels = [row[0] for row in rows]
    co2 = [row[1] for row in rows]
    o2 = [row[2] for row in rows]
    n2o = [row[3] for row in rows]
    bacteria = [row[4] for row in rows]
    status_list = [row[5] for row in rows]
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

@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.json
    mode = data.get("mode", "before")
    if mode == "before":
        co2 = random.randint(350, 600)
        o2 = round(random.uniform(20.5, 22.5), 1)
        n2o = random.randint(0, 5)
        bacteria = random.randint(20, 150)
    elif mode == "during":
        co2 = random.randint(600, 1200)
        o2 = round(random.uniform(19.0, 23.0), 1)
        n2o = random.randint(10, 30)
        bacteria = random.randint(50, 200)
    else:
        co2 = random.randint(400, 800)
        o2 = round(random.uniform(20.0, 22.0), 1)
        n2o = random.randint(0, 10)
        bacteria = random.randint(100, 400)
    level, message = analyze(co2, o2, n2o, bacteria)
    return jsonify({"co2": co2, "o2": o2, "n2o": n2o, "bacteria": bacteria, "level": level, "message": message})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)