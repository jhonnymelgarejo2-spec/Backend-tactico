import json
import os
from typing import List, Dict, Any

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

SIGNALS_FILE = os.path.join(DATA_DIR, "signals.json")

os.makedirs(DATA_DIR, exist_ok=True)


# =========================================================
# HELPERS
# =========================================================
def _load_file() -> List[Dict[str, Any]]:
    if not os.path.exists(SIGNALS_FILE):
        return []

    try:
        with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_file(data: List[Dict[str, Any]]):
    try:
        with open(SIGNALS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[STORAGE] ERROR guardando archivo -> {e}")


# =========================================================
# GUARDAR SEÑAL
# =========================================================
def guardar_senal(senal: Dict[str, Any]):
    data = _load_file()

    senal_copy = dict(senal)
    senal_copy["estado_resultado"] = "pendiente"

    data.append(senal_copy)

    _save_file(data)

    print(f"[STORAGE] señal guardada -> {senal.get('match_id')}")


# =========================================================
# OBTENER TODAS
# =========================================================
def obtener_senales() -> List[Dict[str, Any]]:
    return _load_file()


# =========================================================
# ACTUALIZAR RESULTADO
# =========================================================
def actualizar_resultado(match_id: str, resultado: str):
    """
    resultado: ganada | perdida | void
    """
    data = _load_file()

    updated = False

    for s in data:
        if str(s.get("match_id")) == str(match_id):
            s["estado_resultado"] = resultado

            # calcular profit simple
            stake = float(s.get("stake_amount", 0))
            odd = float(s.get("odd", 1.0))

            if resultado == "ganada":
                s["profit"] = round(stake * (odd - 1), 2)
            elif resultado == "perdida":
                s["profit"] = -stake
            else:
                s["profit"] = 0

            updated = True
            break

    if updated:
        _save_file(data)
        print(f"[STORAGE] resultado actualizado -> {match_id} = {resultado}")
    else:
        print(f"[STORAGE] match_id no encontrado -> {match_id}")
