import os
import flask import Flask, jsonify

from routes.projects_routes import projects_bp
from routes.grants_routes import grants_bp
from routes.publications_routes import publications_bp
from routes.project_staff_routes import project_staff_bp
from routes.grant_alerts_routes import grant_alerts_bp
from routes.ai_analysis_routes import ai_analysis_bp
from routes.ai_mode import ai_mode_bp

app = Flask(__name__)

app.register_blueprint(projects_bp)
app.register_blueprint(grants_bp)
app.register_blueprint(publications_bp)
app.register_blueprint(project_staff_bp)
app.register_blueprint(grant_alerts_bp)
app.register_blueprint(ai_analysis_bp)
app.register_blueprint(ai_mode_bp)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "research-grant-management"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
