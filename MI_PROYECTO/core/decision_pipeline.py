from typing import Dict, Optional

# =========================================================
# IMPORTS DEL SISTEMA
# =========================================================
try:
    from signal_engine import generar_senal
    print("[IMPORTAR] signal_engine OK")
except Exception as e:
    print(f"[IMPORTAR] signal_engine ERROR -> {e}")
    generar_senal = None

try:
    from ai_brain import decision_final_ia
    print("[IMPORTAR] ai_brain OK")
except Exception as e:
    print(f"[IMPORTAR] ai_brain ERROR -> {e}")
    decision_final_ia = None

try:
    from core.context_engine import evaluar_contexto_partido
    print("[IMPORTAR] context_engine OK")
except Exception as e:
    print(f"[IMPORTAR] context_engine ERROR -> {e}")
    evaluar_contexto_partido = None

try:
    from core.chaos_guardian import evaluar_chaos_partido
    print("[IMPORTAR] chaos_guardian OK")
except Exception as e:
    print(f"[IMPORTAR] chaos_guardian ERROR -> {e}")
    evaluar_chaos_partido = None

try:
    from core.adaptive_engine import aplicar_ajuste_senal
    print("[IMPORTAR] motor adaptativo OK")
except Exception as e:
    print(f"[IMPORTAR] adaptive_engine ERROR -> {e}")
    aplicar_ajuste_senal = None

try:
    from core.auto_balance_engine import (
        aplicar_auto_balance,
        validar_confianza_dinamica,
        validar_contexto_dinamico,
        validar_chaos_dinamico,
        permitir_value_flex,
    )
    print("[IMPORTAR] auto_balance_engine OK")
except Exception as e:
    print(f"[IMPORTAR] auto_balance_engine ERROR -> {e}")
    aplicar_auto_balance = None
    validar_confianza_dinamica = None
    validar_contexto_dinamico = None
    validar_chaos_dinamico = None
    permitir_value_flex = None

try:
    from core.bankroll_manager import aplicar_bankroll
    print("[IMPORTAR] bankroll_manager OK")
except Exception as e:
    print(f"[IMPORTAR] bankroll_manager ERROR -> {e}")
    aplicar_bankroll = None

try:
    from core.pre_match_engine import evaluar_pre_match
    print("[IMPORTAR] motor de prepartido OK")
except Exception as e:
    print(f"[IMPORTAR] pre_match_engine ERROR -> {e}")
    evaluar_pre_match = None

try:
    from core.emotional_engine import (
        evaluar_estado_emocional,
        aplicar_emocion_a_senal,
    )
    print("[IMPORTAR] emotional_engine OK")
except Exception as e:
    print(f"[IMPORTAR] emotional_engine ERROR -> {e}")
    evaluar_estado_emocional = None
    aplicar_emocion_a_senal = None

try:
    from core.referee_engine import (
        evaluar_arbitro,
        aplicar_arbitro_a_senal,
    )
    print("[IMPORTAR] motor de árbitro OK")
except Exception as e:
    print(f"[IMPORTAR] referee_engine ERROR -> {e}")
    evaluar_arbitro = None
    aplicar_arbitro_a_senal = None

try:
    from core.tempo_engine import (
        evaluar_tempo_partido,
        aplicar_tempo_a_senal,
    )
    print("[IMPORTAR] tempo_engine OK")
except Exception as e:
    print(f"[IMPORTAR] tempo_engine ERROR -> {e}")
    evaluar_tempo_partido = None
    aplicar_tempo_a_senal = None

try:
    from core.player_impact_engine import (
        evaluar_player_impact,
        aplicar_player_impact_a_senal,
    )
    print("[IMPORTAR] player_impact_engine OK")
except Exception as e:
    print(f"[IMPORTAR] player_impact_engine ERROR -> {e}")
    evaluar_player_impact = None
    aplicar_player_impact_a_senal = None

