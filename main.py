import os
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from telegram.ext import Updater, CommandHandler

# Configuración desde variables de entorno
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
OTA_URL = os.environ.get("OTA_URL", "http://192.168.18.252:8266")  # Dirección del servidor OTA

CHAT_ID_AUTORIZADO = os.environ.get("CHAT_ID_AUTORIZADO")

# Diccionario de comandos
COMANDOS_MQTT = {
    "encender_pc": "mqtt/pc/encender",
    "apagar_pc": "mqtt/pc/apagar",
    "reiniciar_pc": "mqtt/pc/reiniciar",
    "verificar_pc": "mqtt/pc/verificar",
    "estado_esp32": "mqtt/pc/estado_esp32",
    "reiniciar_esp32": "mqtt/pc/reiniciar_esp32",
    "actualizar_ota": "mqtt/pc/actualizar_ota",
    "ayuda": "mqtt/pc/ayuda"
}

# Diccionario de respuestas recibidas por MQTT
RESPUESTAS_TOPICOS = {
    "mqtt/respuesta/verificar": "Estado del PC",
    "mqtt/respuesta/estado_esp32": "Estado del ESP32",
    "mqtt/respuesta/reiniciar_esp32": "Confirmación de reinicio",
    "mqtt/respuesta/apagar": "Apagado del PC",
    "mqtt/respuesta/reiniciar": "Reinicio del PC",
    "mqtt/respuesta/esp32_reinicio_detectado": "Inicio del ESP32",
    "mqtt/respuesta/ota_estado": "Estado del servidor OTA",
    "mqtt/respuesta/reconexion_wifi": "Reconexión WiFi",
    "mqtt/respuesta/ayuda": "Menú de ayuda"
}

# Diccionario temporal para guardar última respuesta por tópico
ultima_respuesta = {}

# MQTT callback para recibir respuestas del ESP32

def on_message(client, userdata, msg):
    contenido = msg.payload.decode()
    topico = msg.topic
    print(f"📩 MQTT [{topico}] {contenido}")

    if topico in RESPUESTAS_TOPICOS:
        if CHAT_ID_AUTORIZADO:
            texto = f"*{RESPUESTAS_TOPICOS[topico]}:*\n\n```\n{contenido}\n```"
            bot.send_message(chat_id=CHAT_ID_AUTORIZADO, text=texto, parse_mode='Markdown')
        ultima_respuesta[topico] = contenido

# Inicializar cliente MQTT para escuchar respuestas
def iniciar_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.on_message = on_message
    for topico in RESPUESTAS_TOPICOS:
        client.subscribe(topico)
    client.loop_start()


# Publicar comando MQTT
def publicar_mqtt(topic):
    publish.single(
        topic,
        payload="true",
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        auth={"username": MQTT_USERNAME, "password": MQTT_PASSWORD},
        tls={}
    )

# Manejar comandos de Telegram
def manejador(update, context):
    comando = update.message.text[1:]
    global CHAT_ID_AUTORIZADO
    CHAT_ID_AUTORIZADO = str(update.message.chat_id)

    if comando == "actualizar_ota":
        update.message.reply_text(f"🔄 Puedes actualizar el ESP32 aquí: {OTA_URL}")
    elif comando in COMANDOS_MQTT:
        publicar_mqtt(COMANDOS_MQTT[comando])
        update.message.reply_text(f"✅ Comando `{comando}` enviado por MQTT", parse_mode="Markdown")
    else:
        update.message.reply_text("❌ Comando no reconocido.")

def main():
    global bot

    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN no está definido")
        return

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher

    for comando in COMANDOS_MQTT:
        dispatcher.add_handler(CommandHandler(comando, manejador))

    iniciar_mqtt()
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
