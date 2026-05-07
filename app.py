from flask import Flask, request
import requests

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================

ESP32_URL = "http://YOUR_ESP32_IP/esp32"  # change later when ESP32 is ready
VERIFY_TOKEN = "esp32secure123"

# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def home():
    return "ESP32 WhatsApp API Running", 200


# =========================
# META WEBHOOK VERIFICATION (CRITICAL)
# =========================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("Webhook verification attempt:")
    print("mode:", mode)
    print("token:", token)
    print("challenge:", challenge)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return str(challenge), 200

    return "Verification failed", 403


# =========================
# RECEIVE WHATSAPP MESSAGES
# =========================
@app.route("/webhook", methods=["POST"])
def receive_messages():
    try:
        data = request.get_json()

        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        print("Received WhatsApp message:", msg)

        # Forward to ESP32
        payload = {"command": msg}

        try:
            requests.post(ESP32_URL, json=payload, timeout=5)
        except Exception as esp_err:
            print("ESP32 ERROR:", esp_err)

    except Exception as e:
        print("Webhook parsing error:", e)

    return "OK", 200


# =========================
# RUN LOCAL (Render uses gunicorn)
# =========================
if __name__ == "__main__":
    app.run(debug=True)
