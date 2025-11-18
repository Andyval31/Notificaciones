# Notification Service - Microservicio de Notificaciones

## Descripción

Microservicio independiente para envío de notificaciones por email cuando se crean nuevos usuarios. Recibe peticiones HTTP del backend y gestiona el envío de emails.

## Tecnologías

- Python 3.9+
- Flask 3.0 / FastAPI
- SMTP (Gmail)
- Docker & Docker Compose

## Estructura del Proyecto

```
Notificaciones/
├── app.py
├── email_service.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── templates/
│   └── usuario_creado.html
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
```

## Dependencias

```txt
Flask==3.0.0
python-decouple==3.8
requests==2.31.0
gunicorn==21.2.0
```

## Instalación Local

### 1. Configurar Gmail

1. Ir a https://myaccount.google.com/security
2. Habilitar "Verificación en 2 pasos"
3. Ir a "Contraseñas de aplicaciones"
4. Generar contraseña (16 caracteres)

### 2. Crear red Docker

```bash
docker network create app-network
```

### 3. Clonar y configurar

```bash
git clone <URL_REPO> Notificaciones
cd Notificaciones
cp .env.example .env
nano .env
```

### 4. Configurar .env

```env
# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=laboratorioinfraestructura@gmail.com
SMTP_PASSWORD=contraseña_app_16_chars

# Admin
ADMIN_EMAIL=laboratorioinfraestructura@gmail.com

# Flask
PORT=8002
FLASK_ENV=development
```

### 5. Levantar servicio

```bash
docker-compose up -d
docker ps | grep notification
docker logs -f notification-service
```

### 6. Probar

```bash
curl -X POST http://localhost:5001/notify \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "usuario_creado",
    "usuario": {
      "nombre": "Juan Pérez",
      "email": "juan@ejemplo.com",
      "telefono": "0 99 123 456"
    }
  }'
```

## API del Servicio

### POST /notify

```http
POST /notify
Content-Type: application/json

{
  "tipo": "usuario_creado",
  "usuario": {
    "nombre": "string",
    "email": "string",
    "telefono": "string"
  }
}
```

**Respuesta (200)**:
```json
{
  "status": "success",
  "message": "Notificación enviada correctamente"
}
```

**Respuesta (500)**:
```json
{
  "status": "error",
  "message": "Error al enviar notificación"
}
```

### GET /health

```http
GET /health
```

**Respuesta (200)**:
```json
{
  "status": "healthy",
  "service": "notification-service"
}
```

## Implementación

### app.py (Flask)

```python
from flask import Flask, request, jsonify
from email_service import enviar_email_usuario_creado
from decouple import config

app = Flask(__name__)

@app.route('/notify', methods=['POST'])
def notify():
    try:
        data = request.get_json()
        
        if not data or 'tipo' not in data:
            return jsonify({'status': 'error', 'message': 'Datos inválidos'}), 400
        
        if data['tipo'] == 'usuario_creado':
            usuario = data.get('usuario', {})
            if enviar_email_usuario_creado(usuario):
                return jsonify({'status': 'success', 'message': 'Email enviado'}), 200
            return jsonify({'status': 'error', 'message': 'Error al enviar'}), 500
        
        return jsonify({'status': 'error', 'message': 'Tipo no soportado'}), 400
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'notification-service'}), 200

if __name__ == '__main__':
    port = int(config('PORT', default=8002))
    app.run(host='0.0.0.0', port=port)
```

### email_service.py

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config

