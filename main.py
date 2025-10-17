from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔓 Habilitar CORS para que el frontend pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 Modelo de entrada
class Datos(BaseModel):
    id: str
    momentum: str
    valor: float
    prob_real: float
    prob_implicita: float

# 🧭 Función táctica para detectar liga
def detectar_liga(id: str) -> str:
    if id.startswith("ATP"):
        return "ATP Tour"
    elif id.startswith("WTA"):
        return "WTA Tour"
    elif id.startswith("FIFA"):
        return "Fútbol Internacional"
    elif id.startswith("NBA"):
        return "NBA"
    else:
        return "Desconocida"

# 🚀 Endpoint principal
@app.post("/analizar/")
def analizar(datos: Datos):
    liga = detectar_liga(datos.id)
    # Aquí puedes agregar más lógica táctica si lo deseas
    return {
        "id": datos.id,
        "liga": liga,
        "equipoA": "Desconocido",
        "equipoB": "Desconocido",
        "confianza": 0.85,
        "señal": "Alta probabilidad de victoria"
    }
