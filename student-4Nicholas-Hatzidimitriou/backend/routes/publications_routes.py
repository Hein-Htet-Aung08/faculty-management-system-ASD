from flask import Blueprint, request, jsonify
from services import database_api
from views.json_views import row_to_dict, rows_to_list

publications_bp = Blueprint("publications", __name__)

@publications_bp.route("/publications", methods=["GET"])
def get_publications():
    rows = database_api.get_publications(
        project_id=request.args.get("projectID"),
        staff_id=request.args.get("staffID"),
        publication_type=request.args.get("publicationType"),
    )
    return jsonify(rows_to_list(rows)), 200

@publications_bp.route("/publications/<int:publication_id>", methods=["GET"])
def get_publication(publication_id):
    row = database_api.get_publication_by_id(publication_id)
    if row is None:
        return jsonify({"error": "Publication not found"}), 404
    return jsonify(row_to_dict(row)), 200

@publications_bp.route("/publications", methods=["POST"])
def create_publication():
    data = request.get_json()
    required_fields = ["projectID","publicationType", "title"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400
    
    if not database_api.project_exists(data["projectID"]):
        return jsonify({"error": f"projectID {data['projectID']} does not exist"}), 400
    
    new_id = database_api.create_publication(data)
    return jsonify({"publicationID": new_id, "message": "Publication created successfully"}),201

@publications_bp.route("/publications/<int:publication_id>", methods=["PUT"])
def update_publication(publication_id):
    data = request.get_json()
    success = database_api.update_publication(publication_id, data)
    if not success:
        return jsonify({"error": "Publication not found or update failed"}), 404
    return jsonify({"message": "Publication updated successfully"}), 200

@publications_bp.route("/publications/<int:publication_id>", methods=["DELETE"])
def delete_publication(publication_id):
    success = database_api.delete_publication(publication_id)
    if not success:
        return jsonify({"error": "Publication not found or delete failed"}), 404
    return jsonify({"message": "Publication deleted successfully"}), 200

    