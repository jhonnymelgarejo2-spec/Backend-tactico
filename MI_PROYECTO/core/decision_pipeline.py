from typing import Dict, Optional
import importlib


# =========================================================
# HELPERS DE IMPORTACIÓN SEGURA
# =========================================================
def _import_attr(module_name: str, attr_name: str, alias: str = ""):
    label = alias or f"{module_name}.{attr_name}"
    try:
        module = importlib.import_module(module_name)
        attr = getattr(module, attr_name, None)
        if attr is None:
            print(f"[IMPORTAR] {label} NO DISPONIBLE")
        else:
            print(f"[IMPORTAR] {label} OK")
        return attr
    except Exception as e:
        print(f"[IMPORTAR] {label} ERROR -> {e}")
        return None


def _import_module(module_name: str, alias: str = ""):
    label = alias or module_name
    try:
        module = importlib.import_module(module_name)
        print(f"[IMPORTAR] {label} OK")
        return module
    except Exception as e:
        print(f"[IMPORTAR] {label} ERROR -> {e}")
        return None


# =========================================================
# IMPORTS DEL SISTEMA
# =========================================================
generar_senal = _import_attr("signal_engine", "generar_senal", "signal_engine")
decision_final_ia = _import_attr("ai_brain", "decision_final_ia", "ai_brain")

evaluar_contexto_partido = _import_attr(
    "core.context_engine", "evaluar_contexto_partido", "context_engine"
)
evaluar_chaos_partido = _import_attr(
    "core.chaos_guardian", "evaluar_chaos_partido", "chaos_guardian"
)
aplicar_ajuste_senal = _import_attr(
    "core.adaptive_engine", "aplicar_ajuste_senal", "motor adaptativo"
)

auto_balance_module = _import_module("core.auto_balance_engine", "auto_balance_engine")
aplicar_auto_balance = getattr(auto_balance_module, "aplicar_auto_balance", None) if auto_balance_module else None
validar_confianza_dinamica = getattr(auto_balance_module, "validar_confianza_dinamica", None) if auto_balance_module else None
validar_contexto_dinamico = getattr(auto_balance_module, "validar_contexto_dinamico", None) if auto_balance_module else None
validar_chaos_dinamico = getattr(auto_balance_module, "validar_chaos_dinamico", None) if auto_balance_module else None
permitir_value_flex = getattr(auto_balance_module, "permitir_value_flex", None) if auto_balance_module else None

aplicar_bankroll = _import_attr(
    "core.bankroll_manager", "aplicar_bankroll", "bankroll_manager"
)

pre_match_module = _import_module("core.pre_match_engine", "motor de prepartido")
evaluar_pre_match = getattr(pre_match_module, "evaluar_pre_match", None) if pre_match_module else None
aplicar_pre_match_a_senal = getattr(pre_match_module, "aplicar_pre_match_a_senal", None) if pre_match_module else None

emotional_module = _import_module("core.emotional_engine", "emotional_engine")
evaluar_estado_emocional = getattr(emotional_module, "evaluar_estado_emocional", None) if emotional_module else None
aplicar_emocion_a_senal = getattr(emotional_module, "aplicar_emocion_a_senal", None) if emotional_module else None

referee_module = _import_module("core.referee_engine", "motor de árbitro")
evaluar_arbitro = getattr(referee_module, "evaluar_arbitro", None) if referee_module else None
aplicar_arbitro_a_senal = getattr(referee_module, "aplicar_arbitro_a_senal", None) if referee_module else None

tempo_module = _import_module("core.tempo_engine", "tempo_engine")
evaluar_tempo_partido = getattr(tempo_module, "evaluar_tempo_partido", None) if tempo_module else None
aplicar_tempo_a_senal = getattr(tempo_module, "aplicar_tempo_a_senal", None) if tempo_module else None

player_module = _import_module("core.player_impact_engine", "player_impact_engine")
evaluar_player_impact = getattr(player_module, "evaluar_player_impact", None) if player_module else None
aplicar_player_impact_a_senal = getattr(player_module, "aplicar_player_impact_a_senal", None) if player_module else None

