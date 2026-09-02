from flask import Blueprint
from services import database_api
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
    project = database_api.get_project(project_id)
    if project is None:
        return "<p>Project not found.</p>", 404

    staff_links = database_api.list_project_staff(project_id=project_id)
    if not staff_links:
        return "<p>No staff are linked to this project yet.</p>", 400

    staff_ids = [s["staffID"] for s in staff_links]
    roles = [f"staffID {s['staffID']} ({s['role']})" for s in staff_links]

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