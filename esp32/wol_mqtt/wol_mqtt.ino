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

unsigned long ultimaConexionExitosa = 0;
bool yaNotificadoReconexion = false;

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
  ultimaConexionExitosa = millis();
  yaNotificadoReconexion = false;

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
      mqttClient.subscribe("mqtt/pc/ayuda");
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
    encenderPC();
  }
  else if (String(topic) == "mqtt/pc/verificar" && mensaje == "true") {
    verificarPC();
  }
  else if (String(topic) == "mqtt/pc/estado_esp32" && mensaje == "true") {
    estadoESP32();
  }
  else if (String(topic) == "mqtt/pc/reiniciar_esp32" && mensaje == "true") {
    reiniciarESP32();
  }
  else if (String(topic) == "mqtt/pc/apagar" && mensaje == "true") {
    apagarPC();
  }
  else if (String(topic) == "mqtt/pc/reiniciar_pc" && mensaje == "true") {
    reiniciarPC();
  }
  else if (String(topic) == "mqtt/pc/ayuda" && mensaje == "true") {
    mostrarAyuda();
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
  mqttClient.publish("mqtt/respuesta/reconexion_wifi", ("✅ Conexión WiFi completada. IP: " + WiFi.localIP().toString()).c_str());

}

void loop() {
  
  void reconectarWiFi();

  if (!mqttClient.connected()) conectarMQTT();
  mqttClient.loop();

  otaServer.handleClient();
  
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
  mqttClient.publish("mqtt/respuesta/ota_estado", "✅ Servidor OTA activo en puerto 8266");

}

void verificarPC() {
  bool encendido = Ping.ping(ipPC);
  String estado = encendido ? "✅ PC ENCENDIDO" : "❌ PC APAGADO";
  Serial.println("📡 Verificación: " + estado);
  mqttClient.publish("mqtt/respuesta/verificar", estado.c_str());
  mqttClient.loop();
  delay(100);
}

void encenderPC() {
  if (enviarWOL()) {
    Serial.println("⚡ Paquete WOL enviado");
    delay(5000);
    bool verificado = false;
    for (int i = 0; i < 5; i++) {
      delay(3000);
      if (Ping.ping(ipPC)) {
        verificado = true;
        break;
      }
    }
    if (verificado) mqttClient.publish("mqtt/respuesta/verificar", "✅ PC ENCENDIDO por WOL");
    else mqttClient.publish("mqtt/respuesta/verificar", "⚠️ WOL enviado pero el PC no respondió tras varios intentos");
  } else {
    mqttClient.publish("mqtt/respuesta/verificar", "❌ Error al enviar paquete WOL");
  }
}

void apagarPC() {
  WiFiClient client;
  if (client.connect(ipPC, PUERTO_FLASK)) {
    client.print("GET /apagar?token=miclave123 HTTP/1.1\r\nHost: " + ipPC.toString() + "\r\nConnection: close\r\n\r\n");
    delay(5000);
    if (!Ping.ping(ipPC)) mqttClient.publish("mqtt/respuesta/apagar", "🔌 PC apagado correctamente.");
    else mqttClient.publish("mqtt/respuesta/apagar", "⚠️ El PC no se apagó correctamente.");
  } else {
    mqttClient.publish("mqtt/respuesta/apagar", "❌ No se pudo conectar al servidor Flask para apagar.");
  }
}

void reiniciarPC() {
  WiFiClient client;
  if (client.connect(ipPC, PUERTO_FLASK)) {
    client.print("GET /reiniciar?token=miclave123 HTTP/1.1\r\nHost: " + ipPC.toString() + "\r\nConnection: close\r\n\r\n");
    delay(10000);
    bool verificado = false;
    for (int i = 0; i < 5; i++) {
      delay(3000);
      if (Ping.ping(ipPC)) {
        verificado = true;
        break;
      }
    }
    if (verificado) mqttClient.publish("mqtt/respuesta/reiniciar_pc", "♻️ PC reiniciado correctamente.");
    else mqttClient.publish("mqtt/respuesta/reiniciar_pc", "⚠️ El PC no respondió después del reinicio.");
  } else {
    mqttClient.publish("mqtt/respuesta/reiniciar_pc", "❌ No se pudo conectar al servidor Flask para reiniciar.");
  }
}

void mostrarAyuda() {
  String ayuda = "🆘 *Menú de ayuda disponible:*\n\n";
  ayuda += "/encender_pc\n";
  ayuda += "/apagar_pc\n";
  ayuda += "/reiniciar_pc\n";
  ayuda += "/verificar_pc\n";
  ayuda += "/estado_esp32\n";
  ayuda += "/reiniciar_esp32\n";
  ayuda += "/actualizar_ota (si aplica)\n";

  mqttClient.publish("mqtt/respuesta/ayuda", ayuda.c_str());
  Serial.println("📤 Menú de ayuda enviado por MQTT.");
}

void estadoESP32() {
  unsigned long uptime = millis() / 1000;
  int horas = uptime / 3600;
  int minutos = (uptime % 3600) / 60;
  int segundos = uptime % 60;

  int rssi = WiFi.RSSI();
  String calidad;

  if (rssi >= -60) {
    calidad = "Excelente";
  } else if (rssi >= -70) {
    calidad = "Buena";
  } else if (rssi >= -80) {
    calidad = "Regular";
  } else {
    calidad = "Mala";
  }

  String info = "📊 Estado del ESP32:\n";
  info += "- IP: " + WiFi.localIP().toString() + "\n";
  info += "- WiFi: " + WiFi.SSID() + " (" + String(rssi) + " dBm, " + calidad + " señal)\n";
  info += "- Uptime: " + String(horas) + "h " + String(minutos) + "m " + String(segundos) + "s";

  Serial.println(info);
  mqttClient.publish("mqtt/respuesta/estado_esp32", info.c_str());
}


void reconectarWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi desconectado. Intentando reconectar...");
    
    WiFi.disconnect();  // Asegura un nuevo intento limpio
    WiFi.begin(ssid, password);
    
    unsigned long inicio = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - inicio < 10000) { // espera máximo 10s
      delay(500);
      Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n✅ WiFi reconectado exitosamente.");
      mqttClient.publish("mqtt/respuesta/reconexion_wifi", ("✅ Reconexión WiFi completada."));
      yaNotificadoReconexion = false;
      ultimaConexionExitosa = millis();
    } else {
      Serial.println("\n⚠️ No se pudo reconectar al WiFi.");
    }
  }
}

void reiniciarESP32() {
  Serial.println("♻️ Reiniciando ESP32...");
  mqttClient.publish("mqtt/respuesta/reiniciar_esp32", "♻️ Reiniciando ESP32...");
  delay(1000);  // Permitir que se envíe el mensaje antes de reiniciar
  ESP.restart();  // Reinicia el microcontrolador
}




