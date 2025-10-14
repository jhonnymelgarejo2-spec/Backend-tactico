# Imagen base de Python
FROM python:3.10

# Crear directorio de trabajo
WORKDIR /app

# Copiar todos los archivos del proyecto
COPY . /app

# Instalar dependencias desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8000 para FastAPI
EXPOSE 8000

# Comando para ejecutar el servidor con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
