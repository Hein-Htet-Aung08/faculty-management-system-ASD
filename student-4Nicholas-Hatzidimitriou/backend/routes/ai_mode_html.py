from flask import Blueprint
from services import database_api
from services import staff_client
from services.prompt_loader import load_prompt
from services.llm_client import OLLAMA_MODEL, create_chat_completion

ai_mode_html_bp = Blueprint("ai_mode_html", __name__)


@ai_mode_html_bp.post("/projects/<int:project_id>/generate_summary")
@ai_mode_html_bp.post("/projects/<int:project_id>/generate-summary")
def generate_summary_html(project_id):
    project = database_api.get_project(project_id)
    if project is None:
        return "<p>Project not found.</p>", 404

    publications = database_api.list_publications(project_id=project_id)
    pub_titles = [p["title"] for p in publications]

    try:
        system_prompt = load_prompt("generate_summary/system_prompt.txt")
        task_prompt = load_prompt("generate_summary/task_prompt.txt")
        context_template = load_prompt("generate_summary/context_prompt.txt")
        context_prompt = context_template.format(
            title=project["title"],
            description=project["description"],
            department=project["department"],
            status=project["status"],
            publications=", ".join(pub_titles) if pub_titles else "None yet",
        )

        final_prompt = f"""
{task_prompt}

{context_prompt}
"""

        answer = create_chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt},
            ],
            max_tokens=300,
            temperature=0.2,
            model=OLLAMA_MODEL,
        )

        database_api.create_ai_analysis({
            "projectID": project_id,
            "generatedSummary": answer.strip(),
        })

        return f"<p>{answer}</p>", 200
    except Exception as exc:
        return (
            "<p>AI summary request failed. "
            "Check that Ollama is running and the model is installed.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@ai_mode_html_bp.post("/projects/<int:project_id>/match_staff")
@ai_mode_html_bp.post("/projects/<int:project_id>/match-staff")
def match_staff_html(project_id):
    """
    Explains why staff ALREADY assigned to this project suit it.
    For actually searching all staff and recommending new candidates
    based on expertise, see recommend_staff_html below.
    """
    project = database_api.get_project(project_id)
    if project is None:
        return "<p>Project not found.</p>", 404

    staff_links = database_api.list_project_staff(project_id=project_id)
    if not staff_links:
        return "<p>No staff are linked to this project yet.</p>", 400

    staff_ids = [s["staffID"] for s in staff_links]
    roles = []
    for link in staff_links:
        staff_detail = staff_client.get_staff_by_id(link["staffID"])
        if staff_detail:
            name = staff_detail.get("name") or f"staffID {link['staffID']}"
            label = f"{name} ({link['role']}"
            if staff_detail.get("expertise_area"):
                label += f", expertise: {staff_detail['expertise_area']}"
            label += ")"
        else:
            label = f"staffID {link['staffID']} ({link['role']})"
        roles.append(label)

    try:
        system_prompt = load_prompt("match_staff/system_prompt.txt")
        task_prompt = load_prompt("match_staff/task_prompt.txt")
        context_template = load_prompt("match_staff/context_prompt.txt")
        context_prompt = context_template.format(
            title=project["title"],
            department=project["department"],
            description=project["description"],
            staff_roles=", ".join(roles),
        )

        final_prompt = f"""
{task_prompt}

{context_prompt}
"""

        answer = create_chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt},
            ],
            max_tokens=300,
            temperature=0.2,
            model=OLLAMA_MODEL,
        )

        database_api.create_ai_analysis({
            "projectID": project_id,
            "recommendedStaffMatches": str(staff_ids),
            "matchRationale": answer.strip(),
        })

        return f"<p>{answer}</p>", 200
    except Exception as exc:
        return (
            "<p>AI staff-match request failed. "
            "Check that Ollama is running and the model is installed.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@ai_mode_html_bp.post("/projects/<int:project_id>/recommend_staff")
@ai_mode_html_bp.post("/projects/<int:project_id>/recommend-staff")
def recommend_staff_html(project_id):
    """
    The actual "match staff to research opportunities based on
    expertise" feature from the spec: searches Andy's FULL staff
    roster (not just staff already linked to this project) and asks
    the LLM to recommend the best-fit candidates.
    """
    project = database_api.get_project(project_id)
    if project is None:
        return "<p>Project not found.</p>", 404

    all_staff = staff_client.get_all_staff()
    if not all_staff:
        return (
            "<p>Could not reach the Staff Management service to search "
            "for candidates. Check that it's running.</p>",
            502,
        )

    already_linked = database_api.list_project_staff(project_id=project_id)
    already_assigned_ids = {s["staffID"] for s in already_linked}

    staff_roster_lines = []
    for s in all_staff:
        name = s.get("name") or f"Staff #{s.get('staff_id')}"
        expertise = s.get("expertise_area", "unspecified")
        dept = s.get("department_name", "unspecified")
        staff_roster_lines.append(f"- {name}, expertise: {expertise}, department: {dept}")

    already_assigned_lines = []
    for s in all_staff:
        if s.get("staff_id") in already_assigned_ids:
            name = s.get("name") or f"Staff #{s.get('staff_id')}"
            already_assigned_lines.append(f"- {name}")
    if not already_assigned_lines:
        already_assigned_lines = ["None yet"]

    try:
        system_prompt = load_prompt("recommend_staff/system_prompt.txt")
        task_prompt = load_prompt("recommend_staff/task_prompt.txt")
        context_template = load_prompt("recommend_staff/context_prompt.txt")
        context_prompt = context_template.format(
            title=project["title"],
            department=project["department"],
            description=project["description"],
            staff_roster="\n".join(staff_roster_lines),
            already_assigned="\n".join(already_assigned_lines),
        )

        final_prompt = f"""
{task_prompt}

{context_prompt}
"""

        answer = create_chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt},
            ],
            max_tokens=350,
            temperature=0.2,
            model=OLLAMA_MODEL,
        )

        if not answer:
            return "<p>LLM returned an empty response.</p>", 502

        database_api.create_ai_analysis({
            "projectID": project_id,
            "matchRationale": answer.strip(),
        })

        return f"<p>{answer}</p>", 200
    except Exception as exc:
        return (
            "<p>AI staff-recommendation request failed. "
            "Check that Ollama is running and the model is installed.</p>"
            f"<pre>{exc}</pre>",
            503,
        )