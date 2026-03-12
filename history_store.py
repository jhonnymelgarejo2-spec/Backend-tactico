# history_store.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "signal_history.json"


def _asegurar_archivo():
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


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


def _crear_clave_unica(signal: Dict[str, Any]) -> str:
    match_id = str(signal.get("match_id", ""))
    market = str(signal.get("market", ""))
    minute = str(signal.get("minute", 0))
    selection = str(signal.get("selection", ""))
    return f"{match_id}__{market}__{minute}__{selection}"


def guardar_senales_en_historial(senales: List[Dict[str, Any]]) -> None:
    if not isinstance(senales, list):
        return

    historial = cargar_historial()
    existentes = {_crear_clave_unica(item): item for item in historial}

    for s in senales:
        clave = _crear_clave_unica(s)

        if clave in existentes:
            continue

        registro = {
            "history_id": clave,
            "created_at": datetime.utcnow().isoformat(),
            "match_id": s.get("match_id", ""),
            "home": s.get("home", ""),
            "away": s.get("away", ""),
            "league": s.get("league", ""),
            "country": s.get("country", ""),
            "minute": s.get("minute", 0),
            "score": s.get("score", "0-0"),
            "market": s.get("market", ""),
            "selection": s.get("selection", ""),
            "line": s.get("line"),
            "odd": s.get("odd", 0),
            "prob": s.get("prob", 0),
            "value": s.get("value", 0),
            "confidence": s.get("confidence", 0),
            "signal_score": s.get("signal_score", 0),
            "tactical_score": s.get("tactical_score", 0),
            "goal_inminente_score": s.get("goal_inminente_score", 0),
            "signal_rank": s.get("signal_rank", "NORMAL"),
            "risk_score": s.get("risk_score", 0),
            "risk_level": s.get("risk_level", "APTO"),
            "value_categoria": s.get("value_categoria", "SIN_VALUE"),
            "recomendacion_value": s.get("recomendacion_value", "NO_APOSTAR"),
            "reason": s.get("reason", ""),
            "razon_value": s.get("razon_value", ""),
            "motivos_riesgo": s.get("motivos_riesgo", []),
            "resultado_real": None,
            "estado_resultado": "pendiente",
            "resuelto": False,
            "resolved_at": None
        }

        historial.append(registro)

    guardar_historial(historial)


def actualizar_registro(history_id: str, nuevos_datos: Dict[str, Any]) -> bool:
    historial = cargar_historial()
    actualizado = False

    for item in historial:
        if item.get("history_id") == history_id:
            item.update(nuevos_datos)
            actualizado = True
            break

    if actualizado:
        guardar_historial(historial)

    return actualizado


def obtener_estadisticas_historial() -> Dict[str, Any]:
    historial = cargar_historial()

    resueltas = [h for h in historial if h.get("resuelto") is True]
    ganadas = [h for h in resueltas if h.get("estado_resultado") == "ganada"]
    perdidas = [h for h in resueltas if h.get("estado_resultado") == "perdida"]

    total_resueltas = len(resueltas)
    total_ganadas = len(ganadas)
    total_perdidas = len(perdidas)

    win_rate = round((total_ganadas / total_resueltas) * 100, 2) if total_resueltas else 0

    elite = sum(1 for h in historial if str(h.get("signal_rank", "")).upper() == "ELITE")
    top = sum(1 for h in historial if str(h.get("signal_rank", "")).upper() == "TOP")

    value_promedio = round(
        sum(float(h.get("value", 0) or 0) for h in historial) / len(historial),
        2
    ) if historial else 0

    riesgo_promedio = round(
        sum(float(h.get("risk_score", 0) or 0) for h in historial) / len(historial),
        2
    ) if historial else 0

    return {
        "total_senales": len(historial),
        "resueltas": total_resueltas,
        "ganadas": total_ganadas,
        "perdidas": total_perdidas,
        "win_rate": win_rate,
        "roi_percent": 0,
        "signals_elite": elite,
        "signals_top": top,
        "value_promedio": value_promedio,
        "riesgo_medio": riesgo_promedio,
        }
