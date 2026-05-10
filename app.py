from flask import Flask, request
import requests

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

VERIFY_TOKEN = "esp32secure123"

PHONE_NUMBER_ID = "1147823905079127"

ACCESS_TOKEN = "EAASO0nhfJKMBRbcatIQsGpZAoEQGgZA7BfsTKsp3o95VfN4NjhsAdjFcXyRdCIw7spQsn9yuebEWKYhBRHFw6GXe3qTWy54UAvGJit5djMaZCLfRAjEqZAX8q59dYRirZCyCmNLi4tOQKVLxmEW9zBELSQ92mDk4u70O28ZBkgvxLu60x5Gd40F9lvLqGkagZDZD"

# CHANGE THIS TO YOUR ESP32 LOCAL IP
ESP32_URL = "http://192.168.137.132/esp32"

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

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        print("WhatsApp Status:", response.status_code)
        print("WhatsApp Response:", response.text)

    except Exception as e:

        print("WhatsApp Send Error:", e)

# =========================================================
# HEALTH CHECK
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

    print("Webhook Verification Request")

    if mode == "subscribe" and token == VERIFY_TOKEN:

        print("WEBHOOK VERIFIED")
        return str(challenge), 200

    return "Verification failed", 403

# =========================================================
# RECEIVE WHATSAPP MESSAGE
# =========================================================

@app.route("/webhook", methods=["POST"])
def receive_messages():

    try:

        data = request.get_json()

        print("================================================")
        print("FULL WEBHOOK DATA:")
        print(data)
        print("================================================")

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

        msg_type = message.get("type", "")

        if msg_type != "text":
            return "OK", 200

        text = message.get("text", {}).get("body", "")

        if not text:
            return "OK", 200

        print("FROM:", sender)
        print("MESSAGE:", text)

        # =================================================
        # SEND COMMAND TO ESP32
        # =================================================

        try:

            payload = {
                "command": text
            }

            esp_response = requests.post(
                ESP32_URL,
                json=payload,
                timeout=5
            )

            print("ESP32 STATUS:", esp_response.status_code)
            print("ESP32 RESPONSE:", esp_response.text)

        except Exception as esp_error:

            print("ESP32 ERROR:", esp_error)

        # =================================================
        # REPLY TO USER
        # =================================================

        send_whatsapp(
            sender,
            f"✔ Command received: {text}"
        )

    except Exception as e:

        print("WEBHOOK ERROR:", e)

    return "OK", 200

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
