import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from sharp_core import SharpQuantEngine

app = Flask(__name__)
app.secret_key = "sotelok_sharp_fortress_2026"
DB_NAME = "sotelok_final.db"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/partidos_hoy', methods=['GET'])
def partidos_hoy():
    try:
        engine = SharpQuantEngine(db_name=DB_NAME)
        return jsonify({"status": "success", "partidos": engine.obtener_partidos_en_vivo()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/analizar_sharp', methods=['POST'])
def analizar_sharp():
    try:
        data = request.json
        local = data.get('local', 'Real Sociedad')
        visitante = data.get('visitante', 'Lyon')
        val_local = float(data.get('xG_local', 1.85))
        val_visitante = float(data.get('xG_visitante', 1.10))
        cuota = float(data.get('cuota', 1.95))

        engine = SharpQuantEngine(db_name=DB_NAME)
        resultado = engine.calcular_metricas_completas(local, visitante, val_local, val_visitante, cuota)

        return jsonify({"status": "success", **resultado})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
