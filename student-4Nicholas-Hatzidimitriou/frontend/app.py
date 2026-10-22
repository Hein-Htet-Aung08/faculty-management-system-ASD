import os
from flask import Flask, render_template

_SHARED_CSS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared", "frontend", "css")
)

app = Flask(__name__, static_folder=_SHARED_CSS_DIR, static_url_path="/css")


@app.route("/")
def index():
    return render_template(
        "index.html",
        research_api_base=os.environ.get("RESEARCH_API_BASE", ""),
        staff_api_base=os.environ.get("STAFF_API_BASE", ""),
    )


@app.route("/tabs/normal")
def tab_normal():
    return render_template("tabs/normal.html")


@app.route("/tabs/ai-mode")
def tab_ai_mode():
    return render_template("tabs/ai_mode.html")


@app.route("/tabs/mcp")
def tab_mcp():
    return render_template("tabs/mcp.html")


@app.route("/tabs/rag")
def tab_rag():
    return render_template("tabs/rag.html")


@app.route("/tabs/multi-agent")
def tab_multi_agent():
    return render_template("tabs/multi-agent.html")


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_RUN_PORT", 8004)), debug=debug_mode)  # noqa: S104 - container needs to bind all interfaces