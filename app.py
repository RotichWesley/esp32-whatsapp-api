from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

VERIFY_TOKEN = "esp32secure123"

ACCESS_TOKEN = "EAASO0nhfJKMBRcXaZAdgQBFqS5OGdysUXWKko1szfFfkWQz2Dc2ilJZBhs9fNL1uVuyPtHp09clLDKDpxkdOclI4mplPdzShIPGyWZCMykGyxgE4CZCSJ1d21ZBCmIvxBq5hpIdQrsb5R4jBQCk6t9MnYBCLp1e2fkZCAZAUtZBaWzzWqh37pyZCboV9tLOXFIgZDZD"

PHONE_NUMBER_ID = "1147823905079127"

# ============================================================
# GLOBAL STORAGE
# ============================================================

latest_command = ""
last_sender = ""

system_logs = []

# ============================================================
# LOG FUNCTION
# ============================================================

def add_log(message):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"[{timestamp}] {message}"

    print(entry)

    system_logs.append(entry)

    # Keep only latest logs
    if len(system_logs) > 200:
        system_logs.pop(0)

# ============================================================
# SEND WHATSAPP MESSAGE
# ============================================================

def send_whatsapp_message(to, message):

    try:

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

        response = requests.post(
            url,
            headers=headers,
            json=data
        )

        add_log(f"WhatsApp Sent -> {to}")

        add_log(f"Meta Response: {response.text}")

    except Exception as e:

        add_log(f"WhatsApp Send ERROR: {str(e)}")

# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return "ESP32 WhatsApp API Running", 200

# ============================================================
# VERIFY WEBHOOK
# ============================================================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:

        add_log("Webhook Verified Successfully")

        return challenge, 200

    add_log("Webhook Verification Failed")

    return "Verification failed", 403

# ============================================================
# RECEIVE WHATSAPP
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    global latest_command
    global last_sender

    try:

        body = request.get_json()

        add_log("Webhook POST Received")

        add_log(json.dumps(body, indent=2))

        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignore status updates
        if "messages" not in value:

            add_log("No message field found")

            return "EVENT_RECEIVED", 200

        message = value["messages"][0]

        sender = message["from"]

        last_sender = sender

        if "text" not in message:

            add_log("Non-text message ignored")

            return "EVENT_RECEIVED", 200

        text = message["text"]["body"]

        latest_command = text.strip()

        add_log(f"COMMAND RECEIVED: {latest_command}")

        # Acknowledge receipt only
        send_whatsapp_message(
            sender,
            f"Command Received: {latest_command}"
        )

        return "EVENT_RECEIVED", 200

    except Exception as e:

        add_log(f"WEBHOOK ERROR: {str(e)}")

        return "ERROR", 500

# ============================================================
# ESP32 FETCH COMMAND
# ============================================================

@app.route("/get_command", methods=["GET"])
def get_command():

    global latest_command

    try:

        cmd = latest_command

        latest_command = ""

        if cmd != "":
            add_log(f"ESP32 FETCHED COMMAND: {cmd}")

            return cmd, 200

        return "NO_COMMAND", 200

    except Exception as e:

        add_log(f"GET_COMMAND ERROR: {str(e)}")

        return "ERROR", 500

# ============================================================
# ESP32 SEND STATUS BACK
# ============================================================

@app.route("/device_status", methods=["POST"])
def device_status():

    global last_sender

    try:

        data = request.get_json()

        status = data.get("status", "")

        add_log(f"ESP32 STATUS: {status}")

        if last_sender != "":

            send_whatsapp_message(
                last_sender,
                status
            )

        return "OK", 200

    except Exception as e:

        add_log(f"DEVICE_STATUS ERROR: {str(e)}")

        return "ERROR", 500

# ============================================================
# LOG VIEWER
# ============================================================

@app.route("/logs")
def logs():

    return "<br>".join(system_logs), 200

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    add_log("Flask Server Started")

    app.run(host="0.0.0.0", port=5000)
