import os

from functools import wraps

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


def _rag_mode_active():
    return (
        os.environ.get(
            "RAG_ENABLED",
            "false",
        ).lower()
        == "true"
    )


def require_rag_mode(
    function,
):
    @wraps(function)
    def wrapper(
        *args,
        **kwargs,
    ):
        if not _rag_mode_active():
            return jsonify(
                {
                    "error":
                        "RAG mode is off. "
                        "The server needs RAG_ENABLED set to true."
                }
            ), 403

        return function(
            *args,
            **kwargs,
        )

    return wrapper


@rag_bp.post(
    "/rag/ask"
)
@require_rag_mode
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
@require_rag_mode
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
@require_rag_mode
def refresh():
    return jsonify(
        rag_refresh()
    )