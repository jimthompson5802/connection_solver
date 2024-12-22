from flask import Flask, render_template, request, jsonify
import signal
import os

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    new_line = "Generated line " + str(request.json.get("count", 0))
    return jsonify({"text": new_line})


@app.route("/stop", methods=["POST"])
def stop():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"status": "stopping"})


if __name__ == "__main__":
    app.run(debug=True)
