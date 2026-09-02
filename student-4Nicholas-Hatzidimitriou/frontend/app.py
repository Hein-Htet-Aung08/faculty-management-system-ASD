import os
from flask import Flask, render_template

app = Flask(__name__, static_folder="css", static_url_path="/css")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tabs/normal")
def tab_normal():
    return render_template("tabs/normal.html")


@app.route("/tabs/ai-mode")
def tab_ai_mode():
    return render_template("tabs/ai_mode.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_RUN_PORT", 8004)), debug=True)