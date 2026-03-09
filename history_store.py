import json
import os
from datetime import datetime
from collections import defaultdict

HISTORY_FILE = "history.json"


def cargar_historial():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar_historial(historial):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Error guardando historial: {e}")
        return False


def existe_senal_parecida(historial, senal):
    """
    Evita duplicados muy parecidos en el historial.
    """
    for h in historial[-200:]:
        if (
            h.get("match_id") == senal.get("match_id")
            and h.get("market") == senal.get("market")
            and h.get("selection") == senal.get("selection")
            and h.get("minute") == senal.get("minute")
        ):
            return True
    return False


def guardar_senales_en_historial(senales):
    historial = cargar_historial()

    for s in senales:
        registro = {
            "timestamp": datetime.utcnow().isoformat(),
            "match_id": s.get("match_id"),
            "home": s.get("home"),
            "away": s.get("away"),
            "league": s.get("league"),
            "event_type": s.get("event_type"),
            "minute": s.get("minute"),
            "score": s.get("score"),
            "market": s.get("market"),
            "selection": s.get("selection"),
            "odd": float(s.get("odd", 0) or 0),
            "prob": float(s.get("prob", 0) or 0),
            "value": float(s.get("value", 0) or 0),
            "confidence": float(s.get("confidence", 0) or 0),
            "reason": s.get("reason"),
            "resultado_real": None,
            "estado_resultado": "pendiente",
        }

        if not existe_senal_parecida(historial, registro):
            historial.append(registro)

    guardar_historial(historial)


def actualizar_resultado_senal(index, estado_resultado, resultado_real=None):
    historial = cargar_historial()

    if index < 0 or index >= len(historial):
        return {"status": "error", "detalle": "Índice fuera de rango"}

    estado = str(estado_resultado).strip().lower()
    if estado not in ["ganada", "perdida", "nula"]:
        return {
            "status": "error",
            "detalle": "Estado inválido. Usa: ganada, perdida o nula",
        }

    historial[index]["estado_resultado"] = estado
    historial[index]["resultado_real"] = resultado_real
    historial[index]["resuelto_en"] = datetime.utcnow().isoformat()

    guardar_historial(historial)

    return {
        "status": "ok",
        "mensaje": "Resultado actualizado",
        "senal": historial[index],
    }


def calcular_beneficio_unitario(senal):
    estado = senal.get("estado_resultado")
    odd = float(senal.get("odd", 0) or 0)

    if estado == "ganada":
        return round(odd - 1.0, 2)
    elif estado == "perdida":
        return -1.0
    elif estado == "nula":
        return 0.0
    return 0.0


def obtener_estadisticas_historial():
    historial = cargar_historial()

    total = len(historial)
    pendientes = sum(1 for x in historial if x.get("estado_resultado") == "pendiente")
    ganadas = sum(1 for x in historial if x.get("estado_resultado") == "ganada")
    perdidas = sum(1 for x in historial if x.get("estado_resultado") == "perdida")
    nulas = sum(1 for x in historial if x.get("estado_resultado") == "nula")

    resueltas = ganadas + perdidas + nulas

    if total == 0:
        return {
            "total_senales": 0,
            "pendientes": 0,
            "resueltas": 0,
            "ganadas": 0,
            "perdidas": 0,
            "nulas": 0,
            "win_rate": 0,
            "roi_percent": 0,
            "profit_units": 0,
            "confidence_promedio": 0,
            "value_promedio": 0,
            "ligas_top": [],
            "mercados_top": [],
        }

    confidence_promedio = round(
        sum(float(x.get("confidence", 0) or 0) for x in historial) / total,
        2,
    )

    value_promedio = round(
        sum(float(x.get("value", 0) or 0) for x in historial) / total,
        2,
    )

    profit_units = round(
        sum(
            calcular_beneficio_unitario(x)
            for x in historial
            if x.get("estado_resultado") != "pendiente"
        ),
        2,
    )

    if resueltas > 0:
        win_rate = round((ganadas / resueltas) * 100, 2)
        roi_percent = round((profit_units / resueltas) * 100, 2)
    else:
        win_rate = 0
        roi_percent = 0

    ligas = defaultdict(lambda: {"ganadas": 0, "perdidas": 0, "nulas": 0, "profit": 0.0})
    mercados = defaultdict(lambda: {"ganadas": 0, "perdidas": 0, "nulas": 0, "profit": 0.0})

    for s in historial:
        if s.get("estado_resultado") == "pendiente":
            continue

        liga = s.get("league") or "Sin liga"
        mercado = s.get("market") or "Sin mercado"
        profit = calcular_beneficio_unitario(s)
        estado = s.get("estado_resultado")

        if estado == "ganada":
            ligas[liga]["ganadas"] += 1
            mercados[mercado]["ganadas"] += 1
        elif estado == "perdida":
            ligas[liga]["perdidas"] += 1
            mercados[mercado]["perdidas"] += 1
        elif estado == "nula":
            ligas[liga]["nulas"] += 1
            mercados[mercado]["nulas"] += 1

        ligas[liga]["profit"] += profit
        mercados[mercado]["profit"] += profit

    ligas_top = sorted(
        [{"liga": k, **v} for k, v in ligas.items()],
        key=lambda x: x["profit"],
        reverse=True,
    )[:5]

    mercados_top = sorted(
        [{"mercado": k, **v} for k, v in mercados.items()],
        key=lambda x: x["profit"],
        reverse=True,
    )[:5]

    return {
        "total_senales": total,
        "pendientes": pendientes,
        "resueltas": resueltas,
        "ganadas": ganadas,
        "perdidas": perdidas,
        "nulas": nulas,
        "win_rate": win_rate,
        "roi_percent": roi_percent,
        "profit_units": profit_units,
        "confidence_promedio": confidence_promedio,
        "value_promedio": value_promedio,
        "ligas_top": ligas_top,
        "mercados_top": mercados_top,
                }
