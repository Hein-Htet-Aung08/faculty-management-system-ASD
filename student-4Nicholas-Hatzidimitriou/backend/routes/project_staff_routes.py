from flask import Blueprint, request, jsonify
from services import database_api
from views.json_views import row_to_dict, rows_to_list

project_staff_bp = Blueprint("project_staff", __name__)

@project_staff_bp.route("/project_staff", methods=["GET"])
def get_project_staff():
    rows = database_api.get_project_staff(
        project_id=request.args.get("projectID"),
        staff_id=request.args.get("staffID"),
    )
    return jsonify(rows_to_list(rows)), 200

@project_staff_bp.route("/project_staff/<int:project_staff_id>", methods=["GET"])
def get_project_staff_member(project_staff_id):
    row = database_api.get_project_staff_by_id(project_staff_id)
    if row is None:
        return jsonify({"error": "Project staff member not found"}), 404
    return jsonify(row_to_dict(row)), 200

@project_staff_bp.route("/project_staff", methods=["POST"])
def create_project_staff():
    data = request.get_json()
    required_fields = ["projectID", "staffID", "role"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400
    
    if not database_api.project_exists(data["projectID"]):
        return jsonify({"error": f"projectID {data['projectID']} does not exist"}), 400
    
    if not database_api.staff_exists(data["staffID"]):
        return jsonify({"error": f"staffID {data['staffID']} does not exist"}), 400
    
    new_id = database_api.create_project_staff(data)
    return jsonify({"projectStaffID": new_id, "message": "Project staff member created successfully"}), 201

@project_staff_bp.route("/project_staff/<int:project_staff_id>", methods=["PUT"])
def update_project_staff(project_staff_id):
    data = request.get_json()
    success = database_api.update_project_staff(project_staff_id, data)
    if not success:
        return jsonify({"error": "Project staff member not found or update failed"}), 404
    return jsonify({"message": "Project staff member updated successfully"}), 200

@project_staff_bp.route("/project_staff/<int:project_staff_id>", methods=["DELETE"])
def delete_project_staff(project_staff_id):
    success = database_api.delete_project_staff(project_staff_id)
    if not success:
        return jsonify({"error": "Project staff member not found or delete failed"}), 404
    return jsonify({"message": "Project staff member deleted successfully"}), 200