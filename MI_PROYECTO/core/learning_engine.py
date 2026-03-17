# core/learning_engine.py

import json
import os
from datetime import datetime
from typing import Dict, List

HISTORY_FILE = "data/match_history.json"


# =========================================================
# HELPERS
# =========================================================
def _ensure_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)


def _load_history() -> List[Dict]:
    _ensure_file()
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(data: List[Dict]):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


# =========================================================
# 1. REGISTRAR SEÑAL
# =========================================================
def registrar_senal(senal: Dict):
    history = _load_history()

    registro = {
        "timestamp": datetime.utcnow().isoformat(),
        "match_id": senal.get("match_id"),
        "home": senal.get("home"),
        "away": senal.get("away"),
        "league": senal.get("league"),
        "market": senal.get("market"),
        "selection": senal.get("selection"),
        "odd": senal.get("odd"),
        "confidence": senal.get("confidence"),
        "value": senal.get("value"),
        "value_score": senal.get("value_score"),
        "risk": senal.get("riesgo_operativo"),
        "minute": senal.get("minute"),
        "result": None,  # Se completa después
    }

    history.append(registro)
    _save_history(history)


# =========================================================
# 2. ACTUALIZAR RESULTADO
# =========================================================
def actualizar_resultado(match_id: str, resultado: str):
    """
    resultado: "WIN", "LOSS", "VOID"
    """
    history = _load_history()

    for item in history:
        if item.get("match_id") == match_id and item.get("result") is None:
            item["result"] = resultado
            item["resolved_at"] = datetime.utcnow().isoformat()

    _save_history(history)


# =========================================================
# 3. ESTADÍSTICAS GENERALES
# =========================================================
def obtener_estadisticas():
    history = _load_history()

    total = 0
    wins = 0
    losses = 0

    for h in history:
        if h.get("result") is None:
            continue

        total += 1

        if h["result"] == "WIN":
            wins += 1
        elif h["result"] == "LOSS":
            losses += 1

    winrate = (wins / total * 100) if total > 0 else 0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "winrate": round(winrate, 2),
    }


# =========================================================
# 4. ESTADÍSTICAS POR MERCADO
# =========================================================
def estadisticas_por_mercado():
    history = _load_history()
    data = {}

    for h in history:
        if h.get("result") is None:
            continue

        market = h.get("market", "UNKNOWN")

        if market not in data:
            data[market] = {"total": 0, "wins": 0}

        data[market]["total"] += 1

        if h["result"] == "WIN":
            data[market]["wins"] += 1

    # calcular winrate
    for market in data:
        total = data[market]["total"]
        wins = data[market]["wins"]
        data[market]["winrate"] = round((wins / total * 100), 2) if total > 0 else 0

    return data


# =========================================================
# 5. ESTADÍSTICAS POR LIGA
# =========================================================
def estadisticas_por_liga():
    history = _load_history()
    data = {}

    for h in history:
        if h.get("result") is None:
            continue

        league = h.get("league", "UNKNOWN")

        if league not in data:
            data[league] = {"total": 0, "wins": 0}

        data[league]["total"] += 1

        if h["result"] == "WIN":
            data[league]["wins"] += 1

    for league in data:
        total = data[league]["total"]
        wins = data[league]["wins"]
        data[league]["winrate"] = round((wins / total * 100), 2) if total > 0 else 0

    return data


# =========================================================
# 6. DETECCIÓN DE PATRONES (BÁSICO)
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
        "insight": "Muchas pérdidas en alta confianza" if high_conf_losses > low_conf_losses else "Pérdidas normales"
      }
