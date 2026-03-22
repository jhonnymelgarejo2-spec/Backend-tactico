from typing import Dict, Optional

# =========================================================
# IMPORTS DEL SISTEMA
# =========================================================
try:
    from signal_engine import generar_senal
    print("[IMPORT] signal_engine OK")
except Exception as e:
    print(f"[IMPORT] signal_engine ERROR -> {e}")
    generar_senal = None

try:
    from ai_brain import decision_final_ia
except Exception:
    decision_final_ia = None

try:
    from core.context_engine import evaluar_contexto_partido
except Exception:
    evaluar_contexto_partido = None

try:
    from core.chaos_guardian import evaluar_chaos_partido
except Exception:
    evaluar_chaos_partido = None

try:
    from core.adaptive_engine import aplicar_ajuste_senal
except Exception:
    aplicar_ajuste_senal = None

try:
    from core.market_memory import aplicar_memoria_mercado
except Exception:
    aplicar_memoria_mercado = None

try:
    from core.learning_engine import registrar_senal
except Exception:
    registrar_senal = None

try:
    from core.auto_balance_engine import (
        aplicar_auto_balance,
        validar_confianza_dinamica,
        validar_contexto_dinamico,
        validar_chaos_dinamico,
        permitir_value_flex,
    )
except Exception:
    aplicar_auto_balance = None
    validar_confianza_dinamica = None
    validar_contexto_dinamico = None
    validar_chaos_dinamico = None
    permitir_value_flex = None

try:
    from core.bankroll_manager import aplicar_bankroll
except Exception:
    aplicar_bankroll = None

try:
    from core.pre_match_engine import (
        evaluar_pre_match,
        aplicar_pre_match_a_senal,
    )
except Exception:
    evaluar_pre_match = None
    aplicar_pre_match_a_senal = None

try:
    from core.emotional_engine import (
        evaluar_estado_emocional,
        aplicar_emocion_a_senal,
    )
except Exception:
    evaluar_estado_emocional = None
    aplicar_emocion_a_senal = None

try:
    from core.referee_engine import (
        evaluar_arbitro,
        aplicar_arbitro_a_senal,
    )
except Exception:
    evaluar_arbitro = None
    aplicar_arbitro_a_senal = None

try:
    from core.tempo_engine import (
        evaluar_tempo_partido,
        aplicar_tempo_a_senal,
    )
except Exception:
    evaluar_tempo_partido = None
    aplicar_tempo_a_senal = None

try:
    from core.player_impact_engine import (
        evaluar_player_impact,
        aplicar_player_impact_a_senal,
    )
except Exception:
    evaluar_player_impact = None
    aplicar_player_impact_a_senal = None

try:
    from core.protocol_output_formatter import formatear_senal_protocolo
except Exception:
    formatear_senal_protocolo = None

try:
    from core.auto_learning_engine import aplicar_auto_learning
except Exception:
    aplicar_auto_learning = None

try:
    from core.history_manager import guardar_senal
except Exception:
    guardar_senal = None


# =========================================================
# IMPORT LAZY tactico_api
# =========================================================
def _get_tactico_helpers():
    try:
        from tactico_api import (
            enriquecer_senal,
            filtro_antifake_partido,
            filtrar_value_bets_reales,
        )
        return enriquecer_senal, filtro_antifake_partido, filtrar_value_bets_reales
    except Exception as e:
        print(f"[PIPELINE] tactico helpers no disponibles -> {e}")
        return None, None, None


# =========================================================
# HELPERS
# =========================================================
def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


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

    enriquecer_senal, filtro_antifake_partido, filtrar_value_bets_reales = _get_tactico_helpers()

    print("[DEBUG] tactico_api activo:", enriquecer_senal is not None)

    # =========================================
    # GENERAR SEÑAL
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
    }

    if generar_senal:
        try:
            senal = generar_senal(datos)
        except Exception:
            senal = generar_senal_fallback(datos)
    else:
        senal = generar_senal_fallback(datos)

    if not senal:
        senal = generar_senal_fallback(datos)

    # =========================================
    # NORMALIZAR
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
        "odd": senal.get("cuota", 1.85),
        "prob": senal.get("prob_real", 0),
        "value": senal.get("valor", 0),
        "confidence": senal.get("confianza", 0),
        "reason": senal.get("razon", ""),
        "estado_partido": senal.get("estado_partido", {}),
        "recomendacion_final": senal.get("recomendacion_final", "OBSERVAR"),
    }

    # =========================================
    # ENRIQUECER
    # =========================================
    if enriquecer_senal:
        try:
            senal_final = enriquecer_senal(senal_final, partido)
        except Exception as e:
            print(f"[PIPELINE] ERROR ENRIQUECER -> {e}")

    # =========================================
    # IA
    # =========================================
    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            if isinstance(ai_data, dict):
                senal_final.update(ai_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR IA -> {e}")

    senal_final.setdefault("ai_recommendation", "APOSTAR_SUAVE")
    senal_final.setdefault("ai_decision_score", 60)

    # 🔥 FIX CRÍTICO
    senal_final["recomendacion_final"] = senal_final.get("ai_recommendation", "OBSERVAR")

    print(f"[PIPELINE OK] {senal_final.get('home')} vs {senal_final.get('away')}")

    return senal_final
