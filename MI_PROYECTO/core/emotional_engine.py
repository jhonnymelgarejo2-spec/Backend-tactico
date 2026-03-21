from typing import Dict


# =========================================================
# HELPERS
# =========================================================
def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_upper(value):
    return str(value or "").upper()


# =========================================================
# ENGINE PRINCIPAL
# =========================================================
def evaluar_estado_emocional(partido: Dict) -> Dict:
    minuto = _safe_int(partido.get("minuto"))
    ml = _safe_int(partido.get("marcador_local"))
    mv = _safe_int(partido.get("marcador_visitante"))

    estado = "NEUTRO"
    intensidad = 0
    razones = []

    diff = abs(ml - mv)

    # =========================================
    # PARTIDO EMPATADO
    # =========================================
    if ml == mv:
        if minuto >= 75:
            estado = "TENSION_ALTA"
            intensidad = 8
            razones.append("Empate en tramo final")
        elif minuto >= 45:
            estado = "CONTROLADO"
            intensidad = 5
            razones.append("Empate en segundo tiempo")
        else:
            estado = "EQUILIBRADO"
            intensidad = 4
            razones.append("Empate temprano")

    # =========================================
    # UN EQUIPO VA PERDIENDO
    # =========================================
    else:
        if diff == 1:
            if minuto >= 75:
                estado = "REMONTADA_DESESPERADA"
                intensidad = 9
                razones.append("Equipo perdiendo por 1 en tramo final")
            elif minuto >= 60:
                estado = "PRESION_ALTA"
                intensidad = 7
                razones.append("Presión por remontar")
            else:
                estado = "PARTIDO_ABIERTO"
                intensidad = 6
                razones.append("Diferencia corta")

        elif diff >= 2:
            if minuto >= 70:
                estado = "PARTIDO_SENTENCIADO"
                intensidad = 3
                razones.append("Diferencia amplia final")
            else:
                estado = "CONTROL_DOMINANTE"
                intensidad = 4
                razones.append("Equipo dominando")

    return {
        "emocion_estado": estado,
        "emocion_intensidad": intensidad,
        "emocion_razon": " | ".join(razones),
    }


# =========================================================
# APLICAR A SEÑAL
# =========================================================
def aplicar_emocion_a_senal(senal: Dict, emocion: Dict) -> Dict:
    estado = emocion.get("emocion_estado")
    intensidad = _safe_int(emocion.get("emocion_intensidad"))

    confianza = _safe_float(senal.get("confidence", 0))
    value = _safe_float(senal.get("value", 0))

    # =========================================
    # AJUSTES SEGÚN EMOCIÓN
    # =========================================
    if estado == "REMONTADA_DESESPERADA":
        confianza += 5
        value += 1.5

    elif estado == "PRESION_ALTA":
        confianza += 3
        value += 1

    elif estado == "TENSION_ALTA":
        confianza += 2

    elif estado == "PARTIDO_SENTENCIADO":
        confianza -= 5
        value -= 2

    elif estado == "CONTROL_DOMINANTE":
        confianza -= 2

    # límites
    confianza = max(0, min(100, confianza))
    value = max(0, value)

    senal.update({
        "emocion_estado": estado,
        "emocion_intensidad": intensidad,
        "emocion_razon": emocion.get("emocion_razon"),
        "confidence": round(confianza, 2),
        "value": round(value, 2),
    })

    return senal
