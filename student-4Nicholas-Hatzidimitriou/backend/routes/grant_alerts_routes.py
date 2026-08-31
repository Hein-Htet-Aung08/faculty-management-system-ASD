from flask import Blueprint, request, jsonify
from services import database_api
from views.json_views import row_to_dict, rows_to_list

grant_alerts_bp = Blueprint("grant_alerts", __name__)

@grant_alerts_bp.route("/grant_alerts", methods=["GET"])
def get_grant_alerts():
    rows = database_api.get_grant_alerts(
        grant_id=request.args.get("grantID"),
        status=request.args.get("status"),
    )
    return jsonify(rows_to_list(rows)), 200

@grant_alerts_bp.route("/grant_alerts/<int:grant_alert_id>", methods=["GET"])
def get_grant_alert(grant_alert_id):
    row = database_api.get_grant_alert_by_id(grant_alert_id)
    if row is None:
        return jsonify({"error": "Grant alert not found"}), 404
    return jsonify(row_to_dict(row)), 200

@grant_alerts_bp.route("/grant_alerts", methods=["POST"])
def create_grant_alert():
    data = request.get_json()
    required_fields = ["grantID", "alertType", "alertDate", "status"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    if not database_api.grant_exists(data["grantID"]):
        return jsonify({"error": f"grantID {data['grantID']} does not exist"}), 400
    
    new_id = database_api.create_grant_alert(data)
    return jsonify({"grantAlertID": new_id, "message": "Grant alert created successfully"}), 201

@grant_alerts_bp.route("/grant_alerts/<int:grant_alert_id>", methods=["PUT"])
def update_grant_alert(grant_alert_id):
    data = request.get_json()
    success = database_api.update_grant_alert(grant_alert_id, data)
    if not success:
        return jsonify({"error": "Grant alert not found or update failed"}), 404
    return jsonify({"message": "Grant alert updated successfully"}), 200

@grant_alerts_bp.route("/grant_alerts/<int:grant_alert_id>", methods=["DELETE"])
def delete_grant_alert(grant_alert_id):
    success = database_api.delete_grant_alert(grant_alert_id)
    if not success:
        return jsonify({"error": "Grant alert not found or delete failed"}), 404
    return jsonify({"message": "Grant alert deleted successfully"}), 200

