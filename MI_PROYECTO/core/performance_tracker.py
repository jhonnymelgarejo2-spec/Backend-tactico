from typing import Dict, List

try:
    from core.learning_engine import obtener_historial
except Exception:
    obtener_historial = None


# =========================================================
# HELPERS
# =========================================================
def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


# =========================================================
# PROFIT POR SEÑAL
# =========================================================
def calcular_profit_senal(signal: Dict) -> float:
    if not isinstance(signal, dict):
        return 0.0

    resultado = _safe_upper(
        signal.get("estado_resultado")
        or signal.get("result")
        or signal.get("resultado")
    )

    stake = _safe_float(signal.get("stake_amount", 0), 0.0)
    odd = _safe_float(signal.get("odd", signal.get("cuota", 0)), 0.0)

    if stake <= 0:
        return 0.0

    if resultado in ("GANADA", "WIN", "WON"):
        if odd <= 1.0:
            return 0.0
        return round(stake * (odd - 1.0), 2)

    if resultado in ("PERDIDA", "LOSS", "LOST"):
        return round(-stake, 2)

    if resultado in ("VOID", "NULA", "PUSH"):
        return 0.0

    return 0.0


# =========================================================
# HISTORIAL RESUELTO
# =========================================================
def obtener_senales_resueltas() -> List[Dict]:
    if not obtener_historial:
        return []

    try:
        historial = obtener_historial()
    except Exception:
        return []

    resueltas = []
    for x in historial:
        resultado = _safe_upper(
            x.get("estado_resultado")
            or x.get("result")
            or x.get("resultado")
        )
        if resultado in ("GANADA", "WIN", "WON", "PERDIDA", "LOSS", "LOST", "VOID", "NULA", "PUSH"):
            resueltas.append(x)

    return resueltas


# =========================================================
# RESUMEN GENERAL
# =========================================================
def obtener_resumen_rendimiento() -> Dict:
    senales = obtener_senales_resueltas()

    total = len(senales)
    wins = 0
    losses = 0
    voids = 0
    total_stake = 0.0
    total_profit = 0.0

    for s in senales:
        resultado = _safe_upper(
            s.get("estado_resultado")
            or s.get("result")
            or s.get("resultado")
        )

        if resultado in ("GANADA", "WIN", "WON"):
            wins += 1
        elif resultado in ("PERDIDA", "LOSS", "LOST"):
            losses += 1
        elif resultado in ("VOID", "NULA", "PUSH"):
            voids += 1

        stake = _safe_float(s.get("stake_amount", 0), 0.0)
        total_stake += stake
        total_profit += calcular_profit_senal(s)

    resolved_effective = wins + losses
    winrate = round((wins / resolved_effective) * 100, 2) if resolved_effective > 0 else 0.0
    roi = round((total_profit / total_stake) * 100, 2) if total_stake > 0 else 0.0
    stake_promedio = round(total_stake / total, 2) if total > 0 else 0.0
    profit_promedio = round(total_profit / total, 2) if total > 0 else 0.0

    return {
        "total_resueltas": total,
        "wins": wins,
        "losses": losses,
        "voids": voids,
        "winrate": winrate,
        "roi_percent": roi,
        "total_stake": round(total_stake, 2),
        "total_profit": round(total_profit, 2),
        "stake_promedio": stake_promedio,
        "profit_promedio": profit_promedio,
    }


# =========================================================
# RESUMEN POR MERCADO
# =========================================================
def obtener_rendimiento_por_mercado() -> List[Dict]:
    senales = obtener_senales_resueltas()
    data = {}

    for s in senales:
        mercado = str(s.get("market") or s.get("mercado") or "SIN_MERCADO").strip()

        if mercado not in data:
            data[mercado] = {
                "market": mercado,
                "total": 0,
                "wins": 0,
                "losses": 0,
                "voids": 0,
                "stake": 0.0,
                "profit": 0.0,
            }

        resultado = _safe_upper(
            s.get("estado_resultado")
            or s.get("result")
            or s.get("resultado")
        )

        data[mercado]["total"] += 1
        data[mercado]["stake"] += _safe_float(s.get("stake_amount", 0), 0.0)
        data[mercado]["profit"] += calcular_profit_senal(s)

        if resultado in ("GANADA", "WIN", "WON"):
            data[mercado]["wins"] += 1
        elif resultado in ("PERDIDA", "LOSS", "LOST"):
            data[mercado]["losses"] += 1
        elif resultado in ("VOID", "NULA", "PUSH"):
            data[mercado]["voids"] += 1

    resultado_final = []
    for mercado, row in data.items():
        effective = row["wins"] + row["losses"]
        row["winrate"] = round((row["wins"] / effective) * 100, 2) if effective > 0 else 0.0
        row["roi_percent"] = round((row["profit"] / row["stake"]) * 100, 2) if row["stake"] > 0 else 0.0
        row["stake"] = round(row["stake"], 2)
        row["profit"] = round(row["profit"], 2)
        resultado_final.append(row)

    resultado_final.sort(key=lambda x: (x["roi_percent"], x["winrate"], x["total"]), reverse=True)
    return resultado_final


# =========================================================
# RESUMEN POR LIGA
# =========================================================
def obtener_rendimiento_por_liga() -> List[Dict]:
    senales = obtener_senales_resueltas()
    data = {}

    for s in senales:
        liga = str(s.get("league") or s.get("liga") or "SIN_LIGA").strip()

        if liga not in data:
            data[liga] = {
                "league": liga,
                "total": 0,
                "wins": 0,
                "losses": 0,
                "voids": 0,
                "stake": 0.0,
                "profit": 0.0,
            }

        resultado = _safe_upper(
            s.get("estado_resultado")
            or s.get("result")
            or s.get("resultado")
        )

        data[liga]["total"] += 1
        data[liga]["stake"] += _safe_float(s.get("stake_amount", 0), 0.0)
        data[liga]["profit"] += calcular_profit_senal(s)

        if resultado in ("GANADA", "WIN", "WON"):
            data[liga]["wins"] += 1
        elif resultado in ("PERDIDA", "LOSS", "LOST"):
            data[liga]["losses"] += 1
        elif resultado in ("VOID", "NULA", "PUSH"):
            data[liga]["voids"] += 1

    resultado_final = []
    for liga, row in data.items():
        effective = row["wins"] + row["losses"]
        row["winrate"] = round((row["wins"] / effective) * 100, 2) if effective > 0 else 0.0
        row["roi_percent"] = round((row["profit"] / row["stake"]) * 100, 2) if row["stake"] > 0 else 0.0
        row["stake"] = round(row["stake"], 2)
        row["profit"] = round(row["profit"], 2)
        resultado_final.append(row)

    resultado_final.sort(key=lambda x: (x["roi_percent"], x["winrate"], x["total"]), reverse=True)
    return resultado_final


# =========================================================
# MEJORES Y PEORES
# =========================================================
def obtener_insights_rendimiento() -> Dict:
    mercados = obtener_rendimiento_por_mercado()
    ligas = obtener_rendimiento_por_liga()
    resumen = obtener_resumen_rendimiento()

    mejor_mercado = mercados[0] if mercados else None
    peor_mercado = mercados[-1] if mercados else None

    mejor_liga = ligas[0] if ligas else None
    peor_liga = ligas[-1] if ligas else None

    return {
        "resumen": resumen,
        "mejor_mercado": mejor_mercado,
        "peor_mercado": peor_mercado,
        "mejor_liga": mejor_liga,
        "peor_liga": peor_liga,
        "mercados": mercados,
        "ligas": ligas,
  }
