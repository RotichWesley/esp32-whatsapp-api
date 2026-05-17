from flask import Flask, request
import requests
import json

app = Flask(__name__)

# ============================================================
# META WHATSAPP CONFIGURATION
# ============================================================

VERIFY_TOKEN = "esp32secure123"

ACCESS_TOKEN = "YOUR_PERMANENT_ACCESS_TOKEN"

PHONE_NUMBER_ID = "1147823905079127"

# ============================================================
# SEND WHATSAPP MESSAGE
# ============================================================

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

    response = requests.post(url, headers=headers, json=data)

    print("WhatsApp Response:", response.text)

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

    return "Hello", 200

# ============================================================
# RECEIVE WHATSAPP MESSAGES
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

            sender = message["from"]
            text = message["text"]["body"]

            command = text.lower().strip()

            print(f"COMMAND: {command}")

            # ====================================================
            # COMMAND PROCESSING
            # ====================================================

            if command == "room 1 on":
                reply = "Room 1 turned ON"

            elif command == "room 1 off":
                reply = "Room 1 turned OFF"

            elif command == "room 2 on":
                reply = "Room 2 turned ON"

            elif command == "room 2 off":
                reply = "Room 2 turned OFF"

            elif command == "all lights on":
                reply = "All lights turned ON"

            elif command == "all lights off":
                reply = "All lights turned OFF"

            elif command == "status":
                reply = "Room1: OFF\nRoom2: OFF"

            else:
                reply = (
                    "Invalid command.\n"
                    "Use:\n"
                    "Room 1 On\n"
                    "Room 1 Off\n"
                    "Room 2 On\n"
                    "Room 2 Off\n"
                    "All Lights On\n"
                    "All Lights Off\n"
                    "Status"
                )

            # ====================================================
            # SEND RESPONSE
            # ====================================================

            send_whatsapp_message(sender, reply)

        return "EVENT_RECEIVED", 200

    except Exception as e:

        print("ERROR:", str(e))
        return "ERROR", 500

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
