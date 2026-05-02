from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import os

app = Flask(__name__, template_folder="../templates", static_folder="../static")

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
    cur.execute('INSERT INTO gas_data (co2, o2, n2o, bacteria, status) VALUES (?, ?, ?, ?, ?)',
                (co2, o2, n2o, bacteria, status))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json
    co2 = int(data.get('co2', random.randint(400, 1200)))
    o2 = float(data.get('o2', random.uniform(19, 24)))
    n2o = int(data.get('n2o', random.randint(0, 30)))
    bacteria = int(data.get('bacteria', random.randint(0, 600)))
    
    status, message = analyze(co2, o2, n2o, bacteria)
    save_data(co2, o2, n2o, bacteria, status)
    
    return jsonify({
        'co2': co2,
        'o2': round(o2, 2),
        'n2o': n2o,
        'bacteria': bacteria,
        'status': status,
        'message': message
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
