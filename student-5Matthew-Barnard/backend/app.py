from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "service": "performance-professional-development-management"
    })


@app.get("/api/performance-reviews")
def get_performance_reviews():
    return jsonify({
        "message": "Performance reviews CRUD endpoint is under development.",
        "data": []
    })


@app.get("/api/development-goals")
def get_development_goals():
    return jsonify({
        "message": "Development goals CRUD endpoint is under development.",
        "data": []
    })


@app.get("/api/training-programs")
def get_training_programs():
    return jsonify({
        "message": "Training programs CRUD endpoint is under development.",
        "data": []
    })


@app.get("/api/staff-training")
def get_staff_training():
    return jsonify({
        "message": "Staff training CRUD endpoint is under development.",
        "data": []
    })


@app.get("/api/development-recommendations")
def get_development_recommendations():
    return jsonify({
        "message": "Development recommendations CRUD endpoint is under development.",
        "data": []
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