try:
    from core.protocol_output_formatter import formatear_senal_protocolo
    print("[IMPORTAR] protocol_output_formatter OK")
except Exception as e:
    print(f"[IMPORTAR] protocol_output_formatter ERROR -> {e}")
    formatear_senal_protocolo = None

# =========================================================
# STORAGE REAL
# =========================================================
try:
    from core.signal_storage import guardar_senal
    print("[IMPORTAR] signal_storage OK")
except Exception as e:
    print(f"[IMPORTAR] signal_storage ERROR -> {e}")
    guardar_senal = None

# =========================================================
# DESACTIVADOS TEMPORALMENTE
# =========================================================
registrar_senal = None
aplicar_memoria_mercado = None
aplicar_auto_learning = None
aplicar_pre_match_a_senal = None


# =========================================================
# HELPERS TACTICOS LOCALES
# SIN IMPORT CIRCULAR
# =========================================================
def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


def _safe_lower(value) -> str:
    return str(value or "").strip().lower()


def _safe_float(value, default=0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def calcular_tactical_score(partido: Dict) -> float:
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    minuto = _safe_int(partido.get("minuto"), 0)
    momentum = _safe_upper(partido.get("momentum"))

    goal_pressure = partido.get("goal_pressure") or {}
    goal_predictor = partido.get("goal_predictor") or {}
    chaos = partido.get("chaos") or {}

    pressure_score = _safe_float(goal_pressure.get("pressure_score"), 0.0)
    predictor_score = _safe_float(goal_predictor.get("predictor_score"), 0.0)
    goal_next_5_prob = _safe_float(goal_predictor.get("goal_next_5_prob"), 0.0) * 100
    goal_next_10_prob = _safe_float(goal_predictor.get("goal_next_10_prob"), 0.0) * 100
    chaos_score = _safe_float(chaos.get("chaos_score"), 0.0)

    score = 0.0
    score += xg * 18.0
    score += shots * 0.8
    score += shots_on_target * 4.0
    score += dangerous_attacks * 0.25
    score += pressure_score * 2.5
    score += predictor_score * 2.0
    score += chaos_score * 1.4
    score += goal_next_5_prob * 0.25
    score += goal_next_10_prob * 0.15

    if momentum == "MUY ALTO":
        score += 16
    elif momentum == "ALTO":
        score += 11
    elif momentum == "MEDIO":
        score += 5

    if 15 <= minuto <= 75:
        score += 8
    elif 76 <= minuto <= 88:
        score += 5

    return round(score, 2)


def calcular_goal_inminente_score(senal: Dict, partido: Dict) -> float:
    gp5 = _safe_float(senal.get("goal_prob_5"), 0.0)
    gp10 = _safe_float(senal.get("goal_prob_10"), 0.0)
    gp15 = _safe_float(senal.get("goal_prob_15"), 0.0)

    if gp5 == 0 and gp10 == 0 and gp15 == 0:
        predictor = partido.get("goal_predictor") or {}
        gp5 = _safe_float(predictor.get("goal_next_5_prob"), 0.0) * 100
        gp10 = _safe_float(predictor.get("goal_next_10_prob"), 0.0) * 100
        gp15 = (gp5 * 0.55) + (gp10 * 0.45)

    estado_obj = senal.get("estado_partido") or {}
    if isinstance(estado_obj, dict):
        estado = _safe_upper(estado_obj.get("estado"))
    else:
        estado = _safe_upper(estado_obj)

    bonus = 0.0
    if estado in ("EXPLOSIVO", "CAOS"):
        bonus = 18
    elif estado == "CALIENTE":
        bonus = 10
    elif estado == "CONTROLADO":
        bonus = 4

    score = (gp5 * 0.50) + (gp10 * 0.30) + (gp15 * 0.20) + bonus
    return round(score, 2)


def calcular_risk_score(senal: Dict, partido: Dict) -> float:
    minuto = _safe_int(partido.get("minuto"), 0)
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)
    odd = _safe_float(senal.get("odd"), 0.0)

    estado_obj = senal.get("estado_partido") or {}
    if isinstance(estado_obj, dict):
        estado = _safe_upper(estado_obj.get("estado"))
    else:
        estado = _safe_upper(estado_obj)

    riesgo = 5.0

    if confidence >= 85:
        riesgo -= 1.5
    elif confidence >= 75:
        riesgo -= 1.0
    elif confidence < 60:
        riesgo += 1.5

    if value >= 10:
        riesgo -= 1.0
    elif value < 3:
        riesgo += 1.0

    if odd >= 2.5:
        riesgo += 1.2
    elif 0 < odd <= 1.45:
        riesgo += 0.8

    if minuto >= 80:
        riesgo += 1.0

    if estado in ("FRIO", "MUERTO"):
        riesgo += 1.2
    elif estado in ("EXPLOSIVO", "CALIENTE"):
        riesgo -= 0.6

    return round(_clamp(riesgo, 1.0, 10.0), 2)


