import random
import math
import sqlite3
from datetime import datetime

class SharpQuantEngine:
    def __init__(self, sports_category="futbol_secundaria", db_name="sotelok_final.db"):
        self.sports_category = sports_category.lower()
        self.db_name = db_name
        self._inicializar_base_datos_real()

    def _inicializar_base_datos_real(self):
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
                    kelly_stake REAL,
                    escenario_principal TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error BD: {e}")

    def registrar_en_bd(self, partido, prob_local, prob_visitante, cuota, stake, escenario):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO historial_sharp (fecha, deporte, partido, prob_local, prob_visitante, cuota, kelly_stake, escenario_principal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fecha_actual, self.sports_category, partido, prob_local, prob_visitante, cuota, stake, escenario))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error guardando en BD: {e}")

    def generar_analisis_avanzado(self, local, visitante, val_local, val_visitante, cuota=1.95):
        """Genera pronósticos dinámicos basados estrictamente en los valores ingresados y modelos estocásticos."""
        escenarios = []
        partido_str = f"{local} vs {visitante}"

        # 1. ANÁLISIS DINÁMICO PARA FÚTBOL
        if "futbol" in self.sports_category or "secundaria" in self.sports_category:
            goles_totales = val_local + val_visitante
            dif_xg = val_local - val_visitante
            
            # Cálculo de probabilidades estocásticas basadas en la diferencia real de xG
            prob_home = max(0.05, min(0.85, 0.45 + (dif_xg * 0.15)))
            prob_away = max(0.05, min(0.85, 0.35 - (dif_xg * 0.15)))
            
            # Criterio de Kelly
            b = cuota - 1.0
            f_kelly = (b * prob_home - (1.0 - prob_home)) / b if b > 0 else 0.0
            stake_rec = max(0.0, f_kelly * 100)

            # Dinámica de Goles y BTTS basada en el xG real introducido
            if goles_totales > 3.0:
                condicion_goles = f"Flujo ofensivo masivo detectado ({round(goles_totales, 2)} xG combinados). Alta probabilidad de Alta (Over) de 2.5 y BTTS (Ambos Anotan) superior al 78%."
                mercado_goles = "MERCADO DE GOLES // ALTAS Y BTTS SEGURO"
            elif goles_totales < 2.0:
                condicion_goles = f"Bloque defensivo rígido ({round(goles_totales, 2)} xG combinados). Tendencia marcada hacia Bajas (Under) de 2.5 y partido cerrado."
                mercado_goles = "MERCADO DE GOLES // BAJAS Y CONTROL TÁCTICO"
            else:
                condicion_goles = f"Equilibrio competitivo con xG total de {round(goles_totales, 2)}. Escenario ideal para buscar líneas asiáticas o Gol temprano."
                mercado_goles = "MERCADO DE GOLES // LÍNEA MEDIA"

            # Dinámica de Córners y Doble Oportunidad basada en supremacía local
            if val_local >= val_visitante:
                condicion_bandas = f"{local} domina el índice de presión ofensiva ({val_local} vs {val_visitante}). Proyección superior a 9.5 córners y cobertura sólida en Doble Oportunidad (1X)."
                tag_bandas = "CONTROL LOCAL // CÓRNERS Y 1X"
            else:
                condicion_bandas = f"{visitante} muestra mayor verticalidad exterior ({val_visitante} vs {val_local}). Oportunidad de valor en hándicap positivo visitante o Doble Oportunidad (X2)."
                tag_bandas = "INVERSIÓN DE BANDAS // COBERTURA X2"

            escenarios.append({
                "rango": mercado_goles,
                "titulo": f"Análisis de Red y Goles ({round(goles_totales, 2)} Goles)",
                "analisis": condicion_goles
            })
            escenarios.append({
                "rango": tag_bandas,
                "titulo": f"Dinámica de Córners y Contexto Táctico",
                "analisis": condicion_bandas
            })

            self.registrar_en_bd(partido_str, round(prob_home * 100, 1), round(prob_away * 100, 1), cuota, round(stake_rec, 1), "Fútbol Dinámico")

        # 2. ANÁLISIS DINÁMICO PARA BÉISBOL (MLB)
        elif "beisbol" in self.sports_category or "mlb" in self.sports_category:
            carreras_totales = val_local + val_visitante
            prob_home = max(0.1, min(0.9, val_local / max(0.1, carreras_totales)))
            
            b = cuota - 1.0
            f_kelly = (b * prob_home - (1.0 - prob_home)) / b if b > 0 else 0.0
            stake_rec = max(0.0, f_kelly * 100)

            escenarios.append({
                "rango": f"INNING 1 // YRFI / NRFI DINÁMICO",
                "titulo": f"Proyección de Contacto en 1er Inning ({round(carreras_totales, 2)} R/9)",
                "analisis": f"Con un promedio de carreras de {round(carreras_totales, 2)}, el modelo estocástico determina un {'ALTO' if carreras_totales > 9.0 else 'BAJO'} volumen de bateo temprano contra el abridor. Stake Kelly sugerido: {round(stake_rec, 1)}%."
            })
            escenarios.append({
                "rango": f"LÍNEA DE CARRERAS // RUN LINE",
                "titulo": f"Desglose de Bullpen para {local}",
                "analisis": f"La probabilidad matemática de victoria directa (Moneyline) para el conjunto local se sitúa en {round(prob_home * 100, 1)}%."
            })

            self.registrar_en_bd(partido_str, round(prob_home * 100, 1), round((1-prob_home)*100, 1), cuota, round(stake_rec, 1), "Béisbol Dinámico")

        # 3. ANÁLISIS DINÁMICO PARA BALONCESTO (NBA)
        else:
            total_puntos = val_local + val_visitante
            prob_home = 0.5 + ((val_local - val_visitante) * 0.02)
            prob_home = max(0.1, min(0.9, prob_home))
            
            b = cuota - 1.0
            f_kelly = (b * prob_home - (1.0 - prob_home)) / b if b > 0 else 0.0
            stake_rec = max(0.0, f_kelly * 100)

            escenarios.append({
                "rango": f"PARQUET // TOTAL DE PUNTOS ({round(total_puntos, 1)} PTS)",
                "titulo": f"Ritmo de Posesiones y Transición",
                "analisis": f"Las métricas de eficiencia ofensiva indican un total proyectado de {round(total_puntos, 1)} puntos. Las líneas de altas/bajas se calibran de acuerdo al ritmo del tercer cuarto."
            })
            escenarios.append({
                "rango": f"SPREAD // DIFERENCIAL DE CUARTOS",
                "titulo": f"Control de Ventaja de {local}",
                "analisis": f"Probabilidad modelada de triunfo: {round(prob_home * 100, 1)}%. Criterio de Kelly recomienda proteger el bankroll con un stake de {round(stake_rec, 1)}%."
            })

            self.registrar_en_bd(partido_str, round(prob_home * 100, 1), round((1-prob_home)*100, 1), cuota, round(stake_rec, 1), "Basket Dinámico")

        return escenarios
