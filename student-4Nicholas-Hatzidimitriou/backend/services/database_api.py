import os
import requests
 
DATABASE_SERVICE_URL = os.environ.get("DATABASE_SERVICE_URL", "http://localhost:5104")
 
 
def _get(path, params=None):
    """GET returning a list, or None on 404."""
    response = requests.get(f"{DATABASE_SERVICE_URL}{path}", params=params, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()
 
 
def _post(path, data):
    response = requests.post(f"{DATABASE_SERVICE_URL}{path}", json=data, timeout=10)
    response.raise_for_status()
    return response.json()
 
 
def _put(path, data):
    response = requests.put(f"{DATABASE_SERVICE_URL}{path}", json=data, timeout=10)
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True
 
 
def _delete(path):
    response = requests.delete(f"{DATABASE_SERVICE_URL}{path}", timeout=10)
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True
 
 
def _clean_params(params):
    """Drop None values so they aren't sent as empty query strings."""
    return {k: v for k, v in params.items() if v is not None}
 
# ResearchProjects
def list_projects(department=None, status=None):
    return _get("/projects", _clean_params({"department": department, "status": status}))
 
 
def get_project(project_id):
    return _get(f"/projects/{project_id}")
 
 
def project_exists(project_id):
    return get_project(project_id) is not None
 
 
def create_project(data):
    return _post("/projects", data)["projectID"]
 
 
def update_project(project_id, data):
    return _put(f"/projects/{project_id}", data)
 
 
def delete_project(project_id):
    return _delete(f"/projects/{project_id}")
 
# Grants
def list_grants(status=None, project_id=None):
    return _get("/grants", _clean_params({"status": status, "projectID": project_id}))
 
 
def get_grant(grant_id):
    return _get(f"/grants/{grant_id}")
 
 
def grant_exists(grant_id):
    return get_grant(grant_id) is not None
 
 
def create_grant(data):
    return _post("/grants", data)["grantID"]
 
 
def update_grant(grant_id, data):
    return _put(f"/grants/{grant_id}", data)
 
 
def delete_grant(grant_id):
    return _delete(f"/grants/{grant_id}")
 
# Publications
def list_publications(project_id=None, staff_id=None, publication_type=None):
    return _get("/publications", _clean_params({
        "projectID": project_id,
        "staffID": staff_id,
        "publicationType": publication_type,
    }))
 
 
def get_publication(publication_id):
    return _get(f"/publications/{publication_id}")
 
 
def create_publication(data):
    return _post("/publications", data)["publicationID"]
 
 
def update_publication(publication_id, data):
    return _put(f"/publications/{publication_id}", data)
 
 
def delete_publication(publication_id):
    return _delete(f"/publications/{publication_id}")
 
# ProjectStaff
def list_project_staff(project_id=None, staff_id=None):
    return _get("/project-staff", _clean_params({
        "projectID": project_id,
        "staffID": staff_id,
    }))
 
 
def get_project_staff_entry(project_staff_id):
    return _get(f"/project-staff/{project_staff_id}")
 
 
def create_project_staff(data):
    return _post("/project-staff", data)["projectStaffID"]
 
 
def update_project_staff(project_staff_id, data):
    return _put(f"/project-staff/{project_staff_id}", data)
 
 
def delete_project_staff(project_staff_id):
    return _delete(f"/project-staff/{project_staff_id}")
 
# GrantAlerts
def list_grant_alerts(grant_id=None, status=None):
    return _get("/grant-alerts", _clean_params({"grantID": grant_id, "status": status}))
 
 
def get_grant_alert(alert_id):
    return _get(f"/grant-alerts/{alert_id}")
 
 
def create_grant_alert(data):
    return _post("/grant-alerts", data)["alertID"]
 
 
def update_grant_alert(alert_id, data):
    return _put(f"/grant-alerts/{alert_id}", data)
 
 
def delete_grant_alert(alert_id):
    return _delete(f"/grant-alerts/{alert_id}")
 
# ResearchAIAnalysis
def list_ai_analyses(project_id=None, staff_id=None):
    return _get("/ai-analysis", _clean_params({
        "projectID": project_id,
        "staffID": staff_id,
    }))
 
 
def get_ai_analysis(analysis_id):
    return _get(f"/ai-analysis/{analysis_id}")
 
 
def create_ai_analysis(data):
    return _post("/ai-analysis", data)["analysisID"]
 
 
def update_ai_analysis(analysis_id, data):
    return _put(f"/ai-analysis/{analysis_id}", data)
 
 
def delete_ai_analysis(analysis_id):
    return _delete(f"/ai-analysis/{analysis_id}")
