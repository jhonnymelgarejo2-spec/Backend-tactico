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


# =========================================================
# FALLBACK
# =========================================================
def generar_senal_fallback(datos: Dict) -> Dict:
    return {
        "mercado": "SIN_SEÑAL",
        "valor": 0,
        "confianza": 0,
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
        "value": senal.get("valor", 0),
        "confidence": senal.get("confianza", 0),
        "goal_prob_5": senal.get("goal_prob_5", 0),
        "goal_prob_10": senal.get("goal_prob_10", 0),
        "goal_prob_15": senal.get("goal_prob_15", 0),
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
    # 3.5 CONTEXTO (AJUSTADO 🔥)
    # =========================================
    if evaluar_contexto_partido:
        try:
            context = evaluar_contexto_partido(partido)
            senal_final.update(context)

            if senal_final.get("context_state") == "CAOS_INESTABLE":
                print("[PIPELINE] RECHAZADO CONTEXT")
                return None

            # 🔥 AJUSTE CLAVE (ANTES 45)
            if _safe_float(senal_final.get("context_score", 0)) < 35:
                print("[PIPELINE] CONTEXT DEBIL PERO PERMITIDO")

        except Exception:
            pass

    # =========================================
    # 3.6 CHAOS GUARDIAN (AJUSTADO 🔥)
    # =========================================
    if evaluar_chaos_partido:
        try:
            chaos = evaluar_chaos_partido(partido, senal_final)
            senal_final.update(chaos)

            # 🔥 SOLO BLOQUEA SI BAJA CONFIANZA
            if senal_final.get("chaos_block_signal") and _safe_float(senal_final.get("confidence", 0)) < 75:
                print("[PIPELINE] RECHAZADO CHAOS")
                return None

        except Exception:
            pass

    # =========================================
    # 4. ANTIFAKE
    # =========================================
    if filtro_antifake_partido:
        try:
            if not filtro_antifake_partido(partido, senal_final):
                return None
        except Exception:
            return None

    # =========================================
    # 5. VALUE (AJUSTADO 🔥)
    # =========================================
    if filtrar_value_bets_reales:
        try:
            if not filtrar_value_bets_reales(senal_final):
                # 🔥 SOLO BLOQUEA SI CONFIANZA BAJA
                if _safe_float(senal_final.get("confidence", 0)) < 70:
                    return None
        except Exception:
            return None

    # =========================================
    # 6. IA
    # =========================================
    if decision_final_ia:
        try:
            ai_data = decision_final_ia(partido, senal_final)
            if isinstance(ai_data, dict):
                senal_final.update(ai_data)
        except Exception:
            pass

    senal_final.setdefault("ai_recommendation", "OBSERVAR")
    senal_final.setdefault("ai_decision_score", 50)

    # =========================================
    # 6.5 ADAPTIVE
    # =========================================
    if aplicar_ajuste_senal:
        try:
            senal_final = aplicar_ajuste_senal(senal_final)
        except Exception:
            pass

    # =========================================
    # 6.6 MARKET MEMORY
    # =========================================
    if aplicar_memoria_mercado:
        try:
            senal_final = aplicar_memoria_mercado(senal_final)
        except Exception:
            pass

    # =========================================
    # 7. DECISION FINAL
    # =========================================
    decision = _safe_upper(senal_final.get("ai_recommendation"))

    if decision == "NO_APOSTAR":
        return None

    senal_final["publish_ready"] = True
    senal_final["publish_rank"] = 1

    print(
        f"[PIPELINE] OK -> {senal_final.get('home')} vs {senal_final.get('away')} | "
        f"{senal_final.get('market')} | "
        f"confidence={senal_final.get('confidence')} | "
        f"chaos={senal_final.get('chaos_level')} | "
        f"memory={senal_final.get('market_memory_label')}"
    )

    if registrar_senal:
        try:
            registrar_senal(senal_final)
        except Exception:
            pass

    return senal_final
