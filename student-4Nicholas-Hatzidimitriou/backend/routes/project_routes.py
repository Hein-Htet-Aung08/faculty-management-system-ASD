from flask import Blueprint, request, jsonify
from services import database_api
from views.json_formatters import row_to_dict, rows_to_list

projects_bp = Blueprint("projects", __name__)

@projects_bp.route("/projects", methods=["GET"])
def get_projects():
    rows = database_api.list_projects(
        department=request.args.get("department"),
        status=request.args.get("status"),
    )
    return jsonify(rows_to_list(rows)), 200

@projects_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    row = database_api.get_project(project_id)
    if row is None:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(row_to_dict(row)), 200

@projects_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    required_fields = ["title", "department", "status"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    new_id = database_api.create_project(data)
    return jsonify({"projectID": new_id, "message": "Project created successfully"}), 201

@projects_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json()
    success = database_api.update_project(project_id, data)
    if not success:
        return jsonify({"error": "Project not found or update failed"}), 404
    return jsonify({"message": "Project updated successfully"}), 200

@projects_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    success = database_api.delete_project(project_id)
    if not success:
        return jsonify({"error": "Project not found or delete failed"}), 404
    return jsonify({"message": "Project deleted successfully"}), 200


#nested sub-resource. it lets the frontend get the related grants via project ID
#instead of getting all related grants and then filtering them on the client side.
@projects_bp.route("/projects/<int:project_id>/grants", methods=["GET"])
def get_project_grants(project_id):
    if not database_api.project_exists(project_id):
        return jsonify({"error": "Project not found"}), 404
    rows = database_api.list_grants(project_id=project_id)
    return jsonify(rows_to_list(rows)), 200

@projects_bp.route("/projects/<int:project_id>/publications", methods=["GET"])
def get_project_publications(project_id):
    if not database_api.project_exists(project_id):
        return jsonify({"error": "Project not found"}), 404
    rows = database_api.list_publications(project_id=project_id)
    return jsonify(rows_to_list(rows)), 200

@projects_bp.route("/projects/<int:project_id>/staff", methods=["GET"])
def get_project_staff(project_id):
    if not database_api.project_exists(project_id):
        return jsonify({"error": "Project not found"}), 404
    rows = database_api.list_project_staff(project_id=project_id)
    return jsonify(rows_to_list(rows)), 200