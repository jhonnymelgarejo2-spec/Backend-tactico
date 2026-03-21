from typing import Dict
from datetime import datetime


# =========================================================
# HELPERS
# =========================================================
def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_str(value, default=""):
    try:
        return str(value if value is not None else default).strip()
    except Exception:
        return default


def _safe_upper(value, default=""):
    return _safe_str(value, default).upper()


# =========================================================
# REGLAS DE VENTANA
# =========================================================
def calcular_ventana_operativa(minuto: int) -> str:
    minuto = _safe_int(minuto, 0)

    if minuto <= 15:
        return f"Min {minuto}-{minuto + 15}"
    if minuto <= 30:
        return f"Min {minuto}-{minuto + 12}"
    if minuto <= 45:
        return f"Min {minuto}-{minuto + 10}"
    if minuto <= 60:
        return f"Min {minuto}-{minuto + 10}"
    if minuto <= 75:
        return f"Min {minuto}-{minuto + 8}"
    if minuto <= 85:
        return f"Min {minuto}-{minuto + 5}"

    return f"Min {minuto}-FT"


# =========================================================
# DECISIÓN EJECUTIVA
# =========================================================
def construir_decision_ejecutiva(signal: Dict) -> str:
    permitido = bool(signal.get("permitido_operar", True))
    ai_rec = _safe_upper(signal.get("ai_recommendation", signal.get("recomendacion_final", "OBSERVAR")))
    confidence = _safe_float(signal.get("confidence", 0), 0)
    value = _safe_float(signal.get("value", 0), 0)

    if not permitido:
        return "NO"

    if ai_rec in ("APOSTAR_FUERTE", "APOSTAR") and confidence >= 72 and value >= 5:
        return "SI"

    if ai_rec in ("APOSTAR_SUAVE", "OBSERVAR") and confidence >= 60 and value >= 3:
        return "ALTERNATIVA"

    return "NO"


# =========================================================
# RESUMEN DE RAZONES
# =========================================================
def construir_resumen_razones(signal: Dict) -> Dict:
    return {
        "razon_tactica": _safe_str(signal.get("reason", "Sin razón táctica")),
        "razon_value": _safe_str(signal.get("razon_value", "Sin razón de value")),
        "razon_ia": _safe_str(signal.get("ai_reason", "Sin lectura IA")),
        "razon_contexto": _safe_str(signal.get("context_reason", signal.get("pre_match_reason", "Sin contexto adicional"))),
        "razon_emocional": _safe_str(signal.get("emocion_razon", "Sin lectura emocional")),
        "razon_arbitral": _safe_str(signal.get("referee_reason", "Sin lectura arbitral")),
        "razon_ritmo": _safe_str(signal.get("tempo_reason", "Sin lectura de ritmo")),
        "razon_jugadores": _safe_str(signal.get("player_impact_reason", "Sin lectura de jugadores")),
    }


