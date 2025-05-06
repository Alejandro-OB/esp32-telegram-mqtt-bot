import os
import paho.mqtt.publish as publish
from telegram.ext import Updater, CommandHandler

# Token y configuración MQTT desde variables de entorno
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")

# Mapa de comandos de Telegram a tópicos MQTT
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

def publicar_mqtt(topic):
    publish.single(
        topic,
        payload="true",
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        auth={"username": MQTT_USERNAME, "password": MQTT_PASSWORD},
        tls={}  # Requiere TLS para HiveMQ Cloud
    )

def manejador(update, context):
    comando = update.message.text[1:]
    if comando in COMANDOS_MQTT:
        publicar_mqtt(COMANDOS_MQTT[comando])
        update.message.reply_text(f"✅ Comando `{comando}` enviado por MQTT", parse_mode="Markdown")
    else:
        update.message.reply_text("❌ Comando no reconocido.")

def main():
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN no está definido")
        return

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    for comando in COMANDOS_MQTT:
        dispatcher.add_handler(CommandHandler(comando, manejador))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()