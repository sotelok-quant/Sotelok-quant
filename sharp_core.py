import random
import math
import sqlite3
from datetime import datetime

class SharpQuantEngine:
    def __init__(self, sports_category="futbol_secundaria", db_name="sotelok_final.db"):
        self.sports_category = sports_category
        self.db_name = db_name
        self._inicializar_tabla_historica()

    def _inicializar_tabla_historica(self):
        """Crea la tabla de registros cuantitativos si no existe."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_sharp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    deporte TEXT,
                    partido TEXT,
                    prob_local REAL,
                    prob_visitante REAL,
                    cuota REAL,
                    kelly_stake REAL
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error inicializando BD en motor: {e}")

    def ejecutar_simulacion_monte_carlo(self, xg_local, xg_visitante, iteraciones=5000):
        """Simulación estocástica avanzada basada en distribución de Poisson."""
        home_wins = 0
        draws = 0
        away_wins = 0

        for _ in range(iteraciones):
            goles_local = self._poisson_random(xg_local)
            goles_visitante = self._poisson_random(xg_visitante)

            if goles_local > goles_visitante:
                home_wins += 1
            elif goles_local == goles_visitante:
                draws += 1
            else:
                away_wins += 1

        total = float(iteraciones)
        return home_wins / total, draws / total, away_wins / total

    def _poisson_random(self, lam):
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.uniform(0.0, 1.0)
        return k - 1

    def registrar_apuesta_bd(self, partido, prob_local, prob_visitante, cuota, stake):
        """Guarda el resultado del análisis directamente en SQLite."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO historial_sharp (fecha, deporte, partido, prob_local, prob_visitante, cuota, kelly_stake)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (fecha_actual, self.sports_category, partido, prob_local, prob_visitante, cuota, stake))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error guardando en BD: {e}")

    def generar_resumen_escenarios(self, local, visitante, prob_home, prob_draw, prob_away, cuota=1.95):
        """Genera el desglose táctico, calcula Kelly y registra en base de datos."""
        escenarios = []
        
        prob_real = prob_home
        ev = (prob_real * (cuota - 1.0)) - (1.0 - prob_real)
        
        b = cuota - 1.0
        p = prob_real
        q = 1.0 - p
        f_kelly = (b * p - q) / b if b > 0 else 0.0
        stake_recomendado = max(0.0, f_kelly * 100)

        # Guardar automáticamente en SQLite
        partido_str = f"{local} vs {visitante}"
        self.registrar_apuesta_bd(partido_str, round(prob_home * 100, 1), round(prob_away * 100, 1), cuota, round(stake_recomendado, 1))

        # Escenario 1: Control Local
        escenarios.append({
            "rango": f"ALTO VALOR // EV: +{round(ev * 100, 1)}%",
            "titulo": f"Control Estructural de {local}",
            "analisis": f"Modelo estocástico validado en BD. EV estimado: {round(ev * 100, 2)}%. Stake recomendado (Kelly): {round(stake_recomendado, 1)}% del bankroll."
        })

        # Escenario 2: Varianza / Visitante
        escenarios.append({
            "rango": f"COBERTURA // VARIANZA {round(prob_draw * 100, 1)}%",
            "titulo": f"Resistencia y Contragolpe de {visitante}",
            "analisis": f"La probabilidad conjunta de empate/visita es de {round((prob_draw + prob_away) * 100, 1)}%. Monitorear comportamiento de líneas secundarias."
        })

        return escenarios
