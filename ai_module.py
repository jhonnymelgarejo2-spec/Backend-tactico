from datetime import datetime

modelo_ia = {
    "precision": 82.5,
    "total": 120,
    "roi": 18.7,
    "errores": 5,
    "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

def obtener_modelo():
    return modelo_ia

def actualizar_modelo(nueva_precision, nuevo_roi, nuevos_errores):
    modelo_ia["precision"] = nueva_precision
    modelo_ia["roi"] = nuevo_roi
    modelo_ia["errores"] += nuevos_errores
    modelo_ia["total"] += 1
    modelo_ia["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")