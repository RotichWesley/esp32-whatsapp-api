# ==============================================================================
# Copyright 2026 The Kipsoen National Polytechnic All Rights Reserved.
#
# Software License Agreement (BSD License)
#
# Author: Kipkemoi Wesley, TeKNP
# ==============================================================================
#
# Project: Hybrid Smart Home Automation System
# (WhatsApp Cloud API + Flask + ESP32)
#
# DESCRIPTION
# ------------------------------------------------------------------------------
# This Flask server:
#
# 1. Receives WhatsApp messages from Meta Cloud API
# 2. Processes user commands
# 3. Forwards commands to ESP32
# 4. Receives ESP32 responses
# 5. Sends feedback back to WhatsApp user
#
# Supported Commands:
#   - Room 1 On
#   - Room 1 Off
#   - Room 2 On
#   - Room 2 Off
#   - All Lights On
#   - All Lights Off
#   - Status
#
# ==============================================================================

from flask import Flask, request
import requests
import json

app = Flask(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

VERIFY_TOKEN = "esp32secure123"

PHONE_NUMBER_ID = "1147823905079127"

ACCESS_TOKEN = "EAASO0nhfJKMBReIXPAsVgmgCk3NBP6kRaQNzdZBuFHSZA2zH611JXO0wG9ZAsfMSZCj8KFozHir3hUURK3hDcOhZCcQFLUXhL1csA0GYw54mHhboh8E41t6OvuaWdm49GBnwLZAYPx3m4fJj9UOXPkMwJBkIFhxfQVcdPHVgHFb0TgrQeLGLfmJin2hIOJ6gZDZD"

# PUBLIC ESP32 ENDPOINT
# Replace with your ngrok URL
ESP32_URL = "https://YOUR-NGROK-URL.ngrok-free.app/command"

# ==============================================================================
# WHATSAPP SEND MESSAGE
# ==============================================================================

def send_whatsapp_message(to_number, message):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
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
            timeout=10
        )

        print("WhatsApp Response:", response.text)

    except Exception as e:
        print("WhatsApp Send Error:", str(e))

# ==============================================================================
# SEND COMMAND TO ESP32
# ==============================================================================

def send_command_to_esp32(command):

    try:

        response = requests.post(
            ESP32_URL,
            data=command,
            timeout=10
        )

        print("ESP32 Response:", response.text)

        return response.text

    except Exception as e:

        print("ESP32 Connection Error:", str(e))

        return "ESP32 Offline or Unreachable"

# ==============================================================================
# WEBHOOK VERIFICATION
# ==============================================================================

@app.route('/webhook', methods=['GET'])
def verify_webhook():

    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if verify_token == VERIFY_TOKEN:
        return challenge

    return "Verification failed", 403

# ==============================================================================
# RECEIVE WHATSAPP MESSAGES
# ==============================================================================

@app.route('/webhook', methods=['POST'])
def webhook():

    try:

        data = request.get_json()

        print(json.dumps(data, indent=2))

        # ----------------------------------------------------------------------
        # EXTRACT WHATSAPP MESSAGE
        # ----------------------------------------------------------------------

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignore statuses
        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]

        sender_number = message["from"]

        # Text message
        if message["type"] == "text":

            user_text = message["text"]["body"]

            print("Message:", user_text)

            # ------------------------------------------------------------------
            # SEND COMMAND TO ESP32
            # ------------------------------------------------------------------

            esp32_response = send_command_to_esp32(user_text)

            # ------------------------------------------------------------------
            # SEND FEEDBACK TO USER
            # ------------------------------------------------------------------

            send_whatsapp_message(
                sender_number,
                esp32_response
            )

        return "ok", 200

    except Exception as e:

        print("Webhook Error:", str(e))

        return "error", 500

# ==============================================================================
# ROOT ROUTE
# ==============================================================================

@app.route('/')
def home():

    return "ESP32 WhatsApp Smart Home API Running"

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000
    )
