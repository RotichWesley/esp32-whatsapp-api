from flask import Flask, request
import requests

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================

ESP32_URL = "http://YOUR_ESP32_IP/esp32"
VERIFY_TOKEN = "esp32secure123"

PHONE_NUMBER_ID = "1147823905079127"
ACCESS_TOKEN = "YOUR_WHATSAPP_TOKEN"
TO_NUMBER = "254759778238"

# =========================
# SEND WHATSAPP MESSAGE
# =========================
def send_whatsapp(text):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": TO_NUMBER,
        "type": "text",
        "text": {
            "body": text
        }
    }

    r = requests.post(url, json=payload, headers=headers)

    print("WhatsApp Response:", r.status_code, r.text)


# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def home():
    return "ESP32 WhatsApp API Running", 200


# =========================
# WEBHOOK VERIFY
# =========================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return str(challenge), 200

    return "Verification failed", 403


# =========================
# RECEIVE WHATSAPP MESSAGE
# =========================
@app.route("/webhook", methods=["POST"])
def receive_messages():
    try:
        data = request.get_json()

        print("RAW:", data)

        # SAFE EXTRACTION
        entry = data.get("entry", [])
        if not entry:
            return "OK", 200

        changes = entry[0].get("changes", [])
        if not changes:
            return "OK", 200

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return "OK", 200

        msg_obj = messages[0]
        msg = msg_obj.get("text", {}).get("body", "")

        if not msg:
            return "OK", 200

        print("WhatsApp MSG:", msg)

        # =========================
        # SEND TO ESP32
        # =========================
        try:
            requests.post(
                ESP32_URL,
                json={"command": msg},
                timeout=5
            )
        except Exception as e:
            print("ESP32 ERROR:", e)

        # =========================
        # SEND CONFIRMATION BACK
        # =========================
        send_whatsapp(f"✔ Command received: {msg}")

    except Exception as e:
        print("Webhook error:", e)

    return "OK", 200


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
