FROM python:3.11-slim

# Configuración básica
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Comando de inicio con Gunicorn (producción)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
