from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/notify', methods=['POST'])
def notify():
    data = request.json
    print(f"📨 Notificación recibida: {data}")
    # Acá después le agregaremos envío de mail real
    return jsonify({"status": "received", "data": data}), 200

@app.route('/healthz')
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
