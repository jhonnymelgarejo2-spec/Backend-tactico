# app/services/scan_service.py

import time
from typing import Dict, Any, List

from app.config.config import settings
from app.fetchers.live_match_fetcher import obtener_partidos_en_vivo
from app.models.models import ScanResult
from app.utils.helpers import safe_float, safe_int, safe_text

# 🔥 IMPORTANTE (tu archivo de odds)
from app.odds.odds_service import obtener_odds_partido


def _is_operable_minute(minuto: int) -> bool:
    return settings.MINUTE_MIN_OPERABLE <= minuto <= settings.MINUTE_MAX_OPERABLE


def _enhanced_signal_logic(match: Dict[str, Any]) -> Dict[str, Any] | None:
    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)

    if not _is_operable_minute(minuto):
        return None

    # 🔥 Obtener odds reales
    odds = obtener_odds_partido(
        local=match.get("local"),
        visitante=match.get("visitante"),
        league=match.get("liga"),
        country=match.get("pais"),
    )

    cuota = safe_float(odds.get("markets", [{}])[0].get("over_price"), 0.0)
    prob_real = safe_float(match.get("prob_real"), 0.0)
    prob_implicita = 1 / cuota if cuota > 0 else 0.0

    value = round((prob_real - prob_implicita) * 100, 2)

    # 🔥 SCORE AVANZADO
    pressure_score = (
        xg * 10 +
        shots_on_target * 6 +
        dangerous_attacks * 0.4
    )

    tempo_bonus = 5 if minuto >= 60 else 0

    confidence = round(
        pressure_score * 0.6 +
        value * 1.8 +
        tempo_bonus,
        2
    )

    # 🔥 FILTRO DURO (evita basura)
    if confidence < 55:
        return None

    # 🔥 DECISIÓN DE MERCADO
    if pressure_score >= 18:
        market = "OVER_NEXT_15"
        selection = "Over próximos 15 min"
        reason = "Alta presión ofensiva + ritmo"
    elif pressure_score < 10:
        market = "UNDER_MATCH"
        selection = "Under partido"
        reason = "Bajo ritmo + baja generación"
    else:
        return None

    signal_score = round(confidence * 1.2 + value * 2.2, 2)

    signal_rank = "NORMAL"
    if signal_score >= 120:
        signal_rank = "TOP"
    if signal_score >= 160:
        signal_rank = "ELITE"

    recomendacion_final = "APOSTAR" if confidence >= 70 and value > 1 else "OBSERVAR"

    return {
        "match_id": safe_text(match.get("id")),
        "partido": f"{safe_text(match.get('local'))} vs {safe_text(match.get('visitante'))}",
        "market": market,
        "selection": selection,
        "odd": cuota,
        "prob_real": prob_real,
        "prob_implicita": prob_implicita,
        "confidence": confidence,
        "value": value,
        "signal_score": signal_score,
        "signal_rank": signal_rank,
        "recomendacion_final": recomendacion_final,
        "publish_ready": recomendacion_final == "APOSTAR",
        "reason": reason,
        "minute": minuto,
        "score": f"{safe_int(match.get('marcador_local'))}-{safe_int(match.get('marcador_visitante'))}",
        "league": safe_text(match.get("liga")),
        "country": safe_text(match.get("pais")),
        "xG": xg,
        "shots_on_target": shots_on_target,
        "dangerous_attacks": dangerous_attacks,
        "odds_data_available": odds.get("odds_data_available", False),
        "odds_source": odds.get("odds_source", ""),
    }


def run_scan_cycle() -> Dict[str, Any]:
    started_at = int(time.time())

    result = ScanResult()
    errors: List[str] = []

    try:
        matches = obtener_partidos_en_vivo()
    except Exception as e:
        matches = []
        errors.append(f"ERROR_FETCH_MATCHES: {e}")

    result.total_matches = len(matches)

    signals: List[Dict[str, Any]] = []
    hot_matches: List[Dict[str, Any]] = []

    for match in matches:
        try:
            minuto = safe_int(match.get("minuto"), 0)
            xg = safe_float(match.get("xG"), 0.0)
            da = safe_int(match.get("dangerous_attacks"), 0)

            # 🔥 HOT MATCHES MEJORADOS
            if minuto >= 20 and (xg >= 1.2 or da >= 15):
                hot_matches.append(match)

            signal = _enhanced_signal_logic(match)
            if signal:
                signals.append(signal)

        except Exception as e:
            errors.append(f"ERROR_MATCH_{safe_text(match.get('id'))}: {e}")

    # 🔥 ORDENAMIENTO PRO
    signals.sort(
        key=lambda s: (
            safe_float(s.get("signal_score"), 0.0),
            safe_float(s.get("confidence"), 0.0),
        ),
        reverse=True,
    )

    signals = signals[:settings.MAX_SIGNALS]
    hot_matches = hot_matches[:10]

    result.total_signals = len(signals)
    result.signals = signals
    result.hot_matches = hot_matches
    result.errors = errors

    return {
        "ok": True,
        "system": settings.SYSTEM_NAME,
        "version": settings.SYSTEM_VERSION,
        "scan_started_at": started_at,
        "scan_finished_at": int(time.time()),
        "stats": {
            "total_matches": result.total_matches,
            "total_signals": result.total_signals,
            "total_hot_matches": len(result.hot_matches),
            "errors": len(result.errors),
        },
        "signals": result.signals,
        "hot_matches": result.hot_matches,
        "errors": result.errors,
    }
