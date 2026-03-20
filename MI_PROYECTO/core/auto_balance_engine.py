from typing import Dict, List

try:
    from core.learning_engine import obtener_historial, obtener_estadisticas
except Exception:
    obtener_historial = None
    obtener_estadisticas = None


# =========================================================
# CONFIG BASE
# =========================================================
RECENT_SAMPLE_SIZE = 20

BASE_MIN_CONFIDENCE = 70
BASE_CONTEXT_MIN_SCORE = 35
BASE_CHAOS_CONFIDENCE_BLOCK = 75

MIN_CONFIDENCE_FLOOR = 62
MIN_CONFIDENCE_CEIL = 82

CONTEXT_SCORE_FLOOR = 25
CONTEXT_SCORE_CEIL = 50

CHAOS_BLOCK_FLOOR = 68
CHAOS_BLOCK_CEIL = 88


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


def _clamp(value, low, high):
    return max(low, min(high, value))


def _get_recent_resolved(history: List[Dict], sample_size: int = RECENT_SAMPLE_SIZE) -> List[Dict]:
    resolved = [x for x in history if x.get("status") == "RESOLVED"]
    resolved.sort(key=lambda x: str(x.get("resolved_at") or x.get("created_at") or ""))
    return resolved[-sample_size:]


def _count_recent_open(history: List[Dict], sample_size: int = RECENT_SAMPLE_SIZE) -> int:
    recent = history[-sample_size:]
    return sum(1 for x in recent if x.get("status") == "OPEN")


# =========================================================
# ANALISIS RECIENTE
# =========================================================
def analizar_rendimiento_reciente() -> Dict:
    if not obtener_historial:
        return {
            "sample_size": 0,
            "wins": 0,
            "losses": 0,
            "voids": 0,
            "resolved": 0,
            "winrate": 0.0,
            "avg_confidence": 0.0,
            "avg_value": 0.0,
            "recent_open_signals": 0,
            "mode": "NEUTRAL",
            "reason": "Sin historial disponible",
        }

    history = obtener_historial()
    recent_resolved = _get_recent_resolved(history, RECENT_SAMPLE_SIZE)

    wins = sum(1 for x in recent_resolved if x.get("result") == "WIN")
    losses = sum(1 for x in recent_resolved if x.get("result") == "LOSS")
    voids = sum(1 for x in recent_resolved if x.get("result") == "VOID")
    effective = wins + losses

    winrate = round((wins / effective) * 100, 2) if effective > 0 else 0.0

    avg_confidence = round(
        sum(_safe_float(x.get("confidence"), 0) for x in recent_resolved) / len(recent_resolved),
        2
    ) if recent_resolved else 0.0

    avg_value = round(
        sum(_safe_float(x.get("value"), 0) for x in recent_resolved) / len(recent_resolved),
        2
    ) if recent_resolved else 0.0

    recent_open = _count_recent_open(history, RECENT_SAMPLE_SIZE)

    mode = "NEUTRAL"
    reason = "Sistema en equilibrio"

    if effective >= 6:
        if winrate < 45:
            mode = "STRICT"
            reason = "Rendimiento reciente bajo, conviene endurecer"
        elif winrate >= 60:
            mode = "FLEX"
            reason = "Rendimiento reciente fuerte, se puede flexibilizar"
    else:
        if recent_open == 0:
            mode = "FLEX"
            reason = "Pocas señales útiles recientes, conviene abrir un poco"

    return {
        "sample_size": len(recent_resolved),
        "wins": wins,
        "losses": losses,
        "voids": voids,
        "resolved": len(recent_resolved),
        "winrate": winrate,
        "avg_confidence": avg_confidence,
        "avg_value": avg_value,
        "recent_open_signals": recent_open,
        "mode": mode,
        "reason": reason,
    }


