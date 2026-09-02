"""
Student 4: Nicholas Hatzidimitriou
Feature: Research and Grant Management

Client for calling Student 1 (Andy)'s Staff Management service.
Used to enrich AI prompts with real staff names/details instead of
bare staffID numbers.
"""

import os
import requests

STAFF_SERVICE_URL = os.environ.get("STAFF_SERVICE_URL", "http://localhost:5001")


def get_staff_by_id(staff_id):
    """
    Fetches one staff member's details from Andy's service.
    Returns None if unreachable or not found, so callers can fall
    back gracefully instead of crashing the whole request.
    """
    try:
        response = requests.get(f"{STAFF_SERVICE_URL}/api/staff/{staff_id}", timeout=5)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_all_staff():
    """
    Fetches the full staff roster from Andy's service, including
    each person's expertise_area (per his /api/staff response shape).
    Returns an empty list if his service is unreachable, so callers
    can fall back gracefully instead of crashing.
    """
    try:
        response = requests.get(f"{STAFF_SERVICE_URL}/api/staff", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []