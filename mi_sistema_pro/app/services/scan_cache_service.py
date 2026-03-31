import time
from threading import Lock
from typing import Dict, Any

from app.services.scan_service import run_scan_cycle
from app.utils.logger import get_logger

logger = get_logger("scan_cache_service")

_CACHE_LOCK = Lock()
_LAST_SCAN_RESULT: Dict[str, Any] = {}
_LAST_SCAN_TS: int = 0

SCAN_CACHE_TTL_SECONDS = 20


def get_scan_result(force_refresh: bool = False) -> Dict[str, Any]:
    global _LAST_SCAN_RESULT, _LAST_SCAN_TS

    now = int(time.time())

    with _CACHE_LOCK:
        cache_valid = (
            not force_refresh
            and bool(_LAST_SCAN_RESULT)
            and (now - _LAST_SCAN_TS) < SCAN_CACHE_TTL_SECONDS
        )

        if cache_valid:
            logger.info(
                "Cache HIT | age=%s s | ttl=%s s",
                now - _LAST_SCAN_TS,
                SCAN_CACHE_TTL_SECONDS,
            )
            return dict(_LAST_SCAN_RESULT)

        logger.info(
            "Cache MISS | force_refresh=%s | last_age=%s",
            force_refresh,
            (now - _LAST_SCAN_TS) if _LAST_SCAN_TS else "none",
        )

        fresh_result = run_scan_cycle()
        if not isinstance(fresh_result, dict):
            fresh_result = {
                "ok": False,
                "error": "SCAN_RESULT_INVALID",
                "signals": [],
                "observed_signals": [],
                "hot_matches": [],
                "stats": {
                    "total_matches": 0,
                    "total_signals": 0,
                    "total_hot_matches": 0,
                    "observed_signals": 0,
                    "strict_signals": 0,
                    "flex_signals": 0,
                    "errors": 1,
                },
            }

        _LAST_SCAN_RESULT = fresh_result
        _LAST_SCAN_TS = now

        return dict(_LAST_SCAN_RESULT)


def get_cache_meta() -> Dict[str, Any]:
    now = int(time.time())

    with _CACHE_LOCK:
        age = (now - _LAST_SCAN_TS) if _LAST_SCAN_TS else None
        return {
            "has_cache": bool(_LAST_SCAN_RESULT),
            "last_scan_ts": _LAST_SCAN_TS,
            "cache_age_seconds": age,
            "cache_ttl_seconds": SCAN_CACHE_TTL_SECONDS,
        }


def clear_scan_cache() -> Dict[str, Any]:
    global _LAST_SCAN_RESULT, _LAST_SCAN_TS

    with _CACHE_LOCK:
        _LAST_SCAN_RESULT = {}
        _LAST_SCAN_TS = 0

    logger.info("Cache limpiada")
    return {
        "ok": True,
        "message": "SCAN_CACHE_CLEARED",
                 }
