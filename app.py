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
            categoria TEXT,
            cuota REAL,
            probabilidad TEXT,
            ev TEXT,
            stake TEXT,
            resultado TEXT,
            fecha_registro TEXT
        )
    ''')
    conn.commit()
    cursor.execute('SELECT COUNT(*) FROM bankroll')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO bankroll (capital_inicial, capital_actual) VALUES (1000.0, 1000.0)')
        conn.commit()
    conn.close()

def motor_mercado_sotelok_v11(local, visitante, cuota_usuario):
    l_lower = local.lower().strip()
    v_lower = visitante.lower().strip()
    
    seed_l = sum(ord(c) * (i + 1) for i, c in enumerate(l_lower))
    seed_v = sum(ord(c) * (i + 1) for i, c in enumerate(v_lower))
    seed_match = seed_l + seed_v

    elo_l = 1450 + (seed_l % 360)
    elo_v = 1450 + (seed_v % 360)
    diff_elo = (elo_l - elo_v) / 400.0
    
    expected_l
