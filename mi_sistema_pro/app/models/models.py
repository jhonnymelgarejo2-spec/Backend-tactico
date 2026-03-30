# app/models/models.py

from typing import Dict, Any


def build_base_match() -> Dict[str, Any]:
    return {
        "id": "",
        "local": "Local",
        "visitante": "Visitante",
        "liga": "Liga desconocida",
        "pais": "Mundo",
        "minuto": 0,
        "estado_partido": "en_juego",
        "marcador_local": 0,
        "marcador_visitante": 0,
        "xG": 0.0,
        "shots": 0,
        "shots_on_target": 0,
        "dangerous_attacks": 0,
        "momentum": "MEDIO",
        "goal_pressure": {
            "pressure_score": 0.0,
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.0,
            "goal_next_10_prob": 0.0,
            "predictor_score": 0.0,
        },
        "chaos": {
            "chaos_score": 0.0,
        },
        "prob_real": 0.0,
        "prob_implicita": 0.0,
        "cuota": 0.0,
        "fetched_at": 0,
        "source_updated_at": 0,
        "source_delay_seconds": 0,
        "time_fresh": True,
        "source": "unknown",
    }


def build_base_signal() -> Dict[str, Any]:
    return {
        "match_id": "",
        "home": "",
        "away": "",
        "league": "",
        "country": "",
        "partido": "",
        "score": "0-0",
        "minute": 0,
        "market": "",
        "selection": "",
        "line": 0.0,
        "odd": 0.0,
        "cuota": 0.0,
        "prob": 0.0,
        "prob_real": 0.0,
        "prob_real_pct": 0.0,
        "prob_implicita": 0.0,
        "confidence": 0.0,
        "value": 0.0,
        "valor": 0.0,
        "reason": "",
        "tier": "",
        "risk_score": 0.0,
        "signal_score": 0.0,
        "signal_rank": "NORMAL",
        "ranking_score": 0.0,
        "publish_ready": False,
        "recomendacion_final": "OBSERVAR",
        "odds_data_available": False,
        "odds_validation_ok": False,
        "market_validation_reason": "Sin validación externa",
    }
