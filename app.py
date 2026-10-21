import random
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

# ==========================================
# 1. MOTOR MATEMÁTICO & MODELOS
# ==========================================

def shin_implied_probability(cuota_l, cuota_v):
    inv_sum = (1/cuota_l) + (1/cuota_v)
    return (1 / cuota_l) / inv_sum

def monte_carlo_poisson(lambda_l, lambda_v, sims=3000):
    goles_l = [sum(1 for _ in range(int(lambda_l * 10)) if random.random() < (lambda_l / 10)) for _ in range(sims)]
    goles_v = [sum(1 for _ in range(int(lambda_v * 10)) if random.random() < (lambda_v / 10)) for _ in range(sims)]
    totales = [l + v for l, v in zip(goles_l, goles_v)]
    mas_1_5 = sum(1 for g in totales if g > 1.5) / sims
    mas_4_5 = sum(1 for g in totales if g > 4.5) / sims
    return mas_1_5 * 100, mas_4_5 * 100

def monte_carlo_normal(proj_l, proj_v, std_dev=11.0, sims=3000):
    return [random.gauss(proj_l, std_dev) + random.gauss(proj_v, std_dev) for _ in range(sims)]

def sotelok_ai_validator(prob_modelo, prob_shin, ev_porcentaje):
    desvio_shin = abs(prob_modelo - (prob_shin * 100))
    score_ia = (prob_modelo * 0.5) + (ev_porcentaje * 3.0) - (desvio_shin * 0.4)
    aprobado = (prob_modelo >= 56.0) and (ev_porcentaje >= 2.0) and (desvio_shin <= 15.0)
    return round(score_ia, 2), aprobado

# ==========================================
# 2. CARTELERA MULTIDEPORTE
# ==========================================

cartelera_general = [
    {
        "fecha": "20/10/2026", "hora_str": "16:00", "hora_num": 16.0,
        "deporte": "Tenis", "liga": "ATP Masters",
        "local": "Carlos Alcaraz", "visitante": "Jannik Sinner",
        "lambda_l": 1.65, "lambda_v": 2.15, "linea_spread": 22.5, "cuota": 1.75, "cuota_rival": 2.10
    },
    {
        "fecha": "20/10/2026", "hora_str": "19:00", "hora_num": 19.0,
        "deporte": "Futbol", "liga": "Champions League",
        "local": "Real Madrid", "visitante": "Bayern Múnich",
        "lambda_l": 2.20, "lambda_v": 1.30, "cuota": 1.62, "cuota_rival": 2.90
    },
    {
        "fecha": "20/10/2026", "hora_str": "20:30", "hora_num": 20.5,
        "deporte": "NBA", "liga": "NBA Regular Season",
        "local": "Golden State Warriors", "visitante": "LA Lakers",
        "lambda_l": 118.0, "lambda_v": 112.0, "linea_spread": 223.5, "cuota": 1.95, "cuota_rival": 1.90
    },
    {
        "fecha": "20/10/2026", "hora_str": "21:15", "hora_num": 21.25,
        "deporte": "NFL", "liga": "Monday Night Football",
        "local": "Kansas City Chiefs", "visitante": "Baltimore Ravens",
        "lambda_l": 27.5, "lambda_v": 24.0, "linea_spread": 49.5, "cuota": 1.90, "cuota_rival": 1.90
    }
]

