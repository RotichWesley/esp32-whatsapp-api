from flask import Flask, request
import requests

app = Flask(__name__)

# ESP32 endpoint (you will update later)
ESP32_URL = "http://YOUR_ESP32_IP:5000/esp32"

# WhatsApp token (Render env variable later)
VERIFY_TOKEN = "esp32secure123"


# =========================
# VERIFY WEBHOOK (Meta requirement)
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # SAFE CHECK (Meta strict validation)
    if token and token == VERIFY_TOKEN:
        return str(challenge)

    return "Invalid verification", 403


# =========================
# RECEIVE WHATSAPP MESSAGES
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        print("Received:", msg)

        # =========================
        # SAFE FORWARD TO ESP32
        # =========================
        payload = {
            "command": msg
        }

        try:
            requests.post(
                ESP32_URL,
                json=payload,
                timeout=5
            )
        except Exception as esp_err:
            print("ESP32 error:", esp_err)

    except Exception as e:
        print("Webhook parsing error:", e)

    return "OK", 200


# =========================
# TEST ROUTE
# =========================
@app.route("/")
def home():
    return "ESP32 WhatsApp API Running"


# =========================
# RUN LOCALLY (Render uses gunicorn)
# =========================
if __name__ == "__main__":
    app.run(debug=True)
