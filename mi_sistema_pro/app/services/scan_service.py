import time
from typing import Dict, Any, List

from app.config.config import settings
from app.fetchers.live_match_fetcher import obtener_partidos_en_vivo
from app.models.models import ScanResult
from app.services.hot_match_service import build_hot_match
from app.services.signal_service import process_match_signal
from app.utils.helpers import safe_float, safe_int, safe_text
from app.utils.logger import get_logger

logger = get_logger("scan_service")


def run_scan_cycle() -> Dict[str, Any]:
    started_at = int(time.time())

    result = ScanResult()
    errors: List[str] = []

    logger.info("Inicio scan cycle")

    try:
        matches = obtener_partidos_en_vivo()
        logger.info(
            "Fetch completado | total_matches_raw=%s",
            len(matches) if isinstance(matches, list) else "invalid",
        )
    except Exception as e:
        matches = []
        errors.append(f"ERROR_FETCH_MATCHES: {e}")
        logger.exception("Error obteniendo partidos en vivo")

    if not isinstance(matches, list):
        matches = []
        errors.append("ERROR_FETCH_MATCHES: respuesta no válida, no es lista")
        logger.error("Respuesta de fetch inválida: no es lista")

    result.total_matches = len(matches)

    signals: List[Dict[str, Any]] = []
    hot_matches: List[Dict[str, Any]] = []
    observed_signals: List[Dict[str, Any]] = []

    for match in matches:
        try:
            if not isinstance(match, dict):
                logger.warning("Match inválido ignorado: no es dict")
                continue

            partido = f"{safe_text(match.get('local'))} vs {safe_text(match.get('visitante'))}"

            hot_match = build_hot_match(match)
            if hot_match:
                hot_matches.append(hot_match)
                logger.info(
                    "Hot match detectado | partido=%s | minuto=%s",
                    partido,
                    hot_match.get("minuto"),
                )

            signal = process_match_signal(match)

            if signal:
                observed_signals.append(signal)

                publish_ready = bool(signal.get("publish_ready", False))
                odds_validation_ok = bool(signal.get("odds_validation_ok", False))
                odds_data_available = bool(signal.get("odds_data_available", False))

                if publish_ready and odds_validation_ok and odds_data_available:
                    signals.append(signal)
                    logger.info(
                        "Señal PUBLICABLE añadida | partido=%s | market=%s | score=%s | rank=%s | publish_ready=%s",
                        partido,
                        signal.get("market"),
                        signal.get("signal_score"),
                        signal.get("signal_rank"),
                        signal.get("publish_ready"),
                    )
                else:
                    logger.info(
                        "Señal observada pero NO publicable | partido=%s | market=%s | publish_ready=%s | odds_data_available=%s | odds_validation_ok=%s | error=%s",
                        partido,
                        signal.get("market"),
                        signal.get("publish_ready"),
                        signal.get("odds_data_available"),
                        signal.get("odds_validation_ok"),
                        signal.get("odds_error", ""),
                    )
            else:
                logger.info("Partido sin señal final | partido=%s", partido)

        except Exception as e:
            errors.append(f"ERROR_PROCESS_MATCH_{safe_text(match.get('id'))}: {e}")
            logger.exception("Error procesando partido id=%s", match.get("id"))

    signals.sort(
        key=lambda s: (
            safe_float(s.get("signal_score"), 0.0),
            safe_float(s.get("confidence"), 0.0),
            safe_float(s.get("value"), 0.0),
        ),
        reverse=True,
    )

    hot_matches.sort(
        key=lambda m: (
            safe_float(m.get("xG"), 0.0),
            safe_int(m.get("shots_on_target"), 0),
            safe_int(m.get("dangerous_attacks"), 0),
        ),
        reverse=True,
    )

    signals = signals[:settings.MAX_SIGNALS]
    hot_matches = hot_matches[:10]

    result.total_signals = len(signals)
    result.signals = signals
    result.hot_matches = hot_matches
    result.errors = errors

    logger.info(
        "Fin scan cycle | total_matches=%s | total_signals=%s | total_hot_matches=%s | observed_signals=%s | errors=%s",
        result.total_matches,
        result.total_signals,
        len(result.hot_matches),
        len(observed_signals),
        len(result.errors),
    )

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
            "observed_signals": len(observed_signals),
            "errors": len(result.errors),
        },
        "signals": result.signals,
        "hot_matches": result.hot_matches,
        "errors": result.errors,
        }
