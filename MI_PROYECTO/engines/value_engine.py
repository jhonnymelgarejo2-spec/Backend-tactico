from typing import Dict, Any


def clamp(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def to_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except Exception:
        return default


def calcular_probabilidad_implicita(cuota: float) -> float:
    cuota = to_float(cuota, 0.0)

    if cuota <= 0:
        return 0.0

    return round(1 / cuota, 4)


def calcular_value(prob_real: float, cuota: float) -> float:
    prob_real = to_float(prob_real, 0.0)
    prob_implicita = calcular_probabilidad_implicita(cuota)

    if prob_real <= 0 or prob_implicita <= 0:
        return 0.0

    value = (prob_real - prob_implicita) * 100
    return round(value, 2)


def calcular_edge(prob_real: float, prob_implicita: float) -> float:
    prob_real = to_float(prob_real, 0.0)
    prob_implicita = to_float(prob_implicita, 0.0)

    if prob_implicita <= 0:
        return 0.0

    edge = ((prob_real / prob_implicita) - 1) * 100
    return round(edge, 2)


def clasificar_value(value_pct: float) -> str:
    value_pct = to_float(value_pct, 0.0)

    if value_pct >= 12:
        return "VALUE_ELITE"
    if value_pct >= 8:
        return "VALUE_ALTO"
    if value_pct >= 5:
        return "VALUE_MEDIO"
    if value_pct >= 2:
        return "VALUE_BAJO"
    return "SIN_VALUE"


def score_value(value_pct: float) -> float:
    value_pct = to_float(value_pct, 0.0)

    if value_pct <= 0:
        return 0.0

    # Escala progresiva, tope 10
    if value_pct >= 15:
        return 10.0
    if value_pct >= 12:
        return 9.0
    if value_pct >= 10:
        return 8.0
    if value_pct >= 8:
        return 7.0
    if value_pct >= 6:
        return 6.0
    if value_pct >= 4:
        return 4.5
    if value_pct >= 2:
        return 3.0

    return 1.0


def evaluar_value(prob_real: float, cuota: float) -> Dict[str, Any]:
    prob_real = clamp(to_float(prob_real, 0.0), 0.0, 1.0)
    cuota = to_float(cuota, 0.0)

    prob_implicita = calcular_probabilidad_implicita(cuota)
    value_pct = calcular_value(prob_real, cuota)
    edge_pct = calcular_edge(prob_real, prob_implicita)
    categoria = clasificar_value(value_pct)
    value_score = score_value(value_pct)

    if categoria == "VALUE_ELITE":
        recomendacion = "APOSTAR_FUERTE"
        razon = "El mercado ofrece una diferencia muy alta a favor de la probabilidad estimada"
    elif categoria == "VALUE_ALTO":
        recomendacion = "APOSTAR"
        razon = "La cuota está claramente por encima del valor esperado"
    elif categoria == "VALUE_MEDIO":
        recomendacion = "APOSTAR_SUAVE"
        razon = "Existe valor positivo razonable en la cuota"
    elif categoria == "VALUE_BAJO":
        recomendacion = "OBSERVAR"
        razon = "Hay pequeño valor, pero no es de máxima calidad"
    else:
        recomendacion = "NO_APOSTAR"
        razon = "No se detecta ventaja real sobre la probabilidad implícita"

    return {
        "prob_real": round(prob_real, 4),
        "prob_implicita": round(prob_implicita, 4),
        "value_pct": round(value_pct, 2),
        "edge_pct": round(edge_pct, 2),
        "value_score": round(value_score, 2),
        "value_categoria": categoria,
        "recomendacion_value": recomendacion,
        "razon_value": razon,
}
