
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import os

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')




mail = Mail(app)

@app.route('/notificaciones', methods=['POST'])
def notificaciones():
    data = request.json
    msg = Message("Notificación",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[data['email']])
    msg.body = data['mensaje']
    mail.send(msg)
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