def calcular_signal_score(
    senal: Dict,
    partido: Dict,
    tactical_score: float,
    goal_score: float,
    risk_score: float,
) -> float:
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)
    ai_decision_score = _safe_float(senal.get("ai_decision_score"), 0.0)
    confianza_prediccion = _safe_float(senal.get("confianza_prediccion"), 0.0)

    score = 0.0
    score += confidence * 1.30
    score += value * 2.40
    score += tactical_score * 0.90
    score += goal_score * 0.85
    score += confianza_prediccion * 0.55
    score += ai_decision_score * 0.35
    score -= risk_score * 5.00

    return round(score, 2)


def calcular_signal_rank(signal_score: float) -> str:
    if signal_score >= 230:
        return "ELITE"
    if signal_score >= 170:
        return "TOP"
    if signal_score >= 110:
        return "ALTA"
    return "NORMAL"


def evaluar_value(prob_real: float, cuota: float) -> Dict:
    prob_real = _safe_float(prob_real, 0.0)
    cuota = _safe_float(cuota, 0.0)

    if cuota <= 1.0:
        return {
            "prob_implicita": 0.0,
            "value_pct": 0.0,
            "edge_pct": 0.0,
            "value_score": 0.0,
            "value_categoria": "SIN_VALUE",
            "recomendacion_value": "NO_APOSTAR",
            "razon_value": "Cuota inválida",
        }

    prob_implicita = round(1.0 / cuota, 4)
    edge_pct = round((prob_real - prob_implicita) * 100, 2)
    value_pct = edge_pct
    value_score = round(max(0.0, edge_pct), 2)

    if edge_pct >= 12:
        categoria = "VALUE_ELITE"
        recomendacion = "APOSTAR_FUERTE"
        razon = "Value muy alto respecto a la probabilidad implícita"
    elif edge_pct >= 8:
        categoria = "VALUE_ALTO"
        recomendacion = "APOSTAR"
        razon = "Value alto y aprovechable"
    elif edge_pct >= 4:
        categoria = "VALUE_MEDIO"
        recomendacion = "APOSTAR_SUAVE"
        razon = "Existe valor positivo razonable en la cuota"
    elif edge_pct > 0:
        categoria = "VALUE_BAJO"
        recomendacion = "OBSERVAR"
        razon = "Hay value leve, pero no es fuerte"
    else:
        categoria = "SIN_VALUE"
        recomendacion = "NO_APOSTAR"
        razon = "No hay ventaja estadística suficiente"

    return {
        "prob_implicita": prob_implicita,
        "value_pct": value_pct,
        "edge_pct": edge_pct,
        "value_score": value_score,
        "value_categoria": categoria,
        "recomendacion_value": recomendacion,
        "razon_value": razon,
    }


