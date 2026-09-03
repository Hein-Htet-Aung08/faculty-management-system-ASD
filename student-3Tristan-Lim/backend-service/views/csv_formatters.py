import csv
import io


def _write(headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


def records_to_csv(records, columns=None):
    """Straight dump of database rows, column order taken from the first record."""
    if not records:
        # Without a record there are no column names to infer, so emit an empty
        # file rather than a stray blank line.
        return _write(columns, []) if columns else ""

    columns = columns or list(records[0].keys())
    rows = [[record.get(column, "") for column in columns] for record in records]
    return _write(columns, rows)


def analysis_to_csv(results):
    """Computed workload figures rather than stored ones."""
    headers = [
        "staff_id", "staff_name", "department", "computed_hours", "recorded_hours",
        "drift", "cap", "warning_threshold", "underload_floor", "headroom",
        "status", "clash_count",
    ]
    rows = [
        [
            result["staff_id"], result["staff_name"], result["department"],
            result["computed_hours"], result["recorded_hours"], result["drift"],
            result["cap"], result["warning_threshold"], result["underload_floor"],
            result["headroom"], result["status"], len(result["clashes"]),
        ]
        for result in sorted(results, key=lambda r: r["staff_id"])
    ]
    return _write(headers, rows)


def clashes_to_csv(results):
    headers = ["staff_id", "staff_name", "kind", "detail"]
    rows = [
        [result["staff_id"], result["staff_name"], clash["kind"], clash["detail"]]
        for result in sorted(results, key=lambda r: r["staff_id"])
        for clash in result["clashes"]
    ]
    return _write(headers, rows)
