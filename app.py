from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "ESP32 Server Running"

@app.route("/esp32", methods=["POST"])
def esp32():
    data = request.data.decode()
    print("ESP32 DATA:", data)
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
