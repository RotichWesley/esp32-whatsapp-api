from flask import Flask, request
import requests
import time

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

VERIFY_TOKEN = "esp32secure123"

PHONE_NUMBER_ID = "1147823905079127"

ACCESS_TOKEN = "EAASO0nhfJKMBRcD9qy4ZAfCclfgxZAA4T4PCKR8K1T52eZCUgYWVRgXep3dP4HRjGLIGngsQfAWcPoD7GbhVZAtsrN2GfiB1FZAHMpZAGB6Npl0HZBMCoZALQVMjSnZCu5bnULy9j5gWILvexq1e3FR8BJJvppANZAsU93dC1aNOEUdiZCQ3GuDn4I5tRH7TzAwgwZDZD"

# ESP32 LOCAL SERVER
ESP32_URL = "http://192.168.137.132/esp32"

# =========================================================
# DEDUPLICATION (prevents repeated WhatsApp triggers)
# =========================================================

recent_messages = {}

def is_duplicate(sender, text):
    key = f"{sender}:{text}"
    now = time.time()

    if key in recent_messages:
        if now - recent_messages[key] < 5:  # 5-second window
            return True

    recent_messages[key] = now
    return False

# =========================================================
# SEND WHATSAPP MESSAGE
# =========================================================

def send_whatsapp(to_number, text):

    url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": text
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("WhatsApp Status:", response.status_code)
        print("WhatsApp Response:", response.text)

    except Exception as e:
        print("WhatsApp Send Error:", e)

# =========================================================
# HOME ROUTE
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "ESP32 WhatsApp API Running", 200

# =========================================================
# WEBHOOK VERIFICATION
# =========================================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED")
        return str(challenge), 200

    return "Verification failed", 403

# =========================================================
# WEBHOOK RECEIVER
# =========================================================

@app.route("/webhook", methods=["POST"])
def receive_messages():

    try:
        data = request.get_json()

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

        message = messages[0]

        sender = message.get("from", "")
        text = message.get("text", {}).get("body", "").strip()

        if not text:
            return "OK", 200

        text_lower = text.lower()

        print("FROM:", sender)
        print("MESSAGE:", text_lower)

        # =====================================================
        # PREVENT DUPLICATES / LOOP
        # =====================================================

        if is_duplicate(sender, text_lower):
            print("Duplicate message ignored")
            return "OK", 200

        # =====================================================
        # SEND TO ESP32
        # =====================================================

        try:
            esp_response = requests.post(
                ESP32_URL,
                json={"command": text_lower},
                timeout=5
            )

            print("ESP32 STATUS:", esp_response.status_code)
            print("ESP32 RESPONSE:", esp_response.text)

        except Exception as esp_error:
            print("ESP32 ERROR:", esp_error)

        # =====================================================
        # REPLY TO USER (ONLY HERE → NO DUPLICATES)
        # =====================================================

        send_whatsapp(sender, f"✔ Executed: {text}")

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return "OK", 200

# =========================================================

@app.route("/privacy", methods=["GET"])
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This system collects only WhatsApp messages for smart home automation.</p>
    <p>No data is stored permanently or shared with third parties.</p>
    """, 200


@app.route("/terms", methods=["GET"])
def terms():
    return """
    <h1>Terms of Service</h1>
    <p>This system is used for controlling IoT devices via WhatsApp API.</p>
    <p>Unauthorized use is prohibited.</p>
    """, 200


@app.route("/delete", methods=["GET", "POST"])
def delete_data():
    return """
    <h1>Data Deletion Request</h1>
    <p>To request data deletion, contact: rotichwesley15@gmail.com</p>
    """, 200
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