formatear_senal_protocolo = _import_attr(
    "core.protocol_output_formatter", "formatear_senal_protocolo", "protocol_output_formatter"
)

guardar_senal_storage = _import_attr(
    "core.signal_storage", "guardar_senal", "signal_storage"
)


# =========================================================
# HELPERS
# =========================================================
def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


def _safe_lower(value) -> str:
    return str(value or "").strip().lower()


def _safe_float(value, default=0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


# =========================================================
# FUNCIONES TÁCTICAS LOCALES
# EVITAN IMPORTACIÓN CIRCULAR CON tactico_api.py
# =========================================================
def calcular_prob_implicita(odd: float) -> float:
    odd = _safe_float(odd, 0.0)
    if odd <= 1.0:
        return 0.0
    return round(1.0 / odd, 4)


def evaluar_value_local(prob_real: float, cuota: float) -> Dict:
    prob_real = _safe_float(prob_real, 0.0)
    cuota = _safe_float(cuota, 0.0)

    if cuota <= 1.0:
        return {
            "prob_implicita_calculada": 0.0,
            "edge_pct": 0.0,
            "value_pct": 0.0,
            "value_score": 0.0,
            "value_categoria": "SIN_VALUE",
            "recomendacion_value": "NO_APOSTAR",
            "razon_value": "Cuota inválida",
        }

    prob_implicita = calcular_prob_implicita(cuota)
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
        "prob_implicita_calculada": prob_implicita,
        "edge_pct": edge_pct,
        "value_pct": value_pct,
        "value_score": value_score,
        "value_categoria": categoria,
        "recomendacion_value": recomendacion,
        "razon_value": razon,
    }


def calcular_tactical_score_local(partido: Dict) -> float:
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


def calcular_goal_inminente_score_local(senal: Dict, partido: Dict) -> float:
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
    if estado in ("EXPLOSIVO", "CAOS", "CAOS_UTIL"):
        bonus = 18
    elif estado == "CALIENTE":
        bonus = 10
    elif estado == "CONTROLADO":
        bonus = 4

    score = (gp5 * 0.50) + (gp10 * 0.30) + (gp15 * 0.20) + bonus
    return round(score, 2)


def calcular_risk_score_local(senal: Dict, partido: Dict) -> float:
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
    elif confidence < 55:
        riesgo += 1.8
    elif confidence < 62:
        riesgo += 0.8

    if value >= 10:
        riesgo -= 1.0
    elif value < 2:
        riesgo += 1.0

    if odd >= 2.8:
        riesgo += 1.3
    elif 0 < odd <= 1.35:
        riesgo += 0.8

    if minuto >= 82:
        riesgo += 1.0
    elif minuto >= 76:
        riesgo += 0.5

    if estado in ("FRIO", "MUERTO", "CAOS_PELIGROSO"):
        riesgo += 1.2
    elif estado in ("EXPLOSIVO", "CALIENTE"):
        riesgo -= 0.6

    return round(_clamp(riesgo, 1.0, 10.0), 2)


