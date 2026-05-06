from flask import Flask, request
import requests
import os

app = Flask(__name__)

# =========================
# CONFIG (use environment variable in production)
# =========================
ESP32_URL = os.getenv("ESP32_URL", "http://YOUR_ESP32_IP/esp32")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "esp32secure123")


# =========================
# HOME ROUTE (TEST)
# =========================
@app.route("/")
def home():
    return "ESP32 WhatsApp API Running"


# =========================
# VERIFY WEBHOOK (Meta REQUIREMENT FIXED)
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # STRICT Meta validation
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return str(challenge), 200

    return "Verification failed", 403


# =========================
# RECEIVE WHATSAPP MESSAGES
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        # Safe extraction (prevents crash if JSON changes)
        msg = (
            data["entry"][0]["changes"][0]["value"]
            ["messages"][0]["text"]["body"]
        )

        print("Received from WhatsApp:", msg)

        # =========================
        # FORWARD TO ESP32
        # =========================
        payload = {
            "command": msg
        }

        try:
            response = requests.post(
                ESP32_URL,
                json=payload,
                timeout=5
            )

            print("ESP32 response:", response.text)

        except Exception as esp_err:
            print("ESP32 connection error:", esp_err)

    except Exception as e:
        print("Webhook parsing error:", e)

    return "OK", 200


# =========================
# RUN LOCALLY (Render uses gunicorn)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
