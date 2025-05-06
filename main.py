#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ESPping.h>
#include "secrets.h"
#include <WebServer.h>
#include <Update.h>

WiFiClientSecure secureClient;
PubSubClient mqttClient(secureClient);
WiFiUDP udp;

WebServer otaServer(8266); // Puerto 8266 para OTA HTTP

// MAC del PC que se va a encender por WOL
byte macPC[] = {0x34, 0x5A, 0x60, 0x4F, 0x9A, 0x02};
IPAddress broadcastIP(192, 168, 18, 255);
IPAddress ipPC(192, 168, 18, 151); // Cambia esto por la IP fija de tu PC

void conectarWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("⚠️ Error configurando IP estática");
  }
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi conectado");
}

void conectarMQTT() {
  secureClient.setInsecure(); // No validación de certificado (TLS simple)
  mqttClient.setServer(mqtt_server, mqtt_port);

  while (!mqttClient.connected()) {
    Serial.print("Conectando a MQTT...");
    if (mqttClient.connect("ESP32Client", mqtt_user, mqtt_password)) {
      Serial.println("✅ Conectado al broker MQTT");
      mqttClient.subscribe("mqtt/pc/encender");
      mqttClient.subscribe("mqtt/pc/verificar");
      mqttClient.subscribe("mqtt/pc/estado_esp32");
      mqttClient.subscribe("mqtt/pc/reiniciar_esp32");
      mqttClient.subscribe("mqtt/pc/apagar");
      mqttClient.subscribe("mqtt/pc/reiniciar_pc");
    } else {
      Serial.print("❌ Error: ");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String mensaje;
  for (int i = 0; i < length; i++) mensaje += (char)payload[i];
  Serial.printf("📩 [%s] %s\n", topic, mensaje.c_str());

  if (String(topic) == "mqtt/pc/encender" && mensaje == "true") {
    if (enviarWOL()) Serial.println("⚡ Paquete WOL enviado");
    else Serial.println("❌ Error al enviar WOL");
  }
  else if (String(topic) == "mqtt/pc/verificar" && mensaje == "true") {
    bool encendido = Ping.ping(ipPC);
    String estado = encendido ? "✅ PC ENCENDIDO" : "❌ PC APAGADO";
    Serial.println("📡 Verificación: " + estado);
    mqttClient.publish("mqtt/respuesta/verificar", estado.c_str());
  }
  else if (String(topic) == "mqtt/pc/estado_esp32" && mensaje == "true") {
    String info = "📊 Estado del ESP32:\n";
    info += "- IP: " + WiFi.localIP().toString() + "\n";
    info += "- WiFi: " + WiFi.SSID() + " (" + String(WiFi.RSSI()) + " dBm)\n";
    info += "- Uptime: " + String(millis() / 1000) + " seg";
    Serial.println(info);
    mqttClient.publish("mqtt/respuesta/estado_esp32", info.c_str());
  }
  else if (String(topic) == "mqtt/pc/reiniciar_esp32" && mensaje == "true") {
    Serial.println("♻️ Reiniciando ESP32...");
    mqttClient.publish("mqtt/respuesta/reiniciar_esp32", "♻️ Reiniciando ESP32...");
    delay(1000);
    ESP.restart();
  }
  else if (String(topic) == "mqtt/pc/apagar" && mensaje == "true") {
    WiFiClient client;
    if (client.connect(ipPC, PUERTO_FLASK)) {
      client.print("GET /apagar?token=miclave123 HTTP/1.1\r\nHost: " + ipPC.toString() + "\r\nConnection: close\r\n\r\n");
      mqttClient.publish("mqtt/respuesta/apagar", "🛑 Comando enviado al servidor Flask para apagar el PC.");
    } else {
      mqttClient.publish("mqtt/respuesta/apagar", "❌ No se pudo conectar al servidor Flask para apagar.");
    }
  }
  else if (String(topic) == "mqtt/pc/reiniciar_pc" && mensaje == "true") {
    WiFiClient client;
    if (client.connect(ipPC, PUERTO_FLASK)) {
      client.print("GET /reiniciar?token=miclave123 HTTP/1.1\r\nHost: " + ipPC.toString() + "\r\nConnection: close\r\n\r\n");
      mqttClient.publish("mqtt/respuesta/reiniciar_pc", "♻️ Comando enviado al servidor Flask para reiniciar el PC.");
    } else {
      mqttClient.publish("mqtt/respuesta/reiniciar_pc", "❌ No se pudo conectar al servidor Flask para reiniciar.");
    }
  }
}

bool enviarWOL() {
  byte packet[102];
  memset(packet, 0xFF, 6);
  for (int i = 1; i <= 16; i++) memcpy(&packet[i * 6], macPC, 6);
  udp.begin(WiFi.localIP(), 9);
  udp.beginPacket(broadcastIP, 9);
  udp.write(packet, sizeof(packet));
  return udp.endPacket() == 1;
}

void setup() {
  Serial.begin(115200);
  conectarWiFi();
  mqttClient.setCallback(callback);
  conectarMQTT();
  iniciarServidorOTA();
}

void loop() {
  if (!mqttClient.connected()) conectarMQTT();
  mqttClient.loop();
}

void iniciarServidorOTA() {
  otaServer.on("/", HTTP_GET, []() {
    otaServer.send(200, "text/html", R"rawliteral(
      <form method='POST' action='/update' enctype='multipart/form-data'>
        <input type='file' name='update'>
        <input type='submit' value='Actualizar'>
      </form>
    )rawliteral");
  });

  otaServer.on("/update", HTTP_POST, []() {
    otaServer.sendHeader("Connection", "close");
    otaServer.send(200, "text/plain", (Update.hasError()) ? "Fallo en actualización" : "Actualización correcta. Reiniciando...");
    delay(1000);
    ESP.restart();
  }, []() {
    HTTPUpload& upload = otaServer.upload();
    if (upload.status == UPLOAD_FILE_START && !Update.begin()) Update.printError(Serial);
    if (upload.status == UPLOAD_FILE_WRITE && Update.write(upload.buf, upload.currentSize) != upload.currentSize) Update.printError(Serial);
    if (upload.status == UPLOAD_FILE_END && !Update.end(true)) Update.printError(Serial);
  });

  otaServer.begin();
  Serial.println("✅ Servidor OTA iniciado en puerto 8266");
}
