import random
import math

class SharpQuantEngine:
    def __init__(self, sports_category="futbol_secundaria"):
        self.sports_category = sports_category

    def ejecutar_simulacion_monte_carlo(self, xg_local, xg_visitante, iteraciones=5000):
        """Simulación estocástica basada en distribución de Poisson."""
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

    def generar_resumen_escenarios(self, local, visitante, prob_home, prob_draw, prob_away, cuota=1.95):
        """Genera el desglose táctico y cuantitativo incluyendo el filtro Kelly."""
        escenarios = []
        
        # Cálculo de Valor Esperado (EV) y Criterio de Kelly
        prob_real = prob_home
        prob_implicita = 1.0 / cuota if cuota > 0 else 0.5
        ev = (prob_real * (cuota - 1.0)) - (1.0 - prob_real)
        
        b = cuota - 1.0
        p = prob_real
        q = 1.0 - p
        f_kelly = (b * p - q) / b if b > 0 else 0.0
        stake_recomendado = max(0.0, f_kelly * 100)

        # Escenario 1: Dominio Local
        escenarios.append({
            "rango": f"ESCENARIO A // PROBABILIDAD {round(prob_home * 100, 1)}%",
            "titulo": f"Control Estructural de {local}",
            "analisis": f"El modelo proyecta presión alta en salida. EV estimado: {round(ev * 100, 2)}%. Stake recomendado (Kelly): {round(stake_recomendado, 1)}% de la caja."
        })

        # Escenario 2: Varianza / Visitante
        escenarios.append({
            "rango": f"ESCENARIO B // VARIANZA / VISITANTE {round(prob_away * 100, 1)}%",
            "titulo": f"Contragolpe y Cobertura de {visitante}",
            "analisis": f"Probabilidad de empate estimada en {round(prob_draw * 100, 1)}%. Se recomienda cautela si la cuota del visitante no supera el umbral de valor estocástico."
        })

        return escenarios
