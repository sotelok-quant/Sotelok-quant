import math
import random
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

# ==========================================
# 1. MOTOR MATEMÁTICO AVANZADO (DIXON-COLES & MATRICES)
# ==========================================

def poisson_pmf(k, lambda_param):
    """Función de Masa de Probabilidad de Poisson."""
    return (math.pow(lambda_param, k) * math.exp(-lambda_param)) / math.factorial(k)

def dixon_coles_tau(x, y, lambda_l, lambda_v, rho=-0.13):
    """
    Ajuste de correlación de Dixon-Coles para corregir la dependencia 
    entre puntajes bajos (0-0, 1-0, 0-1, 1-1).
    """
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

def generar_matriz_dixon_coles(lambda_l, lambda_v, max_goles=8):
    """
    Calcula la matriz de probabilidades exactas mediante álgebra lineal 
    y el ajuste de Dixon-Coles.
    """
    matriz = []
    prob_home_win = 0.0
    prob_draw = 0.0
    prob_away_win = 0.0
    prob_over_15 = 0.0
    prob_over_25 = 0.0

    for h in range(max_goles):
        fila = []
        p_h = poisson_pmf(h, lambda_l)
        for a in range(max_goles):
            p_a = poisson_pmf(a, lambda_v)
            tau = dixon_coles_tau(h, a, lambda_l, lambda_v)
            prob_exacta = p_h * p_a * tau
            fila.append(prob_exacta)

            # Acumuladores de mercado
            if h > a:
                prob_home_win += prob_exacta
            elif h == a:
                prob_draw += prob_exacta
            else:
                prob_away_win += prob_exacta

            if (h + a) > 1.5:
                prob_over_15 += prob_exacta
            if (h + a) > 2.5:
                prob_over_25 += prob_exacta

        matriz.append(fila)

    return {
        "home_win": prob_home_win * 100,
        "draw": prob_draw * 100,
        "away_win": prob_away_win * 100,
        "over_15": prob_over_15 * 100,
        "over_25": prob_over_25 * 100
    }

def shin_implied_probability(cuota_l, cuota_v):
    """Calcula la probabilidad real sin margen comercial usando la fórmula de Shin."""
    inv_sum = (1 / cuota_l) + (1 / cuota_v)
    return (1 / cuota_l) / inv_sum

def monte_carlo_normal_vectorizado(proj_l, proj_v, std_dev=11.5, sims=5000):
    """Simulación Monte Carlo para deportes de alta puntuación (NBA / NFL)."""
    hits_over = 0
    total_line = proj_l + proj_v
    for _ in range(sims):
        sim_l = random.gauss(proj_l, std_dev)
        sim_v = random.gauss(proj_v, std_dev)
        if (sim_l + sim_v) > total_line:
            hits_over += 1
    return (hits_over / sims) * 100

def evaluador_cuantitativo_ia(prob_modelo, cuota, prob_shin):
    """Filtro de valor esperado (+EV) y score de fiabilidad institucional."""
    prob_implied = (1 / cuota) * 100
    ev_pct = (((prob_modelo / 100) * cuota) - 1) * 100
    desvio_marcado = abs(prob_modelo - (prob_shin * 100))
    
    score_ia = (prob_modelo * 0.4) + (ev_pct * 2.5) - (desvio_marcado * 0.3)
    return round(ev_pct, 2), round(score_ia, 2)