def calcular_signal_score_local(
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


def calcular_signal_rank_local(signal_score: float) -> str:
    if signal_score >= 260:
        return "ELITE"
    if signal_score >= 190:
        return "TOP"
    if signal_score >= 125:
        return "ALTA"
    return "NORMAL"


def enriquecer_senal_local(senal: Dict, partido: Dict) -> Dict:
    tactical_score = calcular_tactical_score_local(partido)
    goal_score = calcular_goal_inminente_score_local(senal, partido)
    risk_score = calcular_risk_score_local(senal, partido)

    prob = _safe_float(senal.get("prob"), _safe_float(senal.get("prob_real"), 0.0))
    odd = _safe_float(senal.get("odd"), _safe_float(senal.get("cuota"), 0.0))
    value_data = evaluar_value_local(prob, odd)

    senal["prob_implicita_calculada"] = value_data["prob_implicita_calculada"]
    senal["edge_pct"] = value_data["edge_pct"]
    senal["value_pct"] = value_data["value_pct"]

    current_value_score = _safe_float(senal.get("value_score"), 0.0)
    senal["value_score"] = max(current_value_score, _safe_float(value_data["value_score"], 0.0))
    senal["value_categoria"] = senal.get("value_categoria") or value_data["value_categoria"]
    senal["recomendacion_value"] = senal.get("recomendacion_value") or value_data["recomendacion_value"]
    senal["razon_value"] = senal.get("razon_value") or value_data["razon_value"]

    if _safe_float(senal.get("ai_decision_score"), 0.0) == 0.0:
        senal["ai_decision_score"] = round(
            (_safe_float(senal.get("confidence"), 0.0) * 0.65) +
            (_safe_float(senal.get("value"), 0.0) * 1.2),
            2
        )

    signal_score = calcular_signal_score_local(
        senal=senal,
        partido=partido,
        tactical_score=tactical_score,
        goal_score=goal_score,
        risk_score=risk_score,
    )

    senal["tactical_score"] = tactical_score
    senal["goal_inminente_score"] = goal_score
    senal["risk_score"] = risk_score
    senal["signal_score"] = signal_score
    senal["signal_rank"] = calcular_signal_rank_local(signal_score)

    senal.setdefault("ai_reason", "Lectura IA sin anomalías extremas")
    senal.setdefault("motivo_operacion", "OK")
    senal.setdefault("permitido_operar", True)
    senal.setdefault("stake_pct", 0.0)
    senal.setdefault("stake_amount", 0.0)
    senal.setdefault("stake_label", "N/A")
    senal.setdefault("bankroll_mode", "FLAT")

    return senal


def filtro_antifake_local(partido: Dict, senal: Dict) -> bool:
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

    if confidence < 50:
        return False

    if value < 0:
        return False

    sin_stats = (
        xg == 0 and
        shots == 0 and
        shots_on_target == 0 and
        dangerous_attacks == 0
    )

    if sin_stats:
        return confidence >= 72

    if "OVER" in market or "GOAL" in market:
        if xg < 0.45 and shots_on_target < 1 and dangerous_attacks < 10:
            return False

    if "RESULT" in market:
        if minuto < 20 and xg > 2.0 and shots_on_target >= 3:
            return False

    if momentum == "BAJO" and dangerous_attacks < 8 and shots_on_target == 0 and confidence < 72:
        return False

    return True


def filtrar_value_bets_reales_local(senal: Dict) -> bool:
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

    if 0 < odd < 1.22:
        return False

    if league in ligas_top:
        if value < 2:
            return False
        if confidence < 58:
            return False
    else:
        if value < 1:
            return False
        if confidence < 54:
            return False

    if tactical_score < 5:
        return False

    if signal_score < 55:
        return False

    if risk_score > 9.2:
        return False

    if "RESULT" in market and confidence < 60:
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
        "razon": "Fallback por falta de señal principal",
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
        "recomendacion_final": "APOSTAR_SUAVE",
        "riesgo_operativo": "MEDIO",
        "value_score": 6.0,
        "value_categoria": "VALUE_MEDIO",
        "recomendacion_value": "APOSTAR_SUAVE",
        "razon_value": "Fallback con valor suficiente",
    }


# =========================================================
# VALIDACIONES BASE
# =========================================================
def _partido_es_valido(partido: Dict) -> bool:
    minuto = _safe_int(partido.get("minuto"), 0)
    estado = _safe_lower(partido.get("estado_partido", "activo"))

    estados_bloqueados = {"finalizado", "finished", "ft", "ended"}
    if estado in estados_bloqueados:
        return False

    if minuto >= 90:
        return False

    return True


