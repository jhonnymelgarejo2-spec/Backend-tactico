# Imagen base de Python optimizada
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar solo los archivos necesarios
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Exponer el puerto para FastAPI
EXPOSE 8000

# Comando para ejecutar el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
