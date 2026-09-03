import os

from flask import Flask, Response, jsonify, request
from openai import OpenAIError
from requests import RequestException

import ai_service
import database_client

RESOURCE_FILTERS = {
    "performance-reviews": {"staffID", "reviewerID", "status"},
    "development-goals": {"staffID", "status"},
    "training-programs": {"provider", "skillArea"},
    "staff-training": {"staffID", "trainingID", "status"},
    "development-recommendations": {
        "staffID", "goalID", "recommendationType", "status"
    },
}


def create_app():
    app = Flask(__name__)

    @app.get("/health")
    @app.get("/api/health")
    def health_check():
        return jsonify({
            "status": "ok",
            "service": "performance-professional-development-backend",
            "aiMode": "single-pass Ollama recommendation",
        })

    def proxy(response):
        if response.status_code == 204:
            return "", 204
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )

    def service_unavailable(error):
        return jsonify({
            "error": "database service is unavailable",
            "detail": str(error),
        }), 503

    @app.get("/api/<resource>")
    def list_resource(resource):
        allowed_filters = RESOURCE_FILTERS.get(resource)
        if allowed_filters is None:
            return jsonify({"error": "resource not found"}), 404
        filters = {
            key: value for key, value in request.args.items()
            if key in allowed_filters and value not in (None, "")
        }
        try:
            return proxy(database_client.list_resource(resource, filters))
        except RequestException as exc:
            return service_unavailable(exc)

    @app.get("/api/<resource>/<int:row_id>")
    def get_resource(resource, row_id):
        if resource not in RESOURCE_FILTERS:
            return jsonify({"error": "resource not found"}), 404
        try:
            return proxy(database_client.get_resource(resource, row_id))
        except RequestException as exc:
            return service_unavailable(exc)

    @app.post("/api/<resource>")
    def create_resource(resource):
        if resource not in RESOURCE_FILTERS:
            return jsonify({"error": "resource not found"}), 404
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "request body must be a JSON object"}), 400
        try:
            return proxy(database_client.create_resource(resource, payload))
        except RequestException as exc:
            return service_unavailable(exc)

    @app.put("/api/<resource>/<int:row_id>")
    def update_resource(resource, row_id):
        if resource not in RESOURCE_FILTERS:
            return jsonify({"error": "resource not found"}), 404
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "request body must be a JSON object"}), 400
        try:
            return proxy(database_client.update_resource(resource, row_id, payload))
        except RequestException as exc:
            return service_unavailable(exc)

    @app.delete("/api/<resource>/<int:row_id>")
    def delete_resource(resource, row_id):
        if resource not in RESOURCE_FILTERS:
            return jsonify({"error": "resource not found"}), 404
        try:
            return proxy(database_client.delete_resource(resource, row_id))
        except RequestException as exc:
            return service_unavailable(exc)

    @app.get("/api/ai/health")
    def ai_health():
        try:
            return jsonify(ai_service.health_check())
        except (OpenAIError, OSError) as exc:
            return jsonify({
                "status": "error",
                "error": "Ollama is unavailable or the configured model is not installed",
                "detail": str(exc),
            }), 503

    @app.post("/api/ai/recommend-development")
    def recommend_development():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "request body must be a JSON object"}), 400
        try:
            staff_id = int(payload.get("staffID"))
            if staff_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "staffID must be a positive integer"}), 400

        try:
            return jsonify(ai_service.generate_recommendation(staff_id)), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except RequestException as exc:
            return service_unavailable(exc)
        except (OpenAIError, OSError) as exc:
            return jsonify({
                "error": "AI service is unavailable or returned an unusable response",
                "detail": str(exc),
            }), 503

    return app


app = create_app()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5005"))
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
