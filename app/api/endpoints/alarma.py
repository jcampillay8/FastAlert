# app/api/endpoints/alarma.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.models.database import get_db, Vecino, LogAlerta
from app.schemas.alarma import AlarmStatus, AlarmActivate
from app.services.whatsapp_service import whatsapp_service
from app.core.config import settings
import os
import time
from datetime import datetime

router = APIRouter()

# Estado global en memoria para respuesta ultra-rápida al ESP32
ALARM_STATE = {
    "active": False, 
    "start_time": None, 
    "vecino_id": None,
    "last_notified_log_id": None
}

@router.post("/activar")
async def activar_alarma(data: AlarmActivate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Dispara el estado de alerta. Valida que el vecino exista y esté activo.
    """
    # 1. Validar vecino por teléfono
    vecino = db.query(Vecino).filter(Vecino.telefono == data.telefono, Vecino.activo == True).first()
    if not vecino:
        raise HTTPException(status_code=403, detail="Vecino no autorizado o no encontrado")

    # 2. Evitar disparos múltiples si ya está activa (Cooldown de seguridad)
    if ALARM_STATE["active"]:
        return {"status": "already_active", "message": "La alarma ya se encuentra en curso"}

    # 3. Actualizar estado global
    ALARM_STATE["active"] = True
    ALARM_STATE["start_time"] = time.time()
    ALARM_STATE["vecino_id"] = vecino.id

    # 4. Registrar evento en la base de datos
    nuevo_log = LogAlerta(vecino_id=vecino.id)
    db.add(nuevo_log)
    db.commit()
    db.refresh(nuevo_log)
    ALARM_STATE["last_notified_log_id"] = nuevo_log.id

    # 5. Notificar al grupo de WhatsApp (Asíncrono)
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🚨 *ALERTA VECINAL ACTIVADA* 🚨\n\n"
        f"👤 *Iniciada por:* {vecino.nombre}\n"
        f"⏰ *Hora:* {timestamp_str}\n"
        f"📸 El sistema ESP32-CAM está capturando imágenes en tiempo real..."
    )
    background_tasks.add_task(whatsapp_service.send_text, msg)

    return {"status": "success", "message": f"Alarma activada correctamente por {vecino.nombre}"}

@router.get("/status", response_model=AlarmStatus)
async def get_status():
    """
    Endpoint de alta frecuencia para el ESP32.
    Incluye un auto-apagado de seguridad tras 45 segundos.
    """
    if ALARM_STATE["active"] and ALARM_STATE["start_time"]:
        # Seguridad: Si el ESP32 se desconecta, la alarma no queda activa infinitamente
        if time.time() - ALARM_STATE["start_time"] > 45:
            ALARM_STATE["active"] = False
            
    return {"active": ALARM_STATE["active"]}

@router.post("/upload-foto")
async def upload_foto(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Recibe las imágenes del ESP32, las guarda y las reenvía a WhatsApp.
    """
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 1. Guardar archivo localmente
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"alerta_{timestamp}.jpg"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")

    # 2. Vincular al Log de la DB
    if ALARM_STATE["last_notified_log_id"]:
        log = db.query(LogAlerta).filter(LogAlerta.id == ALARM_STATE["last_notified_log_id"]).first()
        if log:
            log.fotos_count = (log.fotos_count or 0) + 1
            db.commit()

    # 3. Reenviar a WhatsApp (Asíncrono)
    caption = f"📸 Evidencia en vivo - {datetime.now().strftime('%H:%M:%S')}"
    background_tasks.add_task(whatsapp_service.send_image, file_path, caption)

    return {"status": "uploaded", "filename": filename}

@router.post("/webhook")
async def whatsapp_webhook(data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Recibe interacciones desde Evolution API. 
    Detecta comandos de texto para activar o desactivar la alarma.
    """
    # 1. Extraer contenido del mensaje (Soporta texto simple y texto extendido)
    message_obj = data.get("message", {})
    message_content = (
        message_obj.get("conversation") or 
        message_obj.get("extendedTextMessage", {}).get("text") or 
        ""
    ).strip().upper()

    # 2. Extraer número del remitente (Limpia JIDs de grupos o usuarios)
    # Evolution API envía el remitente en 'participant' si es grupo, o 'remoteJid' si es directo
    key = data.get("key", {})
    raw_sender = key.get("participant") or key.get("remoteJid") or ""
    sender_number = raw_sender.split("@")[0].split(":")[0]

    # 3. Lógica de activación por palabras clave
    keywords = ["ALERTA", "SOS", "🚨", "ACTIVAR"]
    if any(k in message_content for k in keywords):
        trigger_data = AlarmActivate(telefono=sender_number)
        return await activar_alarma(trigger_data, background_tasks, db)
    
    # 4. Comando de desactivación manual
    if "DETENER" in message_content or "OFF" in message_content:
        return await desactivar_alarma()
    
    return {"status": "ignored", "reason": "No keyword detected"}

@router.post("/desactivar")
async def desactivar_alarma():
    """
    Rearma el sistema. Invocado por el ESP32 tras la ráfaga o por el Webhook.
    """
    ALARM_STATE["active"] = False
    ALARM_STATE["vecino_id"] = None
    ALARM_STATE["last_notified_log_id"] = None
    return {"status": "inactive", "message": "Sistema rearmado"}