from flask import Blueprint, request, jsonify
from services import database_api
from views.json_formatters import row_to_dict, rows_to_list

ai_analysis_bp = Blueprint("ai_analysis", __name__)

@ai_analysis_bp.route("/ai-analysis", methods=["GET"])
def get_ai_analyses():
    rows = database_api.list_ai_analyses(
        project_id=request.args.get("projectID"),
        staff_id=request.args.get("staffID"),
    )
    return jsonify(rows_to_list(rows)), 200
 
 
@ai_analysis_bp.route("/ai-analysis/<int:analysis_id>", methods=["GET"])
def get_ai_analysis(analysis_id):
    row = database_api.get_ai_analysis(analysis_id)
    if row is None:
        return jsonify({"error": "AI analysis record not found"}), 404
    return jsonify(row_to_dict(row)), 200

@ai_analysis_bp.route("/ai_analysis", methods=["POST"])
def create_ai_analysis():
    data = request.get_json()

    if "projectID" not in data or "staffID" not in data:
        return jsonify({"error": "Missing required fields: projectID and staffID"}), 400
    
    if data.get("projectID") is not None and not database_api.project_exists(data["projectID"]):
        return jsonify({"error": f"projectID {data['projectID']} does not exist"}), 400
    
    new_id = database_api.create_ai_analysis(data)
    return jsonify({"aiAnalysisID": new_id, "message": "AI analysis entry created successfully"}), 201

@ai_analysis_bp.route("/ai_analysis/<int:ai_analysis_id>", methods=["PUT"])
def update_ai_analysis(ai_analysis_id):
    data = request.get_json()
    success = database_api.update_ai_analysis(ai_analysis_id, data)
    if not success:
        return jsonify({"error": "AI analysis entry not found or update failed"}), 404
    return jsonify({"message": "AI analysis entry updated successfully"}), 200

@ai_analysis_bp.route("/ai_analysis/<int:ai_analysis_id>", methods=["DELETE"])
def delete_ai_analysis(ai_analysis_id):
    success = database_api.delete_ai_analysis(ai_analysis_id)
    if not success:
        return jsonify({"error": "AI analysis entry not found or delete failed"}), 404
    return jsonify({"message": "AI analysis entry deleted successfully"}), 200
