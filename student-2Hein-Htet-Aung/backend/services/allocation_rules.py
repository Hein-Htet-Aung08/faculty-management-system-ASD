from datetime import datetime, timedelta


VALID_DAYS = {"MON", "TUE", "WED", "THU", "FRI"}

VALID_CLASS_TYPES = {
    "BCP",
    "BRK",
    "CNR",
    "CMP",
    "DRP",
    "INT",
    "LAB",
    "LDT",
    "LEC",
    "PRC",
    "SEM",
    "STU",
    "TUT",
    "UPS",
    "WRK",
}

VALID_STATUSES = {
    "PENDING",
    "CONFIRMED",
    "NEEDS_ASSIGNMENT",
    "CANCELLED",
}


def parse_time(value):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def parse_date(value, year):
    try:
        return datetime.strptime(
            f"{value}/{year}",
            "%d/%m/%Y",
        ).date()
    except (TypeError, ValueError):
        return None


def parse_date_ranges(value, year):
    if not isinstance(value, str) or not value:
        return None

    if ", " in value or " ," in value:
        return None

    parts = value.split(",")

    if any(not part.strip() for part in parts):
        return None

    ranges = []

    for part in parts:
        pieces = part.split(" - ")

        if len(pieces) != 2:
            return None

        start_date = parse_date(pieces[0], year)
        end_date = parse_date(pieces[1], year)

        if start_date is None or end_date is None:
            return None

        if end_date < start_date:
            return None

        ranges.append((start_date, end_date))

    ranges.sort(key=lambda item: item[0])

    for index in range(1, len(ranges)):
        previous_end = ranges[index - 1][1]
        current_start = ranges[index][0]

        if current_start <= previous_end:
            return None

    return ranges


def date_in_ranges(date_value, ranges):
    for start_date, end_date in ranges:
        if start_date <= date_value <= end_date:
            return True

    return False


def times_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a

def is_staff_available(
    availability_slots,
    requested_day,
    requested_start_time,
    requested_end_time,
):
    start_time = parse_time(requested_start_time)
    end_time = parse_time(requested_end_time)

    if start_time is None or end_time is None:
        return False

    if end_time <= start_time:
        return False

    requested_day = requested_day.strip().upper()

    usable_slots = []

    for slot in availability_slots:
        if slot["day"] != requested_day:
            continue

        slot_start = parse_time(slot["start_time"])
        slot_end = parse_time(slot["end_time"])

        if slot_start is None or slot_end is None:
            continue

        availability = slot["availability"].strip().lower()

        if availability == "unavailable":
            if times_overlap(
                start_time,
                end_time,
                slot_start,
                slot_end,
            ):
                return False

        if availability in {"available", "preferred"}:
            usable_slots.append(
                (slot_start, slot_end)
            )

    for slot_start, slot_end in usable_slots:
        if slot_start <= start_time and end_time <= slot_end:
            return True

    return False

def validate_basic_allocation_fields(data, year=None):
    errors = []

    required_fields = [
        "offer_id",
        "classroom_id",
        "day",
        "date_range",
        "start_time",
        "end_time",
        "class_type",
        "expected_class_size",
    ]

    for field in required_fields:
        value = data.get(field)

        if value is None or value == "":
            errors.append(f"{field} is required.")

    if errors:
        return errors

    day = str(data["day"]).strip().upper()

    if day not in VALID_DAYS:
        errors.append("Day must be MON, TUE, WED, THU or FRI.")

    if year is not None:
        date_ranges = parse_date_ranges(
            data["date_range"],
            year,
        )

        if date_ranges is None:
            errors.append(
                "Date range must use DD/MM - DD/MM format with no spaces around commas."
            )

    class_type = str(data["class_type"]).strip().upper()

    if class_type not in VALID_CLASS_TYPES:
        errors.append("Class type is invalid.")

    date_ranges = parse_date_ranges(data["date_range"], year,)

    if date_ranges is None:
        errors.append(
            "Date range must use DD/MM - DD/MM format with no spaces around commas."
        )

    start_time = parse_time(data["start_time"])
    end_time = parse_time(data["end_time"])

    if start_time is None:
        errors.append("Start time must use HH:MM format.")

    if end_time is None:
        errors.append("End time must use HH:MM format.")

    if start_time is not None and end_time is not None:
        if end_time <= start_time:
            errors.append("End time must be later than start time.")

    expected_class_size = data.get("expected_class_size")

    if isinstance(expected_class_size, bool):
        errors.append("Expected class size must be a positive integer.")
    else:
        try:
            expected_class_size = int(expected_class_size)

            if expected_class_size <= 0:
                errors.append("Expected class size must be greater than zero.")
        except (TypeError, ValueError):
            errors.append("Expected class size must be a positive integer.")

    status = data.get("allocation_status")

    if status is not None:
        status = str(status).strip().upper()

        if status not in VALID_STATUSES:
            errors.append("Allocation status is invalid.")

    staff_id = data.get("assigned_staff_member")

    if staff_id is not None:
        if isinstance(staff_id, bool):
            errors.append("Assigned staff member must be a valid integer.")
        else:
            try:
                staff_id = int(staff_id)

                if staff_id <= 0:
                    errors.append("Assigned staff member must be a valid integer.")
            except (TypeError, ValueError):
                errors.append("Assigned staff member must be a valid integer.")

    return errors


