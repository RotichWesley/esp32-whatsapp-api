from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

# ============================================================================
# META WHATSAPP CONFIGURATION
# ============================================================================

VERIFY_TOKEN = "esp32secure123"

ACCESS_TOKEN = "EAASO0nhfJKMBRgSIlHydEUAkvCSfNGG7GVADPFQkp8bgjJDXF80MAZAxXdJP2VKZBPEZA4MLCsTv500L0lZCOKaZAJRrxhFqx7upYlVqWbHmEDKbpjZCfUjGVZA0jc39W8PytkkYlS6hm5HMiXzM5e42VBWUTH1qUCZBIzxouZCvs2Eo0s3ioqgBvfbnw3q8IpQZDZD"

PHONE_NUMBER_ID = "1147823905079127"

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

latest_command = ""
latest_sender = ""

# ============================================================================
# LOGGING
# ============================================================================

def log(message):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{now}] {message}")

# ============================================================================
# SEND WHATSAPP MESSAGE
# ============================================================================

def send_whatsapp_message(to, message):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=20
        )

        log(f"WhatsApp Sent -> {to}")

        log(f"Meta Response: {response.text}")

    except Exception as e:

        log(f"WhatsApp Send Error: {str(e)}")

# ============================================================================
# VERIFY WEBHOOK
# ============================================================================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:

        if mode == "subscribe" and token == VERIFY_TOKEN:

            log("Webhook Verified")

            return challenge, 200

        return "Verification failed", 403

    return "Hello", 200

# ============================================================================
# RECEIVE WHATSAPP MESSAGES
# ============================================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    global latest_command
    global latest_sender

    try:

        body = request.get_json()

        log("Webhook POST Received")

        log(json.dumps(body, indent=2))

        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # ============================================================
        # IGNORE STATUS EVENTS
        # ============================================================

        if "messages" not in value:

            log("No message field found")

            return "OK", 200

        message = value["messages"][0]

        sender = message["from"]

        text = message["text"]["body"]

        command = text.strip()

        latest_command = command

        latest_sender = sender

        log(f"COMMAND RECEIVED: {command}")

        return "EVENT_RECEIVED", 200

    except Exception as e:

        log(f"WEBHOOK ERROR: {str(e)}")

        return "ERROR", 500

# ============================================================================
# ESP32 FETCH COMMAND
# ============================================================================

@app.route("/get_command", methods=["GET"])
def get_command():

    global latest_command

    if latest_command == "":

        return "NO_COMMAND", 200

    cmd = latest_command

    latest_command = ""

    log(f"ESP32 FETCHED COMMAND: {cmd}")

    return cmd, 200

# ============================================================================
# ESP32 SEND STATUS
# ============================================================================

@app.route("/device_status", methods=["POST"])
def device_status():

    global latest_sender

    try:

        data = request.get_json()

        log(f"DEVICE STATUS RECEIVED: {data}")

        status = data.get("status", "")

        if status == "":

            return "NO STATUS", 400

        if latest_sender != "":

            send_whatsapp_message(
                latest_sender,
                status
            )

        return "STATUS SENT", 200

    except Exception as e:

        log(f"STATUS ERROR: {str(e)}")

        return "ERROR", 500

# ============================================================================
# HOME
# ============================================================================

@app.route("/", methods=["GET"])
def home():

    return "ESP32 WhatsApp Flask Server Running"

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
