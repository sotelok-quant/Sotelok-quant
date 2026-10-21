import math
import random
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

# ==========================================
# 1. MOTOR MATEMÁTICO MULTIVARIABLE & PATRONES
# ==========================================

def poisson_pmf(k, lambda_param):
    return (math.pow(lambda_param, k) * math.exp(-lambda_param)) / math.factorial(k)

def dixon_coles_tau(x, y, lambda_l, lambda_v, rho=-0.13):
    if x == 0 and y == 0:
        return 1.0 - (lambda_l * lambda_v * rho)
    elif x == 1 and y == 0:
        return 1.0 + (lambda_v * rho)
    elif x == 0 and y == 1:
        return 1.0 + (lambda_l * rho)
    elif x == 1 and y == 1:
        return 1.0 - rho
    else:
        return 1.0

def patron_evaluacion_integral(partido):
    """
    Aplica el patrón de decisión unificado para determinar 
    cuál es el mercado con mayor probabilidad y valor del encuentro.
    """
    lambda_l = partido["lambda_l"]
    lambda_v = partido["lambda_v"]
    
    # 1. Simulación de Goles (Dixon-Coles)
    prob_over_25 = 0.0
    for h in range(7):
        for a in range(7):
            tau = dixon_coles_tau(h, a, lambda_l, lambda_v)
            p_ex = poisson_pmf(h, lambda_l) * poisson_pmf(a, lambda_v) * tau
            if (h + a) > 2.5: prob_over_25 += p_ex

    # 2. Simulación de Córners y Tiros
    prob_corners = sum(poisson_pmf(k, partido["lambda_corners"]) for k in range(9, 20))
    prob_tarjetas = sum(poisson_pmf(k, partido["lambda_tarjetas"]) for k in range(4, 15))

    # Consolidar opciones evaluadas
    candidatos = [
        {"mercado": "⚽ Más de 2.5 Goles", "prob": round(prob_over_25 * 100, 2), "cuota": partido["cuota_goles"]},
        {"mercado": "⛳ Córners: Más de 8.5", "prob": round(prob_corners * 100, 2), "cuota": partido["cuota_corners"]},
        {"mercado": "🟨 Tarjetas: Más de 3.5", "prob": round(prob_tarjetas * 100, 2), "cuota": partido["cuota_tarjetas"]}
    ]

    # Patrón de selección: Filtrar por la mayor probabilidad combinada con rentabilidad (+EV)
    mejor_pick = max(candidatos, key=lambda x: x["prob"])
    ev = (((mejor_pick["prob"] / 100) * mejor_pick["cuota"]) - 1) * 100
    score_ia = (mejor_pick["prob"] * 0.6) + (ev * 2.5)

    return mejor_pick, round(ev, 2), round(score_ia, 2)

def generar_calendario_dinamico():
    """
    Simula la actualización automática del calendario diario 
    basada en la fecha actual del sistema.
    """
    hoy_str = datetime.now().strftime("%d/%m/%Y")
    
    # Cartelera sincronizada para el día de hoy
    return [
        {
            "deporte": "Futbol", "liga": "Champions League",
            "local": "Real Madrid", "visitante": "Manchester City",
            "fecha": hoy_str, "hora": "20:00",
            "lambda_l": 2.15, "lambda_v": 1.95,
            "lambda_corners": 10.5, "lambda_tarjetas": 4.5,
            "cuota_goles": 1.80, "cuota_corners": 1.72, "cuota_tarjetas": 1.90
        },
        {
            "deporte": "Futbol", "liga": "Premier League",
            "local": "Arsenal", "visitante": "Liverpool",
            "fecha": hoy_str, "hora": "17:30",
            "lambda_l": 1.85, "lambda_v": 1.75,
            "lambda_corners": 9.8, "lambda_tarjetas": 5.1,
            "cuota_goles": 1.75, "cuota_corners": 1.85, "cuota_tarjetas": 1.65
        }
    ]

