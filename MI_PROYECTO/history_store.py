# history_store.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


# =========================================================
# RUTAS
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "signal_history.json"


# =========================================================
# HELPERS
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


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _asegurar_archivo() -> None:
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


def _crear_clave_unica(signal: Dict[str, Any]) -> str:
    match_id = _safe_text(signal.get("match_id", signal.get("id", "")))
    market = _safe_text(signal.get("market", signal.get("mercado", "")))
    minute = str(_safe_int(signal.get("minute", signal.get("minuto", 0)), 0))
    selection = _safe_text(signal.get("selection", signal.get("apuesta", "")))
    line = str(_safe_float(signal.get("line", signal.get("linea", 0.0)), 0.0))

    return f"{match_id}__{market}__{minute}__{selection}__{line}"


def _calcular_pnl_units(item: Dict[str, Any]) -> float:
    estado = _safe_upper(item.get("estado_resultado", ""))
    odd = _safe_float(item.get("odd", 0.0), 0.0)
    stake = _safe_float(item.get("stake_pct", 1.0), 1.0)

    # Para stats simples usamos stake en unidades relativas.
    # Si stake_pct es 4.0, se toma como 4.0 unidades relativas.
    if stake <= 0:
        stake = 1.0

    if estado == "GANADA":
        return round((odd - 1.0) * stake, 2) if odd > 1.0 else 0.0
    if estado == "PERDIDA":
        return round(-stake, 2)
    if estado in ("VOID", "ANULADA", "NULA"):
        return 0.0

    return 0.0


def _bucket_minuto(minute: int) -> str:
    if minute <= 14:
        return "01-14"
    if minute <= 24:
        return "15-24"
    if minute <= 45:
        return "25-45"
    if minute <= 59:
        return "46-59"
    if minute <= 75:
        return "60-75"
    if minute <= 85:
        return "76-85"
    return "86+"


def _init_segment_stats() -> Dict[str, Any]:
    return {
        "total": 0,
        "resueltas": 0,
        "ganadas": 0,
        "perdidas": 0,
        "win_rate": 0.0,
        "pnl_units": 0.0,
        "roi_percent": 0.0,
        "value_promedio": 0.0,
        "riesgo_medio": 0.0,
    }


def _finalizar_segmento(acumulado: Dict[str, Any]) -> Dict[str, Any]:
    total = acumulado.get("total", 0)
    resueltas = acumulado.get("resueltas", 0)
    ganadas = acumulado.get("ganadas", 0)
    perdidas = acumulado.get("perdidas", 0)
    pnl_units = round(_safe_float(acumulado.get("pnl_units", 0.0), 0.0), 2)

    if resueltas > 0:
        acumulado["win_rate"] = round((ganadas / resueltas) * 100, 2)
        # ROI simplificado: pnl total / total stake resuelto
        # stake total aproximado = suma stake_pct de resueltas; si falta, cuenta 1 por señal
        stake_total = _safe_float(acumulado.get("_stake_total", 0.0), 0.0)
        if stake_total > 0:
            acumulado["roi_percent"] = round((pnl_units / stake_total) * 100, 2)
        else:
            acumulado["roi_percent"] = 0.0
    else:
        acumulado["win_rate"] = 0.0
        acumulado["roi_percent"] = 0.0

    if total > 0:
        acumulado["value_promedio"] = round(
            _safe_float(acumulado.get("_value_sum", 0.0), 0.0) / total,
            2
        )
        acumulado["riesgo_medio"] = round(
            _safe_float(acumulado.get("_risk_sum", 0.0), 0.0) / total,
            2
        )
    else:
        acumulado["value_promedio"] = 0.0
        acumulado["riesgo_medio"] = 0.0

    # limpiar internos
    acumulado.pop("_value_sum", None)
    acumulado.pop("_risk_sum", None)
    acumulado.pop("_stake_total", None)

    return acumulado


# =========================================================
# IO BASICO
# =========================================================
def cargar_historial() -> List[Dict[str, Any]]:
    _asegurar_archivo()
    try:
        contenido = HISTORY_FILE.read_text(encoding="utf-8").strip()
        if not contenido:
            return []
        data = json.loads(contenido)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def guardar_historial(data: List[Dict[str, Any]]) -> None:
    _asegurar_archivo()
    HISTORY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# =========================================================
