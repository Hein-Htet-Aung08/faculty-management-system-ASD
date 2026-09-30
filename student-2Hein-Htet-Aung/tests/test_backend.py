import sys
import unittest
from pathlib import Path


BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "backend"
)

sys.path.insert(
    0,
    str(BACKEND_DIR),
)

from services.allocation_rules import (
    check_classroom_capacity,
    parse_date_ranges,
    times_overlap,
    validate_allocation,
)
from views.html_formatters import (
    format_teaching_allocations_html,
)


class AllocationRulesTests(
    unittest.TestCase
):
    def setUp(self):
        self.subject_offer = {
            "offer_id":
                "41114_SPR_2026",
            "subject_code":
                "41114",
            "semester":
                "SPR",
            "year":
                "2026",
            "expected_enrollment":
                120,
        }

        self.classroom = {
            "classroom_id":
                "CB11.04.406",
            "building":
                "CB11",
            "floor":
                "04",
            "room_number":
                "406",
            "capacity":
                30,
            "room_type":
                "Tutorial Room",
            "facilities":
                "Projector,Whiteboard",
        }

        self.data = {
            "offer_id":
                "41114_SPR_2026",
            "assigned_staff_member":
                None,
            "classroom_id":
                "CB11.04.406",
            "day":
                "THU",
            "date_range":
                "03/08 - 20/09",
            "start_time":
                "14:00",
            "end_time":
                "16:00",
            "class_type":
                "TUT",
            "expected_class_size":
                30,
            "allocation_status":
                "NEEDS_ASSIGNMENT",
        }

    def test_classroom_capacity_accepts_equal_size(
        self
    ):
        self.assertTrue(
            check_classroom_capacity(
                self.classroom,
                30,
            )
        )

    def test_classroom_capacity_rejects_oversized_class(
        self
    ):
        self.assertFalse(
            check_classroom_capacity(
                self.classroom,
                31,
            )
        )

    def test_validate_allocation_rejects_oversized_class(
        self
    ):
        self.data[
            "expected_class_size"
        ] = 31

        result = validate_allocation(
            self.data,
            self.subject_offer,
            self.classroom,
            [],
        )

        self.assertFalse(
            result["valid"]
        )

        self.assertIn(
            "Classroom capacity is smaller than the expected class size.",
            result["errors"],
        )

    def test_validate_allocation_accepts_valid_capacity(
        self
    ):
        result = validate_allocation(
            self.data,
            self.subject_offer,
            self.classroom,
            [],
        )

        self.assertTrue(
            result["valid"]
        )

        self.assertEqual(
            result["errors"],
            [],
        )

    def test_date_ranges_parse_valid_range(
        self
    ):
        ranges = parse_date_ranges(
            "03/08 - 20/09",
            "2026",
        )

        self.assertIsNotNone(
            ranges
        )

        self.assertEqual(
            len(ranges),
            1,
        )

    def test_time_overlap_allows_back_to_back_classes(
        self
    ):
        from datetime import time

        self.assertFalse(
            times_overlap(
                time(10, 0),
                time(12, 0),
                time(12, 0),
                time(14, 0),
            )
        )

    def test_allocation_list_contains_date_range_and_size(
        self
    ):
        allocation = {
            "allocation_id":
                4,
            "offer_id":
                "41114_SPR_2026",
            "assigned_staff_member":
                None,
            "classroom_id":
                "CB11.04.406",
            "day":
                "THU",
            "date_range":
                "03/08 - 20/09",
            "start_time":
                "14:00",
            "end_time":
                "16:00",
            "class_type":
                "TUT",
            "expected_class_size":
                30,
            "allocation_status":
                "NEEDS_ASSIGNMENT",
            "staff_name":
                None,
        }

        html = (
            format_teaching_allocations_html(
                [allocation]
            )
        )

        self.assertIn(
            'data-date-range="03/08 - 20/09"',
            html,
        )

        self.assertIn(
            'data-expected-class-size="30"',
            html,
        )


if __name__ == "__main__":
    unittest.main()