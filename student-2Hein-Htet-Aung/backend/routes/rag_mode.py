from flask import (
    Blueprint,
    jsonify,
    request,
)

from services.rag_api import (
    rag_ask,
    rag_refresh,
    rag_retrieve,
)


rag_bp = Blueprint(
    "rag_mode",
    __name__,
)


@rag_bp.post(
    "/rag/ask"
)
def ask():
    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    query = str(
        body.get(
            "query",
            "",
        )
    ).strip()

    if not query:
        return jsonify(
            {
                "error":
                    "query is required",
            }
        ), 400

    try:
        k = int(
            body.get(
                "k",
                5,
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return jsonify(
            {
                "error":
                    "k must be an integer",
            }
        ), 400

    if k <= 0:
        return jsonify(
            {
                "error":
                    "k must be greater than zero",
            }
        ), 400

    return jsonify(
        rag_ask(
            query,
            k,
        )
    )


@rag_bp.post(
    "/rag/retrieve"
)
def retrieve():
    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    query = str(
        body.get(
            "query",
            "",
        )
    ).strip()

    if not query:
        return jsonify(
            {
                "error":
                    "query is required",
            }
        ), 400

    try:
        k = int(
            body.get(
                "k",
                5,
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return jsonify(
            {
                "error":
                    "k must be an integer",
            }
        ), 400

    if k <= 0:
        return jsonify(
            {
                "error":
                    "k must be greater than zero",
            }
        ), 400

    return jsonify(
        rag_retrieve(
            query,
            k,
        )
    )


@rag_bp.post(
    "/rag/refresh"
)
def refresh():
    return jsonify(
        rag_refresh()
    )