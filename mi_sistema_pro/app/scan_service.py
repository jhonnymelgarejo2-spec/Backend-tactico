# app/services/scan_service.py

import time
from typing import Dict, Any, List

from app.config.config import config


_LAST_SCAN_STATE: Dict[str, Any] = {
    "last_scan": 0,
    "total_matches": 0,
    "total_hot_matches": 0,
    "total_signals": 0,
    "matches": [],
    "hot_matches": [],
    "signals": [],
    "stats": {
        "win_rate": 0.0,
    },
}


def get_last_scan_state() -> Dict[str, Any]:
    return _LAST_SCAN_STATE


def run_scan_cycle() -> Dict[str, Any]:
    """
    Primera versión:
    - no rompe
    - devuelve respuesta segura
    - luego aquí conectaremos fetcher + pipeline
    """
    now_ts = int(time.time())

    result = {
        "last_scan": now_ts,
        "total_matches": 0,
        "total_hot_matches": 0,
        "total_signals": 0,
        "matches": [],
        "hot_matches": [],
        "signals": [],
        "stats": {
            "win_rate": 0.0,
        },
        "status": "ok",
        "message": "Scan ejecutado correctamente",
    }

    _LAST_SCAN_STATE.update(result)
    return _LAST_SCAN_STATE


def get_dashboard_data() -> Dict[str, Any]:
    data = get_last_scan_state()
    return {
        "last_scan": data.get("last_scan", 0),
        "total_matches": data.get("total_matches", 0),
        "total_hot_matches": data.get("total_hot_matches", 0),
        "total_signals": data.get("total_signals", 0),
        "signals": data.get("signals", []),
        "stats": data.get("stats", {"win_rate": 0.0}),
        "status": "ok",
    }


def get_signals() -> Dict[str, Any]:
    data = get_last_scan_state()
    return {
        "signals": data.get("signals", []),
        "total_signals": data.get("total_signals", 0),
        "status": "ok",
    }


def get_hot_matches() -> Dict[str, Any]:
    data = get_last_scan_state()
    return {
        "hot_matches": data.get("hot_matches", []),
        "total_hot_matches": data.get("total_hot_matches", 0),
        "status": "ok",
  }
