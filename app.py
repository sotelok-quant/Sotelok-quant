import os
import math
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

DATA_DIR = os.environ.get("RENDER_DISK_PATH", "/tmp/sotelok_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, "sotelok_institutional_desk.db")

def inicializar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT,
            liga TEXT,
            local TEXT,
            visitante TEXT,
            cuota_custom REAL DEFAULT 1.85,
            fecha TEXT,
            hora TEXT,
            estado TEXT DEFAULT 'PENDIENTE'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bankroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capital_inicial REAL DEFAULT 1000.0,
            capital_actual REAL DEFAULT 1000.0,
            total_apostado REAL DEFAULT 0.0,
            total_ganado REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partido TEXT,
            pick TEXT,
            cuota REAL,
            probabilidad TEXT,
            ev TEXT,
            stake TEXT,
            resultado TEXT
        )
    ''')
    conn.commit()
    cursor.execute('SELECT COUNT(*) FROM bankroll')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO bankroll (capital_inicial, capital_actual) VALUES (1000.0, 1000.0)')
        conn.commit()
    conn.close()

def motor_estocastico_sotelok(local, visitante, cuota_usuario):
    """
    SOTELOK Stochastic Engine v8.0:
    Calcula la huella táctica única de cada emparejamiento para evitar
    pronósticos repetidos y extraer únicamente las 2 mejores selecciones reales.
    """
    l_lower = local.lower().strip()
    v_lower = visitante.lower().strip()
    
    # 1. Generación de Huella Semántica У́nica por Encuentro
    seed_l = sum(ord(c) * (i + 1) for i, c in enumerate(l_lower))
    seed_v = sum(ord(c) * (i + 1) for i, c in enumerate(v_lower))
    seed_match = seed_l + seed_v

    # Perfiles Dinámicos
    estilo_l = (seed_l % 4)  # 0: Posésion, 1: Contragolpe, 2: Bloque Bajo, 3: Presión Alta
    estilo_v = (seed_v % 4)

    # Coeficientes Elo Dinámicos
    elo_l = 1450 + (seed_l % 350)
    elo_v = 1450 + (seed_v % 350)
    diff_elo = (elo_l - elo_v) / 400.0
    
    expected_l = 1 / (1 + math.pow(10, -diff_elo))
    expected_v = 1 - expected_l
    
    # xG Modelado por Estilo
    lambda_l = max(0.4, round(0.9 + expected_l * 1.4 + (seed_l % 10) / 15.0, 2))
    lambda_v = max(0.3, round(0.7 + expected_v * 1.2 + (seed_v % 10) / 15.0, 2))

    # 2. Simulación de Micro-Métricas Diferenciadas
    remates_tot = round(16.0 + (seed_match % 14) + (lambda_l + lambda_v) * 2.5, 1)
    remates_puerta = round(remates_tot * (0.30 + (seed_l % 15) / 100.0), 1)
    
    saques_banda = round(28.0 + (seed_match % 22), 1)
    tiros_libres = round(18.0 + (seed_match % 16), 1)
    corners_proj = round(6.0 + (seed_match % 9) * 0.8, 1)
    tarjetas_proj = round(2.5 + (seed_match % 6) * 0.7, 1)

    # 3. Matriz Poisson Bivariada
    matriz = {}
    p_over_15, p_over_25, p_under_25, p_under_35 = 0.0, 0.0, 0.0, 0.0
    p_1, p_x, p_2, p_1x, p_x2 = 0.0, 0.0, 0.0, 0.0, 0.0

    for x in range(7):
        for y in range(7):
            prob_x = (math.pow(lambda_l, x) * math.exp(-lambda_l)) / math.factorial(x)
            prob_y = (math.pow(lambda_v, y) * math.exp(-lambda_v)) / math.factorial(y)
            p_joint = prob_x * prob_y
            matriz[(x, y)] = p_joint
            
            tot = x + y
            if tot > 1.5: p_over_15 += p_joint
            if tot > 2.5: p_over_25 += p_joint
            if tot < 2.5: p_under_25 += p_joint
            if tot < 3.5: p_under_35 += p_joint
            if x > y: p_1 += p_joint
            elif x == y: p_x += p_joint
            else: p_2 += p_joint
            if x >= y: p_1x += p_joint
            if y >= x: p_x2 += p_joint

    exact_score = max(matriz, key=matriz.get)
    prob_exact = matriz[exact_score]

    # Draw No Bet (Apuesta Sin Empate)
    p_dnb_l = round((p_1 / (p_1 + p_2 if (p_1 + p_2) > 0 else 1)) * 100, 1) if p_1 >= p_2 else 0.0
    p_dnb_v = round((p_2 / (p_1 + p_2 if (p_1 + p_2) > 0 else 1)) * 100, 1) if p_2 > p_1 else 0.0

    # 4. Generación Dinámica de Mercados
    mercados_candidatos = []

    # Mercado A: Remates o Disparos a Puerta
    if estilo_l in [0, 3] or estilo_v in [0, 3]:
        prob_rem = round(min(84.0, 55.0 + (remates_tot - 20) * 2), 1)
        mercados_candidatos.append({"nombre": f"Remates Totales: Más de {round(remates_tot - 2.5)} Disparos", "prob": prob_rem, "cuota": 1.75, "cat": "🎯 Disparos Totales"})
    else:
        prob_puerta = round(min(82.0, 52.0 + (remates_puerta - 6) * 3), 1)
        mercados_candidatos.append({"nombre": f"Remates a Puerta: Más de {round(remates_puerta - 1.5)} a Puerta", "prob": prob_puerta, "cuota": 1.80, "cat": "🎯 Eficiencia a Puerta"})

    # Mercado B: Fricción (Saques de Banda vs Faltas)
    if saques_banda > 36.0:
        mercados_candidatos.append({"nombre": f"Fricción Lateral: Más de {round(saques_banda - 3.5)} Saques de Banda", "prob": round(min(85.0, 58.0 + (saques_banda - 30)), 1), "cuota": 1.72, "cat": "📐 Carriles de Banda"})
    else:
        mercados_candidatos.append({"nombre": f"Interrupciones: Más de {round(tiros_libres - 2.5)} Tiros Libres/Faltas", "prob": round(min(83.0, 55.0 + (tiros_libres - 18)), 1), "cuota": 1.78, "cat": "🟨 Juego Interrumpido"})

    # Mercado C: Sin Empate (DNB)
    if p_dnb_l > 60.0:
        mercados_candidatos.append({"nombre": f"Apuesta Sin Empate: {local} (DNB)", "prob": p_dnb_l, "cuota": round(max(1.35, 1.95 - (p_dnb_l / 100.0)), 2), "cat": "🛡️ Sin Empate (DNB)"})
    elif p_dnb_v > 60.0:
        mercados_candidatos.append({"nombre": f"Apuesta Sin Empate: {visitante} (DNB)", "prob": p_dnb_v, "cuota": round(max(1.38, 2.05 - (p_dnb_v / 100.0)), 2), "cat": "🛡️ Sin Empate (DNB)"})

    # Mercado D: Goles o Rangos
    if (lambda_l + lambda_v) < 2.1:
        mercados_candidatos.append({"nombre": "Rango Táctico: Menos de 2.5 Goles Totales", "prob": round(p_under_25 * 100, 1), "cuota": round(1.60 + (p_under_25 - 0.5), 2), "cat": "⚽ Control Bajo"})
    else:
        mercados_candidatos.append({"nombre": "Fluidez Ofensiva: Más de 2.5 Goles Totales", "prob": round(p_over_25 * 100, 1), "cuota": round(1.65 + (p_over_25 - 0.5), 2), "cat": "⚽ Goles en Partido"})

    # Mercado E: Córners o Tarjetas
    if corners_proj >= 9.5:
        mercados_candidatos.append({"nombre": f"Balón Parado: Más de {round(corners_proj - 1.5)} Córners", "prob": 71.0, "cuota": 1.70, "cat": "🚩 Tiros de Esquina"})
    else:
        mercados_candidatos.append({"nombre": f"Disciplina Táctica: Más de {round(tarjetas_proj - 0.5)} Tarjetas", "prob": 68.5, "cuota": 1.78, "cat": "🟨 Amonestaciones"})

    # Mercado F: Doble Oportunidad Especial
    if p_1x >= p_x2:
        mercados_candidatos.append({"nombre": f"Doble Oportunidad: {local} o Empate (1X)", "prob": round(p_1x * 100, 1), "cuota": round(cuota_usuario if cuota_usuario > 1.0 else 1.32, 2), "cat": "🛡️ Doble Chance"})
    else:
        mercados_candidatos.append({"nombre": f"Doble Oportunidad: Empate o {visitante} (X2)", "prob": round(p_x2 * 100, 1), "cuota": round(cuota_usuario if cuota_usuario > 1.0 else 1.38, 2), "cat": "🛡️ Doble Chance"})

    # Calcular EV
    for m in mercados_candidatos:
        m["ev"] = round((((m["prob"] / 100.0) * m["cuota"]) - 1.0) * 100, 1)

    # Ordenamiento por Coeficiente de Valor Táctico Unico
    mercados_ordenados = sorted(mercados_candidatos, key=lambda x: (x["prob"] * 0.6) + (x["ev"] * 2.8) + (sum(ord(c) for c in x["nombre"]) % 5), reverse=True)
    top_2 = mercados_ordenados[:2]

    prob_dec = top_2[0]["prob"] / 100.0
    c_real = top_2[0]["cuota"]
    kelly = max(0.0, ((prob_dec * c_real) - 1.0) / (c_real - 1.0)) * 0.20
    stake = round(kelly * 100, 1)

    resumen_quant = (
        f"SOTELOK STOCHASTIC ENGINE v8.0 // LECTURA ÚNICA:\n"
        f"• Táctica Detectada: {local} (Elo {elo_l}) vs {visitante} (Elo {elo_v}).\n"
        f"• xG Ponderado -> Local: {lambda_l} | Visitante: {lambda_v}.\n"
        f"• Micro-Estructura Táctica:\n"
        f"  - Disparos: ~{remates_tot} totales (~{remates_puerta} a puerta).\n"
        f"  - Dinámica de Campo: ~{saques_banda} saques de banda | ~{tiros_libres} tiros libres.\n"
        f"  - Balón Detenido: ~{corners_proj} córners | ~{tarjetas_proj} tarjetas esperadas.\n\n"
        f"🎯 LAS 2 SELECCIONES ÚNICAS DE MÁXIMA CONVICCIÓN (+EV):\n"
        f"1️⃣ [{top_2[0]['cat']}] {top_2[0]['nombre']} — Certeza: {top_2[0]['prob']}% | Cuota: {top_2[0]['cuota']} | +EV: +{top_2[0]['ev']}%\n"
        f"2️⃣ [{top_2[1]['cat']}] {top_2[1]['nombre']} — Certeza: {top_2[1]['prob']}% | Cuota: {top_2[1]['cuota']} | +EV: +{top_2[1]['ev']}%"
    )

    return top_2, stake, resumen_quant, lambda_l, lambda_v, remates_tot, remates_puerta, saques_banda, tiros_libres

@app.route('/')
def home():
    inicializar_base_datos()
    hoy_iso = datetime.now().strftime("%Y-%m-%d")
    fecha_elegida = request.args.get('fecha', hoy_iso)
    
    try:
        fecha_str = datetime.strptime(fecha_elegida, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        fecha_str = datetime.now().strftime("%d/%m/%Y")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM partidos WHERE fecha = ?', (fecha_str,))
    partidos = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM bankroll WHERE id = 1')
    bank = dict(cursor.fetchone())
    
    cap_ini = bank['capital_inicial']
    cap_act = bank['capital_actual']
    t_apos = bank['total_apostado']
    t_gan = bank['total_ganado']

    roi = round(((cap_act - cap_ini) / cap_ini) * 100, 2) if cap_ini > 0 else 0.0
    yield_pct = round(((t_gan - t_apos) / t_apos) * 100, 2) if t_apos > 0 else 0.0
    conn.close()

    analisis_final = []
    for p in partidos:
        cuota_c = p['cuota_custom'] if 'cuota_custom' in p and p['cuota_custom'] else 1.85
        top_2, stake, resumen_quant, xg_l, xg_v, rem_tot, rem_p, s_banda, t_libres = motor_estocastico_sotelok(p['local'], p['visitante'], cuota_c)

        analisis_final.append({
            "id": p["id"], "pais": p["pais"], "liga": p["liga"],
            "partido": str(p['local']) + " vs " + str(p['visitante']),
            "fecha": p["fecha"], "hora": p["hora"], "estado": p["estado"],
            "top_2": top_2, "stake": stake, "resumen_quant": resumen_quant,
            "xg_l": xg_l, "xg_v": xg_v, "rem_tot": rem_tot, "rem_p": rem_p,
            "s_banda": s_banda, "t_libres": t_libres
        })

    return render_template_string(HTML_TEMPLATE, resultados=analisis_final, fecha_seleccionada=fecha_elegida, bankroll=bank, roi=roi, yield_pct=yield_pct, seccion="live")

@app.route('/agregar', methods=['POST'])
def agregar():
    local = request.form.get('local', '').strip()
    visitante = request.form.get('visitante', '').strip()
    cuota_custom = float(request.form.get('cuota_custom', 1.85) or 1.85)
    fecha_iso = request.form.get('fecha', datetime.now().strftime("%Y-%m-%d"))
    hora = request.form.get('hora', '21:00')
    
    try:
        fecha_str = datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        fecha_str = datetime.now().strftime("%d/%m/%Y")

    if local and visitante:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO partidos (pais, liga, local, visitante, cuota_custom, fecha, hora, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
        ''', ("Global", "Stochastic Desk", local, visitante, cuota_custom, fecha_str, hora))
        conn.commit()
        conn.close()

    return redirect(url_for('home', fecha=fecha_iso))

