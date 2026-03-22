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
# IMPORTS LAZY DESDE tactico_api
# EVITA IMPORTACIÓN CIRCULAR
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
    enriquecer_senal, filtro_antifake_partido, filtrar_value_bets_reales = _get_tactico_helpers()

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
        print(f"[PIPELINE] fallback activado -> {partido.get('local')} vs {partido.get('visitante')}")
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

    # =========================================
    # 3. ENRIQUECER
    # =========================================
    if enriquecer_senal:
        try:
            senal_final = enriquecer_senal(senal_final, partido)
        except Exception as e:
            print(f"[PIPELINE] ERROR ENRIQUECER -> {e}")

    # =========================================
    # 3.1 AUTO BALANCE
    # =========================================
    if aplicar_auto_balance:
        try:
            senal_final = aplicar_auto_balance(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR AUTO BALANCE -> {e}")

    # =========================================
    # 3.2 PRE MATCH ENGINE
    # =========================================
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

    # =========================================
    # 3.5 CONTEXTO DINÁMICO
    # =========================================
    if evaluar_contexto_partido:
        try:
            context = evaluar_contexto_partido(partido)
            if isinstance(context, dict):
                senal_final.update(context)

            if validar_contexto_dinamico and not validar_contexto_dinamico(senal_final):
                if _safe_float(senal_final.get("confidence", 0)) < 55:
                    print(f"[PIPELINE] RECHAZADO CONTEXT -> {partido.get('local')} vs {partido.get('visitante')}")
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
                if _safe_float(senal_final.get("confidence", 0)) < 58:
                    print(f"[PIPELINE] RECHAZADO CHAOS -> {partido.get('local')} vs {partido.get('visitante')}")
                    return None
        except Exception as e:
            print(f"[PIPELINE] ERROR CHAOS -> {e}")

    # =========================================
    # 3.7 EMOTIONAL ENGINE
    # =========================================
    if evaluar_estado_emocional and aplicar_emocion_a_senal:
        try:
            emocion = evaluar_estado_emocional(partido)
            senal_final = aplicar_emocion_a_senal(senal_final, emocion)
        except Exception as e:
            print(f"[PIPELINE] ERROR EMOTIONAL -> {e}")

    # =========================================
    # 3.8 REFEREE ENGINE
    # =========================================
    if evaluar_arbitro and aplicar_arbitro_a_senal:
        try:
            referee_data = evaluar_arbitro(partido)
            senal_final = aplicar_arbitro_a_senal(senal_final, referee_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR REFEREE -> {e}")

    # =========================================
    # 3.9 TEMPO ENGINE
    # =========================================
    if evaluar_tempo_partido and aplicar_tempo_a_senal:
        try:
            tempo_data = evaluar_tempo_partido(partido)
            senal_final = aplicar_tempo_a_senal(senal_final, tempo_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR TEMPO -> {e}")

    # =========================================
    # 4.0 PLAYER IMPACT ENGINE
    # =========================================
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
    # 4. FILTROS SUAVIZADOS
    # =========================================
    if filtro_antifake_partido:
        try:
            antifake_ok = filtro_antifake_partido(partido, senal_final)
            if not antifake_ok and _safe_float(senal_final.get("confidence", 0)) < 62:
                print(f"[PIPELINE] RECHAZADO ANTIFAKE -> {partido.get('local')} vs {partido.get('visitante')}")
                return None
        except Exception as e:
            print(f"[PIPELINE] ERROR ANTIFAKE -> {e}")

    if filtrar_value_bets_reales:
        try:
            value_ok = filtrar_value_bets_reales(senal_final)
            if not value_ok:
                if permitir_value_flex:
                    flex_mode = permitir_value_flex(senal_final)
                    if not flex_mode and _safe_float(senal_final.get("confidence", 0)) < 60:
                        print(f"[PIPELINE] RECHAZADO VALUE -> {partido.get('local')} vs {partido.get('visitante')}")
                        return None
                else:
                    if _safe_float(senal_final.get("confidence", 0)) < 60:
                        print(f"[PIPELINE] RECHAZADO VALUE -> {partido.get('local')} vs {partido.get('visitante')}")
                        return None
        except Exception as e:
            print(f"[PIPELINE] ERROR VALUE -> {e}")

    # =========================================
    # 5. VALIDACIÓN FINAL DE CONFIANZA
    # =========================================
    if validar_confianza_dinamica:
        try:
            if not validar_confianza_dinamica(senal_final):
                if _safe_float(senal_final.get("confidence", 0)) < 55:
                    print(f"[PIPELINE] RECHAZADO CONFIANZA -> {partido.get('local')} vs {partido.get('visitante')}")
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

    senal_final.setdefault("ai_recommendation", "APOSTAR_SUAVE")
    senal_final.setdefault("ai_decision_score", 60)
    senal_final.setdefault("ai_confidence_final", senal_final.get("confidence", 0))

    # =========================================
    # 6.5 ADAPTIVE + MEMORY
    # =========================================
    if aplicar_ajuste_senal:
        try:
            senal_final = aplicar_ajuste_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR ADAPTIVE -> {e}")

    if aplicar_memoria_mercado:
        try:
            senal_final = aplicar_memoria_mercado(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR MARKET MEMORY -> {e}")

    # =========================================
    # 6.7 BANKROLL
    # =========================================
    if aplicar_bankroll:
        try:
            senal_final = aplicar_bankroll(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR BANKROLL -> {e}")

    # =========================================
    # 6.8 AUTO LEARNING ENGINE
    # =========================================
    if aplicar_auto_learning:
        try:
            senal_final = aplicar_auto_learning(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR AUTO LEARNING -> {e}")

    # =========================================
    # 7. DECISIÓN FINAL SUAVIZADA
    # =========================================
    decision = _safe_upper(senal_final.get("ai_recommendation"))
    confidence = _safe_float(senal_final.get("confidence", 0))
    value = _safe_float(senal_final.get("value", 0))
    ai_score = _safe_float(senal_final.get("ai_decision_score", 0))

    if decision == "NO_APOSTAR":
        if confidence < 75:
            print(f"[PIPELINE] RECHAZADO IA FINAL -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

    if not senal_final.get("permitido_operar", True):
        if confidence < 72:
            print(f"[PIPELINE] RECHAZADO BANKROLL -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

    if decision == "OBSERVAR":
        if ai_score >= 50 and confidence >= 60 and value >= 3:
            senal_final["ai_recommendation"] = "APOSTAR_SUAVE"
        else:
            print(f"[PIPELINE] RECHAZADO OBSERVAR -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

    senal_final["publish_ready"] = True
    senal_final["publish_rank"] = 1

    # =========================================
    # 8. PROTOCOL OUTPUT FORMATTER
    # =========================================
    if formatear_senal_protocolo:
        try:
            protocol_data = formatear_senal_protocolo(senal_final)
            if isinstance(protocol_data, dict):
                senal_final.update(protocol_data)
        except Exception as e:
            print(f"[PIPELINE] ERROR PROTOCOL FORMATTER -> {e}")

    # =========================================
    # 9. REGISTRO / HISTORIAL
    # =========================================
    if registrar_senal:
        try:
            registrar_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR REGISTRAR -> {e}")

    if guardar_senal:
        try:
            guardar_senal(senal_final)
        except Exception as e:
            print(f"[PIPELINE] ERROR GUARDAR HISTORIAL -> {e}")

    print(
        f"[PIPELINE OK] {senal_final.get('home')} vs {senal_final.get('away')} | "
        f"market={senal_final.get('market')} | "
        f"conf={senal_final.get('confidence')} | "
        f"value={senal_final.get('value')} | "
        f"ai={senal_final.get('ai_recommendation')}"
    )

    return senal_final
