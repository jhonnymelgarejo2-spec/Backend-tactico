import json
import os
from datetime import datetime
from typing import Dict, List

try:
    from core.result_resolver import resolver_resultado_senal
except Exception:
    resolver_resultado_senal = None

HISTORY_FILE = "data/match_history.json"


# =========================================================
# HELPERS
# =========================================================
def _ensure_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _load_history() -> List[Dict]:
    _ensure_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(data: List[Dict]):
    _ensure_file()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


# =========================================================
# 1. REGISTRAR SEÑAL
# =========================================================
def registrar_senal(senal: Dict):
    history = _load_history()

    match_id = senal.get("match_id")
    market = senal.get("market")
    minute = senal.get("minute")

    # evitar duplicados exactos
    for item in history:
        if (
            item.get("match_id") == match_id
            and item.get("market") == market
            and item.get("minute") == minute
            and item.get("result") is None
        ):
            return

    registro = {
        "timestamp": datetime.utcnow().isoformat(),
        "match_id": match_id,
        "home": senal.get("home"),
        "away": senal.get("away"),
        "league": senal.get("league"),
        "country": senal.get("country"),
        "market": market,
        "selection": senal.get("selection"),
        "score": senal.get("score"),
        "odd": senal.get("odd"),
        "confidence": senal.get("confidence"),
        "value": senal.get("value"),
        "value_score": senal.get("value_score"),
        "risk": senal.get("riesgo_operativo"),
        "minute": minute,
        "signal_rank": senal.get("signal_rank"),
        "ai_recommendation": senal.get("ai_recommendation"),
        "context_state": senal.get("context_state"),
        "context_score": senal.get("context_score"),
        "resultado_probable": senal.get("resultado_probable"),
        "ganador_probable": senal.get("ganador_probable"),
        "over_under_probable": senal.get("over_under_probable"),
        "line": senal.get("line"),
        "result": None,
        "resolved_at": None,
    }

    history.append(registro)
    _save_history(history)


# =========================================================
# 2. ACTUALIZAR RESULTADO MANUAL
# =========================================================
def actualizar_resultado(match_id: str, resultado: str):
    """
    resultado: WIN, LOSS, VOID
    """
    history = _load_history()
    updated = False

    for item in history:
        if item.get("match_id") == match_id and item.get("result") is None:
            item["result"] = resultado
            item["resolved_at"] = datetime.utcnow().isoformat()
            updated = True

    if updated:
        _save_history(history)


# =========================================================
# 3. RESOLVER AUTOMÁTICAMENTE UN PARTIDO FINALIZADO
# =========================================================
def resolver_partido_finalizado(match: Dict) -> int:
    """
    Recibe un partido ya finalizado y resuelve todas las señales abiertas
    asociadas a ese match_id.

    Devuelve la cantidad de señales resueltas.
    """
    if not resolver_resultado_senal:
        return 0

    history = _load_history()
    resolved_count = 0
    match_id = str(match.get("id"))

    for item in history:
        if str(item.get("match_id")) != match_id:
            continue

        if item.get("result") is not None:
            continue

        try:
            resultado = resolver_resultado_senal(match, item)
            item["result"] = resultado
            item["resolved_at"] = datetime.utcnow().isoformat()
            resolved_count += 1
        except Exception as e:
            print(f"[LEARNING] ERROR resolver_partido_finalizado -> {e}")

    if resolved_count > 0:
        _save_history(history)

    return resolved_count


# =========================================================
# 4. RESOLVER VARIOS PARTIDOS FINALIZADOS
# =========================================================
def resolver_partidos_finalizados(matches: List[Dict]) -> int:
    total_resueltas = 0

    for match in matches:
        try:
            total_resueltas += resolver_partido_finalizado(match)
        except Exception as e:
            print(f"[LEARNING] ERROR resolver_partidos_finalizados -> {e}")

    return total_resueltas


# =========================================================
# 5. ESTADÍSTICAS GENERALES
# =========================================================
def obtener_estadisticas():
    history = _load_history()

    total = 0
    wins = 0
    losses = 0
    voids = 0

    for h in history:
        if h.get("result") is None:
            continue

        total += 1

        if h["result"] == "WIN":
            wins += 1
        elif h["result"] == "LOSS":
            losses += 1
        elif h["result"] == "VOID":
            voids += 1

    winrate = (wins / total * 100) if total > 0 else 0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "voids": voids,
        "winrate": round(winrate, 2),
    }


# =========================================================
# 6. ESTADÍSTICAS POR MERCADO
# =========================================================
def estadisticas_por_mercado():
    history = _load_history()
    data = {}

    for h in history:
        if h.get("result") is None:
            continue

        market = h.get("market", "UNKNOWN")

        if market not in data:
            data[market] = {"total": 0, "wins": 0, "losses": 0, "voids": 0}

        data[market]["total"] += 1

        if h["result"] == "WIN":
            data[market]["wins"] += 1
        elif h["result"] == "LOSS":
            data[market]["losses"] += 1
        elif h["result"] == "VOID":
            data[market]["voids"] += 1

    for market in data:
        total = data[market]["total"]
        wins = data[market]["wins"]
        data[market]["winrate"] = round((wins / total * 100), 2) if total > 0 else 0

    return data


# =========================================================
# 7. ESTADÍSTICAS POR LIGA
# =========================================================
def estadisticas_por_liga():
    history = _load_history()
    data = {}

    for h in history:
        if h.get("result") is None:
            continue

        league = h.get("league", "UNKNOWN")

        if league not in data:
            data[league] = {"total": 0, "wins": 0, "losses": 0, "voids": 0}

        data[league]["total"] += 1

        if h["result"] == "WIN":
            data[league]["wins"] += 1
        elif h["result"] == "LOSS":
            data[league]["losses"] += 1
        elif h["result"] == "VOID":
            data[league]["voids"] += 1

    for league in data:
        total = data[league]["total"]
        wins = data[league]["wins"]
        data[league]["winrate"] = round((wins / total * 100), 2) if total > 0 else 0

    return data


# =========================================================
# 8. DETECCIÓN DE PATRONES BÁSICOS
# =========================================================
def detectar_patrones():
    history = _load_history()

    low_conf_losses = 0
    high_conf_losses = 0

    for h in history:
        if h.get("result") != "LOSS":
            continue

        conf = _safe_float(h.get("confidence"), 0)

        if conf < 70:
            low_conf_losses += 1
        else:
            high_conf_losses += 1

    return {
        "low_conf_losses": low_conf_losses,
        "high_conf_losses": high_conf_losses,
        "insight": (
            "Muchas pérdidas en alta confianza"
            if high_conf_losses > low_conf_losses
            else "Pérdidas normales"
        ),
    }


# =========================================================
# 9. SEÑALES ABIERTAS
# =========================================================
def obtener_senales_abiertas():
    history = _load_history()
    return [x for x in history if x.get("result") is None]
