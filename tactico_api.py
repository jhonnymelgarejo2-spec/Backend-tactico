from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {
        "ok": True,
        "mensaje": "Backend táctico funcionando",
        "version": "TEST_BASE_1"
    }


@app.get("/status")
def status():
    return {
        "status": "ok",
        "service": "backend-tactico",
        "version": "TEST_BASE_1"
    }


@app.get("/debug-routes")
def debug_routes():
    return {
        "ok": True,
        "routes": [
            "/",
            "/status",
            "/debug-routes"
        ],
        "version": "TEST_BASE_1"
    }
