# ESP32 Telegram MQTT Bot

Este proyecto integra un ESP32, un bot de Telegram y un servidor Python para controlar remotamente un computador a través de MQTT utilizando HiveMQ Cloud.

## Funcionalidades

- Control remoto del encendido, apagado y reinicio del computador mediante comandos de Telegram.
- Envío de comandos OTA al ESP32.
- Recepción de estados y eventos desde el ESP32 a través de MQTT.
- Compatible con despliegue en Fly.io y Koyeb.
- Seguridad en la comunicación MQTT mediante TLS.

## Tecnologías utilizadas

- ESP32 (firmware en `wol_mqtt.ino`)
- Python 3.11
- HiveMQ Cloud como broker MQTT
- Fly.io o Koyeb como plataformas de despliegue
- API de Telegram Bot
- MQTT sobre TLS

## Configuración de variables de entorno

Crear un archivo `.env` o configurar las siguientes variables directamente en la plataforma:

```env
TELEGRAM_TOKEN=your_bot_token
CHAT_ID_AUTORIZADO=your_chat_id
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
OTA_URL=http://your_esp32_ip:8266
```

## Instalación de dependencias

```bash
pip install -r requirements.txt
```

## Ejecución local

```bash
python main.py
```

## Despliegue

### Fly.io

1. Instalar Fly CLI: https://fly.io/docs/hands-on/install-flyctl/
2. Crear la aplicación: `fly launch`
3. Configurar secretos:

```bash
fly secrets set TELEGRAM_TOKEN=... CHAT_ID_AUTORIZADO=... MQTT_...
```

4. Ejecutar el despliegue:

```bash
fly deploy
```

### Koyeb

1. Crear una nueva aplicación en https://app.koyeb.com
2. Configurar el repositorio, `Procfile` y `runtime.txt`
3. Definir variables de entorno desde el panel
4. Activar despliegue automático

## Firmware del ESP32

El archivo `wol_mqtt.ino` contiene el firmware que debe cargarse en el ESP32. Este se encarga de escuchar comandos MQTT, ejecutar acciones como Wake-on-LAN y enviar mensajes informativos de vuelta.

## Comandos disponibles en Telegram

- `/encender_pc`
- `/apagar_pc`
- `/reiniciar_pc`
- `/verificar_pc`
- `/estado_esp32`
- `/reiniciar_esp32`
- `/actualizar_ota`
- `/ayuda`

## Autor

Desarrollado por Alejandro-OB.
