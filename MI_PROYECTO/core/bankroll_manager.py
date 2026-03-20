from typing import Dict

try:
    from core.learning_engine import obtener_estadisticas
except Exception:
    obtener_estadisticas = None


# =========================================================
# CONFIG BASE
# =========================================================
DEFAULT_BANKROLL = 1000.0

MIN_STAKE_PCT = 1.0
BASE_STAKE_PCT = 2.0
MAX_STAKE_PCT = 5.0

MAX_OPERACIONES_DIA = 3
STOP_LOSS_CONSECUTIVO = 2


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


# =========================================================
# LECTURA SIMPLE DE RENDIMIENTO
# =========================================================
def obtener_contexto_bankroll() -> Dict:
    if not obtener_estadisticas:
        return {
            "wins": 0,
            "losses": 0,
            "resolved": 0,
            "winrate": 0.0,
            "modo": "NEUTRAL",
            "permitido_operar": True,
            "motivo": "Sin learning disponible",
            "operaciones_hoy": 0,
            "fallos_consecutivos": 0,
        }

    try:
        stats = obtener_estadisticas()
    except Exception:
        return {
            "wins": 0,
            "losses": 0,
            "resolved": 0,
            "winrate": 0.0,
            "modo": "NEUTRAL",
            "permitido_operar": True,
            "motivo": "Error leyendo estadísticas",
            "operaciones_hoy": 0,
            "fallos_consecutivos": 0,
        }

    wins = _safe_int(stats.get("wins", 0), 0)
    losses = _safe_int(stats.get("losses", 0), 0)
    resolved = _safe_int(stats.get("resolved", 0), 0)
    winrate = _safe_float(stats.get("winrate", 0), 0.0)

    modo = "NEUTRAL"
    if resolved >= 5:
        if winrate >= 60:
            modo = "AGRESIVO"
        elif winrate < 45:
            modo = "DEFENSIVO"

    return {
        "wins": wins,
        "losses": losses,
        "resolved": resolved,
        "winrate": winrate,
        "modo": modo,
        "permitido_operar": True,
        "motivo": "Contexto bankroll calculado",
        "operaciones_hoy": 0,
        "fallos_consecutivos": 0,
    }


# =========================================================
# STAKE
# =========================================================
def calcular_stake(signal: Dict, bankroll: float = DEFAULT_BANKROLL) -> Dict:
    bankroll = _safe_float(bankroll, DEFAULT_BANKROLL)

    confidence = _safe_float(signal.get("confidence", 0), 0)
    value = _safe_float(signal.get("value", 0), 0)
    ai_score = _safe_float(signal.get("ai_decision_score", 0), 0)
    risk_score = _safe_float(signal.get("risk_score", 5), 5)

    contexto = obtener_contexto_bankroll()
    modo = contexto.get("modo", "NEUTRAL")

    stake_pct = BASE_STAKE_PCT

    # confianza
    if confidence >= 85:
        stake_pct += 1.2
    elif confidence >= 78:
        stake_pct += 0.8
    elif confidence >= 72:
        stake_pct += 0.4

    # value
    if value >= 15:
        stake_pct += 1.0
    elif value >= 10:
        stake_pct += 0.6
    elif value >= 6:
        stake_pct += 0.3

    # IA
    if ai_score >= 110:
        stake_pct += 0.7
    elif ai_score >= 90:
        stake_pct += 0.4

    # riesgo
    if risk_score >= 6:
        stake_pct -= 1.0
    elif risk_score >= 4:
        stake_pct -= 0.5

    # modo bankroll
    if modo == "AGRESIVO":
        stake_pct += 0.4
    elif modo == "DEFENSIVO":
        stake_pct -= 0.8

    stake_pct = _clamp(stake_pct, MIN_STAKE_PCT, MAX_STAKE_PCT)
    stake_amount = round(bankroll * (stake_pct / 100.0), 2)

    if stake_pct >= 4.0:
        stake_label = "FUERTE"
    elif stake_pct >= 2.5:
        stake_label = "MEDIO"
    else:
        stake_label = "BAJO"

    return {
        "stake_pct": round(stake_pct, 2),
        "stake_amount": stake_amount,
        "stake_label": stake_label,
        "bankroll_mode": modo,
    }


# =========================================================
# REGLAS DE BLOQUEO
# =========================================================
def validar_operacion(signal: Dict, bankroll: float = DEFAULT_BANKROLL) -> Dict:
    contexto = obtener_contexto_bankroll()
    confidence = _safe_float(signal.get("confidence", 0), 0)
    value = _safe_float(signal.get("value", 0), 0)

    permitido = True
    motivo = "OK"

    if confidence < 60:
        permitido = False
        motivo = "Confianza insuficiente"

    if value < 3:
        permitido = False
        motivo = "Value insuficiente"

    if contexto.get("operaciones_hoy", 0) >= MAX_OPERACIONES_DIA:
        permitido = False
        motivo = "Límite diario alcanzado"

    if contexto.get("fallos_consecutivos", 0) >= STOP_LOSS_CONSECUTIVO:
        permitido = False
        motivo = "Stop loss activado"

    stake_data = calcular_stake(signal, bankroll)

    return {
        "permitido_operar": permitido,
        "motivo_operacion": motivo,
        "stake_pct": stake_data.get("stake_pct", 0),
        "stake_amount": stake_data.get("stake_amount", 0),
        "stake_label": stake_data.get("stake_label", "BAJO"),
        "bankroll_mode": stake_data.get("bankroll_mode", "NEUTRAL"),
        "max_operaciones_dia": MAX_OPERACIONES_DIA,
        "stop_loss_consecutivo": STOP_LOSS_CONSECUTIVO,
    }


# =========================================================
# APLICAR SOBRE SEÑAL
# =========================================================
def aplicar_bankroll(signal: Dict, bankroll: float = DEFAULT_BANKROLL) -> Dict:
    if not isinstance(signal, dict):
        return signal

    data = validar_operacion(signal, bankroll)
    signal.update(data)
    return signal
