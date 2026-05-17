from flask import Flask, request
import requests
import json

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

VERIFY_TOKEN = "esp32secure123"

ACCESS_TOKEN = "YOUR_NEW_PERMANENT_TOKEN"

PHONE_NUMBER_ID = "1147823905079127"

# ESP32 LOCAL SERVER
ESP32_URL = "http://192.168.137.50/command"

# ============================================================
# SEND WHATSAPP MESSAGE
# ============================================================

def send_whatsapp(to, message):

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

    response = requests.post(url, headers=headers, json=data)

    print(response.text)

# ============================================================
# VERIFY WEBHOOK
# ============================================================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

        return "Verification failed", 403

    return "OK", 200

# ============================================================
# RECEIVE WHATSAPP MESSAGE
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        body = request.get_json()

        print(json.dumps(body, indent=2))

        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:

            message = value["messages"][0]

            if message.get("type") != "text":
                return "OK", 200

            sender = message["from"]

            text = message["text"]["body"]

            print("MESSAGE:", text)

            # ====================================================
            # FORWARD TO ESP32
            # ====================================================

            esp32_response = requests.post(
                ESP32_URL,
                data=text,
                timeout=5
            )

            reply = esp32_response.text

            # ====================================================
            # SEND BACK TO USER
            # ====================================================

            send_whatsapp(sender, reply)

        return "EVENT_RECEIVED", 200

    except Exception as e:

        print("ERROR:", str(e))

        return "ERROR", 500

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