def check_classroom_capacity(classroom, expected_class_size):
    try:
        expected_class_size = int(expected_class_size)
        capacity = int(classroom["capacity"])
    except (TypeError, ValueError, KeyError):
        return False

    return capacity >= expected_class_size


def is_classroom_available(
    classroom_id,
    requested_date,
    year,
    requested_start_time,
    requested_end_time,
    allocations,
    exclude_allocation_id=None,
):
    date_value = parse_date(requested_date, year)
    start_time = parse_time(requested_start_time)
    end_time = parse_time(requested_end_time)

    if date_value is None or start_time is None or end_time is None:
        return {
            "available": False,
            "error": "Invalid date or time.",
        }

    if end_time <= start_time:
        return {
            "available": False,
            "error": "End time must be later than start time.",
        }

    weekday = date_value.strftime("%a").upper()

    for allocation in allocations:
        if exclude_allocation_id is not None:
            if allocation["allocation_id"] == exclude_allocation_id:
                continue

        if allocation["allocation_status"] == "CANCELLED":
            continue

        if allocation["classroom_id"] != classroom_id:
            continue

        if allocation["day"] != weekday:
            continue

        ranges = parse_date_ranges(allocation["date_range"], year)

        if ranges is None:
            continue

        if not date_in_ranges(date_value, ranges):
            continue

        allocation_start = parse_time(allocation["start_time"])
        allocation_end = parse_time(allocation["end_time"])

        if allocation_start is None or allocation_end is None:
            continue

        if times_overlap(
            start_time,
            end_time,
            allocation_start,
            allocation_end,
        ):
            return {
                "available": False,
                "conflicting_allocation_id": allocation["allocation_id"],
            }

    return {
        "available": True,
    }


def validate_allocation(
    data,
    subject_offer,
    classroom,
    allocations,
    staff=None,
    staff_checked=False,
    staff_availability=None,
    exclude_allocation_id=None,
):
    year = None

    if subject_offer is not None:
        year = subject_offer["year"]

    errors = validate_basic_allocation_fields(
        data,
        year=year,
    )

    if errors:
        return {
            "valid": False,
            "errors": errors,
        }

    if subject_offer is None:
        errors.append("Subject offer does not exist.")

    if classroom is None:
        errors.append("Classroom does not exist.")

    if classroom is not None:
        if not check_classroom_capacity(
            classroom,
            data["expected_class_size"],
        ):
            errors.append(
                "Classroom capacity is smaller than the expected class size."
            )

    if classroom is not None:
        year = None

        if subject_offer is not None:
            year = subject_offer["year"]

        errors = validate_basic_allocation_fields(
            data,
            year=year,
        )

        ranges = parse_date_ranges(data["date_range"], year)

        if ranges is not None:
            for start_date, end_date in ranges:
                current_date = start_date

                while current_date <= end_date:
                    if current_date.strftime("%a").upper() == data["day"].strip().upper():
                        availability = is_classroom_available(
                            data["classroom_id"],
                            current_date.strftime("%d/%m"),
                            subject_offer["year"],
                            data["start_time"],
                            data["end_time"],
                            allocations,
                            exclude_allocation_id=exclude_allocation_id,
                        )

                        if not availability["available"]:
                            errors.append(
                                "Classroom is unavailable during one or more requested dates."
                            )
                            break

                    current_date += timedelta(days=1)

                if errors and errors[-1] == (
                    "Classroom is unavailable during one or more requested dates."
                ):
                    break

    if data.get("assigned_staff_member") is not None:
        if staff_checked and staff is None:
            errors.append("Assigned staff member does not exist.")

        elif staff is not None and staff_availability is not None:
            available = is_staff_available(
                staff_availability,
                data["day"],
                data["start_time"],
                data["end_time"],
            )

            if not available:
                errors.append(
                    "Assigned staff member is unavailable during the requested time."
                )
                
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }

