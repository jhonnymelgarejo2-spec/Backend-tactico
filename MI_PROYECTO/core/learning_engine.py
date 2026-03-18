import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from core.result_resolver import resolver_resultado_senal
except Exception:
    resolver_resultado_senal = None


HISTORY_DIR = "data"
HISTORY_FILE = os.path.join(HISTORY_DIR, "match_history.json")


# =========================================================
# HELPERS
# =========================================================
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _safe_str(value, default="") -> str:
    try:
        return str(value if value is not None else default)
    except Exception:
        return default


def _ensure_storage():
    os.makedirs(HISTORY_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load_history() -> List[Dict]:
    _ensure_storage()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_history(history: List[Dict]):
    _ensure_storage()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _build_signal_uid(signal: Dict) -> str:
    match_id = _safe_str(signal.get("match_id"))
    market = _safe_str(signal.get("market"))
    minute = _safe_str(signal.get("minute"))
    selection = _safe_str(signal.get("selection"))
    return f"{match_id}__{market}__{minute}__{selection}"


# =========================================================
# REGISTRO DE SEÑALES
# =========================================================
def registrar_senal(signal: Dict) -> bool:
    """
    Registra una señal aprobada por el pipeline.
    Evita duplicados por match_id + market + minute + selection.
    """
    if not isinstance(signal, dict):
        return False

    history = _load_history()
    signal_uid = _build_signal_uid(signal)

    for item in history:
        if item.get("signal_uid") == signal_uid:
            return False

    record = {
        "signal_uid": signal_uid,
        "created_at": _utc_now_iso(),
        "resolved_at": None,
        "status": "OPEN",  # OPEN / RESOLVED
        "result": None,    # WIN / LOSS / VOID

        "match_id": _safe_str(signal.get("match_id")),
        "home": _safe_str(signal.get("home")),
        "away": _safe_str(signal.get("away")),
        "league": _safe_str(signal.get("league")),
        "country": _safe_str(signal.get("country")),
        "minute": _safe_int(signal.get("minute"), 0),
        "score_at_signal": _safe_str(signal.get("score")),

        "market": _safe_str(signal.get("market")),
        "selection": _safe_str(signal.get("selection")),
        "line": signal.get("line"),
        "odd": _safe_float(signal.get("odd"), 0.0),
        "prob": _safe_float(signal.get("prob"), 0.0),
        "value": _safe_float(signal.get("value"), 0.0),
        "value_score": _safe_float(signal.get("value_score"), 0.0),
        "confidence": _safe_float(signal.get("confidence"), 0.0),

        "signal_score": _safe_float(signal.get("signal_score"), 0.0),
        "tactical_score": _safe_float(signal.get("tactical_score"), 0.0),
        "goal_inminente_score": _safe_float(signal.get("goal_inminente_score"), 0.0),
        "risk_score": _safe_float(signal.get("risk_score"), 0.0),

        "publish_ready": bool(signal.get("publish_ready", False)),
        "publish_rank": _safe_int(signal.get("publish_rank"), 0),
        "signal_rank": _safe_str(signal.get("signal_rank")),
        "tier": _safe_str(signal.get("tier")),

        "ai_recommendation": _safe_str(signal.get("ai_recommendation")),
        "ai_decision_score": _safe_float(signal.get("ai_decision_score"), 0.0),
        "ai_confidence_final": _safe_float(signal.get("ai_confidence_final"), 0.0),
        "ai_state": _safe_str(signal.get("ai_state")),
        "ai_reason": _safe_str(signal.get("ai_reason")),
        "ai_fit": _safe_str(signal.get("ai_fit")),
        "ai_fit_reason": _safe_str(signal.get("ai_fit_reason")),

        "context_state": _safe_str(signal.get("context_state")),
        "context_score": _safe_float(signal.get("context_score"), 0.0),
        "context_risk": _safe_str(signal.get("context_risk")),
        "context_reason": _safe_str(signal.get("context_reason")),

        "resultado_probable": _safe_str(signal.get("resultado_probable")),
        "ganador_probable": _safe_str(signal.get("ganador_probable")),
        "doble_oportunidad_probable": _safe_str(signal.get("doble_oportunidad_probable")),
        "total_goles_estimado": _safe_float(signal.get("total_goles_estimado"), 0.0),
        "linea_goles_probable": _safe_str(signal.get("linea_goles_probable")),
        "over_under_probable": _safe_str(signal.get("over_under_probable")),

        "reason": _safe_str(signal.get("reason")),
        "razon_value": _safe_str(signal.get("razon_value")),
        "riesgo_operativo": _safe_str(signal.get("riesgo_operativo")),

        "final_home_goals": None,
        "final_away_goals": None,
        "final_score": None,
    }

    history.append(record)
    _save_history(history)
    return True


# =========================================================
# RESOLUCIÓN MANUAL
# =========================================================
def actualizar_resultado(signal_uid: str, result: str) -> bool:
    history = _load_history()
    updated = False
    result = _safe_str(result).upper()

    if result not in ("WIN", "LOSS", "VOID"):
        return False

    for item in history:
        if item.get("signal_uid") == signal_uid:
            item["result"] = result
            item["status"] = "RESOLVED"
            item["resolved_at"] = _utc_now_iso()
            updated = True
            break

    if updated:
        _save_history(history)

    return updated


# =========================================================
# RESOLVER PARTIDO FINALIZADO
# =========================================================
def resolver_partido_finalizado(match: Dict) -> int:
    """
    Resuelve todas las señales OPEN del partido finalizado.
    Devuelve cuántas señales resolvió.
    """
    if not isinstance(match, dict):
        return 0

    if resolver_resultado_senal is None:
        return 0

    match_id = _safe_str(match.get("id"))
    if not match_id:
        return 0

    history = _load_history()
    resolved_count = 0

    final_home = _safe_int(match.get("marcador_local"), 0)
    final_away = _safe_int(match.get("marcador_visitante"), 0)
    final_score = f"{final_home}-{final_away}"

    for item in history:
        if _safe_str(item.get("match_id")) != match_id:
            continue

        if item.get("status") == "RESOLVED":
            continue

        try:
            result = resolver_resultado_senal(match, item)
        except Exception as e:
            print(f"[LEARNING] ERROR resolver_resultado_senal -> {e}")
            continue

        if result not in ("WIN", "LOSS", "VOID"):
            continue

        item["result"] = result
        item["status"] = "RESOLVED"
        item["resolved_at"] = _utc_now_iso()
        item["final_home_goals"] = final_home
        item["final_away_goals"] = final_away
        item["final_score"] = final_score
        resolved_count += 1

    if resolved_count > 0:
        _save_history(history)

    return resolved_count


def resolver_partidos_finalizados(matches: List[Dict]) -> int:
    total = 0
    for match in matches:
        try:
            total += resolver_partido_finalizado(match)
        except Exception as e:
            print(f"[LEARNING] ERROR resolver_partido_finalizado -> {e}")
    return total


# =========================================================
# CONSULTAS BÁSICAS
# =========================================================
def obtener_historial() -> List[Dict]:
    return _load_history()


def obtener_senales_abiertas() -> List[Dict]:
    history = _load_history()
    return [x for x in history if x.get("status") == "OPEN"]


def obtener_senales_resueltas() -> List[Dict]:
    history = _load_history()
    return [x for x in history if x.get("status") == "RESOLVED"]


# =========================================================
# MÉTRICAS GENERALES
# =========================================================
def obtener_estadisticas() -> Dict:
    history = _load_history()

    total = len(history)
    open_count = sum(1 for x in history if x.get("status") == "OPEN")
    resolved = [x for x in history if x.get("status") == "RESOLVED"]

    wins = sum(1 for x in resolved if x.get("result") == "WIN")
    losses = sum(1 for x in resolved if x.get("result") == "LOSS")
    voids = sum(1 for x in resolved if x.get("result") == "VOID")

    effective_resolved = wins + losses
    winrate = round((wins / effective_resolved) * 100, 2) if effective_resolved > 0 else 0.0

    avg_value = round(
        sum(_safe_float(x.get("value"), 0) for x in history) / total, 2
    ) if total > 0 else 0.0

    avg_risk = round(
        sum(_safe_float(x.get("risk_score"), 0) for x in history) / total, 2
    ) if total > 0 else 0.0

    avg_conf = round(
        sum(_safe_float(x.get("confidence"), 0) for x in history) / total, 2
    ) if total > 0 else 0.0

    return {
        "total": total,
        "open": open_count,
        "resolved": len(resolved),
        "wins": wins,
        "losses": losses,
        "voids": voids,
        "winrate": winrate,
        "avg_value": avg_value,
        "avg_risk": avg_risk,
        "avg_confidence": avg_conf,
    }


# =========================================================
# MÉTRICAS POR MERCADO
# =========================================================
def estadisticas_por_mercado() -> Dict[str, Dict]:
    history = _load_history()
    grouped: Dict[str, Dict] = {}

    for item in history:
        market = _safe_str(item.get("market"), "UNKNOWN")
        if market not in grouped:
            grouped[market] = {
                "total": 0,
                "resolved": 0,
                "wins": 0,
                "losses": 0,
                "voids": 0,
                "winrate": 0.0,
                "avg_value": 0.0,
                "avg_confidence": 0.0,
            }

        grouped[market]["total"] += 1
        grouped[market]["avg_value"] += _safe_float(item.get("value"), 0)
        grouped[market]["avg_confidence"] += _safe_float(item.get("confidence"), 0)

        if item.get("status") == "RESOLVED":
            grouped[market]["resolved"] += 1
            if item.get("result") == "WIN":
                grouped[market]["wins"] += 1
            elif item.get("result") == "LOSS":
                grouped[market]["losses"] += 1
            elif item.get("result") == "VOID":
                grouped[market]["voids"] += 1

    for market, stats in grouped.items():
        total = stats["total"]
        effective = stats["wins"] + stats["losses"]
        stats["avg_value"] = round(stats["avg_value"] / total, 2) if total > 0 else 0.0
        stats["avg_confidence"] = round(stats["avg_confidence"] / total, 2) if total > 0 else 0.0
        stats["winrate"] = round((stats["wins"] / effective) * 100, 2) if effective > 0 else 0.0

    return grouped


# =========================================================
# MÉTRICAS POR LIGA
# =========================================================
def estadisticas_por_liga() -> Dict[str, Dict]:
    history = _load_history()
    grouped: Dict[str, Dict] = {}

    for item in history:
        league = _safe_str(item.get("league"), "UNKNOWN")
        if league not in grouped:
            grouped[league] = {
                "total": 0,
                "resolved": 0,
                "wins": 0,
                "losses": 0,
                "voids": 0,
                "winrate": 0.0,
                "avg_value": 0.0,
                "avg_confidence": 0.0,
            }

        grouped[league]["total"] += 1
        grouped[league]["avg_value"] += _safe_float(item.get("value"), 0)
        grouped[league]["avg_confidence"] += _safe_float(item.get("confidence"), 0)

        if item.get("status") == "RESOLVED":
            grouped[league]["resolved"] += 1
            if item.get("result") == "WIN":
                grouped[league]["wins"] += 1
            elif item.get("result") == "LOSS":
                grouped[league]["losses"] += 1
            elif item.get("result") == "VOID":
                grouped[league]["voids"] += 1

    for league, stats in grouped.items():
        total = stats["total"]
        effective = stats["wins"] + stats["losses"]
        stats["avg_value"] = round(stats["avg_value"] / total, 2) if total > 0 else 0.0
        stats["avg_confidence"] = round(stats["avg_confidence"] / total, 2) if total > 0 else 0.0
        stats["winrate"] = round((stats["wins"] / effective) * 100, 2) if effective > 0 else 0.0

    return grouped


# =========================================================
# MEJORES Y PEORES SEGMENTOS
# =========================================================
def obtener_mejor_mercado() -> Optional[Dict]:
    stats = estadisticas_por_mercado()
    candidates = []

    for market, data in stats.items():
        if data["wins"] + data["losses"] < 3:
            continue
        candidates.append({
            "market": market,
            "winrate": data["winrate"],
            "resolved": data["resolved"],
            "wins": data["wins"],
            "losses": data["losses"],
        })

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x["winrate"], x["wins"]), reverse=True)
    return candidates[0]


def obtener_peor_mercado() -> Optional[Dict]:
    stats = estadisticas_por_mercado()
    candidates = []

    for market, data in stats.items():
        if data["wins"] + data["losses"] < 3:
            continue
        candidates.append({
            "market": market,
            "winrate": data["winrate"],
            "resolved": data["resolved"],
            "wins": data["wins"],
            "losses": data["losses"],
        })

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x["winrate"], -x["losses"]))
    return candidates[0]


def obtener_mejor_liga() -> Optional[Dict]:
    stats = estadisticas_por_liga()
    candidates = []

    for league, data in stats.items():
        if data["wins"] + data["losses"] < 3:
            continue
        candidates.append({
            "league": league,
            "winrate": data["winrate"],
            "resolved": data["resolved"],
            "wins": data["wins"],
            "losses": data["losses"],
        })

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x["winrate"], x["wins"]), reverse=True)
    return candidates[0]


# =========================================================
# INSIGHTS SIMPLES
# =========================================================
def detectar_patrones() -> Dict:
    history = _load_history()
    resolved = [x for x in history if x.get("status") == "RESOLVED"]

    high_conf_losses = 0
    low_conf_losses = 0
    high_value_losses = 0
    hold_wins = 0
    hold_total = 0

    for item in resolved:
        conf = _safe_float(item.get("confidence"), 0)
        value = _safe_float(item.get("value"), 0)
        market = _safe_str(item.get("market"))

        if item.get("result") == "LOSS":
            if conf >= 80:
                high_conf_losses += 1
            else:
                low_conf_losses += 1

            if value >= 10:
                high_value_losses += 1

        if "RESULT_HOLDS" in market or "HOLD" in market:
            hold_total += 1
            if item.get("result") == "WIN":
                hold_wins += 1

    hold_winrate = round((hold_wins / hold_total) * 100, 2) if hold_total > 0 else 0.0

    return {
        "high_conf_losses": high_conf_losses,
        "low_conf_losses": low_conf_losses,
        "high_value_losses": high_value_losses,
        "hold_winrate": hold_winrate,
        "insight": (
            "El sistema está fallando señales de alta confianza"
            if high_conf_losses > low_conf_losses
            else "El sistema mantiene una pérdida más controlada en señales altas"
        ),
              }