def enriquecer_senal(senal: Dict, partido: Dict) -> Dict:
    tactical_score = calcular_tactical_score(partido)
    goal_score = calcular_goal_inminente_score(senal, partido)
    risk_score = calcular_risk_score(senal, partido)

    prob = _safe_float(senal.get("prob"), _safe_float(senal.get("prob_real"), 0.0))
    odd = _safe_float(senal.get("odd"), _safe_float(senal.get("cuota"), 0.0))
    value_data = evaluar_value(prob, odd)

    senal["prob_implicita_calculada"] = value_data["prob_implicita"]
    senal["value_pct"] = value_data["value_pct"]
    senal["edge_pct"] = value_data["edge_pct"]
    senal["value_score"] = max(
        _safe_float(senal.get("value_score"), 0.0),
        _safe_float(value_data["value_score"], 0.0),
    )
    senal["value_categoria"] = senal.get("value_categoria") or value_data["value_categoria"]
    senal["recomendacion_value"] = senal.get("recomendacion_value") or value_data["recomendacion_value"]
    senal["razon_value"] = senal.get("razon_value") or value_data["razon_value"]

    if "ai_decision_score" not in senal or _safe_float(senal.get("ai_decision_score"), 0.0) == 0.0:
        senal["ai_decision_score"] = round(
            (_safe_float(senal.get("confidence"), 0.0) * 0.65) +
            (_safe_float(senal.get("value"), 0.0) * 1.2),
            2
        )

    signal_score = calcular_signal_score(
        senal=senal,
        partido=partido,
        tactical_score=tactical_score,
        goal_score=goal_score,
        risk_score=risk_score,
    )
    signal_rank = calcular_signal_rank(signal_score)

    senal["tactical_score"] = tactical_score
    senal["goal_inminente_score"] = goal_score
    senal["risk_score"] = risk_score
    senal["signal_score"] = signal_score
    senal["signal_rank"] = signal_rank

    senal.setdefault("ai_reason", "Lectura IA sin anomalías extremas")
    senal.setdefault("razon_value", "La cuota ofrece valor razonable frente a la probabilidad estimada")
    senal.setdefault("motivo_operacion", "OK")
    senal.setdefault("permitido_operar", True)
    senal.setdefault("stake_pct", 0.0)
    senal.setdefault("stake_amount", 0.0)
    senal.setdefault("stake_label", "N/A")
    senal.setdefault("bankroll_mode", "FLAT")

    return senal


def filtro_antifake_partido(partido: Dict, senal: Dict) -> bool:
    minuto = _safe_int(partido.get("minuto"), 0)
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    momentum = _safe_upper(partido.get("momentum"))
    market = _safe_upper(senal.get("market"))
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)

    if minuto < 8:
        return False
    if confidence < 58:
        return False
    if value <= 0:
        return False

    sin_stats = (
        xg == 0 and shots == 0 and shots_on_target == 0 and dangerous_attacks == 0
    )

    if sin_stats:
        return confidence >= 74

    if "OVER" in market or "GOAL" in market or "NEXT_GOAL" in market:
        if xg < 0.60 and shots_on_target < 1 and dangerous_attacks < 12:
            return False

    if "RESULT" in market:
        if minuto < 20 and xg > 1.8 and shots_on_target >= 3:
            return False

    if momentum == "BAJO" and dangerous_attacks < 8 and shots_on_target == 0 and confidence < 75:
        return False

    return True


def filtrar_value_bets_reales(senal: Dict) -> bool:
    league = _safe_lower(senal.get("league"))
    market = _safe_upper(senal.get("market"))
    value = _safe_float(senal.get("value"), 0.0)
    confidence = _safe_float(senal.get("confidence"), 0.0)
    tactical_score = _safe_float(senal.get("tactical_score"), 0.0)
    signal_score = _safe_float(senal.get("signal_score"), 0.0)
    risk_score = _safe_float(senal.get("risk_score"), 10.0)
    odd = _safe_float(senal.get("odd"), 0.0)
    minute = _safe_int(senal.get("minute"), 0)

    ligas_top = {
        "premier league",
        "la liga",
        "serie a",
        "bundesliga",
        "ligue 1",
        "champions league",
        "uefa champions league",
        "europa league",
        "uefa europa league",
    }

    if minute >= 89:
        return False
    if 0 < odd < 1.30:
        return False

    if league in ligas_top:
        if value < 4 or confidence < 62:
            return False
    else:
        if value < 2 or confidence < 58:
            return False

    if tactical_score < 6:
        return False
    if signal_score < 70:
        return False
    if risk_score > 8.5:
        return False
    if "RESULT" in market and confidence < 64:
        return False

    return True


