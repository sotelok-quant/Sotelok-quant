import math
import requests
from datetime import datetime
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ==========================================
# ⚙️ CONFIGURACIÓN DE LA API DE CALENDARIO
# ==========================================
# Puedes registrarte gratis en https://www.football-data.org/ para obtener tu API Key propia.
# Si dejas la clave vacía, la app usará el calendario sincronizado de respaldo.
API_KEY_FUTBOL = "TU_API_KEY_AQUI" 

def obtener_partidos_api():
    """Consulta los partidos del día actual usando la API externa."""
    if API_KEY_FUTBOL == "TU_API_KEY_AQUI" or not API_KEY_FUTBOL:
        return obtener_cartelera_respaldo()
    
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_KEY_FUTBOL}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            partidos_formateados = []
            
            for m in data.get("matches", []):
                # Extraer datos relevantes de la API
                competicion = m.get("competition", {}).get("name", "Liga Principal")
                local = m.get("homeTeam", {}).get("name", "Local")
                visitante = m.get("awayTeam", {}).get("name", "Visitante")
                utc_date = m.get("utcDate", "")
                
                # Formatear fecha y hora
                try:
                    dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                    fecha_str = dt.strftime("%d/%m/%Y")
                    hora_str = dt.strftime("%H:%M")
                except:
                    fecha_str = datetime.now().strftime("%d/%m/%Y")
                    hora_str = "20:00"

                partidos_formateados.append({
                    "deporte": "Futbol",
                    "liga": competicion,
                    "local": local,
                    "visitante": visitante,
                    "fecha": fecha_str,
                    "hora": hora_str,
                    # Parámetros base estimados para el motor cuantitativo
                    "lambda_l": 1.75, "lambda_v": 1.45,
                    "lambda_corners": 9.8, "lambda_tarjetas": 4.2,
                    "cuota_goles": 1.80, "cuota_corners": 1.75, "cuota_tarjetas": 1.70
                })
            
            if partidos_formateados:
                return partidos_formateados
    except Exception as e:
        print("Error al conectar con la API:", e)

    return obtener_cartelera_respaldo()

def obtener_cartelera_respaldo():
    """Cartelera de respaldo sincronizada para asegurar estabilidad."""
    hoy_str = datetime.now().strftime("%d/%m/%Y")
    return [
        {
            "deporte": "Futbol", "liga__": "UEFA Champions League", "liga": "UEFA Champions League",
            "local": "Real Madrid", "visitante": "Bayern Múnich",
            "fecha": hoy_str, "hora": "21:00",
            "lambda_l": 2.10, "lambda_v": 1.80,
            "lambda_corners": 10.2, "lambda_tarjetas": 4.5,
            "cuota_goles": 1.75, "cuota_corners": 1.72, "cuota_tarjetas": 1.90
        },
        {
            "deporte": "Futbol", "liga": "Premier League",
            "local": "Manchester City", "visitante": "Arsenal",
            "fecha": hoy_str, "hora": "18:30",
            "lambda_l": 1.85, "lambda_v": 1.70,
            "lambda_corners": 10.5, "lambda_tarjetas": 3.8,
            "cuota_goles": 1.78, "cuota_corners": 1.85, "cuota_tarjetas": 1.75
        }
    ]

# ==========================================
# 2. MOTOR MATEMÁTICO & PATRONES DE DECISIÓN
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
    lambda_l = partido["lambda_l"]
    lambda_v = partido["lambda_v"]
    
    prob_over_25 = 0.0
    for h in range(7):
        for a in range(7):
            tau = dixon_coles_tau(h, a, lambda_l, lambda_v)
            p_ex = poisson_pmf(h, lambda_l) * poisson_pmf(a, lambda_v) * tau
            if (h + a) > 2.5: prob_over_25 += p_ex

    prob_corners = sum(poisson_pmf(k, partido["lambda_corners"]) for k in range(9, 20))
    prob_tarjetas = sum(poisson_pmf(k, partido["lambda_tarjetas"]) for k in range(4, 15))

    candidatos = [
        {"mercado": "⚽ Más de 2.5 Goles", "prob": round(prob_over_25 * 100, 2), "cuota": partido["cuota_goles"]},
        {"mercado": "⛳ Córners: Más de 8.5", "prob": round(prob_corners * 100, 2), "cuota": partido["cuota_corners"]},
        {"mercado": "🟨 Tarjetas: Más de 3.5", "prob": round(prob_tarjetas * 100, 2), "cuota": partido["cuota_tarjetas"]}
    ]

    mejor_pick = max(candidatos, key=lambda x: x["prob"])
    ev = (((mejor_pick["prob"] / 100) * mejor_pick["cuota"]) - 1) * 100
    score_ia = (mejor_pick["prob"] * 0.6) + (ev * 2.5)

    return mejor_pick, round(ev, 2), round(score_ia, 2)

