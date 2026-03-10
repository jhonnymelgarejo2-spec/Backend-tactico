from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# importar router
from live_router import router as live_router

app = FastAPI(
    title="JHONNY ELITE API",
    version="1.0"
)

# permitir acceso desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# conectar router
app.include_router(live_router)

@app.get("/")
def home():
    return {
        "ok": True,
        "mensaje": "Backend táctico funcionando",
        "version": "V1_REAL"
    }

@app.get("/status")
def status():
    return {
        "status": "ok",
        "service": "backend-tactico",
        "version": "V1_REAL"
    }
