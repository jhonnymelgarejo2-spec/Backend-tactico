from app.api.app import app


# Render usa esta variable automáticamente
# NO cambies el nombre "app"
# Esto es lo que hace que el deploy funcione

if __name__ == "__main__":
    # Solo para correr local
    app.run(host="0.0.0.0", port=10000, debug=True)
