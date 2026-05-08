/*
 * FastAlert ESP32-CAM Logic - Versión Ingeniería Mejorada
 * Hardware: ESP32-CAM + ESP32-CAM-MB
 * Objetivo: Priorizar WiFi para evitar bloqueos y asegurar ráfaga de fotos.
 */

#include "esp_camera.h"
#include <HTTPClient.h>
#include <WiFi.h>

// --- CONFIGURACIÓN DE RED Y SERVIDOR ---
const char *ssid = "Sofia2022";
const char *password = "Seattle2022";
// IMPORTANTE: Se agrega /api/v1 para coincidir con el router de FastAPI
const char *serverUrl = "http://192.168.100.32:8000/alarma";

const int BUZZER_PIN = 13;

// --- PINES ESP32-CAM (MODELO AI-THINKER) ---
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

void setup() {
  Serial.begin(115200);

  // 1. Configurar periféricos básicos
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // 2. PRIORIDAD: Conectar WiFi primero
  // Esto evita que un error de hardware en la cámara deje al dispositivo mudo.
  Serial.printf("\nConectando a %s ", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] WiFi Conectado");
  Serial.print("IP Local: ");
  Serial.println(WiFi.localIP());

  // 3. Configuración de la Cámara
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Ajuste inteligente de resolución (Basado en PSRAM)
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA; // 640x480 - Óptimo para WhatsApp
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_CIF; // Resolución menor si no hay PSRAM
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // 4. Inicializar Cámara
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf(
        "!!! Error Cámara 0x%x. El sistema seguirá operando sin video.\n", err);
    // No hacemos return para que el loop() siga consultando el status aunque no
    // haya cámara.
  } else {
    Serial.println("[OK] Hardware de Cámara listo");
  }
}

void sendPhoto() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Fallo al capturar cuadro de video");
    return;
  }

  HTTPClient http;
  String url = String(serverUrl) + "/upload-foto";
  http.begin(url);

  // Preparar Multipart Form Data para FastAPI
  String boundary = "--------------------------ESP32CAM";
  String head = "--" + boundary +
                "\r\nContent-Disposition: form-data; name=\"file\"; "
                "filename=\"alarma.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
  String tail = "\r\n--" + boundary + "--\r\n";

  size_t headLen = head.length();
  size_t tailLen = tail.length();
  size_t totalLen = headLen + fb->len + tailLen;

  // Construir el body completo en un buffer porque el core 3.3.8 no tiene
  // sendRequest con 7 parámetros
  uint8_t *body = (uint8_t *)malloc(totalLen);
  if (!body) {
    Serial.println("Error de memoria al asignar buffer");
    esp_camera_fb_return(fb);
    return;
  }

  memcpy(body, (uint8_t *)head.c_str(), headLen);
  memcpy(body + headLen, fb->buf, fb->len);
  memcpy(body + headLen + fb->len, (uint8_t *)tail.c_str(), tailLen);

  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

  int httpResponseCode = http.sendRequest("POST", body, totalLen);

  if (httpResponseCode > 0) {
    Serial.printf("Foto enviada correctamente: %d\n", httpResponseCode);
  } else {
    Serial.printf("Fallo al enviar foto: %s\n",
                  http.errorToString(httpResponseCode).c_str());
  }

  free(body);
  http.end();
  esp_camera_fb_return(fb);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String statusUrl = String(serverUrl) + "/status";

    http.begin(statusUrl);
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();

      // Verificamos si la alarma está activa en el servidor
      if (payload.indexOf("\"active\":true") != -1) {
        Serial.println("🚨 ALERTA DETECTADA. Iniciando ráfaga de captura...");

        digitalWrite(BUZZER_PIN, HIGH); // Activar sirena local

        for (int i = 0; i < 5; i++) {
          Serial.printf("Capturando evidencia %d/5...\n", i + 1);
          sendPhoto();
          delay(800); // Pequeña pausa para estabilidad del sensor
        }

        digitalWrite(BUZZER_PIN, LOW); // Apagar sirena local

        // Notificar al servidor que la cámara ya cumplió su ciclo
        http.begin(String(serverUrl) + "/desactivar");
        http.POST("");
        http.end();
        Serial.println("Ciclo completado. Sistema rearmado.");
      }
    } else {
      Serial.printf("Error consultando servidor (Status: %d)\n", httpCode);
    }
    http.end();
  }

  delay(1500); // Polling cada 1.5 segundos
}