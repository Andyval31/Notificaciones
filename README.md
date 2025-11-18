# Notification Service - Microservicio de Notificaciones

## Descripción

Microservicio independiente responsable del envío de notificaciones por correo electrónico cuando se crean nuevos usuarios en el sistema.

**NOTA IMPORTANTE:** En el **Ejercicio 1**, esta funcionalidad está integrada dentro del backend. Este repositorio se crea en preparación para el **Ejercicio 2**, donde se convertirá en un microservicio independiente.

**Ejercicio**: 2 en adelante (preparación)  
**Tecnologías**: Python 3.9+, Flask, SMTP (Gmail)

---

## ⚠️ Estado Actual (Ejercicio 1)

**En el Ejercicio 1:**
- ❌ Este servicio NO está implementado como microservicio independiente
- ✅ La funcionalidad de emails está en el **Backend** (archivo `services.py`)
- ✅ El backend envía emails directamente usando SMTP

**A partir del Ejercicio 2:**
- ✅ Se separará en este microservicio independiente
- ✅ El backend se comunicará con este servicio vía HTTP
- ✅ Arquitectura de microservicios

---

## Migración desde Backend (Ejercicio 1 → 2)

### Código Actual en Backend (services.py)

Actualmente, en el backend existe esta función:

```python
# Backend: users_api/services.py
import smtplib
from email.mime.text import MIMEText
from decouple import config

def enviar_notificacion_email(usuario):
    """Envía email cuando se crea un usuario"""
    try:
        smtp_host = config('SMTP_HOST')
        smtp_port = config('SMTP_PORT', cast=int)
        smtp_user = config('SMTP_USER')
        smtp_password = config('SMTP_PASSWORD')
        admin_email = config('ADMIN_EMAIL')
        
        mensaje = MIMEText(f"""
        Nuevo usuario registrado:
        
        Nombre: {usuario.nombre}
        Email: {usuario.email}
        Teléfono: {usuario.telefono}
        """)
        
        mensaje['Subject'] = 'Nuevo Usuario Registrado'
        mensaje['From'] = smtp_user
        mensaje['To'] = admin_email
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(mensaje)
        
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False
```

### Conversión a Microservicio (Ejercicio 2)

Este código se moverá a este repositorio como servicio HTTP independiente.

---

## Estructura del Proyecto (Preparación Ejercicio 2)

```
Notificaciones/
├── app.py                 # Aplicación Flask (API HTTP)
├── email_service.py       # Lógica de envío de emails
├── requirements.txt       # Dependencias
├── Dockerfile            # Para containerización
├── docker-compose.yml    # Orquestación local
├── .env.example          # Plantilla de variables
├── templates/            # Plantillas HTML de emails
│   └── usuario_creado.html
├── k8s/                  # Manifiestos Kubernetes (Ejercicio 3)
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
```

---

## Dependencias (Preparación)

### requirements.txt

```txt
Flask==3.0.0
python-decouple==3.8
requests==2.31.0
gunicorn==21.2.0
```

---

## Configuración para Ejercicio 2

### Paso 1: Configurar Gmail

1. Ir a https://myaccount.google.com/security
2. Activar "Verificación en 2 pasos"
3. Ir a https://myaccount.google.com/apppasswords
4. Generar contraseña de aplicación (16 caracteres)
5. Guardar esta contraseña para el .env

### Paso 2: Crear Red Docker

```bash
# Si no existe, crear la red compartida
docker network create app-network
```

### Paso 3: Clonar Repositorio

```bash
git clone <URL_DE_ESTE_REPOSITORIO>
cd Notificaciones
```

### Paso 4: Configurar Variables de Entorno

```bash
cp .env.example .env
nano .env
```

**Contenido del .env:**

