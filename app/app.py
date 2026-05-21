from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

# Variables potentiellement injectées par ConfigMap / Secret (Partie 3)
APP_ENV   = os.getenv("APP_ENV", "local")
APP_PORT  = int(os.getenv("APP_PORT", "5000"))
APP_USER  = os.getenv("APP_USER", "anonymous")
# Le mot de passe ne sera JAMAIS retourné dans la réponse ; on expose seulement
# le fait qu'il est bien injecté pour démontrer le montage du Secret.
APP_PWD_OK = bool(os.getenv("APP_PASSWORD"))


@app.route("/")
def hello():
    return jsonify({
        "message":   "Hello World",
        "hostname":  socket.gethostname(),
        "env":       APP_ENV,
        "user":      APP_USER,
        "secret_ok": APP_PWD_OK,
    })


@app.route("/healthz")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
