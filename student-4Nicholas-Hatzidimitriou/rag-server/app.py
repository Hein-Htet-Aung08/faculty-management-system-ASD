import os

from flask import Flask, jsonify, request

from retriever import retrieve_context

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "rag-server"}), 200


@app.route("/retrieve", methods=["GET"])
def retrieve():
    project_id_raw = request.args.get("project_id")
    if not project_id_raw:
        return jsonify({"error": "Missing required query param: project_id"}), 400

    try:
        project_id = int(project_id_raw)
    except ValueError:
        return jsonify({"error": "project_id must be an integer"}), 400

    try:
        snippets = retrieve_context(project_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"Retrieval failed: {exc}"}), 503

    return jsonify({"projectID": project_id, "context": snippets}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5204)), debug=True)