def enviar_email_usuario_creado(usuario_data):
    try:
        smtp_host = config('SMTP_HOST')
        smtp_port = config('SMTP_PORT', cast=int)
        smtp_user = config('SMTP_USER')
        smtp_password = config('SMTP_PASSWORD')
        admin_email = config('ADMIN_EMAIL')
        
        mensaje = MIMEMultipart('alternative')
        mensaje['Subject'] = 'Nuevo Usuario Registrado'
        mensaje['From'] = smtp_user
        mensaje['To'] = admin_email
        
        html = f"""
        <html>
          <body>
            <h2>Nuevo Usuario Registrado</h2>
            <p><strong>Nombre:</strong> {usuario_data.get('nombre')}</p>
            <p><strong>Email:</strong> {usuario_data.get('email')}</p>
            <p><strong>Teléfono:</strong> {usuario_data.get('telefono')}</p>
          </body>
        </html>
        """
        
        parte_html = MIMEText(html, 'html')
        mensaje.attach(parte_html)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(mensaje)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
```

## Comandos Útiles

```bash
# Ver logs
docker logs -f notification-service

# Acceder al contenedor
docker exec -it notification-service /bin/bash

# Reiniciar
docker-compose restart

# Detener
docker-compose down
```

## Despliegue en AWS EKS

### 1. Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["gunicorn", "--bind", "0.0.0.0:8002", "--workers", "2", "app:app"]
```

### 2. Build y Push a ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker build -t notification-service .
docker tag notification-service:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/notification-service:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/notification-service:latest
```

### 3. Manifiestos Kubernetes

**IMPORTANTE**: Este servicio NO debe ser público. Solo ClusterIP.

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
  namespace: usuarios-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: notification-service
  template:
    metadata:
      labels:
        app: notification-service
    spec:
      containers:
      - name: notification-service
        image: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/notification-service:latest
        ports:
        - containerPort: 8002
        env:
        - name: SMTP_USER
          valueFrom:
            secretKeyRef:
              name: smtp-credentials
              key: SMTP_USER
        - name: SMTP_PASSWORD
          valueFrom:
            secretKeyRef:
              name: smtp-credentials
              key: SMTP_PASSWORD
        - name: ADMIN_EMAIL
          valueFrom:
            secretKeyRef:
              name: smtp-credentials
              key: ADMIN_EMAIL
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: notification-service
  namespace: usuarios-app
spec:
  type: ClusterIP  # Solo interno
  selector:
    app: notification-service
  ports:
  - protocol: TCP
    port: 8002
    targetPort: 8002
```

### 4. Crear Secret

```bash
kubectl create secret generic smtp-credentials \
  --from-literal=SMTP_USER=tu_email@gmail.com \
  --from-literal=SMTP_PASSWORD=tu_password_app \
  --from-literal=ADMIN_EMAIL=admin@ejemplo.com \
  -n usuarios-app
```

## Seguridad

### Medidas Implementadas

1. Secrets en Kubernetes
2. No expuesto públicamente (ClusterIP)
3. Validación de inputs
4. Logging sin datos sensibles

### Análisis

```bash
# SAST
bandit -r .

# SCA
safety check

# Container scan
trivy image notification-service:latest
```

## Troubleshooting

### Error: Authentication failed

```bash
# Verificar credenciales
cat .env | grep SMTP

# Regenerar password en Google
# https://myaccount.google.com/apppasswords
```

### Error: Connection refused desde users-api

```bash
# Verificar red
docker network inspect app-network

# Verificar servicio
docker ps | grep notification
kubectl get svc -n usuarios-app

# Probar conectividad
docker exec -it backend-usuarios ping notification-service
```

### Emails no llegan

1. Verificar logs: `docker logs notification-service`
2. Verificar carpeta SPAM
3. Test SMTP: `telnet smtp.gmail.com 587`
4. Verificar bloqueo de Gmail

## Escalabilidad

```bash
# Escalar manualmente
kubectl scale deployment notification-service --replicas=5 -n usuarios-app

# HPA
kubectl autoscale deployment notification-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n usuarios-app
```

## Repositorios Relacionados

- Backend: `https://github.com/Andyval31/Backend_Usuarios_Registro.git`
- Frontend: `https://github.com/Andyval31/Frontend_Usuarios_Registro.git`

---

**UTEC - Administración de Infraestructuras - 2025**
**Integrantes: Matias Ferreira y Andrea Valdez**