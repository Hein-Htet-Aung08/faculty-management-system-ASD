import requests

from flask import (
    Blueprint,
    jsonify,
)

from services.database_api import (
    get_subjects,
    get_subject_offers,
    get_classrooms,
    get_teaching_allocations,
)


rag_source_bp = Blueprint(
    "rag_source",
    __name__,
)


@rag_source_bp.get(
    "/api/rag/context"
)
def get_rag_context():
    """
    Return Student 2 feature data as structured JSON for the
    shared RAG service.

    This endpoint is read-only. It exposes feature data through
    the Student 2 backend instead of allowing the shared RAG
    service to access the Student 2 database directly.
    """

    try:
        return jsonify(
            {
                "subjects":
                    get_subjects(),

                "subject_offers":
                    get_subject_offers(),

                "classrooms":
                    get_classrooms(),

                "teaching_allocations":
                    get_teaching_allocations(),
            }
        ), 200

    except requests.RequestException as exc:
        return jsonify(
            {
                "error":
                    "Unable to load Student 2 RAG context.",

                "details":
                    str(exc),
            }
        ), 503