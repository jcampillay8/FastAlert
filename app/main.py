# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # Importación necesaria
from app.api.endpoints import alarma
from app.core.config import settings
from app.models.database import init_db
import uvicorn
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema de Seguridad Vecinal con Integración IoT y WhatsApp",
    version="1.0.0"
)

# Crear el directorio de capturas si no existe al arrancar
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Montar la carpeta de archivos estáticos
# Esto permite acceder a las fotos vía: http://192.168.100.32:8000/static/capturas/archivo.jpg
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inicializar base de datos
@app.on_event("startup")
def startup_event():
    init_db()

# Rutas
app.include_router(alarma.router, prefix="/alarma", tags=["Alarma"])

@app.get("/")
def read_root():
    return {
        "message": f"{settings.PROJECT_NAME} API is running",
        "docs": "/docs",
        "status": "ready"
    }

if __name__ == "__main__":
    # Importante: host 0.0.0.0 para que el ESP32 te vea en la red local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)