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
    minuto = _safe_int(datos.get("minuto"), 0)
    xg = _safe_float(datos.get("xG"), 0)
    ml = _safe_int(datos.get("marcador_local"), 0)
    mv = _safe_int(datos.get("marcador_visitante"), 0)

    market = "OVER_NEXT_15_DYNAMIC" if xg >= 1.2 else "RESULT_HOLDS_NEXT_15"
    apuesta = "Over próximos 15 min" if market == "OVER_NEXT_15_DYNAMIC" else "Se mantiene el resultado próximos 15 min"

    return {
        "id": datos.get("id", ""),
        "minuto": minuto,
        "mercado": market,
        "apuesta": apuesta,
        "linea": (ml + mv + 0.5) if market == "OVER_NEXT_15_DYNAMIC" else None,
        "cuota": _safe_float(datos.get("cuota"), 1.85),
        "prob_real": 0.64 if market == "OVER_NEXT_15_DYNAMIC" else 0.61,
        "valor": 6.5 if market == "OVER_NEXT_15_DYNAMIC" else 5.0,
        "confianza": 75 if market == "OVER_NEXT_15_DYNAMIC" else 72,
        "razon": "Fallback por presión/xG básica",
        "tier": "NORMAL",
        "signal_status": "OPEN",
        "goal_prob_5": 30,
        "goal_prob_10": 40,
        "goal_prob_15": 50,
        "estado_partido": {"estado": "CONTROLADO"},
        "gol_inminente": {"gol_inminente": xg >= 1.8},
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
            print(f"[DEBUG] señal generada: {senal}")
        except Exception as e:
            print(f"[PIPELINE] ERROR generar_senal -> {e}")
            senal = generar_senal_fallback(datos)
    else:
        senal = generar_senal_fallback(datos)

    if not senal or senal.get("mercado") == "SIN_SEÑAL":
        print("[PIPELINE] FORZANDO SEÑAL FALLBACK")
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
    }

    # =========================================
    # 3. ENRIQUECER
    # =========================================
    if enriquecer_senal:
        try:
            senal_final = enriquecer_senal(senal_final, partido)
        except Exception as e:
            print(f"[PIPELINE] ERROR ENRIQUECER -> {e}")
            return None

    # =========================================
    # 3.1 AUTO BALANCE
    # =========================================
    if aplicar_auto_balance:
        try:
            senal_final = aplicar_auto_balance(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR AUTO BALANCE -> {e}")

    # =========================================
    # 3.5 CONTEXTO DINÁMICO
    # =========================================
    if evaluar_contexto_partido:
        try:
            context = evaluar_contexto_partido(partido)
            if isinstance(context, dict):
                senal_final.update(context)

            if validar_contexto_dinamico and not validar_contexto_dinamico(senal_final):
                # solo bloquea si la confianza no es suficientemente fuerte
                if _safe_float(senal_final.get("confidence", 0)) < 65:
                    print("[PIPELINE] RECHAZADO CONTEXT DINAMICO")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CONTEXT -> {e}")

    # =========================================
    # 3.6 CHAOS DINÁMICO
    # =========================================
    if evaluar_chaos_partido:
        try:
            chaos = evaluar_chaos_partido(partido, senal_final)
            if isinstance(chaos, dict):
                senal_final.update(chaos)

            if validar_chaos_dinamico and not validar_chaos_dinamico(senal_final):
                # solo bloquea si la confianza no es suficientemente fuerte
                if _safe_float(senal_final.get("confidence", 0)) < 70:
                    print("[PIPELINE] RECHAZADO CHAOS DINAMICO")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CHAOS -> {e}")

    # =========================================
    # 4. ANTIFAKE
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
    # 5. VALUE DINÁMICO
    # =========================================
    if filtrar_value_bets_reales:
        try:
            if not filtrar_value_bets_reales(senal_final):
                if permitir_value_flex:
                    flex_mode = permitir_value_flex(senal_final)
                    if not flex_mode and _safe_float(senal_final.get("confidence", 0)) < 70:
                        print("[PIPELINE] RECHAZADO VALUE DINAMICO")
                        return None
                else:
                    if _safe_float(senal_final.get("confidence", 0)) < 70:
                        print("[PIPELINE] RECHAZADO VALUE")
                        return None
        except Exception as e:
            print(f"[PIPELINE] ERROR VALUE -> {e}")
            return None

    # =========================================
    # VALIDACIÓN FINAL DE CONFIANZA
    # =========================================
    if validar_confianza_dinamica:
        try:
            if not validar_confianza_dinamica(senal_final):
                # solo bloquea si es realmente baja
                if _safe_float(senal_final.get("confidence", 0)) < 60:
                    print("[PIPELINE] RECHAZADO POR CONFIANZA BAJA REAL")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CONFIANZA DINAMICA -> {e}")

    # =========================================
    # 6. IA
    # =========================================
    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            if isinstance(ai_data, dict):
                senal_final.update(ai_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR IA -> {e}")

    senal_final.setdefault("ai_recommendation", "OBSERVAR")
    senal_final.setdefault("ai_decision_score", 50)
    senal_final.setdefault("ai_confidence_final", senal_final.get("confidence", 0))

    # =========================================
    # 6.5 ADAPTIVE
    # =========================================
    if aplicar_ajuste_senal:
        try:
            senal_final = aplicar_ajuste_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR ADAPTIVE -> {e}")

    # =========================================
    # 6.6 MARKET MEMORY
    # =========================================
    if aplicar_memoria_mercado:
        try:
            senal_final = aplicar_memoria_mercado(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR MARKET MEMORY -> {e}")

  # =========================================
  # 6.7 BANKROLL MANAGER
  # =========================================
  if aplicar_bankroll:
      try:
          senal_final = aplicar_bankroll(senal_final)
      except Exception as e:
          print(f"[PIPELINE] ERROR BANKROLL -> {e}")
    
    # =========================================
    # 7. DECISIÓN FINAL
    # =========================================
    decision = _safe_upper(senal_final.get("ai_recommendation"))

    if decision == "NO_APOSTAR":
    print("[PIPELINE] RECHAZADO IA FINAL")
    return None

if not senal_final.get("permitido_operar", True):
    print(f"[PIPELINE] RECHAZADO BANKROLL -> {senal_final.get('motivo_operacion')}")
    return None

    # si viene observación, pero ya sobrevivió a todo y tiene valores decentes, se publica
    if decision == "OBSERVAR":
        ai_score = _safe_float(senal_final.get("ai_decision_score", 0))
        confidence = _safe_float(senal_final.get("confidence", 0))
        value = _safe_float(senal_final.get("value", 0))

        if ai_score >= 50 and confidence >= 60 and value >= 3:
            senal_final["ai_recommendation"] = "APOSTAR_SUAVE"
        else:
            print("[PIPELINE] RECHAZADO OBSERVAR SIN FUERZA")
            return None

    senal_final["publish_ready"] = True
    senal_final["publish_rank"] = 1

    print(
        f"[PIPELINE] OK -> {senal_final.get('home')} vs {senal_final.get('away')} | "
        f"{senal_final.get('market')} | "
        f"confidence={senal_final.get('confidence')} | "
        f"mode={senal_final.get('auto_balance_mode')}"
    )

    if registrar_senal:
        try:
            registrar_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR REGISTRAR -> {e}")

    return senal_final