```env
# Configuración SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=contraseña_aplicacion_16_caracteres

# Email del administrador (recibe notificaciones)
ADMIN_EMAIL=admin@ejemplo.com

# Puerto del servicio
PORT=8002

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## Implementación (Ejercicio 2)

### app.py (API Flask)

```python
from flask import Flask, request, jsonify
from email_service import enviar_email_usuario_creado
from decouple import config
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/notify', methods=['POST'])
def notify():
    """
    Endpoint para recibir eventos y enviar notificaciones
    
    Body esperado:
    {
        "tipo": "usuario_creado",
        "usuario": {
            "nombre": "string",
            "email": "string",
            "telefono": "string"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'tipo' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Datos inválidos'
            }), 400
        
        if data['tipo'] == 'usuario_creado':
            usuario = data.get('usuario', {})
            
            # Validar que el usuario tenga los datos necesarios
            if not all(k in usuario for k in ['nombre', 'email', 'telefono']):
                return jsonify({
                    'status': 'error',
                    'message': 'Faltan datos del usuario'
                }), 400
            
            # Enviar email
            if enviar_email_usuario_creado(usuario):
                logging.info(f"Email enviado para usuario: {usuario['email']}")
                return jsonify({
                    'status': 'success',
                    'message': 'Notificación enviada correctamente'
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Error al enviar email'
                }), 500
        
        return jsonify({
            'status': 'error',
            'message': 'Tipo de notificación no soportado'
        }), 400
        
    except Exception as e:
        logging.error(f"Error en /notify: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification-service',
        'version': '1.0.0'
    }), 200

if __name__ == '__main__':
    port = int(config('PORT', default=8002))
    app.run(host='0.0.0.0', port=port, debug=config('FLASK_DEBUG', default=False, cast=bool))
```

### email_service.py

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
import logging
from datetime import datetime

def enviar_email_usuario_creado(usuario_data):
    """
    Envía un email HTML notificando la creación de un nuevo usuario
    
    Args:
        usuario_data (dict): Diccionario con nombre, email, telefono
    
    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    try:
        # Configuración SMTP desde variables de entorno
        smtp_host = config('SMTP_HOST')
        smtp_port = config('SMTP_PORT', cast=int)
        smtp_user = config('SMTP_USER')
        smtp_password = config('SMTP_PASSWORD')
        admin_email = config('ADMIN_EMAIL')
        
        # Crear mensaje
        mensaje = MIMEMultipart('alternative')
        mensaje['Subject'] = '🔔 Nuevo Usuario Registrado'
        mensaje['From'] = smtp_user
        mensaje['To'] = admin_email
        
        # Cuerpo del email en HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .label {{ font-weight: bold; color: #333; width: 30%; }}
                .value {{ color: #555; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ Nuevo Usuario Registrado</h2>
                </div>
                <div class="content">
                    <p>Se ha registrado un nuevo usuario en el sistema:</p>
                    <table>
                        <tr>
                            <td class="label">Nombre:</td>
                            <td class="value">{usuario_data.get('nombre', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td class="label">Email:</td>
                            <td class="value">{usuario_data.get('email', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td class="label">Teléfono:</td>
                            <td class="value">{usuario_data.get('telefono', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td class="label">Fecha:</td>
                            <td class="value">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td>
                        </tr>
                    </table>
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático del Sistema de Registro de Usuarios.</p>
                    <p>Por favor, no responda a este correo.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Adjuntar HTML al mensaje
        parte_html = MIMEText(html, 'html')
        mensaje.attach(parte_html)
        
        # Enviar email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(mensaje)
        
        logging.info(f"Email enviado exitosamente para usuario: {usuario_data.get('email')}")
        return True
        
    except Exception as e:
        logging.error(f"Error al enviar email: {str(e)}")
        return False
```

---

## Ejecución Local (Ejercicio 2)

### Con Docker

```bash
# Levantar servicio
docker-compose up -d

# Ver logs
docker logs -f notification-service

# Verificar que está corriendo
docker ps | grep notification
```

### Sin Docker (desarrollo)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servicio
python app.py

# Se ejecutará en http://localhost:8002
```

---

## Probar el Servicio (Ejercicio 2)

### Test con cURL

```bash
curl -X POST http://localhost:5001/notify \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "usuario_creado",
    "usuario": {
      "nombre": "Juan Pérez",
      "email": "juan@ejemplo.com",
      "telefono": "+598 99 123 456"
    }
  }'
```

**Respuesta esperada (200 OK):**
```json
{
  "status": "success",
  "message": "Notificación enviada correctamente"
}
```

### Health Check

```bash
curl http://localhost:5005/api/healthz/
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "notification-service",
  "version": "1.0.0"
}
```

---

## Integración con Backend (Ejercicio 2)

### Modificar Backend para Usar este Servicio

En el backend, cambiar `services.py`:

```python
# Backend: users_api/services.py
import requests
from decouple import config

def enviar_notificacion(usuario):
    """
    Envía evento al microservicio de notificaciones
    """
    try:
        notification_service_url = config('NOTIFICATION_SERVICE_URL', default='http://notification-service:8002')
        
        payload = {
            'tipo': 'usuario_creado',
            'usuario': {
                'nombre': usuario.nombre,
                'email': usuario.email,
                'telefono': usuario.telefono
            }
        }
        
        response = requests.post(
            f'{notification_service_url}/notify',
            json=payload,
            timeout=5
        )
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error al comunicar con notification service: {e}")
        return False
```

### Agregar Variable de Entorno en Backend

En `Backend/.env`:
```env
NOTIFICATION_SERVICE_URL=http://notification-service:8002
```

---

## docker-compose.yml

```yml
version: "3.9"

services:
  notificaciones:
    build: .
    container_name: notificaciones-service
    ports:
      - "5001:5000"
    environment:
      MAIL_USERNAME: ${MAIL_USERNAME}
      MAIL_PASSWORD: ${MAIL_PASSWORD}
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    external: true  # ← Usa la red compartida externa
```

---

## Dockerfile

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

---

## Comandos Útiles

### Ver Logs

```bash
# Logs en tiempo real
docker logs -f notification-service

# Últimas 100 líneas
docker logs --tail=100 notification-service
```

### Reiniciar Servicio

```bash
docker restart notification-service

# O con docker-compose
docker-compose restart
```

### Detener Servicio

```bash
docker-compose down
```

### Acceder al Contenedor

```bash
docker exec -it notification-service /bin/bash
```

---

## Troubleshooting

### Error: Authentication failed (Gmail)

**Solución:**
1. Usar contraseña de APLICACIÓN (16 caracteres), NO la contraseña normal
2. Generar en: https://myaccount.google.com/apppasswords
3. Verificar que la verificación en 2 pasos está activa

### Error: Connection refused desde Backend

**Solución:**
```bash
# Verificar que ambos están en la misma red
docker network inspect app-network

# Verificar que el servicio está corriendo
docker ps | grep notification

# Probar conectividad
docker exec -it backend-usuarios ping notification-service
docker exec -it backend-usuarios curl http://notification-service:8002/health
```

### Emails no llegan

1. Verificar logs: `docker logs notification-service | grep -i error`
2. Revisar carpeta SPAM del email destino
3. Probar manualmente con cURL
4. Verificar credenciales SMTP en .env

---

## Próximos Pasos (Ejercicio 3)

En el Ejercicio 3:
- ✅ Desplegar en AWS EKS con Kubernetes
- ✅ Crear manifiestos en carpeta `k8s/`
- ✅ Subir imagen a Amazon ECR
- ✅ Configurar como ClusterIP (NO público)
- ✅ Secrets en Kubernetes para credenciales SMTP

---

## Repositorios Relacionados

- **Backend**: `<URL_REPOSITORIO_BACKEND>`
- **Frontend**: `<URL_REPOSITORIO_FRONTEND>`

---

## Contacto

- **Equipo**: [Nombres de integrantes]
- **Email**: [email_del_equipo@ejemplo.com]

---

**Proyecto**: Administración de Infraestructuras  
**Institución**: ITSJ  
**Fecha**: Noviembre 2025  
**Ejercicio**: 2-3 (Microservicios y AWS EKS)

---

## Nota Final

Este repositorio se crea en el **Ejercicio 1** como preparación, pero se implementa realmente a partir del **Ejercicio 2** cuando se separa la arquitectura en microservicios.

En Ejercicio 1, la funcionalidad de notificaciones está integrada en el backend.