# GUARDADO DE SENALES
# =========================================================
def guardar_senales_en_historial(senales: List[Dict[str, Any]]) -> None:
    if not isinstance(senales, list):
        return

    historial = cargar_historial()
    existentes = {_crear_clave_unica(item): item for item in historial}

    for s in senales:
        if not isinstance(s, dict):
            continue

        clave = _crear_clave_unica(s)
        if clave in existentes:
            continue

        minute = _safe_int(s.get("minute", s.get("minuto", 0)), 0)

        registro = {
            "history_id": clave,
            "created_at": _now_iso(),

            # Identidad
            "match_id": _safe_text(s.get("match_id", s.get("id", ""))),
            "home": _safe_text(s.get("home", s.get("local", ""))),
            "away": _safe_text(s.get("away", s.get("visitante", ""))),
            "league": _safe_text(s.get("league", s.get("liga", ""))),
            "country": _safe_text(s.get("country", s.get("pais", ""))),

            # Momento de entrada
            "minute": minute,
            "minute_bucket": _bucket_minuto(minute),
            "score": _safe_text(s.get("score", "0-0")),

            # Mercado
            "market": _safe_text(s.get("market", s.get("mercado", ""))),
            "selection": _safe_text(s.get("selection", s.get("apuesta", ""))),
            "line": _safe_float(s.get("line", s.get("linea", 0.0)), 0.0),
            "odd": _safe_float(s.get("odd", s.get("cuota", 0.0)), 0.0),

            # Métricas principales
            "prob": _safe_float(s.get("prob", s.get("prob_real", 0.0)), 0.0),
            "prob_real": _safe_float(s.get("prob_real", s.get("prob", 0.0)), 0.0),
            "prob_implicita": _safe_float(s.get("prob_implicita", 0.0), 0.0),
            "value": _safe_float(s.get("value", s.get("valor", 0.0)), 0.0),
            "confidence": _safe_float(s.get("confidence", s.get("confianza", 0.0)), 0.0),

            # Scores
            "signal_score": _safe_float(s.get("signal_score", 0.0), 0.0),
            "tactical_score": _safe_float(s.get("tactical_score", 0.0), 0.0),
            "goal_inminente_score": _safe_float(s.get("goal_inminente_score", 0.0), 0.0),
            "ai_decision_score": _safe_float(s.get("ai_decision_score", 0.0), 0.0),
            "ranking_score": _safe_float(s.get("ranking_score", 0.0), 0.0),
            "signal_rank": _safe_text(s.get("signal_rank", "NORMAL"), "NORMAL"),

            # Riesgo / value
            "risk_score": _safe_float(s.get("risk_score", 0.0), 0.0),
            "risk_level": _safe_text(s.get("risk_level", s.get("riesgo_operativo", "MEDIO")), "MEDIO"),
            "value_score": _safe_float(s.get("value_score", 0.0), 0.0),
            "value_categoria": _safe_text(s.get("value_categoria", "SIN_VALUE"), "SIN_VALUE"),
            "recomendacion_value": _safe_text(s.get("recomendacion_value", "NO_APOSTAR"), "NO_APOSTAR"),

            # Contexto ampliado
            "xG": _safe_float(s.get("xG", 0.0), 0.0),
            "shots": _safe_int(s.get("shots", 0), 0),
            "shots_on_target": _safe_int(s.get("shots_on_target", 0), 0),
            "dangerous_attacks": _safe_int(s.get("dangerous_attacks", 0), 0),
            "momentum": _safe_text(s.get("momentum", "MEDIO"), "MEDIO"),

            "goal_prob_5": _safe_float(s.get("goal_prob_5", 0.0), 0.0),
            "goal_prob_10": _safe_float(s.get("goal_prob_10", 0.0), 0.0),
            "goal_prob_15": _safe_float(s.get("goal_prob_15", 0.0), 0.0),

            "estado_partido": s.get("estado_partido", {}),
            "context_state": _safe_text(s.get("context_state", ""), ""),
            "context_score": _safe_float(s.get("context_score", 0.0), 0.0),
            "tempo_state": _safe_text(s.get("tempo_state", ""), ""),
            "tempo_score": _safe_float(s.get("tempo_score", 0.0), 0.0),
            "emocion_estado": _safe_text(s.get("emocion_estado", ""), ""),
            "emocion_intensidad": _safe_float(s.get("emocion_intensidad", 0.0), 0.0),

            "chaos_level": _safe_text(s.get("chaos_level", ""), ""),
            "chaos_detector_score": _safe_float(s.get("chaos_detector_score", 0.0), 0.0),
            "chaos_reason": _safe_text(s.get("chaos_reason", ""), ""),

            # Validación de mercado
            "odds_data_available": bool(s.get("odds_data_available", False)),
            "odds_validation_ok": bool(s.get("odds_validation_ok", False)),
            "market_validation_reason": _safe_text(s.get("market_validation_reason", ""), ""),
            "odds_selected_bookmaker": _safe_text(s.get("odds_selected_bookmaker", ""), ""),
            "odds_selected_line": _safe_float(s.get("odds_selected_line", 0.0), 0.0),
            "odds_selected_price": _safe_float(s.get("odds_selected_price", 0.0), 0.0),
            "market_edge_with_odds": _safe_float(s.get("market_edge_with_odds", 0.0), 0.0),

            # Operativa
            "stake_pct": _safe_float(s.get("stake_pct", 1.0), 1.0),
            "stake_amount": _safe_float(s.get("stake_amount", 0.0), 0.0),
            "stake_label": _safe_text(s.get("stake_label", "NORMAL"), "NORMAL"),
            "recomendacion_final": _safe_text(s.get("recomendacion_final", "OBSERVAR"), "OBSERVAR"),
            "publish_ready": bool(s.get("publish_ready", False)),
            "publish_rank": _safe_int(s.get("publish_rank", 0), 0),
            "publish_blocked_reasons": s.get("publish_blocked_reasons", []),

            # Razones explicativas
            "reason": _safe_text(s.get("reason", ""), ""),
            "razon_value": _safe_text(s.get("razon_value", ""), ""),
            "razon_tactica": _safe_text(s.get("razon_tactica", ""), ""),
            "razon_contexto": _safe_text(s.get("razon_contexto", ""), ""),
            "razon_ia": _safe_text(s.get("razon_ia", ""), ""),
            "motivos_riesgo": s.get("motivos_riesgo", []),

            # Resolución
            "resultado_real": None,
            "estado_resultado": "pendiente",
            "resuelto": False,
            "resolved_at": None,
            "motivo_fallo": "",
            "categoria_fallo": "",
            "comentario_revision": "",
            "pnl_units": 0.0,
        }

        historial.append(registro)

    guardar_historial(historial)


