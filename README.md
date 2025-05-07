# ESP32 Telegram MQTT Bot

Este repositorio contiene un sistema completo para controlar un computador remotamente usando un ESP32, MQTT y un bot de Telegram. Incluye un servidor HTTP con Flask para ejecutar acciones sobre el sistema operativo y configuración para despliegue automatizado en Fly.io o Koyeb.

## Tabla de contenidos

- [Estructura del proyecto](#estructura-del-proyecto)
- [Configuración de entorno](#configuración-de-entorno)
- [Instalación](#instalación)
- [Ejecución local](#ejecución-local)
- [Despliegue](#despliegue)
- [Servicios systemd](#servicios-systemd)
- [Comandos disponibles](#comandos-disponibles)
- [Endpoints HTTP del servidor](#endpoints-http-del-servidor)
- [Licencia y autor](#licencia-y-autor)

## Estructura del proyecto

```
esp32-telegram-mqtt-bot/
├── .env.example
├── requirements.txt
├── bot/
│   └── main.py
├── server/
│   └── pc_controll_server.py
├── esp32/
│   └── wol_mqtt/
│       └── wol_mqtt.ino
├── systemd/
│   ├── contoll_pc_server.service
│   └── wol.service
└── deploy/
    ├── fly/
    │   ├── Dockerfile.txt
    │   └── fly.toml
    └── koyeb/
        ├── Procfile
        └── runtime.txt
```

## Configuración de entorno

1. Copia el archivo `.env.example` y renómbralo como `.env`.
2. Completa las siguientes variables con tus credenciales:

```env
TELEGRAM_TOKEN=token_de_tu_bot
CHAT_ID_AUTORIZADO=id_chat_autorizado
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=8883
MQTT_USERNAME=usuario_mqtt
MQTT_PASSWORD=contraseña_mqtt
OTA_URL=http://ip_esp32:8266
```

> Estas variables deben estar disponibles como variables de entorno en producción (Fly.io/Koyeb) o ser cargadas localmente.

## Instalación

Asegúrate de usar Python 3.11+ y luego ejecuta:

```bash
pip install -r requirements.txt
```

## Ejecución local

### Iniciar el bot de Telegram:

```bash
python bot/main.py
```

### Iniciar el servidor Flask:

```bash
python server/pc_controll_server.py
```

## Despliegue

### Fly.io

1. Instala la CLI: https://fly.io/docs/hands-on/install-flyctl/
2. Crea la app:

```bash
fly launch
```

3. Agrega los secretos:

```bash
fly secrets set TELEGRAM_TOKEN=... CHAT_ID_AUTORIZADO=... MQTT_BROKER=... MQTT_PORT=... MQTT_USERNAME=... MQTT_PASSWORD=... OTA_URL=...
```

4. Despliega:

```bash
fly deploy
```

### Koyeb

1. Crea una nueva app desde https://app.koyeb.com
2. Usa el `Procfile` y `runtime.txt` ubicados en `deploy/koyeb/`
3. Define las variables de entorno en el panel de configuración.
4. Elige un builder de Python y habilita el despliegue automático.

## Servicios systemd

Para ejecutar el servidor Flask y el comando Wake-on-LAN al iniciar el sistema:

```bash
# Copiar servicios
sudo cp systemd/*.service /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reexec

# Habilitar servicios
sudo systemctl enable contoll_pc_server.service
sudo systemctl enable wol.service

# Iniciar manualmente (si deseas probarlos)
sudo systemctl start contoll_pc_server.service
sudo systemctl start wol.service
```

## Comandos disponibles

Estos comandos se envían desde Telegram al bot:

- `/encender_pc`
- `/apagar_pc`
- `/reiniciar_pc`
- `/verificar_pc`
- `/estado_esp32`
- `/reiniciar_esp32`
- `/actualizar_ota`
- `/ayuda`

## Endpoints HTTP del servidor

Estos endpoints son accesibles vía navegador, ESP32 u otros sistemas:

- `GET /estado`: verifica que el servidor esté activo.
- `GET /info`: retorna información del sistema (RAM, CPU, uptime).
- `GET /apagar?token=...`: apaga el equipo de forma remota.
- `GET /reiniciar?token=...`: reinicia el equipo.
- `GET /logs`: muestra los últimos eventos registrados en log.

## Licencia y autor

Este proyecto fue desarrollado por Alejandro-OB. Puedes modificarlo y adaptarlo según tus necesidades.
