# Imagen base oficial de Python 3.11
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de tu proyecto
COPY . .

# Instala las dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expone el puerto (opcional, útil si luego usas servicios HTTP)
EXPOSE 8080

# Comando para iniciar tu bot
CMD ["python", "main.py"]
