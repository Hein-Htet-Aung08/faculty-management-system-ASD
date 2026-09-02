def format_subjects_html(subjects):
    if not subjects:
        return "<p>No subjects found.</p>"

    html = "<ul>"
    for subject in subjects:
        html += (
            f"<li>{subject['subject_code']} - "
            f"{subject['name']} - "
            f"{subject['required_expertise']}</li>"
        )
    html += "</ul>"
    return html


def format_subject_html(subject):
    return (
        f"<p>Subject Code: {subject['subject_code']}<br>"
        f"Name: {subject['name']}<br>"
        f"Required Expertise: {subject['required_expertise']}</p>"
    )


def format_subject_offers_html(offers):
    if not offers:
        return "<p>No subject offers found.</p>"

    html = "<ul>"
    for offer in offers:
        html += (
            f"<li>{offer['offer_id']} - "
            f"{offer['subject_code']} - "
            f"{offer['semester']} {offer['year']} - "
            f"Expected Enrolment: {offer['expected_enrollment']}</li>"
        )
    html += "</ul>"
    return html


def format_subject_offer_html(offer):
    return (
        f"<p>Offer ID: {offer['offer_id']}<br>"
        f"Subject Code: {offer['subject_code']}<br>"
        f"Semester: {offer['semester']}<br>"
        f"Year: {offer['year']}<br>"
        f"Expected Enrolment: {offer['expected_enrollment']}</p>"
    )


def format_classrooms_html(classrooms):
    if not classrooms:
        return "<p>No classrooms found.</p>"

    html = "<ul>"
    for classroom in classrooms:
        html += (
            f"<li>{classroom['classroom_id']} - "
            f"{classroom['room_type']} - "
            f"Capacity: {classroom['capacity']} - "
            f"{classroom['facilities']}</li>"
        )
    html += "</ul>"
    return html


def format_classroom_html(classroom):
    return (
        f"<p>Classroom ID: {classroom['classroom_id']}<br>"
        f"Building: {classroom['building']}<br>"
        f"Floor: {classroom['floor']}<br>"
        f"Room Number: {classroom['room_number']}<br>"
        f"Capacity: {classroom['capacity']}<br>"
        f"Room Type: {classroom['room_type']}<br>"
        f"Facilities: {classroom['facilities']}</p>"
    )


def format_teaching_allocations_html(allocations):
    if not allocations:
        return "<p>No teaching allocations found.</p>"

    html = "<ul>"
    for allocation in allocations:
        staff = allocation["assigned_staff_member"]

        if staff is None:
            staff_display = "Unassigned"
        else:
            staff_display = f"Staff {staff}"

        html += (
            f"<li>{allocation['allocation_id']} - "
            f"{allocation['offer_id']} - "
            f"{staff_display} - "
            f"{allocation['classroom_id']} - "
            f"{allocation['day']} "
            f"{allocation['start_time']}-{allocation['end_time']} - "
            f"{allocation['class_type']} - "
            f"{allocation['allocation_status']}</li>"
        )

    html += "</ul>"
    return html


def format_teaching_allocation_html(allocation):
    staff_name = allocation.get("staff_name")

    if allocation["assigned_staff_member"] is None:
        staff_display = "Unassigned"
    elif staff_name == "Unavailable":
        staff_display = "Staff details unavailable"
    else:
        staff_display = staff_name

    return (
        f"<p>Allocation ID: {allocation['allocation_id']}<br>"
        f"Offer ID: {allocation['offer_id']}<br>"
        f"Assigned Staff Member: {staff_display}<br>"
        f"Classroom ID: {allocation['classroom_id']}<br>"
        f"Day: {allocation['day']}<br>"
        f"Date Range: {allocation['date_range']}<br>"
        f"Start Time: {allocation['start_time']}<br>"
        f"End Time: {allocation['end_time']}<br>"
        f"Class Type: {allocation['class_type']}<br>"
        f"Expected Class Size: {allocation['expected_class_size']}<br>"
        f"Allocation Status: {allocation['allocation_status']}</p>"
    )