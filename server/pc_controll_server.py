
from flask import Flask, request, jsonify

import subprocess
import datetime
import socket
import platform
import psutil
import os

app = Flask(__name__)
TOKEN_SEGURO = "miclave123"  # Cámbialo por algo más robusto

LOG_PATH = "/home/ortega/Documentos/apagar_log.txt"

def log_event(mensaje):
    with open(LOG_PATH, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {mensaje}\n")

@app.route('/apagar', methods=['GET'])
def apagar():
    token = request.args.get('token')
    if token == TOKEN_SEGURO:
        log_event("✅ Solicitud de apagado recibida desde navegador o ESP32")
        subprocess.run(["sudo", "/sbin/shutdown", "now"])
        return "🛑 Apagando el sistema...", 200
    else:
        log_event("❌ Intento fallido de apagado con token inválido")
        return "❌ Acceso denegado", 403

@app.route('/estado', methods=['GET'])
def estado():
    log_event("🔍 Solicitud de verificación del servidor")
    return "✅ Servidor Flask activo y funcionando", 200


@app.route('/info', methods=['GET'])
def info():
    temp_c = None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c = int(f.read()) / 1000.0
    except Exception:
        temp_c = None

    data = {
        "hostname": socket.gethostname(),
        "sistema": platform.system(),
        "version": platform.version(),
        "uptime": subprocess.getoutput("uptime -p"),
        "cpu_uso_percent": psutil.cpu_percent(interval=None),
        "ram_uso_percent": psutil.virtual_memory().percent,
        "temperatura_cpu": temp_c
    }
    return jsonify(data), 200

@app.route('/reiniciar', methods=['GET'])
def reiniciar():
    token = request.args.get('token')
    if token == TOKEN_SEGURO:
        log_event("🔄 Solicitud de reinicio recibida desde navegador o ESP32")
        subprocess.run(["sudo", "/sbin/reboot"])
        return "♻️ Reiniciando el sistema...", 200
    else:
        log_event("❌ Intento fallido de reinicio con token inválido")
        return "❌ Acceso denegado", 403
        
@app.route('/logs', methods=['GET'])
def ver_logs():
    try:
        with open(LOG_PATH, "r") as f:
            contenido = f.readlines()[-10:]  # Solo los últimos 10 eventos
        return ''.join(contenido), 200
    except Exception as e:
        return f"Error leyendo el log: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9123)