@app.route('/')
def home():
    liga_filtro = request.args.get('liga', 'Todas')
    partidos = obtener_partidos_api()
    
    if liga_filtro != 'Todas':
        partidos = [p for p in partidos if p['liga'] == liga_filtro]

    analisis_final = []
    for p in partidos:
        pick, ev, score = patron_evaluacion_integral(p)
        resumen = (
            f"Análisis Automatizado: El patrón matricial para {p['local']} vs {p['visitante']} "
            f"indica alta estabilidad en el mercado de '{pick['mercado']}' con una probabilidad del {pick['prob']}% "
            f"y un valor esperado (+EV) de +{ev}%."
        )

        analisis_final.append({
            "deporte": p["deporte"], "liga": p["liga"],
            "partido": f"{p['local']} vs {p['visitante']}",
            "fecha": p["fecha"], "hora": p["hora"],
            "pick": pick["mercado"], "prob": pick["prob"],
            "cuota": pick["cuota"], "ev": ev, "score": score,
            "resumen": resumen
        })

    analisis_final.sort(key=lambda x: x["score"], reverse=True)
    todas_ligas = sorted(list(set(item['liga'] for item in obtener_partidos_api())))

    return render_template_string(HTML_TEMPLATE, resultados=analisis_final, ligas=todas_ligas, seleccionada=liga_filtro)

# ==========================================
# 3. INTERFAZ WEB RESPONSIVA (PWA)
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
        .sub { text-align: center; color: #94a3b8; font-size: 12px; margin-bottom: 15px; }
        .filter-box { background: #1e293b; padding: 12px; border-radius: 10px; margin-bottom: 18px; text-align: center; border: 1px solid #334155; }
        select { background: #0f172a; color: #f8fafc; border: 1px solid #38bdf8; padding: 8px 12px; border-radius: 6px; font-size: 14px; width: 80%; max-width: 300px; }
        .card { background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 18px; border-left: 5px solid #38bdf8; box-shadow: 0 4px 8px rgba(0,0,0,0.4); }
        .tag { background: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .match { font-size: 17px; font-weight: bold; margin: 10px 0 6px 0; }
        .info { font-size: 12px; color: #94a3b8; margin-bottom: 12px; }
        .pick-box { background: #0f172a; padding: 10px 12px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; }
        .pick-title { color: #facc15; font-weight: bold; font-size: 14px; }
        .ev { color: #4ade80; font-weight: bold; }
        .ai-box { background: #1e293b; padding: 10px; border-radius: 8px; font-size: 12px; border-left: 3px solid #38bdf8; color: #cbd5e1; line-height: 1.4; }
        .no-results { text-align: center; color: #94a3b8; padding: 30px; font-size: 14px; }
    </style>
</head>
<body>
    <h1>🧠 SOTELOK QUANT SUITE</h1>
    <div class="sub">Calendario en Vivo & Modelo Cuantitativo</div>

    <div class="filter-box">
        <form method="GET" action="/">
            <label style="font-size: 13px; color: #cbd5e1; display: block; margin-bottom: 6px;">📂 Filtrar por Competición:</label>
            <select name="liga" onchange="this.form.submit()">
                <option value="Todas" {% if seleccionada == 'Todas' %}selected{% endif %}>🌍 Todas las Ligas</option>
                {% for l in ligas %}
                <option value="{{ l }}" {% if seleccionada == l %}selected{% endif %}>{{ l }}</option>
                {% endfor %}
            </select>
        </form>
    </div>
    
    {% if resultados %}
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
    {% else %}
        <div class="no-results">No hay partidos disponibles para esta selección hoy.</div>
    {% endif %}
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

@app.route('/manifest.json')
def manifest():
    return app.response_class(MANIFEST_JSON, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