# =========================================================
# ACTUALIZACION
# =========================================================
def actualizar_registro(history_id: str, nuevos_datos: Dict[str, Any]) -> bool:
    historial = cargar_historial()
    actualizado = False

    for item in historial:
        if item.get("history_id") == history_id:
            item.update(nuevos_datos)

            if bool(item.get("resuelto", False)) and not item.get("resolved_at"):
                item["resolved_at"] = _now_iso()

            item["pnl_units"] = _calcular_pnl_units(item)
            actualizado = True
            break

    if actualizado:
        guardar_historial(historial)

    return actualizado


# =========================================================
# CONSULTAS
# =========================================================
def obtener_historial(limit: int = 100) -> List[Dict[str, Any]]:
    historial = cargar_historial()
    if limit <= 0:
        return historial
    return historial[-limit:]


def obtener_registro_por_id(history_id: str) -> Dict[str, Any] | None:
    historial = cargar_historial()
    for item in historial:
        if item.get("history_id") == history_id:
            return item
    return None


# =========================================================
# ESTADISTICAS
# =========================================================
def obtener_estadisticas_historial() -> Dict[str, Any]:
    historial = cargar_historial()

    resueltas = [h for h in historial if h.get("resuelto") is True]
    ganadas = [h for h in resueltas if _safe_upper(h.get("estado_resultado")) == "GANADA"]
    perdidas = [h for h in resueltas if _safe_upper(h.get("estado_resultado")) == "PERDIDA"]

    total = len(historial)
    total_resueltas = len(resueltas)
    total_ganadas = len(ganadas)
    total_perdidas = len(perdidas)

    win_rate = round((total_ganadas / total_resueltas) * 100, 2) if total_resueltas else 0.0

    elite = sum(1 for h in historial if _safe_upper(h.get("signal_rank")) == "ELITE")
    top = sum(1 for h in historial if _safe_upper(h.get("signal_rank")) == "TOP")

    value_promedio = round(
        sum(_safe_float(h.get("value", 0.0), 0.0) for h in historial) / total,
        2
    ) if total else 0.0

    riesgo_promedio = round(
        sum(_safe_float(h.get("risk_score", 0.0), 0.0) for h in historial) / total,
        2
    ) if total else 0.0

    pnl_total = round(sum(_safe_float(h.get("pnl_units", 0.0), 0.0) for h in resueltas), 2)
    stake_total = round(
        sum(_safe_float(h.get("stake_pct", 1.0), 1.0) if _safe_float(h.get("stake_pct", 1.0), 1.0) > 0 else 1.0 for h in resueltas),
        2
    )
    roi_percent = round((pnl_total / stake_total) * 100, 2) if stake_total > 0 else 0.0

    # -----------------------------------------------------
    # Segmentación por mercado
    # -----------------------------------------------------
    por_mercado: Dict[str, Dict[str, Any]] = {}
    por_liga: Dict[str, Dict[str, Any]] = {}
    por_rango_minuto: Dict[str, Dict[str, Any]] = {}
    por_rank: Dict[str, Dict[str, Any]] = {}

    def acumular(seg: Dict[str, Dict[str, Any]], key: str, item: Dict[str, Any]) -> None:
        if key not in seg:
            seg[key] = _init_segment_stats()

        seg[key]["total"] += 1
        seg[key]["_value_sum"] = _safe_float(seg[key].get("_value_sum", 0.0), 0.0) + _safe_float(item.get("value", 0.0), 0.0)
        seg[key]["_risk_sum"] = _safe_float(seg[key].get("_risk_sum", 0.0), 0.0) + _safe_float(item.get("risk_score", 0.0), 0.0)

        if bool(item.get("resuelto", False)):
            seg[key]["resueltas"] += 1

            stake_item = _safe_float(item.get("stake_pct", 1.0), 1.0)
            if stake_item <= 0:
                stake_item = 1.0
            seg[key]["_stake_total"] = _safe_float(seg[key].get("_stake_total", 0.0), 0.0) + stake_item

            pnl_item = _safe_float(item.get("pnl_units", 0.0), 0.0)
            seg[key]["pnl_units"] = _safe_float(seg[key].get("pnl_units", 0.0), 0.0) + pnl_item

            estado = _safe_upper(item.get("estado_resultado", ""))
            if estado == "GANADA":
                seg[key]["ganadas"] += 1
            elif estado == "PERDIDA":
                seg[key]["perdidas"] += 1

    for item in historial:
        mercado = _safe_text(item.get("market", "DESCONOCIDO"), "DESCONOCIDO")
        liga = _safe_text(item.get("league", "SIN_LIGA"), "SIN_LIGA")
        bucket = _safe_text(item.get("minute_bucket", _bucket_minuto(_safe_int(item.get("minute", 0), 0))), "SIN_BUCKET")
        rank = _safe_text(item.get("signal_rank", "NORMAL"), "NORMAL")

        acumular(por_mercado, mercado, item)
        acumular(por_liga, liga, item)
        acumular(por_rango_minuto, bucket, item)
        acumular(por_rank, rank, item)

    por_mercado = {k: _finalizar_segmento(v) for k, v in por_mercado.items()}
    por_liga = {k: _finalizar_segmento(v) for k, v in por_liga.items()}
    por_rango_minuto = {k: _finalizar_segmento(v) for k, v in por_rango_minuto.items()}
    por_rank = {k: _finalizar_segmento(v) for k, v in por_rank.items()}

    return {
        "total_senales": total,
        "resueltas": total_resueltas,
        "ganadas": total_ganadas,
        "perdidas": total_perdidas,
        "win_rate": win_rate,
        "pnl_units": pnl_total,
        "roi_percent": roi_percent,
        "signals_elite": elite,
        "signals_top": top,
        "value_promedio": value_promedio,
        "riesgo_medio": riesgo_promedio,
        "por_mercado": por_mercado,
        "por_liga": por_liga,
        "por_rango_minuto": por_rango_minuto,
        "por_rank": por_rank,
        }
