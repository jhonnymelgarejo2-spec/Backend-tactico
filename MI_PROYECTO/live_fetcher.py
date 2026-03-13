import requests

API_KEY = "TU_API_KEY_AQUÍ"  # ← reemplaza esto cuando la tengas
BASE_URL = "https://apiclient.besoccerapps.com/scripts/api/api.php"

def obtener_partidos_en_vivo():
    params = {
        "key": API_KEY,
        "tz": "Europe/Madrid",
        "format": "json",
        "req": "match_live"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        partidos = data.get("matches", [])
        return partidos
    except Exception as e:
        print("Error al conectar con BeSoccer:", e)
        return []
