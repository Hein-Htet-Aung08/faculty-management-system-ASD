import os
from html.parser import HTMLParser

import requests


WORKLOAD_SERVICE_URL = os.getenv(
    "WORKLOAD_SERVICE_URL",
    "http://student-3-backend:5003",
)


class HTMLTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = data.strip()

        if value:
            self.parts.append(value)

    def get_text(self):
        return "\n".join(self.parts)


class AvailabilityTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = []
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.current_row = []

        if tag == "td":
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td":
            value = "".join(self.current_cell).strip()
            self.current_row.append(value)
            self.current_cell = []
            self.in_cell = False

        if tag == "tr":
            if self.current_row:
                self.rows.append(self.current_row)

            self.current_row = []


def html_to_text(html):
    parser = HTMLTextParser()
    parser.feed(html)
    return parser.get_text()


def parse_availability_html(html):
    parser = AvailabilityTableParser()
    parser.feed(html)

    slots = []

    for row in parser.rows:
        if len(row) != 7:
            continue

        try:
            slot = {
                "slot_id": int(row[0]),
                "staff_id": int(row[1]),
                "day": row[2].strip().upper(),
                "start_time": row[3].strip(),
                "end_time": row[4].strip(),
                "availability": row[5].strip().lower(),
                "is_recurring": row[6].strip().lower() == "yes",
            }
        except ValueError:
            continue

        slots.append(slot)

    return slots


def get_staff_analysis_response(staff_id):
    return requests.get(
        f"{WORKLOAD_SERVICE_URL}/analysis",
        params={"staff_id": staff_id},
        timeout=5,
    )


def get_staff_availability_response(staff_id):
    return requests.get(
        f"{WORKLOAD_SERVICE_URL}/availability",
        params={"staff_id": staff_id},
        timeout=5,
    )


def get_staff_analysis(staff_id):
    response = get_staff_analysis_response(staff_id)
    response.raise_for_status()

    return {
        "staff_id": staff_id,
        "text": html_to_text(response.text),
    }


def get_staff_availability_slots(staff_id):
    response = get_staff_availability_response(staff_id)
    response.raise_for_status()

    return parse_availability_html(response.text)


def get_staff_workload_context(staff_id):
    analysis = get_staff_analysis(staff_id)
    availability = get_staff_availability_slots(staff_id)

    return {
        "staff_id": staff_id,
        "analysis": analysis["text"],
        "availability": availability,
    }