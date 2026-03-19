from typing import Dict

try:
    from core.learning_engine import estadisticas_por_mercado
except:
    estadisticas_por_mercado = None


# =========================================================
# CONFIG BASE
# =========================================================
MIN_MATCHES = 5
LOW_WINRATE_THRESHOLD = 45
HIGH_WINRATE_THRESHOLD = 60


# =========================================================
# ANALISIS DE MERCADOS
# =========================================================
def analizar_mercados() -> Dict[str, Dict]:
    if not estadisticas_por_mercado:
        return {}

    stats = estadisticas_por_mercado()
    ajustes = {}

    for market, data in stats.items():
        total = data.get("total", 0)
        winrate = data.get("winrate", 0)

        if total < MIN_MATCHES:
            ajustes[market] = {
                "action": "NEUTRAL",
                "weight": 1.0
            }
            continue

        if winrate < LOW_WINRATE_THRESHOLD:
            ajustes[market] = {
                "action": "DOWNGRADE",
                "weight": 0.7
            }

        elif winrate > HIGH_WINRATE_THRESHOLD:
            ajustes[market] = {
                "action": "UPGRADE",
                "weight": 1.25
            }

        else:
            ajustes[market] = {
                "action": "NEUTRAL",
                "weight": 1.0
            }

    return ajustes


# =========================================================
# APLICAR AJUSTE A UNA SEÑAL
# =========================================================
def aplicar_ajuste_senal(signal: Dict) -> Dict:
    ajustes = analizar_mercados()

    market = str(signal.get("market", "")).upper()

    ajuste = ajustes.get(market, {"weight": 1.0})

    weight = ajuste.get("weight", 1.0)

    # aplicar sobre confidence y value
    signal["confidence"] = round(signal.get("confidence", 0) * weight, 2)
    signal["value"] = round(signal.get("value", 0) * weight, 2)

    # marcar ajuste
    signal["adaptive_adjustment"] = ajuste.get("action", "NEUTRAL")

    return signal
