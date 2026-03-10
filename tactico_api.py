from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>HOME OK NUEVO</h1>"

@app.get("/scan")
def scan():
    return {"ok": True, "ruta": "/scan funcionando"}

@app.get("/signals")
def signals():
    return {"ok": True, "ruta": "/signals funcionando"}

@app.get("/debug-routes")
def debug_routes():
    return {
        "ok": True,
        "rutas": ["/", "/scan", "/signals", "/debug-routes"]
    }