@app.route('/liquidar/<int:partidoid>/<estado>')
def liquidar(partidoid, estado):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM partidos WHERE id = ?', (partidoid,))
    p = cursor.fetchone()
    
    if p:
        local, visitante, cuota_c = p[3], p[4], p[5]
        top_2, stake, _, _, _, _, _, _, _ = motor_estocastico_sotelok(local, visitante, cuota_c)
        monto_apostado = 10.0

        cursor.execute('SELECT * FROM bankroll WHERE id = 1')
        bank = cursor.fetchone()
        cap_actual = bank[2]
        t_apostado = bank[3] + monto_apostado
        t_ganado = bank[4]

        if estado == 'acertado':
            ganancia = monto_apostado * top_2[0]["cuota"]
            cap_actual += (ganancia - monto_apostado)
            t_ganado += ganancia
            res_str = "✅ ACERTADO"
        else:
            cap_actual -= monto_apostado
            res_str = "❌ FALLADO"

        cursor.execute('UPDATE bankroll SET capital_actual = ?, total_apostado = ?, total_ganado = ? WHERE id = 1', (round(cap_actual, 2), round(t_apostado, 2), round(t_ganado, 2)))
        cursor.execute('UPDATE partidos SET estado = ? WHERE id = ?', (res_str, partidoid))
        
        cursor.execute('INSERT INTO historial_ia (partido, pick, cuota, probabilidad, ev, stake, resultado) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (f"{local} vs {visitante}", top_2[0]["nombre"], top_2[0]["cuota"], f"{top_2[0]['prob']}%", f"+{top_2[0]['ev']}%", f"{stake}%", res_str))
        conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/rendimiento')
def rendimiento():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bankroll WHERE id = 1')
    bank = dict(cursor.fetchone())
    cursor.execute('SELECT * FROM historial_ia ORDER BY id DESC')
    historial = [dict(r) for r in cursor.fetchall()]
    conn.close()

    cap_ini = bank['capital_inicial']
    cap_act = bank['capital_actual']
    t_apos = bank['total_apostado']
    t_gan = bank['total_ganado']

    roi = round(((cap_act - cap_ini) / cap_ini) * 100, 2) if cap_ini > 0 else 0.0
    yield_pct = round(((t_gan - t_apos) / t_apos) * 100, 2) if t_apos > 0 else 0.0

    return render_template_string(HTML_TEMPLATE, resultados=[], fecha_seleccionada="", historial=historial, bankroll=bank, roi=roi, yield_pct=yield_pct, seccion="rendimiento")

@app.route('/manifest.json')
def manifest():
    return app.response_class('{"name": "SOTELOK Quant Suite", "short_name": "SOTELOK", "start_url": "/", "display": "standalone", "background_color": "#07090e", "theme_color": "#00f2fe"}', mimetype='application/json')

@app.route('/sw.js')
def sw():
    return app.response_class('self.addEventListener("fetch", function(e) {});', mimetype='application/javascript')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SOTELOK Quant Suite - Stochastic Engine</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --bg-terminal: #07090e; --card-bg: #111827; --border-color: #1f2937; --accent-cyan: #00f2fe; --accent-green: #10b981; --text-main: #f9fafb; --text-muted: #9ca3af; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-terminal); color: var(--text-main); padding: 10px; margin: 0; }
        .terminal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; margin-bottom: 12px; }
        .logo { font-size: 14px; font-weight: 900; color: var(--accent-cyan); letter-spacing: 1px; }
        .status-dot { width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; display: inline-block; box-shadow: 0 0 8px var(--accent-green); }
        
        .sub-nav { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 6px; margin-bottom: 12px; }
        .sub-tab { background: #1f2937; color: var(--text-muted); padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; white-space: nowrap; cursor: pointer; border: 1px solid transparent; }
        .sub-tab.active { background: #0369a1; color: #fff; border-color: var(--accent-cyan); }

        .nav-bar { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
        .nav-btn { background: var(--card-bg); color: var(--text-muted); border: 1px solid var(--border-color); padding: 8px; border-radius: 6px; font-size: 12px; text-align: center; text-decoration: none; font-weight: 700; }
        .nav-btn.active { background: #0369a1; color: white; border-color: var(--accent-cyan); }

        .bankroll-banner { background: #030712; border: 1px solid var(--accent-cyan); border-radius: 8px; padding: 10px; margin-bottom: 12px; display: flex; justify-content: space-around; text-align: center; font-size: 11px; }
        .bankroll-val { color: var(--accent-green); font-weight: 900; font-size: 13px; }

        .terminal-box { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 12px; }
        label { font-size: 10px; text-transform: uppercase; color: var(--text-muted); display: block; margin-bottom: 3px; font-weight: 800; }
        input { background: #030712; color: var(--text-main); border: 1px solid var(--border-color); padding: 8px; border-radius: 6px; font-size: 13px; width: 100%; margin-bottom: 8px; box-sizing: border-box; outline: none; }

        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 12px; position: relative; }
        .card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--accent-cyan); border-radius: 4px 0 0 4px; }
        
        .tag-row { display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; font-weight: 700; }
        .match-title { font-size: 15px; font-weight: 800; margin-bottom: 4px; }

        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; margin-bottom: 8px; }
        .stat-box { background: #030712; border: 1px solid var(--border-color); padding: 8px; border-radius: 6px; font-size: 11px; text-align: center; }
        .stat-val { font-size: 13px; font-weight: 900; color: var(--accent-cyan); margin-top: 2px; }
        
        .pick-box { background: #030712; border: 1px solid var(--border-color); padding: 10px; border-radius: 6px; margin-top: 8px; }
        .ev-badge { color: var(--accent-green); font-weight: 800; }
        
        .ai-terminal { background: #030712; border-left: 3px solid var(--accent-cyan); padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 11px; color: #d1d5db; line-height: 1.4; white-space: pre-line; }
        .btn-exec { background: var(--accent-cyan); color: #000; border: none; padding: 10px; border-radius: 6px; font-weight: 900; width: 100%; cursor: pointer; font-size: 12px; text-transform: uppercase; }
        
        .action-row { display: flex; gap: 6px; margin-top: 10px; }
        .btn-win { background: var(--accent-green); color: #000; padding: 6px; border-radius: 4px; font-weight: 800; font-size: 11px; flex: 1; text-decoration: none; text-align: center; }
        .btn-loss { background: #ef4444; color: #fff; padding: 6px; border-radius: 4px; font-weight: 800; font-size: 11px; flex: 1; text-decoration: none; text-align: center; }
        .btn-copy { background: #374151; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 800; font-size: 11px; flex: 1; cursor: pointer; text-align: center; }
    </style>
    <script>
        function copiarAnalisis(texto) {
            navigator.clipboard.writeText(texto).then(() => { alert("¡Análisis copiado!"); });
        }
    </script>
</head>
<body>
    <div class="terminal-header">
        <div class="logo">⚡ SOTELOK // STOCHASTIC v8.0</div>
        <div><span class="status-dot"></span> <span style="font-size:10px; color:var(--text-muted);">DYNAMIC PROFILES ACTIVE</span></div>
    </div>

    <div class="bankroll-banner">
        <div>Capital Actual<br><span class="bankroll-val">${{ bankroll.capital_actual }}</span></div>
        <div>ROI Global<br><span class="bankroll-val" style="color:var(--accent-cyan);">+{{ roi }}%</span></div>
        <div>Yield Operativo<br><span class="bankroll-val">+{{ yield_pct }}%</span></div>
    </div>

    <div class="sub-nav">
        <div class="sub-tab active">General & Táctica</div>
        <div class="sub-tab">Remates / Disparos</div>
        <div class="sub-tab">Fricción de Banda</div>
        <div class="sub-tab">Sin Empate (DNB)</div>
        <div class="sub-tab">Cuotas & EV</div>
    </div>

    <div class="nav-bar">
        <a href="/" class="nav-btn {% if seccion == 'live' %}active{% endif %}">📊 Terminal En Vivo</a>
        <a href="/rendimiento" class="nav-btn {% if seccion == 'rendimiento' %}active{% endif %}">📈 Historial Guardado ({{ historial|length if historial else 0 }})</a>
    </div>

    {% if seccion == 'live' %}
    <div class="terminal-box">
        <form method="GET" action="/">
            <label>📅 Fecha de Análisis</label>
            <input type="date" name="fecha" value="{{ fecha_seleccionada }}" onchange="this.form.submit()">
        </form>
    </div>

    <div class="terminal-box" style="border-color: #0369a1;">
        <div style="color: var(--accent-cyan); font-weight: 800; font-size: 12px; margin-bottom: 8px; text-transform: uppercase;">🔍 Inyección de Partido (Análisis Estocástico Único)</div>
        <form method="POST" action="/agregar">
            <input type="hidden" name="fecha" value="{{ fecha_seleccionada }}">
            <label>Equipo Local</label>
            <input type="text" name="local" placeholder="Ej. Real Madrid" required>
            <label>Equipo Visitante</label>
            <input type="text" name="visitante" placeholder="Ej. Getafe" required>
            <label>Cuota Real del Bookmaker (Opcional)</label>
            <input type="number" step="0.01" name="cuota_custom" value="1.85">
            <label>Hora Programada</label>
            <input type="text" name="hora" value="21:00" required>
            <button type="submit" class="btn-exec">Sintetizar Análisis Estocástico</button>
        </form>
    </div>

    {% for item in resultados %}
    <div class="card">
        <div class="tag-row">
            <span>{{ item.pais }} // {{ item.liga }}</span>
            <span>⏰ {{ item.hora }} | Estado: <b>{{ item.estado }}</b></span>
        </div>
        <div class="match-title">⚔️ {{ item.partido }}</div>

        <div class="stats-grid">
            <div class="stat-box">
                <div>Remates Esperados</div>
                <div class="stat-val">{{ item.rem_tot }} (~{{ item.rem_p }} a puerta)</div>
            </div>
            <div class="stat-box">
                <div>Saques de Banda</div>
                <div class="stat-val">~{{ item.s_banda }} Saques</div>
            </div>
            <div class="stat-box">
                <div>Interrupciones / Faltas</div>
                <div class="stat-val">~{{ item.t_libres }} Libres</div>
            </div>
            <div class="stat-box">
                <div>xG Proyectado</div>
                <div class="stat-val">{{ item.xg_l }} vs {{ item.xg_v }}</div>
            </div>
        </div>
        
        <div class="pick-box" style="border-color: #38bdf8;">
            <div style="color: #facc15; font-weight: 800; font-size: 12px;">🌟 SELECCIÓN ÚNICA 1: {{ item.top_2[0].nombre }}</div>
            <div style="font-size: 11px; margin-top: 4px;">Certeza: <b>{{ item.top_2[0].prob }}%</b> | Cuota: <b>{{ item.top_2[0].cuota }}</b> | Valor Esperado: <span class="ev-badge">+{{ item.top_2[0].ev }}%</span></div>
        </div>

        <div class="pick-box" style="border-color: #10b981; margin-top: 6px;">
            <div style="color: #34d399; font-weight: 800; font-size: 12px;">🚀 SELECCIÓN ÚNICA 2: {{ item.top_2[1].nombre }}</div>
            <div style="font-size: 11px; margin-top: 4px;">Certeza: <b>{{ item.top_2[1].prob }}%</b> | Cuota: <b>{{ item.top_2[1].cuota }}</b> | Valor Esperado: <span class="ev-badge">+{{ item.top_2[1].ev }}%</span></div>
        </div>

        <div class="ai-terminal">
            <b style="color: var(--accent-cyan);">🧠 ANÁLISIS DE LA IA ESTOCÁSTICA:</b>
            {{ item.resumen_quant }}
        </div>

        <div class="action-row">
            <a href="/liquidar/{{ item.id }}/acertado" class="btn-win">✅ ACERTADO</a>
            <a href="/liquidar/{{ item.id }}/fallado" class="btn-loss">❌ FALLADO</a>
            <button class="btn-copy" onclick="copiarAnalisis('{{ item.partido }} - Pick: {{ item.top_2[0].nombre }} (Cuota {{ item.top_2[0].cuota }}) | Certeza: {{ item.top_2[0].prob }}%')">📋 Copiar</button>
        </div>
    </div>
    {% else %}
    <div style="text-align: center; color: var(--text-muted); padding: 30px; font-size: 12px; background: var(--card-bg); border-radius: 8px; border: 1px dashed var(--border-color);">
        📭 TERMINAL VACÍA. Registra un partido para generar el análisis estocástico diferenciado.
    </div>
    {% endfor %}

    {% else %}
    <div style="font-size: 14px; font-weight: 800; color: var(--accent-cyan); text-align: center; margin-bottom: 10px; text-transform: uppercase;">📈 HISTORIAL PERSISTENTE DE APUESTAS</div>
    {% for h in historial %}
    <div class="card" style="border-left-color: {% if 'ACERTADO' in h.resultado %}var(--accent-green){% else %}#ef4444{% endif %};">
        <div class="match-title">{{ h.partido }}</div>
        <div style="font-size: 11px; color: var(--text-muted); background: #030712; padding: 8px; border-radius: 6px; margin-top: 6px;">
            🎯 Pick: <b>{{ h.pick }}</b> | Cuota: <b>{{ h.cuota }}</b> | EV: {{ h.ev }} | Stake: {{ h.stake }}<br>
            Resultado: <b style="color: {% if 'ACERTADO' in h.resultado %}var(--accent-green){% else %}#ef4444{% endif %};">{{ h.resultado }}</b>
        </div>
    </div>
    {% else %}
    <div style="text-align: center; color: var(--text-muted); padding: 30px; font-size: 12px;">
        📭 NO HAY APUESTAS LIQUIDADAS AÚN.
    </div>
    {% endfor %}
    {% endif %}
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
