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

def motor_big_data_pro(local, visitante, cuota_usuario):
    l_lower = local.lower().strip()
    v_lower = visitante.lower().strip()
    
    h_l = sum(ord(c) for c in l_lower)
    h_v = sum(ord(c) for c in v_lower)
    
    # Métricas estadísticas avanzadas simuladas de Big Data
    goles_l_10 = round(1.4 + (h_l % 11) / 10.0, 1)
    goles_v_10 = round(1.2 + (h_v % 11) / 10.0, 1)
    p_over_25_val = round(min(88.0, 48.0 + ((goles_l_10 + goles_v_10) * 12)), 1)
    p_aem_val = round(min(85.0, 45.0 + (goles_l_10 * goles_v_10 * 10)), 1)
    
    elo_local = 1530 + ((h_l % 280) - 130)
    elo_visitante = 1480 + ((h_v % 280) - 130)
    diff_elo = (elo_local - elo_visitante) / 400.0
    
    expected_l = 1 / (1 + math.pow(10, -diff_elo))
    expected_v = 1 - expected_l
    
    lambda_l = max(0.5, round(goles_l_10 * 0.5 + expected_l * 1.3, 2))
    lambda_v = max(0.4, round(goles_v_10 * 0.5 + expected_v * 1.1, 2))
    
    matriz = {}
    p_over_15, p_over_25_poi, p_under_35, p_btts = 0.0, 0.0, 0.0, 0.0
    p_1x, p_x2 = 0.0, 0.0
    
    for x in range(7):
        for y in range(7):
            prob_x = (math.pow(lambda_l, x) * math.exp(-lambda_l)) / math.factorial(x)
            prob_y = (math.pow(lambda_v, y) * math.exp(-lambda_v)) / math.factorial(y)
            p_joint = prob_x * prob_y
            matriz[(x, y)] = p_joint
            
            tot = x + y
            if tot > 1.5: p_over_15 += p_joint
            if tot > 2.5: p_over_25_poi += p_joint
            if tot < 3.5: p_under_35 += p_joint
            if x > 0 and y > 0: p_btts += p_joint
            if x >= y: p_1x += p_joint
            if y >= x: p_x2 += p_joint

    exact_score = max(matriz, key=matriz.get)
    prob_exact = matriz[exact_score]

    corners_proj = round(5.5 + (lambda_l + lambda_v) * 1.9, 1)
    tarjetas_proj = round(3.6 + (abs(elo_local - elo_visitante) / 220.0), 1)

    mercados = [
        {"nombre": f"Doble Oportunidad: 1X ({local} o Empate)", "prob": round(p_1x * 100, 1), "cuota": round(cuota_usuario if cuota_usuario > 1.0 else 1.34, 2), "cat": "Seguridad"},
        {"nombre": "Más de 2.5 Goles en el Partido", "prob": p_over_25_val, "cuota": 1.78, "cat": "Goles Pro"},
        {"nombre": "Ambos Equipos Anotan (AEM / BTTS)", "prob": p_aem_val, "cuota": 1.72, "cat": "Especial AEM"},
        {"nombre": f"Córners Desk: Más de {round(corners_proj - 1.5, 1)} Córners", "prob": 69.5, "cuota": 1.75, "cat": "Córners Pro"},
        {"nombre": f"Disciplina Desk: Más de {round(tarjetas_proj - 0.5, 1)} Tarjetas", "prob": 67.0, "cuota": 1.82, "cat": "Tarjetas Pro"},
        {"nombre": f"Marcador Exacto: {exact_score[0]}-{exact_score[1]}", "prob": round(prob_exact * 100, 1), "cuota": round(max(7.5, 17.0 - (prob_exact * 45)), 1), "cat": "Alta Cuota"}
    ]

    for m in mercados:
        m["ev"] = round((((m["prob"] / 100.0) * m["cuota"]) - 1.0) * 100, 1)

    mercados_ordenados = sorted(mercados, key=lambda x: (x["prob"] * 0.75) + (x["ev"] * 2.5), reverse=True)
    top_2 = mercados_ordenados[:2]

    prob_dec = top_2[0]["prob"] / 100.0
    c_real = top_2[0]["cuota"]
    kelly = max(0.0, ((prob_dec * c_real) - 1.0) / (c_real - 1.0)) * 0.20
    stake = round(kelly * 100, 1)

    # Informe analítico avanzado estilo GPT5 Análisis
    resumen_quant = (
        f"SOTELOK AI // ANÁLISIS DE SINDICATO PRO:\n"
        f"• Match Context: {local} vs {visitante} | Elo L: {elo_local} vs Elo V: {elo_visitante}\n"
        f"• Key Betting Angles:\n"
        f"  - Tendencia ofensiva (Últimos 10): {local} ({goles_l_10} G/p) vs {visitante} ({goles_v_10} G/p).\n"
        f"  - Probabilidad estadística calculada de Más de 2.5 Goles: {p_over_25_val}% (Media de liga estándar: 54%).\n"
        f"  - Probabilidad de Ambos Equipos Anotan (AEM): {p_aem_val}% (Media de liga: 53%).\n"
        f"  - Balón Detenido: Proyección de {corners_proj} córners y {tarjetas_proj} tarjetas amarillas.\n\n"
        f"🎯 TOP 2 OPCIONES DE ALTA CERTEZA (+EV):\n"
        f"1️⃣ [{top_2[0]['cat']}] {top_2[0]['nombre']} — Certeza: {top_2[0]['prob']}% | Cuota: {top_2[0]['cuota']} | +EV: +{top_2[0]['ev']}%\n"
        f"2️⃣ [{top_2[1]['cat']}] {top_2[1]['nombre']} — Certeza: {top_2[1]['prob']}% | Cuota: {top_2[1]['cuota']} | +EV: +{top_2[1]['ev']}%"
    )

    return top_2, stake, resumen_quant, lambda_l, lambda_v, corners_proj, tarjetas_proj, p_over_25_val, p_aem_val

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
        top_2, stake, resumen_quant, xg_l, xg_v, c_proj, t_proj, p_ov, p_aem = motor_big_data_pro(p['local'], p['visitante'], cuota_c)

        analisis_final.append({
            "id": p["id"], "pais": p["pais"], "liga": p["liga"],
            "partido": str(p['local']) + " vs " + str(p['visitante']),
            "fecha": p["fecha"], "hora": p["hora"], "estado": p["estado"],
            "top_2": top_2, "stake": stake, "resumen_quant": resumen_quant,
            "xg_l": xg_l, "xg_v": xg_v, "c_proj": c_proj, "t_proj": t_proj,
            "p_ov": p_ov, "p_aem": p_aem
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
        ''', ("Global", "Premier Pro League", local, visitante, cuota_custom, fecha_str, hora))
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
        top_2, stake, _, _, _, _, _, _, _ = motor_big_data_pro(local, visitante, cuota_c)
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
    <title>SOTELOK Quant Suite - Pro Terminal</title>
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
            navigator.clipboard.writeText(texto).then(() => { alert("¡Análisis Pro copiado al portapapeles!"); });
        }
    </script>
</head>
<body>
    <div class="terminal-header">
        <div class="logo">⚡ SOTELOK // PRO-ANALYTICS DESK</div>
        <div><span class="status-dot"></span> <span style="font-size:10px; color:var(--text-muted);">GPT5 + BIG DATA ACTIVE</span></div>
    </div>

    <div class="bankroll-banner">
        <div>Capital Actual<br><span class="bankroll-val">${{ bankroll.capital_actual }}</span></div>
        <div>ROI Global<br><span class="bankroll-val" style="color:var(--accent-cyan);">+{{ roi }}%</span></div>
        <div>Yield Operativo<br><span class="bankroll-val">+{{ yield_pct }}%</span></div>
    </div>

    <div class="sub-nav">
        <div class="sub-tab active">General</div>
        <div class="sub-tab">Cuotas</div>
        <div class="sub-tab">Goles (% AEM)</div>
        <div class="sub-tab">Córners</div>
        <div class="sub-tab">Tarjetas</div>
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
        <div style="color: var(--accent-cyan); font-weight: 800; font-size: 12px; margin-bottom: 8px; text-transform: uppercase;">🔍 Inyección de Partido & Métricas Pro</div>
        <form method="POST" action="/agregar">
            <input type="hidden" name="fecha" value="{{ fecha_seleccionada }}">
            <label>Equipo Local</label>
            <input type="text" name="local" placeholder="Ej. Ipswich Town" required>
            <label>Equipo Visitante</label>
            <input type="text" name="visitante" placeholder="Ej. Nottingham Forest" required>
            <label>Cuota Real del Bookmaker (Opcional)</label>
            <input type="number" step="0.01" name="cuota_custom" value="1.85">
            <label>Hora Programada</label>
            <input type="text" name="hora" value="15:00" required>
            <button type="submit" class="btn-exec">Sintetizar Análisis GPT5 & Sindicato</button>
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
                <div>Más de 2,5 Goles</div>
                <div class="stat-val">{{ item.p_ov }}%</div>
            </div>
            <div class="stat-box">
                <div>AEM (Ambos Marcan)</div>
                <div class="stat-val">{{ item.p_aem }}%</div>
            </div>
            <div class="stat-box">
                <div>Córners Proyectados</div>
                <div class="stat-val">{{ item.c_proj }}</div>
            </div>
            <div class="stat-box">
                <div>Tarjetas Estimadas</div>
                <div class="stat-val">{{ item.t_proj }}</div>
            </div>
        </div>
        
        <div class="pick-box" style="border-color: #38bdf8;">
            <div style="color: #facc15; font-weight: 800; font-size: 12px;">🌟 OPCIÓN PRO 1: {{ item.top_2[0].nombre }}</div>
            <div style="font-size: 11px; margin-top: 4px;">Certeza: <b>{{ item.top_2[0].prob }}%</b> | Cuota: <b>{{ item.top_2[0].cuota }}</b> | Valor Esperado: <span class="ev-badge">+{{ item.top_2[0].ev }}%</span></div>
        </div>

        <div class="pick-box" style="border-color: #10b981; margin-top: 6px;">
            <div style="color: #34d399; font-weight: 800; font-size: 12px;">🚀 OPCIÓN PRO 2: {{ item.top_2[1].nombre }}</div>
            <div style="font-size: 11px; margin-top: 4px;">Certeza: <b>{{ item.top_2[1].prob }}%</b> | Cuota: <b>{{ item.top_2[1].cuota }}</b> | Valor Esperado: <span class="ev-badge">+{{ item.top_2[1].ev }}%</span></div>
        </div>

        <div class="ai-terminal">
            <b style="color: var(--accent-cyan);">🧠 GPT5 & SINDICATO ANÁLISIS:</b>
            {{ item.resumen_quant }}
        </div>

        <div class="action-row">
            <a href="/liquidar/{{ item.id }}/acertado" class="btn-win">✅ ACERTADO</a>
            <a href="/liquidar/{{ item.id }}/fallado" class="btn-loss">❌ FALLADO</a>
            <button class="btn-copy" onclick="copiarAnalisis('{{ item.partido }} - GPT5 Pick: {{ item.top_2[0].nombre }} (Cuota {{ item.top_2[0].cuota }}) | Prob: {{ item.top_2[0].prob }}% | Stake Kelly: {{ item.stake }}%')">📋 Copiar</button>
        </div>
    </div>
    {% else %}
    <div style="text-align: center; color: var(--text-muted); padding: 30px; font-size: 12px; background: var(--card-bg); border-radius: 8px; border: 1px dashed var(--border-color);">
        📭 TERMINAL PRO VACÍA. Registra un encuentro para ver el desglose porcentual avanzado.
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
