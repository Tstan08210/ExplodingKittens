from flask import Flask

app = Flask(__name__)

@app.route("/kill")
def kill():
    return 1

@app.route("/")
def tcp():
    return "HEALTHY"


def run_app():
    app.run(host="0.0.0.0", port=8000)
