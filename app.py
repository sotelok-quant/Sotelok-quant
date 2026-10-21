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
    aprobado = (prob_modelo >= 56.0) and (ev_porcentaje >= 2.0
