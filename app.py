import os
import math
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Importamos nuestro motor cuantitativo autónomo SHARP v22.0
from sharp_core import SharpQuantEngine

app = Flask(__name__)
app.secret_key = "sotelok_sharp_fortress_2026"

DB_NAME = "sotelok_final.db"

def inicializar_base_datos():
    """Inicializa la base de datos de manera segura."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correo TEXT UNIQUE,
                password TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error DB: {e}")

# Ruta principal del Radar Sharp / Inyección Fortress
@app.route('/analizar_sharp', methods=['POST'])
def analizar_sharp():
    try:
        # Recibimos los datos enviados desde la interfaz web
        data = request.json
        deporte = data.get('deporte', 'futbol_secundaria')
        equipo_local = data.get('local', 'Equipo Local')
        equipo_visitante = data.get('visitante', 'Equipo Visitante')
        
        # Métricas o promedios simulados/extraídos de la base de datos pública
        xG_local = float(data.get('xG_local', 1.75))
        xG_visitante = float(data.get('xG_visitante', 1.10))
        cuota_bookmaker = float(data.get('cuota', 1.90))

        # Instanciamos el motor analítico
        engine = SharpQuantEngine(sports_category=deporte)

        # 1. Ejecutar simulación estocástica masiva (Monte Carlo / Poisson)
        p_home, p_draw, p_away = engine.ejecutar_simulacion_monte_carlo(xG_local, xG_visitante)

        # 2. Generar el desglose de los 2 escenarios de alto valor y filtro Kelly
        resumen_escenarios = engine.generar_resumen_escenarios(
            local=equipo_local, 
            visitante=equipo_visitante, 
            prob_home=p_home, 
            prob_draw=p_draw, 
            prob_away=p_away, 
            cuota_bookmaker=cuota_bookmaker
        )

        # Retornamos el resultado en JSON listo para la interfaz
        return jsonify({
            "status": "success",
            "partido": f"{equipo_local} vs {equipo_visitante}",
            "probabilidades": {
                "local": round(p_home * 100, 1),
                "empate": round(p_draw * 100, 1),
                "visitante": round(p_away * 100, 1)
            },
            "escenarios_estrategicos": resumen_escenarios
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    inicializar_base_datos()
    app.run(host="0.0.0.0", port=5000, debug=True)
