from flask import Blueprint, request, jsonify
from services import database_api
from views.json_views import row_to_dict, rows_to_list

grants_bp = Blueprint("grants", __name__)

@grants_bp.route("/grants", methods=["GET"])
def get_grants():
    rows = database_apo.get_grants(
        status=request.args.get("status"),
        project_id=request.args.get("project_id"),
    )
    return jsonify(rows_to_list(rows)), 200

@grants_bp.route("/grants/<int:grant_id>", methods=["GET"])
def get_grant(grant_id):
    row = database_api.get_grant_by_id(grant_id)
    if row is None:
        return jsonify({"error": "Grant not found"}), 404
    return jsonify(row_to_dict(row)), 200

@grants_bp.route("/grants", methods=["POST"])
def create_grant():
    data = request.get_json()
    required_fields = ["projectID", "fundingBody", "amountRequestd", "applicationDeadline", "status"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    if not database_api.project_exists(data["projectID"]):
        return jsonify({"error": f"projectID {data['projectID']} does not exist"}), 400
    
    new_id = database_api.create_grant(data)
    return jsonify({"grantID": new_id, "message": "Grant created successfully"}), 201

@grants_bp.route("/grants/<int:grant_id>", methods=["PUT"])
def update_grant(grant_id):
    data = request.get_json()
    success = database_api.update_grant(grant_id, data)
    if not success:
        return jsonify({"error": "Grant not found or update failed"}), 404
    return jsonify({"message": "Grant updated successfully"}), 200

@grants_bp.route("/grants/<int:grant_id>", methods=["DELETE"])
def delete_grant(grant_id):
    success = database_api.delete_grant(grant_id)
    if not success:
        return jsonify({"error": "Grant not found or delete failed"}), 404
    return jsonify({"message": "Grant deleted successfully"}), 200


#same nested sub-resource as in project routes but for grants
@grants_bp.route("/grants/<int:grant_id>/alerts", methods=["GET"])
def get_grant_alerts(grant_id):
    if not database_api.grant_exists(grant_id):
        return jsonify({"error": "Grant not found"}), 404
    rows = database_api.get_grant_alerts(grant_id)
    return jsonify(rows_to_list(rows)), 200