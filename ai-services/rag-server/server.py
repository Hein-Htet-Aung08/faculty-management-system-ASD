from flask import Flask, request, jsonify
from rag_pipeline import refresh_corpus, retrieve_context, answer_question

app = Flask(__name__)

@app.route("/refresh", methods=["POST"])
def refresh():
    return jsonify(refresh_corpus())

@app.route("/retrieve", methods=["POST"])
def retrieve():
    body = request.get_json(force=True)
    return jsonify(retrieve_context(body.get("query", ""), k=body.get("k", 5)))

@app.route("/answer", methods=["POST"])
def answer():
    body = request.get_json(force=True)
    return jsonify(answer_question(body.get("query", "")))

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
