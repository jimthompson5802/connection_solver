from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setup-puzzle", methods=["POST"])
def setup_puzzle():
    setup_text = request.json.get("setup")
    setup_text = setup_text.upper()
    print(f"Received puzzle setup: {setup_text}")
    return jsonify({"status": "success", "upperText": setup_text})


if __name__ == "__main__":
    app.run(debug=True)
