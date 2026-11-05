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

@app.route('/analizar_sharp', methods=['POST'])
def analizar_sharp():
    try:
        data = request.json
        deporte = data.get('deporte', 'futbol_secundaria')
        equipo_local = data.get('local', 'Equipo Local')
        equipo_visitante = data.get('visitante', 'Equipo Visitante')
        
        val_local = float(data.get('xG_local', 1.75))
        val_visitante = float(data.get('xG_visitante', 1.10))
        cuota_bookmaker = float(data.get('cuota', 1.90))

        # Instanciamos el motor con la base de datos real
        engine = SharpQuantEngine(sports_category=deporte, db_name=DB_NAME)

        # Generar los 2 escenarios con mayor probabilidad
        resumen_escenarios = engine.generar_analisis_avanzado(
            local=equipo_local, 
            visitante=equipo_visitante, 
            val_local=val_local, 
            val_visitante=val_visitante, 
            cuota=cuota_bookmaker
        )

        # Normalizar probabilidades para que sumen exacto el 100%
        total_val = max(0.1, val_local + val_visitante)
        is_basket = "basket" in deporte.lower() or "nba" in deporte.lower()
        
        if is_basket:
            p_local = round((val_local / total_val) * 100, 1)
            p_visitante = round(100.0 - p_local, 1)
            p_empate = 0.0
        else:
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