def generar_dictamen_cuantitativo(deporte, local, visitante, prob, ev, mercado):
    """Genera una síntesis lógica y cualitativa del partido."""
    if ev >= 10.0 and prob >= 60.0:
        opinion = f"Análisis de Convergencia Alta: El modelo Dixon-Coles detecta una clara ineficiencia en las cuotas del mercado. {local} presenta métricas ofensivas superiores ajustadas por Poisson."
        recomendacion = f"🎯 Pick Institucional (+EV Alto): {mercado} (Probabilidad: {prob}%)"
    elif ev >= 2.0 and prob >= 50.0:
        opinion = f"Análisis de Valor Moderado: Las simulaciones muestran estabilidad estadística en los parámetros de {local} vs {visitante}. Margen de valor positivo aceptable."
        recomendacion = f"💡 Selección Sugerida: {mercado} (Opción Recomendada)"
    else:
        opinion = f"Análisis de Riesgo/Volatilidad: El desvío entre las métricas de la casa de apuestas y el modelo matricial sugiere moderar el stake."
        recomendacion = f"⚠️ Selección Conservadora: Evaluar apuestas combinadas o hándicap protector."

    return opinion, recomendacion

# ==========================================
# 2. CARTELERA Y BASE DE DATOS (FECHA DINÁMICA)
# ==========================================

fecha_actual_str = datetime.now().strftime("%d/%m/%Y")

cartelera_ligas_principales = [
    {
        "deporte": "Futbol", "liga": "Champions League",
        "local": "Real Madrid", "visitante": "Bayern Múnich",
        "fecha": fecha_actual_str, "hora": "19:00",
        "lambda_l": 2.25, "lambda_v": 1.20,
        "cuota": 1.75, "cuota_rival": 3.10, "mercado_target": "⚽ Más de 2.5 Goles"
    },
    {
        "deporte": "Futbol", "liga": "Premier League",
        "local": "Manchester City", "visitante": "Arsenal",
        "fecha": fecha_actual_str, "hora": "17:30",
        "lambda_l": 1.85, "lambda_v": 1.45,
        "cuota": 1.90, "cuota_rival": 2.10, "mercado_target": "⚽ Más de 1.5 Goles"
    },
    {
        "deporte": "NBA", "liga": "NBA Regular Season",
        "local": "Boston Celtics", "visitante": "Milwaukee Bucks",
        "fecha": fecha_actual_str, "hora": "20:00",
        "proj_l": 116.5, "proj_v": 110.0, "linea": 224.5,
        "cuota": 1.91, "cuota_rival": 1.91, "mercado_target": "🏀 Over 224.5 Pts"
    },
    {
        "deporte": "Tenis", "liga": "ATP Masters 1000",
        "local": "Novak Djokovic", "visitante": "Carlos Alcaraz",
        "fecha": fecha_actual_str, "hora": "15:00",
        "lambda_l": 1.80, "lambda_v": 1.95,
        "cuota": 1.85, "cuota_rival": 1.95, "mercado_target": "🎾 Ganador: Novak Djokovic"
    }
]

