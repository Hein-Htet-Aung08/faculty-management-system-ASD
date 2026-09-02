from pathlib import Path
import sys

from flask import Flask
from flask_cors import CORS


BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from routes.subjects import subjects_bp
from routes.classrooms import classrooms_bp
from routes.allocations import allocations_bp
from routes.ai_mode import ai_mode_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.get("/")
    def health():
        return "<p>allocation-service running</p>", 200

    app.register_blueprint(subjects_bp)
    app.register_blueprint(classrooms_bp)
    app.register_blueprint(allocations_bp)
    app.register_blueprint(ai_mode_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)