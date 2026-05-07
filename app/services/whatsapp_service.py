# app/services/whatsapp_service.py
import httpx
import logging
from app.core.config import settings
import os
import base64

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.base_url = f"{settings.EVOLUTION_API_URL}/message"
        self.headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        self.instance = settings.EVOLUTION_INSTANCE

    async def send_text(self, text: str):
        url = f"{self.base_url}/sendText/{self.instance}"
        payload = {
            "number": settings.WHATSAPP_GROUP_ID,
            "text": text,
            "delay": 1200,
            "linkPreview": False
        }
        
        # DEBUG PRINT PARA DOCKER LOGS
        print(f"🚀 [WHATSAPP] Intentando enviar texto a: {url}")
        print(f"📦 [WHATSAPP] Payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                print(f"📥 [WHATSAPP] Respuesta API ({response.status_code}): {response.text}")
                
                if response.status_code != 201 and response.status_code != 200:
                    logger.error(f"Error Evolution API ({response.status_code}): {response.text}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"❌ [WHATSAPP] ERROR CRÍTICO: {e}")
            logger.error(f"Error enviando mensaje de WhatsApp: {e}")
            return None

    async def send_image(self, file_path: str, caption: str = ""):
        url = f"{self.base_url}/sendMedia/{self.instance}"
        print(f"📸 [WHATSAPP] Intentando enviar imagen a: {url}")
        
        try:
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            payload = {
                "number": settings.WHATSAPP_GROUP_ID,
                "mediatype": "image",
                "mimetype": "image/jpeg",
                "caption": caption,
                "media": encoded_string
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                print(f"📥 [WHATSAPP] Respuesta API Media ({response.status_code}): {response.text}")
                
                if response.status_code != 201 and response.status_code != 200:
                    logger.error(f"Error Evolution API Media ({response.status_code}): {response.text}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"❌ [WHATSAPP] ERROR CRÍTICO MEDIA: {e}")
            logger.error(f"Error enviando imagen de WhatsApp: {e}")
            return None

whatsapp_service = WhatsAppService()