# =========================================================
# FALLBACK
# =========================================================
def generar_senal_fallback(datos: Dict) -> Dict:
    xg = _safe_float(datos.get("xG"), 0)
    ml = _safe_int(datos.get("marcador_local"), 0)
    mv = _safe_int(datos.get("marcador_visitante"), 0)

    market = "OVER_NEXT_15_DYNAMIC" if xg >= 1.2 else "RESULT_HOLDS_NEXT_15"

    return {
        "mercado": market,
        "apuesta": "Fallback automático",
        "linea": (ml + mv + 0.5),
        "cuota": 1.85,
        "prob_real": 0.64,
        "valor": 6.0,
        "confianza": 72,
        "razon": "Fallback por falta de señal",
        "tier": "NORMAL",
        "signal_status": "OPEN",
        "goal_prob_5": 30,
        "goal_prob_10": 40,
        "goal_prob_15": 50,
        "estado_partido": {"estado": "CONTROLADO"},
        "gol_inminente": {"gol_inminente": False},
        "resultado_probable": f"{ml}-{mv}",
        "ganador_probable": "LOCAL" if ml >= mv else "VISITANTE",
        "doble_oportunidad_probable": "LOCAL_O_EMPATE",
        "total_goles_estimado": ml + mv + 1,
        "linea_goles_probable": "OVER_2_5",
        "over_under_probable": "OVER 2.5",
        "confianza_prediccion": 72,
        "recomendacion_final": "APOSTAR",
        "riesgo_operativo": "MEDIO",
        "value_score": 6.0,
        "value_categoria": "VALUE_MEDIO",
        "recomendacion_value": "APOSTAR_SUAVE",
        "razon_value": "Fallback con valor suficiente",
    }


