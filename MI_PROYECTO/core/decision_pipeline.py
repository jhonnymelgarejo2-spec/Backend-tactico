from typing import Dict, Optional

# =========================================================
# IMPORTS DEL SISTEMA
# =========================================================
try:
    from signal_engine import generar_senal
except Exception:
    generar_senal = None

try:
    from ai_brain import decision_final_ia
except Exception:
    decision_final_ia = None

try:
    from tactico_api import (
        enriquecer_senal,
        filtro_antifake_partido,
        filtrar_value_bets_reales,
    )
except Exception:
    enriquecer_senal = None
    filtro_antifake_partido = None
    filtrar_value_bets_reales = None

try:
    from core.context_engine import evaluar_contexto_partido
except Exception:
    evaluar_contexto_partido = None


# =========================================================
# HELPERS
# =========================================================
def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


# =========================================================
# FALLBACK SIGNAL
# =========================================================
def generar_senal_fallback(datos: Dict) -> Dict:
    return {
        "mercado": "SIN_SEÑAL",
        "apuesta": "Sin señal",
        "linea": None,
        "cuota": 1.0,
        "prob_real": 0.5,
        "valor": 0.0,
        "confianza": 50,
        "razon": "Fallback",
        "tier": "DESCARTAR",
        "signal_status": "WAIT",
        "estado_partido": {"estado": "FRIO"},
        "goal_prob_5": 0,
        "goal_prob_10": 0,
        "goal_prob_15": 0,
        "confianza_prediccion": 0,
        "ganador_probable": "",
        "doble_oportunidad_probable": "",
        "resultado_probable": "",
        "total_goles_estimado": 0,
        "linea_goles_probable": "",
        "over_under_probable": "",
        "recomendacion_final": "OBSERVAR",
        "riesgo_operativo": "ALTO",
        "value_score": 0.0,
        "value_categoria": "SIN_VALUE",
        "recomendacion_value": "NO_APOSTAR",
        "razon_value": "Fallback sin value",
    }


