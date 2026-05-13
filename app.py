from flask import Flask, request
import requests
import time

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

VERIFY_TOKEN = "esp32secure123"
PHONE_NUMBER_ID = "1147823905079127"
ACCESS_TOKEN = "YOUR_META_ACCESS_TOKEN_HERE"

# MUST MATCH ESP32 HTTP SERVER ROUTE
ESP32_URL = "http://10.11.84.99/esp32"

# =========================================================
# MEMORY CACHE (ANTI DUPLICATE)
# =========================================================

recent_messages = {}

def cleanup_cache():
    now = time.time()
    for k in list(recent_messages.keys()):
        if now - recent_messages[k] > 60:
            del recent_messages[k]

def is_duplicate(sender, text):
    cleanup_cache()
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
        print("WhatsApp RESPONSE:", r.status_code, r.text)
    except Exception as e:
        print("WhatsApp ERROR:", e)

# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "ESP32 WhatsApp API Running", 200

# =========================================================
# WEBHOOK VERIFY (META)
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
# WEBHOOK RECEIVE (FIXED + ROBUST)
# =========================================================

@app.route("/webhook", methods=["POST"])
def receive_messages():
    try:
        data = request.get_json(force=True, silent=True) or {}

        # Safe navigation (Meta structure)
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
        text = message.get("text", {}).get("body")

        if not sender or not text:
            print("INVALID MESSAGE SKIPPED")
            return "OK", 200

        # Normalize command
        text_clean = text.strip().lower()

        print("\n==============================")
        print("FROM:", sender)
        print("MESSAGE:", text_clean)
        print("==============================\n")

        # Duplicate protection
        if is_duplicate(sender, text_clean):
            print("DUPLICATE IGNORED")
            return "OK", 200

        # =====================================================
        # SEND TO ESP32
        # =====================================================

        try:
            r = requests.post(
                ESP32_URL,
                data=text_clean,
                headers={"Content-Type": "text/plain"},
                timeout=5
            )

            print("ESP32 STATUS:", r.status_code)
            print("ESP32 RESPONSE:", r.text)

        except Exception as e:
            print("ESP32 CONNECTION ERROR:", e)

        # =====================================================
        # AUTO REPLY USER
        # =====================================================

        send_whatsapp(sender, f"✔ Executed: {text_clean}")

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return "OK", 200

# =========================================================
# STATIC META REQUIRED PAGES
# =========================================================

@app.route("/privacy")
def privacy():
    return "<h1>Privacy Policy</h1><p>Smart home automation system.</p>", 200

@app.route("/terms")
def terms():
    return "<h1>Terms</h1><p>IoT control system usage only.</p>", 200

@app.route("/delete", methods=["GET", "POST"])
def delete():
    return "<h1>Data Deletion</h1><p>Email: rotichwesley15@gmail.com</p>", 200

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