# =========================================================
# PIPELINE
# =========================================================
def procesar_partido(partido: Dict) -> Optional[Dict]:
    datos = {
        "id": partido.get("id"),
        "xG": partido.get("xG"),
        "minuto": partido.get("minuto"),
        "momentum": partido.get("momentum"),
        "marcador_local": partido.get("marcador_local", 0),
        "marcador_visitante": partido.get("marcador_visitante", 0),
        "goal_pressure": partido.get("goal_pressure", {}),
        "goal_predictor": partido.get("goal_predictor", {}),
        "chaos": partido.get("chaos", {}),
        "prob_real": partido.get("prob_real", 0.75),
        "prob_implicita": partido.get("prob_implicita", 0.54),
        "cuota": partido.get("cuota", 1.85),
    }

    if generar_senal:
        try:
            senal = generar_senal(datos)
        except Exception as e:
            print(f"[PIPELINE] ERROR generar_senal -> {e}")
            senal = generar_senal_fallback(datos)
    else:
        senal = generar_senal_fallback(datos)

    if not senal or senal.get("mercado") == "SIN_SEÑAL":
        print(f"[PIPELINE] fallback activado -> {partido.get('local')} vs {partido.get('visitante')}")
        senal = generar_senal_fallback(datos)

    senal_final = {
        "match_id": partido.get("id"),
        "home": partido.get("local"),
        "away": partido.get("visitante"),
        "league": partido.get("liga"),
        "country": partido.get("pais"),
        "minute": partido.get("minuto"),
        "score": f"{partido.get('marcador_local', 0)}-{partido.get('marcador_visitante', 0)}",
        "market": senal.get("mercado"),
        "selection": senal.get("apuesta"),
        "line": senal.get("linea"),
        "odd": senal.get("cuota", 1.85),
        "prob": senal.get("prob_real", 0.0),
        "value": senal.get("valor", 0),
        "confidence": senal.get("confianza", 0),
        "reason": senal.get("razon", ""),
        "tier": senal.get("tier", "NORMAL"),
        "goal_prob_5": senal.get("goal_prob_5", 0),
        "goal_prob_10": senal.get("goal_prob_10", 0),
        "goal_prob_15": senal.get("goal_prob_15", 0),
        "estado_partido": senal.get("estado_partido", {}),
        "gol_inminente": senal.get("gol_inminente", {}),
        "signal_status": senal.get("signal_status", "OPEN"),
        "resultado_probable": senal.get("resultado_probable", ""),
        "ganador_probable": senal.get("ganador_probable", ""),
        "doble_oportunidad_probable": senal.get("doble_oportunidad_probable", ""),
        "total_goles_estimado": senal.get("total_goles_estimado", 0),
        "linea_goles_probable": senal.get("linea_goles_probable", ""),
        "over_under_probable": senal.get("over_under_probable", ""),
        "confianza_prediccion": senal.get("confianza_prediccion", 0),
        "recomendacion_final": senal.get("recomendacion_final", "OBSERVAR"),
        "riesgo_operativo": senal.get("riesgo_operativo", "MEDIO"),
        "value_score": senal.get("value_score", senal.get("valor", 0)),
        "value_categoria": senal.get("value_categoria", "SIN_VALUE"),
        "recomendacion_value": senal.get("recomendacion_value", "OBSERVAR"),
        "razon_value": senal.get("razon_value", ""),
        "stake_pct": 0,
        "stake_amount": 0,
        "stake_label": "N/A",
        "bankroll_mode": "FLAT",
        "permitido_operar": True,
    }

    try:
        senal_final = enriquecer_senal(senal_final, partido)
    except Exception as e:
        print(f"[PIPELINE] ERROR enriquecer_senal -> {e}")

    if aplicar_auto_balance:
        try:
            senal_final = aplicar_auto_balance(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR AUTO BALANCE -> {e}")

    if evaluar_pre_match:
        try:
            pre_match_data = evaluar_pre_match(
                partido,
                partido.get("home_recent_matches", []),
                partido.get("away_recent_matches", []),
                partido.get("h2h_matches", []),
                partido.get("league_stats", {}),
            )
            if isinstance(pre_match_data, dict):
                senal_final.update(pre_match_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR PRE MATCH -> {e}")

    if evaluar_contexto_partido:
        try:
            context = evaluar_contexto_partido(partido)
            if isinstance(context, dict):
                senal_final.update(context)

            if validar_contexto_dinamico and not validar_contexto_dinamico(senal_final):
                if _safe_float(senal_final.get("confidence", 0)) < 55:
                    print(f"[FILTRO] CONTEXT bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CONTEXT -> {e}")

    if evaluar_chaos_partido:
        try:
            chaos = evaluar_chaos_partido(partido, senal_final)
            if isinstance(chaos, dict):
                senal_final.update(chaos)

            if validar_chaos_dinamico and not validar_chaos_dinamico(senal_final):
                if _safe_float(senal_final.get("confidence", 0)) < 58:
                    print(f"[FILTRO] CHAOS bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CHAOS -> {e}")

    if evaluar_estado_emocional and aplicar_emocion_a_senal:
        try:
            emocion = evaluar_estado_emocional(partido)
            senal_final = aplicar_emocion_a_senal(senal_final, emocion)
        except Exception as e:
            print(f"[PIPELINE] ERROR EMOTIONAL -> {e}")

    if evaluar_arbitro and aplicar_arbitro_a_senal:
        try:
            referee_data = evaluar_arbitro(partido)
            senal_final = aplicar_arbitro_a_senal(senal_final, referee_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR REFEREE -> {e}")

    if evaluar_tempo_partido and aplicar_tempo_a_senal:
        try:
            tempo_data = evaluar_tempo_partido(partido)
            senal_final = aplicar_tempo_a_senal(senal_final, tempo_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR TEMPO -> {e}")

    if evaluar_player_impact and aplicar_player_impact_a_senal:
        try:
            player_data = evaluar_player_impact(
                partido,
                partido.get("home_players", []),
                partido.get("away_players", []),
            )
            senal_final = aplicar_player_impact_a_senal(senal_final, player_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR PLAYER IMPACT -> {e}")

    try:
        antifake_ok = filtro_antifake_partido(partido, senal_final)
        if not antifake_ok and _safe_float(senal_final.get("confidence", 0)) < 62:
            print(f"[FILTRO] ANTIFAKE bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
            return None
    except Exception as e:
        print(f"[PIPELINE] ERROR ANTIFAKE -> {e}")

    try:
        value_ok = filtrar_value_bets_reales(senal_final)
        if not value_ok:
            if permitir_value_flex:
                flex_mode = permitir_value_flex(senal_final)
                if not flex_mode and _safe_float(senal_final.get("confidence", 0)) < 60:
                    print(f"[FILTRO] VALUE bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
                    return None
            else:
                if _safe_float(senal_final.get("confidence", 0)) < 60:
                    print(f"[FILTRO] VALUE bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
                    return None
    except Exception as e:
        print(f"[PIPELINE] ERROR VALUE -> {e}")

    if validar_confianza_dinamica:
        try:
            if not validar_confianza_dinamica(senal_final):
                if _safe_float(senal_final.get("confidence", 0)) < 55:
                    print(f"[FILTRO] CONFIANZA bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CONFIANZA DINAMICA -> {e}")

    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            if isinstance(ai_data, dict):
                senal_final.update(ai_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR IA -> {e}")

    senal_final.setdefault("ai_recommendation", "APOSTAR_SUAVE")
    senal_final.setdefault("ai_decision_score", 60)
    senal_final.setdefault("ai_confidence_final", senal_final.get("confidence", 0))

    if aplicar_ajuste_senal:
        try:
            senal_final = aplicar_ajuste_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR ADAPTIVE -> {e}")

    if aplicar_bankroll:
        try:
            senal_final = aplicar_bankroll(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR BANKROLL -> {e}")

    decision = _safe_upper(senal_final.get("ai_recommendation"))
    confidence = _safe_float(senal_final.get("confidence", 0))
    value = _safe_float(senal_final.get("value", 0))
    ai_score = _safe_float(senal_final.get("ai_decision_score", 0))

    if decision == "NO_APOSTAR":
        if confidence < 75:
            print(f"[FILTRO] IA FINAL bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

    if not senal_final.get("permitido_operar", True):
        if confidence < 72:
            print(f"[FILTRO] BANKROLL bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

    if decision == "OBSERVAR":
        if ai_score >= 50 and confidence >= 60 and value >= 3:
            senal_final["ai_recommendation"] = "APOSTAR_SUAVE"
        else:
            print(f"[FILTRO] OBSERVAR bloqueó -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

    senal_final["recomendacion_final"] = senal_final.get("ai_recommendation", "OBSERVAR")
    senal_final["publish_ready"] = True
    senal_final["publish_rank"] = 1

    if formatear_senal_protocolo:
        try:
            protocol_data = formatear_senal_protocolo(senal_final)
            if isinstance(protocol_data, dict):
                senal_final.update(protocol_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR PROTOCOL FORMATTER -> {e}")

    if registrar_senal:
        try:
            registrar_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR REGISTRAR -> {e}")

    print(
        f"[PIPELINE OK] {senal_final.get('home')} vs {senal_final.get('away')} | "
        f"market={senal_final.get('market')} | "
        f"conf={senal_final.get('confidence')} | "
        f"value={senal_final.get('value')} | "
        f"ai={senal_final.get('ai_recommendation')}"
    )

    return senal_final
