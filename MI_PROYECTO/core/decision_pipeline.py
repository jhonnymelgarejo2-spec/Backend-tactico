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
    }


# =========================================================
# PIPELINE
# =========================================================
def procesar_partido(partido: Dict) -> Optional[Dict]:

    # =========================================
    # 1. GENERAR SEÑAL
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
        "market": senal.get("mercado"),
        "selection": senal.get("apuesta"),
        "line": senal.get("linea"),
        "odd": senal.get("cuota", 1.85),
        "prob": senal.get("prob_real", 0.0),
        "value": senal.get("valor", 0),
        "confidence": senal.get("confianza", 0),
        "reason": senal.get("razon", ""),
        "goal_prob_5": senal.get("goal_prob_5", 0),
        "goal_prob_10": senal.get("goal_prob_10", 0),
        "goal_prob_15": senal.get("goal_prob_15", 0),
        "estado_partido": senal.get("estado_partido", {}),
        "gol_inminente": senal.get("gol_inminente", {}),
    }

    # =========================================
    # 3. ENRIQUECER
    # =========================================
    if enriquecer_senal:
        try:
            senal_final = enriquecer_senal(senal_final, partido)
        except Exception:
            return None

    # =========================================
    # CONTEXTO + CHAOS
    # =========================================
    if evaluar_contexto_partido:
        try:
            senal_final.update(evaluar_contexto_partido(partido))
        except:
            pass

    if evaluar_chaos_partido:
        try:
            senal_final.update(evaluar_chaos_partido(partido, senal_final))
        except:
            pass

    # =========================================
    # FILTROS
    # =========================================
    if filtro_antifake_partido and not filtro_antifake_partido(partido, senal_final):
        return None

    if filtrar_value_bets_reales and not filtrar_value_bets_reales(senal_final):
        if _safe_float(senal_final.get("confidence")) < 70:
            return None

    # =========================================
    # IA
    # =========================================
    if decision_final_ia:
        try:
            senal_final.update(decision_final_ia(partido, senal_final))
        except:
            pass

    senal_final.setdefault("ai_recommendation", "APOSTAR_SUAVE")
    senal_final.setdefault("ai_decision_score", 60)

    # =========================================
    # ADAPTIVE + MEMORY
    # =========================================
    if aplicar_ajuste_senal:
        try:
            senal_final = aplicar_ajuste_senal(senal_final)
        except:
            pass

    if aplicar_memoria_mercado:
        try:
            senal_final = aplicar_memoria_mercado(senal_final)
        except:
            pass

    # =========================================
    # BANKROLL
    # =========================================
    if aplicar_bankroll:
        try:
            senal_final = aplicar_bankroll(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR BANKROLL -> {e}")

    # =========================================
    # DECISIÓN FINAL
    # =========================================
    if _safe_upper(senal_final.get("ai_recommendation")) == "NO_APOSTAR":
        return None

    if not senal_final.get("permitido_operar", True):
        return None

    senal_final["publish_ready"] = True
    senal_final["publish_rank"] = 1

    if registrar_senal:
        try:
            registrar_senal(senal_final)
        except:
            pass

    return senal_final