def obtener_mejores_picks():
    oportunidades = []

    for partido in cartelera_general:
        deporte = partido["deporte"]
        cuota = partido["cuota"]
        prob_shin = shin_implied_probability(cuota, partido.get("cuota_rival", 2.00))

        if deporte in ["Futbol", "NHL"]:
            mc_15, mc_45 = monte_carlo_poisson(partido["lambda_l"], partido["lambda_v"])
            prob_final = mc_15 if deporte == "Futbol" else mc_45
            mercado = "⚽ Más de 1.5 Goles" if deporte == "Futbol" else "🏒 Más de 4.5 Goles"
            ev_pct = (((prob_final / 100) * cuota) - 1) * 100
            score_ia, apto = sotelok_ai_validator(prob_final, prob_shin, ev_pct)

            if apto:
                oportunidades.append({
                    "score": score_ia, "deporte": deporte, "liga": partido["liga"],
                    "partido": f"{partido['local']} vs {partido['visitante']}", "mercado": mercado,
                    "hora": partido["hora_str"], "prob": round(prob_final, 2), "cuota": cuota, "ev": round(ev_pct, 2)
                })

        elif deporte in ["NBA", "NFL"]:
            sims = monte_carlo_normal(partido["lambda_l"], partido["lambda_v"], std_dev=12.0 if deporte=="NBA" else 13.5)
            over_hits = sum(1 for total in sims if total > partido["linea_spread"])
            prob_final = (over_hits / len(sims)) * 100
            mercado = f"🏀 Over {partido['linea_spread']} Pts" if deporte == "NBA" else f"🏈 Over {partido['linea_spread']} Pts"
            ev_pct = (((prob_final / 100) * cuota) - 1) * 100
            score_ia, apto = sotelok_ai_validator(prob_final, prob_shin, ev_pct)

            if apto:
                oportunidades.append({
                    "score": score_ia, "deporte": deporte, "liga": partido["liga"],
                    "partido": f"{partido['local']} vs {partido['visitante']}", "mercado": mercado,
                    "hora": partido["hora_str"], "prob": round(prob_final, 2), "cuota": cuota, "ev": round(ev_pct, 2)
                })

        elif deporte == "Tenis":
            prob_final = round((1 / partido["lambda_l"]) / ((1 / partido["lambda_l"]) + (1 / partido["lambda_v"])) * 100, 2)
            mercado = f"🎾 Ganador: {partido['local']}"
            ev_pct = (((prob_final / 100) * cuota) - 1) * 100
            score_ia, apto = sotelok_ai_validator(prob_final, prob_shin, ev_pct)

            if apto:
                oportunidades.append({
                    "score": score_ia, "deporte": deporte, "liga": partido["liga"],
                    "partido": f"{partido['local']} vs {partido['visitante']}", "mercado": mercado,
                    "hora": partido["hora_str"], "prob": round(prob_final, 2), "cuota": cuota, "ev": round(ev_pct, 2)
                })

    oportunidades.sort(key=lambda x: x["score"], reverse=True)
    return oportunidades

# ==========================================
# 3. INTERFAZ WEB RESPONSIVA CON PWA (MANIFEST)
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
        h1 { color: #38bdf8; text-align: center; font-size: 22px; margin-bottom: 5px; }
        .sub { text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 20px; }
        .card { background: #1e293b; border-radius: 10px; padding: 15px; margin-bottom: 12px; border-left: 4px solid #38bdf8; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .tag { background: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .match { font-size: 16px; font-weight: bold; margin: 8px 0; }
        .stats { font-size: 13px; color: #cbd5e1; }
        .ev { color: #4ade80; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🧠 SOTELOK QUANT SUITE</h1>
    <div class="sub">Panel Cuantitativo & IA (+EV) en la Nube</div>
    
    {% for item in resultados %}
    <div class="card">
        <span class="tag">{{ item.deporte }} | {{ item.liga }}</span>
        <div class="match">⚔️ {{ item.partido }}</div>
        <div class="stats">
            🎯 <b>Mercado:</b> {{ item.mercado }} | ⏰ {{ item.hora }}<br>
            📈 <b>Probabilidad:</b> {{ item.prob }}% | 💰 <b>Cuota:</b> {{ item.cuota }}<br>
            🚀 <b>+EV Esperado:</b> <span class="ev">+{{ item.ev }}%</span> | ⭐ <b>Score IA:</b> {{ item.score }} pts
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
    mejores = obtener_mejores_picks()
    return render_template_string(HTML_TEMPLATE, resultados=mejores)

@app.route('/manifest.json')
def manifest():
    return app.response_class(MANIFEST_JSON, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
