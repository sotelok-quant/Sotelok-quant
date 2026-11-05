import os
import math
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Importamos nuestro motor cuantitativo avanzado SHARP v22.0
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

# Ruta principal: Muestra nuestra interfaz visual estilo Radar Táctico
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para procesar el análisis cuantitativo avanzado y mercados múltiples
@app.route('/analizar_sharp', methods=['POST'])
def analizar_sharp():
    try:
        data = request.json
        deporte = data.get('deporte', 'futbol_secundaria')
        equipo_local = data.get('local', 'Equipo Local')
        equipo_visitante = data.get('visitante', 'Equipo Visitante')
        
        # Métricas flexibles (xG, carreras o puntos esperados según el deporte)
        val_local = float(data.get('xG_local', 1.75))
        val_visitante = float(data.get('xG_visitante', 1.10))
        cuota_bookmaker = float(data.get('cuota', 1.90))

        # Instanciamos el motor con la categoría seleccionada
        engine = SharpQuantEngine(sports_category=deporte)

        # Generamos los escenarios avanzados multimercado (FootyStats / Flashscore style)
        resumen_escenarios = engine.generar_resumen_escenarios(
            local=equipo_local, 
            visitante=equipo_visitante, 
            val_local=val_local, 
            val_visitante=val_visitante, 
            cuota=cuota_bookmaker
        )

        return jsonify({
            "status": "success",
            "partido": f"{equipo_local} vs {equipo_visitante}",
            "probabilidades": {
                "local": round(val_local / max(0.1, (val_local + val_visitante)) * 100, 1),
                "empate": 22.5,
                "visitante": round(val_visitante / max(0.1, (val_local + val_visitante)) * 100, 1)
            },
            "escenarios_estrategicos": resumen_escenarios
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    inicializar_base_datos()
    app.run(host="0.0.0.0", port=5000, debug=True)