# =========================================================
# PIPELINE PRINCIPAL
# =========================================================
def procesar_partido(partido: Dict) -> Optional[Dict]:
    # =========================================
    # 1. GENERAR SEÑAL BASE
    # =========================================
    datos = {
        "id": partido.get("id"),
        "momentum": partido.get("momentum"),
        "xG": partido.get("xG"),
        "minuto": partido.get("minuto"),
        "marcador_local": partido.get("marcador_local"),
        "marcador_visitante": partido.get("marcador_visitante"),
        "goal_pressure": partido.get("goal_pressure"),
        "goal_predictor": partido.get("goal_predictor"),
        "chaos": partido.get("chaos"),
        "prob_real": partido.get("prob_real", 0.75),
        "prob_implicita": partido.get("prob_implicita", 0.55),
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
        return None

    # =========================================
    # 2. NORMALIZAR FORMATO
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
        "odd": senal.get("cuota"),
        "prob": senal.get("prob_real"),
        "value": senal.get("valor"),
        "confidence": senal.get("confianza"),
        "reason": senal.get("razon"),
        "tier": senal.get("tier"),
        "estado_partido": senal.get("estado_partido", {}),
        "goal_prob_5": senal.get("goal_prob_5", 0),
        "goal_prob_10": senal.get("goal_prob_10", 0),
        "goal_prob_15": senal.get("goal_prob_15", 0),
        "confianza_prediccion": senal.get("confianza_prediccion", 0),
        "signal_status": senal.get("signal_status", "WAIT"),
        "ganador_probable": senal.get("ganador_probable", ""),
        "doble_oportunidad_probable": senal.get("doble_oportunidad_probable", ""),
        "resultado_probable": senal.get("resultado_probable", ""),
        "total_goles_estimado": senal.get("total_goles_estimado", 0),
        "linea_goles_probable": senal.get("linea_goles_probable", ""),
        "over_under_probable": senal.get("over_under_probable", ""),
        "recomendacion_final": senal.get("recomendacion_final", "OBSERVAR"),
        "riesgo_operativo": senal.get("riesgo_operativo", "MEDIO"),
        "value_score": senal.get("value_score", senal.get("valor", 0)),
        "value_categoria": senal.get("value_categoria", "SIN_VALUE"),
        "recomendacion_value": senal.get("recomendacion_value", "OBSERVAR"),
        "razon_value": senal.get("razon_value", ""),
    }

    # =========================================
    # 3. ENRIQUECER
    # =========================================
    if enriquecer_senal:
        try:
            senal_final = enriquecer_senal(senal_final, partido)
        except Exception as e:
            print(f"[PIPELINE] ERROR enriquecer_senal -> {e}")
            return None

    # =========================================
    # 3.5 CONTEXTO DEL PARTIDO
    # =========================================
    if evaluar_contexto_partido:
        try:
            context_data = evaluar_contexto_partido(partido)
            senal_final.update(context_data)

            market = _safe_upper(senal_final.get("market", ""))

            if senal_final.get("context_state") == "CAOS_INESTABLE":
                print("[PIPELINE] RECHAZADO CONTEXT -> caos inestable")
                return None

            if "OVER" in market and not senal_final.get("context_supports_over", False):
                print("[PIPELINE] RECHAZADO CONTEXT -> over no alineado con contexto")
                return None

            if ("HOLD" in market or "RESULT_HOLDS" in market) and not senal_final.get("context_supports_hold", False):
                print("[PIPELINE] RECHAZADO CONTEXT -> hold no alineado con contexto")
                return None

            if ("NEXT_GOAL" in market or market == "GOAL") and not senal_final.get("context_supports_next_goal", False):
                print("[PIPELINE] RECHAZADO CONTEXT -> next goal no alineado con contexto")
                return None

        except Exception as e:
            print(f"[PIPELINE] ERROR CONTEXT -> {e}")

    # =========================================
    # 4. FILTRO ANTIFAKE
    # =========================================
    if filtro_antifake_partido:
        try:
            if not filtro_antifake_partido(partido, senal_final):
                print("[PIPELINE] RECHAZADO ANTIFAKE")
                return None
        except Exception as e:
            print(f"[PIPELINE] ERROR ANTIFAKE -> {e}")
            return None

    # =========================================
    # 5. FILTRO VALUE
    # =========================================
    if filtrar_value_bets_reales:
        try:
            if not filtrar_value_bets_reales(senal_final):
                print("[PIPELINE] RECHAZADO VALUE")
                return None
        except Exception as e:
            print(f"[PIPELINE] ERROR VALUE -> {e}")
            return None

    # =========================================
    # 6. IA DECISION
    # =========================================
    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            if isinstance(ai_data, dict):
                senal_final.update(ai_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR IA -> {e}")

    # Defaults por si la IA no devolvió algo
    senal_final.setdefault("ai_recommendation", "OBSERVAR")
    senal_final.setdefault("ai_decision_score", senal_final.get("signal_score", 0))
    senal_final.setdefault("ai_confidence_final", senal_final.get("confidence", 0))
    senal_final.setdefault("ai_reason", "Sin lectura IA")
    senal_final.setdefault("ai_fit", "NEUTRO")
    senal_final.setdefault("ai_fit_reason", "Sin ajuste especial")
    senal_final.setdefault("chaos_level", "BAJO")
    senal_final.setdefault("chaos_detector_score", 0)
    senal_final.setdefault("chaos_reason", "Sin evaluación")
    senal_final.setdefault("goal_imminent_score", senal_final.get("goal_inminente_score", 0))
    senal_final.setdefault("goal_imminent_level", "BAJO")
    senal_final.setdefault("goal_imminent_reason", "Sin evaluación")

    # =========================================
    # 7. DECISION FINAL
    # =========================================
    ai_decision = _safe_upper(senal_final.get("ai_recommendation", "OBSERVAR"))

    if ai_decision in ("NO_APOSTAR", "OBSERVAR"):
        print("[PIPELINE] RECHAZADO IA FINAL")
        return None

    # =========================================
    # 8. OUTPUT FINAL
    # =========================================
    print(
        f"[PIPELINE] SEÑAL APROBADA -> "
        f"{partido.get('local')} vs {partido.get('visitante')} | "
        f"market={senal_final.get('market')} | "
        f"context_state={senal_final.get('context_state', '')} | "
        f"context_score={senal_final.get('context_score', 0)} | "
        f"context_risk={senal_final.get('context_risk', '')}"
    )

    return senal_final
