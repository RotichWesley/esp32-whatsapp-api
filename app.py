from flask import Flask, request
import requests
import time

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

VERIFY_TOKEN = "esp32secure123"
PHONE_NUMBER_ID = "1147823905079127"

ACCESS_TOKEN = "EAASO0nhfJKMBRddJM0mZCvNazjDAcXEJIXZA1pm1kzrwPq2NbMvRxNYA29KVSvEfYxwxgtiYh047eRHgQ1yh5AB5HKcR9AugjdpYKBJ8ZBY2XUiRaNE6iAEgGqO9UlUDcZA5vMK4s6QoKTBQ74eBZAgEME9M9cSy9FvfHvcx2gMPkp1H5Dj4YaKufPRsAyon8Tf"

ESP32_URL = "http://192.168.137.132/esp32"

# =========================================================
# DEDUPLICATION
# =========================================================

recent_messages = {}

def is_duplicate(sender, text):
    key = f"{sender}:{text}"
    now = time.time()

    if key in recent_messages and (now - recent_messages[key]) < 5:
        return True

    recent_messages[key] = now
    return False

# =========================================================
# WHATSAPP SENDER
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
        "text": {"body": text}
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        print("WhatsApp:", r.status_code, r.text)
    except Exception as e:
        print("WhatsApp Error:", e)

# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "ESP32 WhatsApp API Running", 200

# =========================================================
# WEBHOOK VERIFY
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
# WEBHOOK RECEIVE
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

        sender = message.get("from")
        text = message.get("text", {}).get("body", "").strip()

        # 🔴 SAFETY CHECK (IMPORTANT FIX)
        if not sender or not text:
            return "OK", 200

        text_lower = text.lower()

        print("FROM:", sender)
        print("MESSAGE:", text_lower)

        # PREVENT DUPLICATES
        if is_duplicate(sender, text_lower):
            print("Duplicate ignored")
            return "OK", 200

        # SEND TO ESP32
        try:
            r = requests.post(
                ESP32_URL,
                json={"command": text_lower},
                timeout=5
            )
            print("ESP32:", r.status_code, r.text)

        except Exception as e:
            print("ESP32 ERROR:", e)

        # REPLY ONCE
        send_whatsapp(sender, f"✔ Executed: {text}")

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return "OK", 200

# =========================================================
# STATIC PAGES (FIX FOR META 404 ISSUE)
# =========================================================

@app.route("/privacy")
def privacy():
    return "<h1>Privacy Policy</h1><p>Smart home WhatsApp automation system.</p>", 200

@app.route("/terms")
def terms():
    return "<h1>Terms</h1><p>IoT control system usage only.</p>", 200

@app.route("/delete", methods=["GET", "POST"])
def delete():
    return "<h1>Data Deletion</h1><p>Email: rotichwesley15@gmail.com</p>", 200

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
