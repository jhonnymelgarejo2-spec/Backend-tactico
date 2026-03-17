# core/decision_pipeline.py

from typing import Dict, Optional

# IMPORTAMOS LO QUE YA EXISTE (NO ROMPEMOS NADA)
try:
    from signal_engine import generar_senal
except:
    generar_senal = None

try:
    from ai_brain import decision_final_ia
except:
    decision_final_ia = None

try:
    from tactico_api import (
        enriquecer_senal,
        filtro_antifake_partido,
        filtrar_value_bets_reales
    )
except:
    enriquecer_senal = None
    filtro_antifake_partido = None
    filtrar_value_bets_reales = None


# =========================================================
# FALLBACK SIGNAL
# =========================================================
def generar_senal_fallback(datos: Dict) -> Dict:
    return {
        "mercado": "SIN_SEÑAL",
        "apuesta": "Sin señal",
        "cuota": 1.0,
        "prob_real": 0.5,
        "valor": 0,
        "confianza": 50,
        "razon": "Fallback",
        "tier": "DESCARTAR",
        "signal_status": "WAIT"
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
        "prob_real": 0.75,
        "prob_implicita": 0.55,
        "cuota": 1.85,
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
    }

    # =========================================
    # 3. ENRIQUECER
    # =========================================
    if enriquecer_senal:
        senal_final = enriquecer_senal(senal_final, partido)

    # =========================================
    # 4. FILTRO ANTIFAKE
    # =========================================
    if filtro_antifake_partido:
        if not filtro_antifake_partido(partido, senal_final):
            print("[PIPELINE] RECHAZADO ANTIFAKE")
            return None

    # =========================================
    # 5. FILTRO VALUE
    # =========================================
    if filtrar_value_bets_reales:
        if not filtrar_value_bets_reales(senal_final):
            print("[PIPELINE] RECHAZADO VALUE")
            return None

    # =========================================
    # 6. IA DECISION
    # =========================================
    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            senal_final.update(ai_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR IA -> {e}")

    # =========================================
    # 7. DECISION FINAL
    # =========================================
    ai_decision = senal_final.get("ai_recommendation", "OBSERVAR")

    if ai_decision in ("NO_APOSTAR", "OBSERVAR"):
        print("[PIPELINE] RECHAZADO IA FINAL")
        return None

    # =========================================
    # 8. OUTPUT FINAL
    # =========================================
    print("[PIPELINE] SEÑAL APROBADA")
    return senal_final
