# signals.py

from typing import List, Dict, Any, Tuple
import config

# =========================================================
# IMPORT PIPELINE OFICIAL
# =========================================================
try:
    from pipeline_de_decisión import procesar_partido
except Exception:
    try:
        from core.decision_pipeline import procesar_partido
    except Exception as e:
        print(f"[SIGNALS] ERROR import procesar_partido -> {e}")
        procesar_partido = None


# =========================================================
# HELPERS SEGUROS
# =========================================================
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_upper(value: Any) -> str:
    return _safe_text(value).upper()


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


# =========================================================
# NORMALIZACION SIMPLE DE ESTADO
# =========================================================
def _normalizar_estado_partido(value: Any) -> str:
    estado = _safe_lower(value, "en_juego")

    if estado in {"ft", "finished", "finalizado", "ended", "after extra time", "penalties"}:
        return "finalizado"

    if estado in {"1h", "2h", "ht", "live", "en_juego", "activo", "playing"}:
        return "en_juego"

    return "en_juego"


# =========================================================
# VALIDACION BASE DEL PARTIDO
# =========================================================
def partido_es_apostable(p: Dict[str, Any]) -> Tuple[bool, str]:
    minuto = _safe_int(p.get("minuto", 0), 0)
    estado = _normalizar_estado_partido(p.get("estado_partido", "en_juego"))

    if estado == "finalizado":
        return False, "Partido finalizado"

    if minuto > 92:
        return False, "Minuto demasiado alto"

    return True, "OK"


# =========================================================
# NORMALIZACION PARA PIPELINE
# =========================================================
def normalizar_partido_para_pipeline(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte el partido crudo en un objeto consistente
    para el pipeline oficial.
    """
    goal_pressure = p.get("goal_pressure", {}) or {}
    goal_predictor = p.get("goal_predictor", {}) or {}
    chaos = p.get("chaos", {}) or {}

    cuota = _safe_float(p.get("cuota", 0.0), 0.0)
    if cuota <= 0:
        cuota = config.DEFAULT_ODD

    prob_real = _safe_float(p.get("prob_real", 0.0), 0.0)
    if prob_real <= 0:
        prob_real = config.DEFAULT_PROB_REAL

    prob_implicita = _safe_float(p.get("prob_implicita", 0.0), 0.0)
    if prob_implicita <= 0:
        prob_implicita = config.DEFAULT_PROB_IMPLICITA

    partido = {
        # Identidad
        "id": p.get("id", ""),
        "local": _safe_text(p.get("local", "Local"), "Local"),
        "visitante": _safe_text(p.get("visitante", "Visitante"), "Visitante"),
        "liga": _safe_text(p.get("liga", "Liga desconocida"), "Liga desconocida"),
        "pais": _safe_text(p.get("pais", "Mundo"), "Mundo"),

        # Estado vivo
        "estado_partido": _normalizar_estado_partido(p.get("estado_partido", "EN_JUEGO")),
        "minuto": _safe_int(p.get("minuto", 0), 0),
        "marcador_local": _safe_int(p.get("marcador_local", 0), 0),
        "marcador_visitante": _safe_int(p.get("marcador_visitante", 0), 0),

        # Stats principales
        "xG": _safe_float(p.get("xG", 0.0), 0.0),
        "shots": _safe_int(p.get("shots", 0), 0),
        "shots_on_target": _safe_int(p.get("shots_on_target", 0), 0),
        "dangerous_attacks": _safe_int(p.get("dangerous_attacks", 0), 0),
        "momentum": _safe_text(p.get("momentum", "MEDIO"), "MEDIO"),

        # Submotores
        "goal_pressure": {
            "pressure_score": _safe_float(goal_pressure.get("pressure_score", 0.0), 0.0)
        },
        "goal_predictor": {
            "goal_next_5_prob": _safe_float(goal_predictor.get("goal_next_5_prob", 0.0), 0.0),
            "goal_next_10_prob": _safe_float(goal_predictor.get("goal_next_10_prob", 0.0), 0.0),
            "predictor_score": _safe_float(goal_predictor.get("predictor_score", 0.0), 0.0),
        },
        "chaos": {
            "chaos_score": _safe_float(chaos.get("chaos_score", 0.0), 0.0)
        },

        # Mercado / value base
        "prob_real": prob_real,
        "prob_implicita": prob_implicita,
        "cuota": cuota,

        # Frescura / delay
        "fetched_at": _safe_int(p.get("fetched_at", 0), 0),
        "source_updated_at": _safe_int(p.get("source_updated_at", 0), 0),
        "source_delay_seconds": _safe_int(p.get("source_delay_seconds", 0), 0),
        "time_fresh": bool(p.get("time_fresh", True)),

        # Extras
        "fixture": p.get("fixture", {}),
        "live": bool(p.get("live", True)),
    }

    return partido


# =========================================================
# GENERADOR OFICIAL DE SEÑALES
# =========================================================
def generar_senales(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Wrapper oficial:
    - valida partido básico
    - normaliza datos
    - llama al pipeline oficial
    - devuelve solo señales aprobadas por el pipeline
    """
    senales: List[Dict[str, Any]] = []

    if not procesar_partido:
        print("[SIGNALS] procesar_partido no disponible")
        return senales

    if not isinstance(partidos, list):
        print("[SIGNALS] partidos no es una lista")
        return senales

    for p in partidos:
        try:
            if not isinstance(p, dict):
                continue

            ok, motivo = partido_es_apostable(p)
            if not ok:
                print(f"[SIGNALS] partido omitido -> {motivo}")
                continue

            partido = normalizar_partido_para_pipeline(p)
            senal = procesar_partido(partido)

            if not senal:
                continue

            market = _safe_upper(senal.get("market"))
            if market == "SIN_SEÑAL":
                continue

            senales.append(senal)

        except Exception as e:
            print(f"[SIGNALS] ERROR procesando partido {p.get('id', '')} -> {e}")

    senales.sort(
        key=lambda s: (
            _safe_float(s.get("ranking_score", 0.0), 0.0),
            _safe_float(s.get("ai_decision_score", 0.0), 0.0),
            _safe_float(s.get("signal_score", 0.0), 0.0),
            _safe_float(s.get("confidence", 0.0), 0.0),
            _safe_float(s.get("value", 0.0), 0.0),
        ),
        reverse=True
    )

    return senales[:config.PUBLISH_MAX_SIGNALS]
