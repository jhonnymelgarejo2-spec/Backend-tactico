import time
from typing import Dict, Any, List

from app.config.config import settings
from app.models.models import ScanResult
from app.utils.helpers import safe_float, safe_int, safe_text


def _dummy_matches() -> List[Dict[str, Any]]:
    return [
        {
            "id": "1",
            "local": "Equipo A",
            "visitante": "Equipo B",
            "liga": "Liga Demo",
            "pais": "Demo",
            "minuto": 67,
            "estado_partido": "en_juego",
            "marcador_local": 1,
            "marcador_visitante": 1,
            "xG": 1.74,
            "shots": 13,
            "shots_on_target": 5,
            "dangerous_attacks": 24,
            "momentum": "ALTO",
            "prob_real": 0.66,
            "prob_implicita": 0.54,
            "cuota": 1.92,
            "goal_pressure": {"pressure_score": 7.2},
            "goal_predictor": {
                "goal_next_5_prob": 0.22,
                "goal_next_10_prob": 0.35,
                "predictor_score": 6.8,
            },
            "chaos": {"chaos_score": 4.1},
        },
        {
            "id": "2",
            "local": "Equipo C",
            "visitante": "Equipo D",
            "liga": "Liga Demo",
            "pais": "Demo",
            "minuto": 74,
            "estado_partido": "en_juego",
            "marcador_local": 0,
            "marcador_visitante": 0,
            "xG": 0.88,
            "shots": 7,
            "shots_on_target": 2,
            "dangerous_attacks": 11,
            "momentum": "MEDIO",
            "prob_real": 0.58,
            "prob_implicita": 0.52,
            "cuota": 1.80,
            "goal_pressure": {"pressure_score": 4.0},
            "goal_predictor": {
                "goal_next_5_prob": 0.10,
                "goal_next_10_prob": 0.18,
                "predictor_score": 3.2,
            },
            "chaos": {"chaos_score": 2.0},
        },
    ]


def _is_operable_minute(minuto: int) -> bool:
    return settings.MINUTE_MIN_OPERABLE <= minuto <= settings.MINUTE_MAX_OPERABLE


def _simple_signal_logic(match: Dict[str, Any]) -> Dict[str, Any] | None:
    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    cuota = safe_float(match.get("cuota"), 0.0)
    prob_real = safe_float(match.get("prob_real"), 0.0)
    prob_implicita = safe_float(match.get("prob_implicita"), 0.0)

    if not _is_operable_minute(minuto):
        return None

    value = round((prob_real - prob_implicita) * 100, 2)
    confidence = 50.0

    if xg >= 1.5:
        confidence += 12
    elif xg >= 1.0:
        confidence += 7

    if shots_on_target >= 5:
        confidence += 10
    elif shots_on_target >= 3:
        confidence += 6

    if dangerous_attacks >= 20:
        confidence += 8
    elif dangerous_attacks >= 12:
        confidence += 4

    if minuto >= 60:
        confidence += 5

    market = ""
    selection = ""
    reason = ""

    if xg >= 1.5 and shots_on_target >= 4 and dangerous_attacks >= 18:
        market = "OVER_NEXT_15_DYNAMIC"
        selection = "Over próximos 15 min"
        reason = "Presión ofensiva real y ritmo alto"
    elif minuto >= 65 and xg < 1.1 and shots_on_target <= 2 and dangerous_attacks < 14:
        market = "UNDER_MATCH_DYNAMIC"
        selection = "Under partido"
        reason = "Partido cerrado y producción baja"
    else:
        return None

    signal_score = round(confidence * 1.1 + value * 2.0, 2)

    signal_rank = "NORMAL"
    if signal_score >= 120:
        signal_rank = "TOP"
    if signal_score >= 160:
        signal_rank = "ELITE"

    recomendacion_final = "APOSTAR" if confidence >= 68 and value > 1 else "OBSERVAR"

    return {
        "match_id": safe_text(match.get("id")),
        "partido": f"{safe_text(match.get('local'))} vs {safe_text(match.get('visitante'))}",
        "market": market,
        "selection": selection,
        "line": 0.0,
        "odd": cuota,
        "prob_real": prob_real,
        "prob_implicita": prob_implicita,
        "confidence": round(confidence, 2),
        "value": value,
        "risk_score": 5.0,
        "signal_score": signal_score,
        "signal_rank": signal_rank,
        "recomendacion_final": recomendacion_final,
        "publish_ready": recomendacion_final == "APOSTAR",
        "reason": reason,
        "minute": minuto,
        "score": f"{safe_int(match.get('marcador_local'))}-{safe_int(match.get('marcador_visitante'))}",
        "league": safe_text(match.get("liga")),
        "country": safe_text(match.get("pais")),
        "home": safe_text(match.get("local")),
        "away": safe_text(match.get("visitante")),
        "xG": xg,
        "shots": safe_int(match.get("shots")),
        "shots_on_target": shots_on_target,
        "dangerous_attacks": dangerous_attacks,
        "momentum": safe_text(match.get("momentum")),
        "odds_data_available": cuota > 0,
        "odds_validation_ok": cuota > 0,
    }


def run_scan_cycle() -> Dict[str, Any]:
    started_at = int(time.time())

    result = ScanResult()
    errors: List[str] = []

    try:
        matches = _dummy_matches()
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

            if minuto >= 15 and (xg >= 1.0 or da >= 12):
                hot_matches.append(match)

            signal = _simple_signal_logic(match)
            if signal:
                signals.append(signal)

        except Exception as e:
            errors.append(f"ERROR_PROCESS_MATCH_{safe_text(match.get('id'))}: {e}")

    signals.sort(
        key=lambda s: (
            safe_float(s.get("signal_score"), 0.0),
            safe_float(s.get("confidence"), 0.0),
            safe_float(s.get("value"), 0.0),
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
