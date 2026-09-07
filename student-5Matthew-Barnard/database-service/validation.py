from datetime import date
from math import isfinite

from resource_config import RESOURCES

ENUMS = {
    ("performance-reviews", "status"): {
        "Draft", "Scheduled", "Completed", "Acknowledged"
    },
    ("development-goals", "status"): {
        "Planned", "In Progress", "Completed", "On Hold", "Cancelled"
    },
    ("staff-training", "status"): {
        "Enrolled", "In Progress", "Completed", "Withdrawn"
    },
    ("development-recommendations", "recommendationType"): {
        "Training", "Goal", "Mentoring", "Experience"
    },
    ("development-recommendations", "status"): {
        "Pending", "Accepted", "Rejected", "Modified"
    },
}

REQUIRED = {
    "performance-reviews": {"staffID", "reviewDate", "reviewerID", "status"},
    "development-goals": {"staffID", "title", "status"},
    "training-programs": {"title"},
    "staff-training": {"staffID", "trainingID", "status"},
    "development-recommendations": {
        "staffID", "recommendationType", "recommendation", "dateGenerated", "status"
    },
}

INTEGER_FIELDS = {"staffID", "reviewerID", "trainingID", "goalID"}
DATE_FIELDS = {"reviewDate", "targetDate", "startDate", "endDate", "enrolmentDate",
               "completionDate", "dateGenerated"}
TEXT_LIMITS = {
    "title": 160,
    "description": 1000,
    "feedback": 2000,
    "provider": 160,
    "skillArea": 120,
    "recommendation": 2000,
    "rationale": 3000,
}


def _positive_integer(value, field, nullable=False):
    if value in (None, "") and nullable:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if parsed <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return parsed


def _number_in_range(value, field, minimum, maximum):
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number from {minimum} to {maximum}") from exc
    if not isfinite(parsed) or not minimum <= parsed <= maximum:
        raise ValueError(f"{field} must be a number from {minimum} to {maximum}")
    return parsed


def _iso_date(value, field, nullable=True):
    if value in (None, "") and nullable:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def _text(value, field, required=False):
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    parsed = str(value).strip()
    if required and not parsed:
        raise ValueError(f"{field} is required")
    maximum = TEXT_LIMITS.get(field, 300)
    if len(parsed) > maximum:
        raise ValueError(f"{field} must not exceed {maximum} characters")
    return parsed


def validate_payload(resource, payload, partial=False):
    """Normalize one whitelisted resource payload and reject invalid fields early."""
    spec = RESOURCES.get(resource)
    if spec is None:
        raise ValueError("unknown resource")
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")

    allowed = set(spec["fields"])
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")

    if partial:
        if not payload:
            raise ValueError("at least one field must be supplied")
    else:
        missing = REQUIRED[resource] - set(payload)
        if missing:
            raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")

    normalized = {}
    for field, value in payload.items():
        if field in INTEGER_FIELDS:
            normalized[field] = _positive_integer(
                value, field, nullable=(field == "goalID")
            )
        elif field in DATE_FIELDS:
            normalized[field] = _iso_date(
                value,
                field,
                nullable=field not in {"reviewDate", "dateGenerated"},
            )
        elif field == "progress":
            normalized[field] = _number_in_range(value, field, 0, 100)
        elif field == "rating":
            normalized[field] = (
                None if value in (None, "") else _number_in_range(value, field, 1, 5)
            )
        elif (resource, field) in ENUMS:
            parsed = str(value).strip()
            if parsed not in ENUMS[(resource, field)]:
                allowed_values = ", ".join(sorted(ENUMS[(resource, field)]))
                raise ValueError(f"{field} must be one of: {allowed_values}")
            normalized[field] = parsed
        else:
            normalized[field] = _text(
                value,
                field,
                required=field in REQUIRED[resource],
            )

    if resource == "development-goals" and not partial and "progress" not in normalized:
        normalized["progress"] = 0.0

    if resource == "training-programs":
        start = normalized.get("startDate", payload.get("startDate"))
        end = normalized.get("endDate", payload.get("endDate"))
        if start and end and end < start:
            raise ValueError("endDate must be on or after startDate")

    return normalized


def validate_filter(resource, field, value):
    if field in INTEGER_FIELDS:
        return _positive_integer(value, field)
    if (resource, field) in ENUMS:
        parsed = str(value).strip()
        if parsed not in ENUMS[(resource, field)]:
            raise ValueError(f"unknown {field} filter")
        return parsed
    return str(value).strip()