def _calcular_ranking_score(senal: Dict) -> float:
    ai_score = _safe_float(senal.get("ai_decision_score"), 0.0)
    signal_score = _safe_float(senal.get("signal_score"), 0.0)
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)
    tactical_score = _safe_float(senal.get("tactical_score"), 0.0)
    goal_score = _safe_float(senal.get("goal_inminente_score"), 0.0)
    risk_score = _safe_float(senal.get("risk_score"), 10.0)

    ranking = 0.0
    ranking += ai_score * 1.35
    ranking += signal_score * 0.85
    ranking += confidence * 1.10
    ranking += value * 2.20
    ranking += tactical_score * 0.60
    ranking += goal_score * 0.45
    ranking -= risk_score * 6.0

    return round(ranking, 2)


def _clasificar_publicacion(senal: Dict) -> Dict:
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)
    ai_score = _safe_float(senal.get("ai_decision_score"), 0.0)
    ranking_score = _safe_float(senal.get("ranking_score"), 0.0)
    risk_score = _safe_float(senal.get("risk_score"), 10.0)
    ai_rec = _safe_upper(senal.get("ai_recommendation"))
    antifake_ok = bool(senal.get("antifake_ok", True))
    value_filter_ok = bool(senal.get("value_filter_ok", True))

    blocked_reasons = []

    if ai_rec == "NO_APOSTAR":
        blocked_reasons.append("IA_NO_APOSTAR")
    if confidence < 54:
        blocked_reasons.append("CONFIANZA_BAJA")
    if value < 0:
        blocked_reasons.append("VALUE_NEGATIVO")
    if risk_score >= 9.5:
        blocked_reasons.append("RIESGO_EXTREMO")
    if not antifake_ok and confidence < 60:
        blocked_reasons.append("ANTIFAKE_DURO")
    if not value_filter_ok and value < 1 and confidence < 58:
        blocked_reasons.append("VALUE_INSUFICIENTE")

    publish_ready = len(blocked_reasons) == 0

    qualifies_for_top = (
        confidence >= 58 and
        value >= 1 and
        risk_score <= 8.8 and
        ai_rec != "NO_APOSTAR" and
        ranking_score >= 70
    )

    if confidence >= 78 and value >= 8 and ai_score >= 70 and risk_score <= 6.5:
        publish_rank = 1
    elif confidence >= 70 and value >= 4 and ai_score >= 60 and risk_score <= 7.5:
        publish_rank = 2
    elif confidence >= 60 and value >= 1 and ai_score >= 50 and risk_score <= 8.8:
        publish_rank = 3
    else:
        publish_rank = 4

    return {
        "publish_ready": publish_ready,
        "publish_blocked_reasons": blocked_reasons,
        "qualifies_for_top": qualifies_for_top,
        "publish_rank": publish_rank,
    }


