from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"ok": True, "ruta": "/"}

@app.get("/debug-routes")
def debug_routes():
    return {"ok": True, "ruta": "/debug-routes"}

@app.get("/scan")
def scan():
    return {"ok": True, "ruta": "/scan"}

@app.get("/signals")
def signals():
    return {"ok": True, "ruta": "/signals"}

@app.get("/status")
def status():
    return {"ok": True, "ruta": "/status"}

@app.get("/partidos-en-vivo")
def partidos():
    return {"ok": True, "ruta": "/partidos-en-vivo"}