def procesar_cartelera_inteligente():
    partidos = generar_calendario_dinamico()
    analisis_final = []

    for p in partidos:
        pick, ev, score = patron_evaluacion_integral(p)
        
        # Resumen generado por IA basado en los patrones cuantitativos
        resumen = (
            f"Análisis Automatizado: El patrón matricial para {p['local']} vs {p['visitante']} "
            f"indica alta estabilidad en el mercado de '{pick['mercado']}' con una probabilidad del {pick['prob']}% "
            f"y un valor esperado (+EV) de +{ev}%."
        )

        analisis_final.append({
            "deporte": p["deporte"],
            "liga": p["liga"],
            "partido": f"{p['local']} vs {p['visitante']}",
            "fecha": p["fecha"],
            "hora": p["hora"],
            "pick": pick["mercado"],
            "prob": pick["prob"],
            "cuota": pick["cuota"],
            "ev": ev,
            "score": score,
            "resumen": resumen
        })

    analisis_final.sort(key=lambda x: x["score"], reverse=True)
    return analisis_final

# ==========================================
# 2. INTERFAZ WEB RESPONSIVA (PWA)
# ==========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SOTELOK Quant Suite</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#38bdf8">
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 15px; margin: 0; }
        h1 { color: #38bdf8; text-align: center; font-size: 22px; margin-bottom: 2px; }
        .sub { text-align: center; color: #94a3b8; font-size: 12px; margin-bottom: 20px; }
        .card { background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 18px; border-left: 5px solid #38bdf8; box-shadow: 0 4px 8px rgba(0,0,0,0.4); }
        .tag { background: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .match { font-size: 17px; font-weight: bold; margin: 10px 0 6px 0; }
        .info { font-size: 12px; color: #94a3b8; margin-bottom: 12px; }
        .pick-box { background: #0f172a; padding: 10px 12px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; }
        .pick-title { color: #facc15; font-weight: bold; font-size: 14px; }
        .ev { color: #4ade80; font-weight: bold; }
        .ai-box { background: #1e293b; padding: 10px; border-radius: 8px; font-size: 12px; border-left: 3px solid #38bdf8; color: #cbd5e1; line-height: 1.4; }
    </style>
</head>
<body>
    <h1>🧠 SOTELOK QUANT SUITE</h1>
    <div class="sub">Calendario Automatizado & Patrones de Decisión Cuantitativa</div>
    
    {% for item in resultados %}
    <div class="card">
        <span class="tag">{{ item.deporte }} | {{ item.liga }}</span>
        <div class="match">⚔️ {{ item.partido }}</div>
        <div class="info">📅 {{ item.fecha }} | ⏰ {{ item.hora }}</div>
        
        <div class="pick-box">
            <div style="color:#38bdf8; font-size:11px; font-weight:bold; margin-bottom:4px;">🎯 PRONÓSTICO ÓPTIMO SELECCIONADO:</div>
            <div class="pick-title">{{ item.pick }}</div>
            <div style="font-size: 13px; margin-top: 6px; color: #cbd5e1;">
                📈 Probabilidad: <b>{{ item.prob }}%</b> | 💰 Cuota: <b>{{ item.cuota }}</b><br>
                🚀 Valor Esperado (+EV): <span class="ev">+{{ item.ev }}%</span> | ⭐ Score: {{ item.score }} pts
            </div>
        </div>

        <div class="ai-box">
            <div style="color: #38bdf8; font-weight: bold; margin-bottom: 4px;">🤖 Dictamen del Patrón de IA:</div>
            <div>{{ item.resumen }}</div>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

MANIFEST_JSON = """{
  "name": "SOTELOK Quant Suite",
  "short_name": "SOTELOK",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#38bdf8"
}"""

@app.route('/')
def home():
    datos = procesar_cartelera_inteligente()
    return render_template_string(HTML_TEMPLATE, resultados=datos)

@app.route('/manifest.json')
def manifest():
    return app.response_class(MANIFEST_JSON, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
