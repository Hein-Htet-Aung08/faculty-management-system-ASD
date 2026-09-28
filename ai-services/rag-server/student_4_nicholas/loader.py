import os

import requests

DATABASE_SERVICE_URL = os.environ.get("STUDENT4_DATABASE_SERVICE_URL", "http://localhost:5104")
STAFF_SERVICE_URL = os.environ.get("STAFF_SERVICE_URL", "http://localhost:5001")


def _staff_name_resolver():
    cache = {}

    def resolve(staff_id):
        if staff_id is None:
            return "unassigned"
        if staff_id in cache:
            return cache[staff_id]
        display = f"staff ID {staff_id} (name unavailable)"
        try:
            response = requests.get(f"{STAFF_SERVICE_URL}/api/staff/{staff_id}", timeout=3)
            if response.status_code == 200:
                name = response.json().get("name")
                if name:
                    display = f"{name} (staff ID {staff_id})"
        except requests.RequestException:
            pass
        cache[staff_id] = display
        return display

    return resolve


def load_research_chunks():
    chunks = []
    try:
        projects = requests.get(f"{DATABASE_SERVICE_URL}/projects", timeout=5).json()
        grants = requests.get(f"{DATABASE_SERVICE_URL}/grants", timeout=5).json()
        publications = requests.get(f"{DATABASE_SERVICE_URL}/publications", timeout=5).json()
    except requests.RequestException as exc:
        print(f"[student_4_nicholas.loader] database-service unreachable: {exc}")
        return chunks

    resolve_staff = _staff_name_resolver()
    project_titles = {p.get("projectID"): p.get("title", "untitled") for p in projects}

    for p in projects:
        lead_id = p.get("leadStaffID")
        lead_display = resolve_staff(lead_id) if lead_id is not None else "unassigned"
        text = (
            f"Research Project: {p.get('title')}. "
            f"Department: {p.get('department')}. "
            f"Status: {p.get('status')}. "
            f"Lead staff: {lead_display}. "
            f"Start date: {p.get('startDate', 'unspecified')}. "
            f"End date: {p.get('endDate', 'ongoing')}. "
            f"Description: {p.get('description', 'no description provided')}."
        )
        chunks.append(
            {"id": f"project-{p.get('projectID')}", "text": text, "tier": "tier_1", "source": "ResearchProjects"}
        )

    for g in grants:
        awarded = g.get("amountAwarded")
        project_id = g.get("projectID")
        project_title = project_titles.get(project_id, "unknown project")
        text = (
            f"Grant from {g.get('fundingBody')} for project {project_id} "
            f"({project_title}). "
            f"Amount requested: {g.get('amountRequested')}. "
            f"Amount awarded: {awarded if awarded is not None else 'not yet awarded'}. "
            f"Application deadline: {g.get('applicationDeadline')}. "
            f"Status: {g.get('status')}."
        )
        chunks.append({"id": f"grant-{g.get('grantID')}", "text": text, "tier": "tier_1", "source": "Grants"})

    for pub in publications:
        staff_id = pub.get("staffID")
        staff_display = resolve_staff(staff_id) if staff_id is not None else "unspecified"
        project_id = pub.get("projectID")
        project_title = project_titles.get(project_id, "unknown project")
        text = (
            f"Publication: {pub.get('title')}. "
            f"Linked project: {project_title} (project ID {project_id}). "
            f"Type: {pub.get('publicationType')}. "
            f"Journal/venue: {pub.get('journalOrVenue', 'unspecified')}. "
            f"Date published: {pub.get('datePublished', 'unpublished/pending')}. "
            f"Staff: {staff_display}."
        )
        chunks.append(
            {"id": f"publication-{pub.get('publicationID')}", "text": text, "tier": "tier_1", "source": "Publications"}
        )

    chunks.append(
        {
            "id": "summary-counts",
            "text": (
                f"This research and grant management system currently tracks "
                f"{len(projects)} research project(s), {len(grants)} grant(s), "
                f"and {len(publications)} publication(s)."
            ),
            "tier": "tier_1",
            "source": "summary",
        }
    )

    return chunks
