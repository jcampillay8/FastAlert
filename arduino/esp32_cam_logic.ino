/*
 * FastAlert ESP32-CAM Logic - Versión Ingeniería
 * Hardware: ESP32-CAM + ESP32-CAM-MB
 * PIN Buzzer: GPIO 13 (Conectar polo positivo aquí)
 */

#include "esp_camera.h"
#include <HTTPClient.h>
#include <WiFi.h>

// --- CONFIGURACIÓN ---
const char *ssid = "Sofia2022";
const char *password = "Seattle2022";
const char *serverUrl = "http://192.168.100.32:8000/alarma";

const int BUZZER_PIN = 13; // GPIO 13 es seguro en la placa MB

// --- PINES ESP32-CAM (AI-THINKER) ---
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

  // Configurar Pin de Alarma
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // Configuración Cámara
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

  // Ajuste según disponibilidad de PSRAM
  if (psramFound()) {
    config.frame_size =
        FRAMESIZE_VGA; // VGA es ideal para ráfagas rápidas y WhatsApp
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error camara 0x%x", err);
    return;
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] WiFi Conectado");
}

void sendPhoto() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Error captura");
    return;
  }

  HTTPClient http;
  String url = String(serverUrl) + "/upload-foto";
  http.begin(url);

  // Formatear como Multipart/form-data para FastAPI
  String boundary = "--------------------------ESP32CAM";
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

  String head = "--" + boundary +
                "\r\nContent-Disposition: form-data; name=\"file\"; "
                "filename=\"alarma.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
  String tail = "\r\n--" + boundary + "--\r\n";

  size_t totalLen = head.length() + fb->len + tail.length();
  uint8_t *fbBuf = fb->buf;
  size_t fbLen = fb->len;

  // Realizar el POST
  int httpResponseCode =
      http.sendRequest("POST", (uint8_t *)head.c_str(), head.length(), fbBuf,
                       fbLen, (uint8_t *)tail.c_str(), tail.length());

  if (httpResponseCode > 0) {
    Serial.printf("Envío exitoso: %d\n", httpResponseCode);
  } else {
    Serial.printf("Error envío: %s\n",
                  http.errorToString(httpResponseCode).c_str());
  }

  http.end();
  esp_camera_fb_return(fb);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverUrl) + "/status");
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();
      // Si el JSON contiene "active": true
      if (payload.indexOf("\"active\":true") != -1) {
        Serial.println("!!! ALERTA RECIBIDA DESDE WHATSAPP !!!");

        digitalWrite(BUZZER_PIN, HIGH); // Encender sirena

        for (int i = 0; i < 5; i++) {
          Serial.printf("Capturando foto %d/5...\n", i + 1);
          sendPhoto();
          delay(1000); // 1 segundo entre fotos para estabilidad
        }

        digitalWrite(BUZZER_PIN, LOW); // Apagar sirena

        // Avisar al servidor que ya procesamos la alerta para que la desactive
        http.begin(String(serverUrl) + "/desactivar");
        http.POST("");
        http.end();
      }
    }
    http.end();
  }
  delay(1500); // Polling cada 1.5 seg para no saturar el servidor
}