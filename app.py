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
        partidos = engine.obtener_partidos_en_vivo()
        return jsonify({"status": "success", "partidos": partidos})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/analizar_sharp', methods=['POST'])
def analizar_sharp():
    try:
        data = request.json
        deporte = data.get('deporte', 'futbol_secundaria')
        equipo_local = data.get('local', 'Real Sociedad')
        equipo_visitante = data.get('visitante', 'Lyon')
        
        val_local = float(data.get('xG_local', 1.85))
        val_visitante = float(data.get('xG_visitante', 1.10))
        cuota_bookmaker = float(data.get('cuota', 1.95))

        engine = SharpQuantEngine(sports_category=deporte, db_name=DB_NAME)
        resumen_escenarios = engine.generar_analisis_avanzado(
            local=equipo_local, 
            visitante=equipo_visitante, 
            val_local=val_local, 
            val_visitante=val_visitante, 
            cuota=cuota_bookmaker
        )

        total_val = max(0.1, val_local + val_visitante)
        p_empate = 22.5
        resto = 100.0 - p_empate
        p_local = round((val_local / total_val) * resto, 1)
        p_visitante = round(resto - p_local, 1)

        return jsonify({
            "status": "success",
            "partido": f"{equipo_local} vs {equipo_visitante}",
            "probabilidades": {
                "local": p_local,
                "empate": p_empate,
                "visitante": p_visitante
            },
            "escenarios_estrategicos": resumen_escenarios
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
