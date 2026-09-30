import os
import requests

WORKLOAD_SERVICE_URL = os.environ.get("WORKLOAD_SERVICE_URL", "http://localhost:5003")

#calls tristan's workload and availability to recommend a staff memeber for a research opportunity
def get_workload_profile(staff_id):
    try:
        response = requests.get(
            f"{WORKLOAD_SERVICE_URL}/profiles/{staff_id}/json", timeout=5
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return data.get("profile")
    except requests.exceptions.RequestException:
        return None