# =========================================================
# FORMATO PROTOCOLO
# =========================================================
def formatear_senal_protocolo(signal: Dict) -> Dict:
    if not isinstance(signal, dict):
        return {}

    minuto = _safe_int(signal.get("minute", signal.get("minuto", 0)), 0)
    confidence = round(_safe_float(signal.get("confidence", 0), 0), 2)
    value = round(_safe_float(signal.get("value", 0), 0), 2)
    prob = round(_safe_float(signal.get("prob", signal.get("prob_real", 0)), 0), 4)
    prob_pct = round(prob * 100, 2) if prob <= 1 else round(prob, 2)

    stake_pct = round(_safe_float(signal.get("stake_pct", 0), 0), 2)
    stake_amount = round(_safe_float(signal.get("stake_amount", 0), 0), 2)

    ventana = calcular_ventana_operativa(minuto)
    decision = construir_decision_ejecutiva(signal)
    razones = construir_resumen_razones(signal)

    protocolo = {
        "senal_id": _safe_str(signal.get("match_id", signal.get("id", ""))),
        "hora_generada": datetime.now().strftime("%H:%M:%S"),
        "liga": _safe_str(signal.get("league", "")),
        "pais": _safe_str(signal.get("country", "")),
        "partido": f"{_safe_str(signal.get('home', 'LOCAL'))} vs {_safe_str(signal.get('away', 'VISITANTE'))}",
        "minuto": minuto,
        "score": _safe_str(signal.get("score", "0-0")),

        "mercado": _safe_str(signal.get("market", "")),
        "apuesta": _safe_str(signal.get("selection", signal.get("apuesta", ""))),
        "cuota": round(_safe_float(signal.get("odd", signal.get("cuota", 0)), 0), 2),

        "confianza": confidence,
        "value": value,
        "prob_real_pct": prob_pct,

        "ventana": ventana,
        "stake_pct": stake_pct,
        "stake_amount": stake_amount,
        "stake_label": _safe_str(signal.get("stake_label", "N/A")),

        "decision_ia": _safe_str(signal.get("ai_recommendation", signal.get("recomendacion_final", "OBSERVAR"))),
        "decision_ejecutiva": decision,
        "permitido_operar": bool(signal.get("permitido_operar", True)),
        "motivo_operacion": _safe_str(signal.get("motivo_operacion", "OK")),

        "ganador_probable": _safe_str(signal.get("ganador_probable", "")),
        "resultado_probable": _safe_str(signal.get("resultado_probable", "")),
        "over_under_probable": _safe_str(signal.get("over_under_probable", "")),

        "tier": _safe_str(signal.get("tier", "NORMAL")),
        "signal_rank": _safe_str(signal.get("signal_rank", "NORMAL")),
        "bankroll_mode": _safe_str(signal.get("bankroll_mode", "NEUTRAL")),

        "razon_tactica": razones["razon_tactica"],
        "razon_value": razones["razon_value"],
        "razon_ia": razones["razon_ia"],
        "razon_contexto": razones["razon_contexto"],
        "razon_emocional": razones["razon_emocional"],
        "razon_arbitral": razones["razon_arbitral"],
        "razon_ritmo": razones["razon_ritmo"],
        "razon_jugadores": razones["razon_jugadores"],
    }

    return protocolo


# =========================================================
# TEXTO FINAL OPERATIVO
# =========================================================
def renderizar_senal_protocolo_texto(signal: Dict) -> str:
    s = formatear_senal_protocolo(signal)
    if not s:
        return "Sin señal disponible"

    return (
        f"🎯 SEÑAL #{s['senal_id']} - {s['hora_generada']}\n"
        f"⚽ {s['liga']} | {s['partido']} - Min {s['minuto']}\n"
        f"📊 SCORE: {s['score']} | 🎯 CONFIANZA: {s['confianza']}%\n"
        f"💡 APUESTA: {s['apuesta']} @ {s['cuota']}\n"
        f"⏱️ VENTANA: {s['ventana']} | 💰 TAMAÑO: {s['stake_pct']}% ({s['stake_amount']})\n"
        f"📈 VALOR: +{s['value']}% | 🎲 PROB REAL: {s['prob_real_pct']}%\n"
        f"🧠 IA: {s['decision_ia']} | 🏦 BANKROLL: {s['bankroll_mode']}\n"
        f"🔍 TÁCTICA: {s['razon_tactica']}\n"
        f"📚 CONTEXTO: {s['razon_contexto']}\n"
        f"🔥 EMOCIÓN: {s['razon_emocional']}\n"
        f"🟨 ÁRBITRO: {s['razon_arbitral']}\n"
        f"⚡ RITMO: {s['razon_ritmo']}\n"
        f"👥 JUGADORES: {s['razon_jugadores']}\n"
        f"💎 VALUE: {s['razon_value']}\n"
        f"✅ ¿EJECUTAMOS?: {s['decision_ejecutiva']}"
  )