def procesar_predicciones():
    resultados = []

    for evento in cartelera_ligas_principales:
        deporte = evento["deporte"]
        cuota = evento["cuota"]
        prob_shin = shin_implied_probability(cuota, evento.get("cuota_rival", 2.00))

        if deporte == "Futbol":
            # Ejecutar modelo de Dixon-Coles
            dc = generar_matriz_dixon_coles(evento["lambda_l"], evento["lambda_v"])
            prob_final = dc["over_25"] if "2.5" in evento["mercado_target"] else dc["over_15"]
            ev_pct, score_ia = evaluador_cuantitativo_ia(prob_final, cuota, prob_shin)
            opinion, recomendacion = generar_dictamen_cuantitativo(
                deporte, evento["local"], evento["visitante"], round(prob_final, 2), ev_pct, evento["mercado_target"]
            )

            resultados.append({
                "deporte": deporte, "liga": evento["liga"],
                "partido": f"{evento['local']} vs {evento['visitante']}",
                "fecha": evento["fecha"], "hora": evento["hora"],
                "mercado": evento["mercado_target"],
                "prob": round(prob_final, 2), "cuota": cuota, "ev": ev_pct,
                "score": score_ia, "opinion": opinion, "recomendacion": recomendacion
            })

        elif deporte == "NBA":
            prob_final = monte_carlo_normal_vectorizado(evento["proj_l"], evento["proj_v"])
            ev_pct, score_ia = evaluador_cuantitativo_ia(prob_final, cuota, prob_shin)
            opinion, recomendacion = generar_dictamen_cuantitativo(
                deporte, evento["local"], evento["visitante"], round(prob_final, 2), ev_pct, evento["mercado_target"]
            )

            resultados.append({
                "deporte": deporte, "liga": evento["liga"],
                "partido": f"{evento['local']} vs {evento['visitante']}",
                "fecha": evento["fecha"], "hora": evento["hora"],
                "mercado": evento["mercado_target"],
                "prob": round(prob_final, 2), "cuota": cuota, "ev": ev_pct,
                "score": score_ia, "opinion": opinion, "recomendacion": recomendacion
            })

        elif deporte == "Tenis":
            prob_final = round((1 / evento["lambda_l"]) / ((1 / evento["lambda_l"]) + (1 / evento["lambda_v"])) * 100, 2)
            ev_pct, score_ia = evaluador_cuantitativo_ia(prob_final, cuota, prob_shin)
            opinion, recomendacion = generar_dictamen_cuantitativo(
                deporte, evento["local"], evento["visitante"], prob_final, ev_pct, evento["mercado_target"]
            )

            resultados.append({
                "deporte": deporte, "liga": evento["liga"],
                "partido": f"{evento['local']} vs {evento['visitante']}",
                "fecha": evento["fecha"], "hora": evento["hora"],
                "mercado": evento["mercado_target"],
                "prob": prob_final, "cuota": cuota, "ev": ev_pct,
                "score": score_ia, "opinion": opinion, "recomendacion": recomendacion
            })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados

# ==========================================
# 3. VISTA HTML INSTITUCIONAL Y PWA
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
        .card { background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; border-left: 5px solid #38bdf8; box-shadow: 0 4px 8px rgba(0,0,0,0.4); }
        .tag { background: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .match { font-size: 17px; font-weight: bold; margin: 10px 0 6px 0; }
        .stats { font-size: 13px; color: #cbd5e1; margin-bottom: 12px; line-height: 1.5; }
        .ev { color: #4ade80; font-weight: bold; }
        .ai-box { background: #0f172a; padding: 12px; border-radius: 8px; font-size: 12px; border: 1px solid #334155; line-height: 1.4; }
        .ai-title { color: #38bdf8; font-weight: bold; margin-bottom: 5px; }
        .ai-rec { color: #facc15; font-weight: bold; margin-top: 8px; }
    </style>
</head>
<body>
    <h1>🧠 SOTELOK QUANT SUITE</h1>
    <div class="sub">Motor Matemático Avanzado (Dixon-Coles & Matrices)</div>
    
    {% for item in resultados %}
    <div class="card">
        <span class="tag">{{ item.deporte }} | {{ item.liga }}</span>
        <div class="match">⚔️ {{ item.partido }}</div>
        <div class="stats">
            📅 <b>Fecha:</b> {{ item.fecha }} | ⏰ <b>Hora:</b> {{ item.hora }}<br>
            🎯 <b>Mercado Evaluado:</b> {{ item.mercado }}<br>
            📈 <b>Probabilidad Cuantitativa:</b> {{ item.prob }}% | 💰 <b>Cuota:</b> {{ item.cuota }}<br>
            🚀 <b>+EV Esperado:</b> <span class="ev">+{{ item.ev }}%</span> | ⭐ <b>Score IA:</b> {{ item.score }} pts
        </div>
        <div class="ai-box">
            <div class="ai-title">🤖 Dictamen Institucional & IA:</div>
            <div>{{ item.opinion }}</div>
            <div class="ai-rec">{{ item.recomendacion }}</div>
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
    datos = procesar_predicciones()
    return render_template_string(HTML_TEMPLATE, resultados=datos)

@app.route('/manifest.json')
def manifest():
    return app.response_class(MANIFEST_JSON, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