# =========================================================
# GENERAR AJUSTES
# =========================================================
def obtener_balance_dinamico() -> Dict:
    recent = analizar_rendimiento_reciente()

    min_confidence = BASE_MIN_CONFIDENCE
    context_min_score = BASE_CONTEXT_MIN_SCORE
    chaos_confidence_block = BASE_CHAOS_CONFIDENCE_BLOCK
    value_flex_mode = False

    mode = recent.get("mode", "NEUTRAL")
    winrate = _safe_float(recent.get("winrate"), 0)
    resolved = _safe_int(recent.get("resolved"), 0)
    recent_open = _safe_int(recent.get("recent_open_signals"), 0)

    if mode == "STRICT":
        min_confidence += 4
        context_min_score += 4
        chaos_confidence_block += 3
        value_flex_mode = False

        if resolved >= 10 and winrate < 40:
            min_confidence += 2
            context_min_score += 2

    elif mode == "FLEX":
        min_confidence -= 4
        context_min_score -= 5
        chaos_confidence_block -= 4
        value_flex_mode = True

        if resolved >= 8 and winrate >= 65:
            min_confidence -= 2
            context_min_score -= 2

        if recent_open == 0:
            min_confidence -= 2
            context_min_score -= 2
            value_flex_mode = True

    min_confidence = _clamp(min_confidence, MIN_CONFIDENCE_FLOOR, MIN_CONFIDENCE_CEIL)
    context_min_score = _clamp(context_min_score, CONTEXT_SCORE_FLOOR, CONTEXT_SCORE_CEIL)
    chaos_confidence_block = _clamp(chaos_confidence_block, CHAOS_BLOCK_FLOOR, CHAOS_BLOCK_CEIL)

    return {
        "mode": mode,
        "reason": recent.get("reason", "Sin razón"),
        "recent_winrate": winrate,
        "recent_resolved": resolved,
        "recent_open_signals": recent_open,
        "min_confidence": min_confidence,
        "context_min_score": context_min_score,
        "chaos_confidence_block": chaos_confidence_block,
        "value_flex_mode": value_flex_mode,
    }


# =========================================================
# APLICAR SOBRE UNA SEÑAL
# =========================================================
def aplicar_auto_balance(signal: Dict) -> Dict:
    if not isinstance(signal, dict):
        return signal

    balance = obtener_balance_dinamico()

    signal["auto_balance_mode"] = balance.get("mode", "NEUTRAL")
    signal["auto_balance_reason"] = balance.get("reason", "")
    signal["auto_balance_recent_winrate"] = balance.get("recent_winrate", 0)
    signal["auto_balance_recent_resolved"] = balance.get("recent_resolved", 0)

    signal["dynamic_min_confidence"] = balance.get("min_confidence", BASE_MIN_CONFIDENCE)
    signal["dynamic_context_min_score"] = balance.get("context_min_score", BASE_CONTEXT_MIN_SCORE)
    signal["dynamic_chaos_confidence_block"] = balance.get("chaos_confidence_block", BASE_CHAOS_CONFIDENCE_BLOCK)
    signal["dynamic_value_flex_mode"] = balance.get("value_flex_mode", False)

    return signal


# =========================================================
# VALIDACIONES DINAMICAS
# =========================================================
def validar_confianza_dinamica(signal: Dict) -> bool:
    confidence = _safe_float(signal.get("confidence"), 0)
    dynamic_min = _safe_float(signal.get("dynamic_min_confidence"), BASE_MIN_CONFIDENCE)
    return confidence >= dynamic_min


def validar_contexto_dinamico(signal: Dict) -> bool:
    context_score = _safe_float(signal.get("context_score"), BASE_CONTEXT_MIN_SCORE)
    dynamic_context_min = _safe_float(signal.get("dynamic_context_min_score"), BASE_CONTEXT_MIN_SCORE)

    if signal.get("context_state") == "CAOS_INESTABLE":
        return False

    return context_score >= dynamic_context_min


def validar_chaos_dinamico(signal: Dict) -> bool:
    chaos_block_signal = bool(signal.get("chaos_block_signal", False))
    confidence = _safe_float(signal.get("confidence"), 0)
    dynamic_chaos_block = _safe_float(signal.get("dynamic_chaos_confidence_block"), BASE_CHAOS_CONFIDENCE_BLOCK)

    if chaos_block_signal and confidence < dynamic_chaos_block:
        return False

    return True


def permitir_value_flex(signal: Dict) -> bool:
    return bool(signal.get("dynamic_value_flex_mode", False))