# =========================================================
# PIPELINE PRINCIPAL
# MENOS ESTRICTO: PRIORIZA RANKING, NO RECHAZO ABSOLUTO
# =========================================================
def procesar_partido(partido: Dict) -> Optional[Dict]:
    if not isinstance(partido, dict):
        return None

    if not _partido_es_valido(partido):
        print(f"[PIPELINE] partido inválido o no operable -> {partido}")
        return None

    # =========================================
    # 1. GENERAR SEÑAL BASE
    # =========================================
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
        senal = generar_senal_fallback(datos)

    # =========================================
    # 2. NORMALIZAR
    # =========================================
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
        "odd": senal.get("cuota", partido.get("cuota", 1.85)),
        "prob": senal.get("prob_real", partido.get("prob_real", 0.0)),
        "value": senal.get("valor", 0.0),
        "confidence": senal.get("confianza", 0.0),
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
        "stake_pct": 0.0,
        "stake_amount": 0.0,
        "stake_label": "N/A",
        "bankroll_mode": "FLAT",
        "permitido_operar": True,
        "publish_ready": False,
        "qualifies_for_top": False,
        "publish_rank": 4,
        "ranking_score": 0.0,
        "publish_blocked_reasons": [],
    }

    # =========================================
    # 3. ENRIQUECIMIENTO BASE LOCAL
    # =========================================
    try:
        senal_final = enriquecer_senal_local(senal_final, partido)
    except Exception as e:
        print(f"[PIPELINE] ERROR enriquecer local -> {e}")

    # =========================================
    # 4. MÓDULOS OPCIONALES
    # NO BLOQUEAN SEÑAL SI FALLAN
    # =========================================
    if aplicar_auto_balance:
        try:
            senal_final = aplicar_auto_balance(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR AUTO BALANCE -> {e}")

    if evaluar_pre_match and aplicar_pre_match_a_senal:
        try:
            pre_match_data = evaluar_pre_match(
                partido,
                partido.get("home_recent_matches", []),
                partido.get("away_recent_matches", []),
                partido.get("h2h_matches", []),
                partido.get("league_stats", {}),
            )
            senal_final = aplicar_pre_match_a_senal(senal_final, pre_match_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR PRE MATCH -> {e}")

    if evaluar_contexto_partido:
        try:
            context = evaluar_contexto_partido(partido)
            if isinstance(context, dict):
                senal_final.update(context)
        except Exception as e:
            print(f"[PIPELINE] ERROR CONTEXT -> {e}")

    if evaluar_chaos_partido:
        try:
            chaos = evaluar_chaos_partido(partido, senal_final)
            if isinstance(chaos, dict):
                senal_final.update(chaos)
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

    # =========================================
    # 5. IA
    # NO BLOQUEA SALVO CASOS EXTREMOS
    # =========================================
    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            if isinstance(ai_data, dict):
                senal_final.update(ai_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR IA -> {e}")

    senal_final.setdefault("ai_recommendation", "APOSTAR_SUAVE")
    senal_final.setdefault("ai_decision_score", 60.0)
    senal_final.setdefault("ai_confidence_final", senal_final.get("confidence", 0))
    senal_final.setdefault("ai_reason", "Sin bloqueo IA")

    # =========================================
    # 6. AJUSTES
    # =========================================
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

    # =========================================
    # 7. RE-ENRIQUECER
    # POR SI LOS MÓDULOS CAMBIARON DATOS
    # =========================================
    try:
        senal_final = enriquecer_senal_local(senal_final, partido)
    except Exception as e:
        print(f"[PIPELINE] ERROR re-enriquecer local -> {e}")

    # =========================================
    # 8. FILTROS SUAVES
    # NO RECHAZAN POR DEFECTO; SOLO MARCAN
    # =========================================
    antifake_ok = True
    value_filter_ok = True
    context_ok = True
    chaos_ok = True
    confianza_ok = True

    try:
        antifake_ok = filtro_antifake_local(partido, senal_final)
    except Exception as e:
        print(f"[PIPELINE] ERROR ANTIFAKE -> {e}")

    try:
        value_filter_ok = filtrar_value_bets_reales_local(senal_final)
    except Exception as e:
        print(f"[PIPELINE] ERROR VALUE FILTER -> {e}")

    if validar_contexto_dinamico:
        try:
            context_ok = validar_contexto_dinamico(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR CONTEXT VALIDATOR -> {e}")

    if validar_chaos_dinamico:
        try:
            chaos_ok = validar_chaos_dinamico(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR CHAOS VALIDATOR -> {e}")

    if validar_confianza_dinamica:
        try:
            confianza_ok = validar_confianza_dinamica(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR CONFIANZA VALIDATOR -> {e}")

    senal_final["antifake_ok"] = antifake_ok
    senal_final["value_filter_ok"] = value_filter_ok
    senal_final["context_ok"] = context_ok
    senal_final["chaos_ok"] = chaos_ok
    senal_final["confianza_ok"] = confianza_ok

    # =========================================
    # 9. RANKING
    # AQUÍ ESTÁ EL CAMBIO CLAVE:
    # NO BLOQUEAMOS CASI TODO, ORDENAMOS
    # =========================================
    soft_penalty = 0.0

    if not antifake_ok:
        soft_penalty += 18
    if not value_filter_ok:
        soft_penalty += 14
    if not context_ok:
        soft_penalty += 12
    if not chaos_ok:
        soft_penalty += 12
    if not confianza_ok:
        soft_penalty += 10

    if _safe_upper(senal_final.get("ai_recommendation")) == "OBSERVAR":
        soft_penalty += 8
    elif _safe_upper(senal_final.get("ai_recommendation")) == "NO_APOSTAR":
        soft_penalty += 22

    base_ranking = _calcular_ranking_score(senal_final)
    senal_final["ranking_score_base"] = base_ranking
    senal_final["ranking_penalty"] = round(soft_penalty, 2)
    senal_final["ranking_score"] = round(base_ranking - soft_penalty, 2)

    publish_meta = _clasificar_publicacion(senal_final)
    senal_final.update(publish_meta)

    # =========================================
    # 10. RECOMENDACIÓN FINAL
    # =========================================
    ai_rec = _safe_upper(senal_final.get("ai_recommendation"))
    confidence = _safe_float(senal_final.get("confidence"), 0)
    value = _safe_float(senal_final.get("value"), 0)
    ranking_score = _safe_float(senal_final.get("ranking_score"), 0)

    if ai_rec in {"APOSTAR_FUERTE", "APOSTAR", "APOSTAR_SUAVE"}:
        senal_final["recomendacion_final"] = ai_rec
    elif ranking_score >= 150 and confidence >= 72 and value >= 6:
        senal_final["recomendacion_final"] = "APOSTAR_FUERTE"
    elif ranking_score >= 110 and confidence >= 64 and value >= 3:
        senal_final["recomendacion_final"] = "APOSTAR"
    elif ranking_score >= 70 and confidence >= 58 and value >= 1:
        senal_final["recomendacion_final"] = "APOSTAR_SUAVE"
    else:
        senal_final["recomendacion_final"] = "OBSERVAR"

    # =========================================
    # 11. FORMATEADOR
    # =========================================
    if formatear_senal_protocolo:
        try:
            protocol_data = formatear_senal_protocolo(senal_final)
            if isinstance(protocol_data, dict):
                senal_final.update(protocol_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR PROTOCOL FORMATTER -> {e}")

    # =========================================
    # 12. BLOQUEO SOLO EN CASOS GRAVES
    # =========================================
    if not senal_final.get("market"):
        print(f"[PIPELINE] RECHAZADO por market vacío -> {partido.get('local')} vs {partido.get('visitante')}")
        return None

    if _safe_float(senal_final.get("odd"), 0) <= 1.0:
        print(f"[PIPELINE] RECHAZADO por cuota inválida -> {partido.get('local')} vs {partido.get('visitante')}")
        return None

    if _safe_float(senal_final.get("confidence"), 0) < 45:
        print(f"[PIPELINE] RECHAZADO por confianza crítica -> {partido.get('local')} vs {partido.get('visitante')}")
        return None

    if _safe_float(senal_final.get("ranking_score"), 0) < 35:
        print(f"[PIPELINE] RECHAZADO por ranking crítico -> {partido.get('local')} vs {partido.get('visitante')}")
        return None

    # =========================================
    # 13. GUARDAR EN STORAGE SI ES PUBLICABLE O CANDIDATA
    # =========================================
    if guardar_senal_storage and senal_final.get("qualifies_for_top"):
        try:
            guardar_senal_storage(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR GUARDAR STORAGE -> {e}")

    print(
        f"[PIPELINE OK] {senal_final.get('home')} vs {senal_final.get('away')} | "
        f"market={senal_final.get('market')} | "
        f"conf={senal_final.get('confidence')} | "
        f"value={senal_final.get('value')} | "
        f"ai={senal_final.get('ai_recommendation')} | "
        f"rank={senal_final.get('ranking_score')} | "
        f"top={senal_final.get('qualifies_for_top')}"
    )

    return senal_final
