import math
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ==========================================
# 🌐 CONECTOR DE PARTIDOS REALES EN VIVO (THE SPORTS DB & API LIBRE)
# ==========================================
def obtener_partidos_reales_en_vivo(fecha_elegida):
    """Consulta en tiempo real los eventos deportivos oficiales de la fecha elegida
    utilizando pasarelas públicas de eventos deportivos reales."""
    
    # Formatear la fecha a YYYY-MM-DD
    if not fecha_elegida:
        fecha_elegida = datetime.now().strftime("%Y-%m-%d")
        
    try:
        dt_obj = datetime.strptime(fecha_elegida, "%Y-%m-%d")
        fecha_str_visual = dt_obj.strftime("%d/%m/%Y")
    except:
        fecha_str_visual = datetime.now().strftime("%d/%m/%Y")
        fecha_elegida = datetime.now().strftime("%Y-%m-%d")

    partidos_encontrados = []

    # 1. Intentar conectar con la API pública de eventos en vivo por fecha
    url_api = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={fecha_elegida}&s=Soccer"
    
    try:
        response = requests.get(url_api, timeout=6)
        if response.status_code == 200:
            data = response.json()
            events = data.get("events")
            
            if events:
                for ev in events:
                    home = ev.get("strHomeTeam", "Equipo Local")
                    away = ev.get("strAwayTeam", "Equipo Visitante")
                    liga = ev.get("strLeague", "Liga Profesional")
                    pais = ev.get("strCountry", "Internacional")
                    hora_utc = ev.get("strTime", "20:00")[:5]
                    
                    if not pais or pais == "":
                        pais = "Europa / Global"

                    partidos_encontrados.append({
                        "deporte": "Fútbol",
                        "pais": pais,
                        "liga": liga,
                        "local": home,
                        "visitante": away,
                        "fecha": fecha_str_visual,
                        "hora": hora_utc,
                        "lambda_l": 1.85, "lambda_v": 1.55,
                        "lambda_corners": round(10.1, 1),
                        "lambda_tarjetas": round(4.2, 1),
                        "cuota_
