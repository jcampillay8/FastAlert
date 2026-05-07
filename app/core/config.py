# app/core/config.py
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Configuración de Pydantic ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # --- App Settings ---
    PROJECT_NAME: str = "FastAlert Security System"
    API_V1_STR: str = "/api/v1"
    
    # --- Database ---
    DATABASE_URL: str = "sqlite:///./fastalert.db"
    
    # --- Evolution API (WhatsApp) ---
    # Cambiamos localhost por el nombre del servicio en la red de Docker
    EVOLUTION_API_URL: str = "http://evolution_api:8080"
    # Usamos la API Key que vimos activa en tus logs (terminada en E0E)
    EVOLUTION_API_KEY: str = "B1442D24B582-44A6-9F2E-DE64D8C65E0E"
    # Cambiamos 'FastAlert' por 'FastAlert_Instance' para evitar el 404
    EVOLUTION_INSTANCE: str = "FastAlert_Instance"
    
    # ID del grupo de vecinos
    WHATSAPP_GROUP_ID: str
    
    # --- Media / Directorios ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: str = "static/capturas"

    @property
    def ABSOLUTE_UPLOAD_PATH(self) -> Path:
        return self.BASE_DIR / self.UPLOAD_DIR

settings = Settings()

# Verificación de carpetas
settings.ABSOLUTE_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)