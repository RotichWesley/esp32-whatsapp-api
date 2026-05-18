from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "esp32secure123"

ACCESS_TOKEN = "EAASO0nhfJKMBRcXaZAdgQBFqS5OGdysUXWKko1szfFfkWQz2Dc2ilJZBhs9fNL1uVuyPtHp09clLDKDpxkdOclI4mplPdzShIPGyWZCMykGyxgE4CZCSJ1d21ZBCmIvxBq5hpIdQrsb5R4jBQCk6t9MnYBCLp1e2fkZCAZAUtZBaWzzWqh37pyZCboV9tLOXFIgZDZD"

PHONE_NUMBER_ID = "1147823905079127"

latest_command = ""

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

    print(response.text)

# ============================================================
# VERIFY WEBHOOK
# ============================================================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification Failed", 403

# ============================================================
# RECEIVE WHATSAPP
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    global latest_command

    try:

        body = request.get_json()

        print(json.dumps(body, indent=2))

        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:

            msg = value["messages"][0]

            sender = msg["from"]

            text = msg["text"]["body"]

            latest_command = text.strip()

            print("NEW COMMAND:", latest_command)

            send_whatsapp_message(
                sender,
                f"Command Received: {latest_command}"
            )

        return "OK", 200

    except Exception as e:

        print("ERROR:", str(e))

        return "ERROR", 500

# ============================================================
# ESP32 FETCH COMMAND
# ============================================================

@app.route("/get_command", methods=["GET"])
def get_command():

    global latest_command

    cmd = latest_command

    latest_command = ""

    return cmd, 200

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
