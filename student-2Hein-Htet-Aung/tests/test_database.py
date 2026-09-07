import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


DATABASE_APP_PATH = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "database"
    / "app.py"
)

spec = (
    importlib.util
    .spec_from_file_location(
        "student2_database_app",
        DATABASE_APP_PATH,
    )
)

database_app = (
    importlib.util
    .module_from_spec(spec)
)

spec.loader.exec_module(
    database_app
)


class DatabaseApiTests(
    unittest.TestCase
):
    def setUp(self):
        self.temp_dir = (
            tempfile
            .TemporaryDirectory()
        )

        self.database_path = (
            os.path.join(
                self.temp_dir.name,
                "allocation.db",
            )
        )

        database_app.DATABASE_NAME = (
            self.database_path
        )

        self.create_schema()

        self.client = (
            database_app.app
            .test_client()
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_schema(self):
        conn = sqlite3.connect(
            self.database_path
        )

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        conn.execute(
            """
            CREATE TABLE subjects (
                subject_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                required_expertise TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE subject_offers (
                offer_id TEXT PRIMARY KEY,
                subject_code TEXT NOT NULL,
                semester TEXT NOT NULL,
                year TEXT NOT NULL,
                expected_enrollment INTEGER NOT NULL,
                FOREIGN KEY (subject_code)
                    REFERENCES subjects(subject_code)
                    ON DELETE RESTRICT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE classrooms (
                classroom_id TEXT PRIMARY KEY,
                building TEXT NOT NULL,
                floor TEXT NOT NULL,
                room_number TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                room_type TEXT NOT NULL,
                facilities TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE teaching_allocations (
                allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_id TEXT NOT NULL,
                assigned_staff_member INTEGER,
                classroom_id TEXT NOT NULL,
                day TEXT NOT NULL,
                date_range TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                class_type TEXT NOT NULL,
                expected_class_size INTEGER NOT NULL,
                allocation_status TEXT NOT NULL,
                FOREIGN KEY (offer_id)
                    REFERENCES subject_offers(offer_id)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,
                FOREIGN KEY (classroom_id)
                    REFERENCES classrooms(classroom_id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
            """
        )

        conn.execute(
            """
            INSERT INTO subjects
            VALUES (?, ?, ?)
            """,
            (
                "41114",
                "Advanced Software Development",
                "Software Engineering,DevOps,Agentic AI",
            ),
        )

        conn.execute(
            """
            INSERT INTO subject_offers
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "41114_SPR_2026",
                "41114",
                "SPR",
                "2026",
                120,
            ),
        )

        conn.execute(
            """
            INSERT INTO classrooms
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "CB11.04.406",
                "CB11",
                "04",
                "406",
                30,
                "Tutorial Room",
                "Projector,Whiteboard",
            ),
        )

        conn.commit()
        conn.close()

    def allocation_payload(self):
        return {
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

    def test_create_and_get_teaching_allocation(
        self
    ):
        create_response = (
            self.client.post(
                "/teaching-allocations",
                json=
                    self.allocation_payload(),
            )
        )

        self.assertEqual(
            create_response.status_code,
            201,
        )

        allocation_id = (
            create_response
            .get_json()[
                "allocation_id"
            ]
        )

        get_response = (
            self.client.get(
                f"/teaching-allocations/{allocation_id}"
            )
        )

        self.assertEqual(
            get_response.status_code,
            200,
        )

        allocation = (
            get_response.get_json()
        )

        self.assertEqual(
            allocation[
                "expected_class_size"
            ],
            30,
        )

        self.assertEqual(
            allocation[
                "allocation_status"
            ],
            "NEEDS_ASSIGNMENT",
        )

    def test_update_teaching_allocation(
        self
    ):
        create_response = (
            self.client.post(
                "/teaching-allocations",
                json=
                    self.allocation_payload(),
            )
        )

        allocation_id = (
            create_response
            .get_json()[
                "allocation_id"
            ]
        )

        payload = (
            self.allocation_payload()
        )

        payload[
            "expected_class_size"
        ] = 25

        update_response = (
            self.client.put(
                f"/teaching-allocations/{allocation_id}",
                json=payload,
            )
        )

        self.assertEqual(
            update_response.status_code,
            200,
        )

        get_response = (
            self.client.get(
                f"/teaching-allocations/{allocation_id}"
            )
        )

        self.assertEqual(
            get_response
            .get_json()[
                "expected_class_size"
            ],
            25,
        )

    def test_delete_teaching_allocation(
        self
    ):
        create_response = (
            self.client.post(
                "/teaching-allocations",
                json=
                    self.allocation_payload(),
            )
        )

        allocation_id = (
            create_response
            .get_json()[
                "allocation_id"
            ]
        )

        delete_response = (
            self.client.delete(
                f"/teaching-allocations/{allocation_id}"
            )
        )

        self.assertEqual(
            delete_response.status_code,
            200,
        )

        get_response = (
            self.client.get(
                f"/teaching-allocations/{allocation_id}"
            )
        )

        self.assertEqual(
            get_response.status_code,
            404,
        )

    def test_unassigned_staff_forces_needs_assignment(
        self
    ):
        payload = (
            self.allocation_payload()
        )

        payload[
            "allocation_status"
        ] = "CONFIRMED"

        create_response = (
            self.client.post(
                "/teaching-allocations",
                json=payload,
            )
        )

        allocation_id = (
            create_response
            .get_json()[
                "allocation_id"
            ]
        )

        get_response = (
            self.client.get(
                f"/teaching-allocations/{allocation_id}"
            )
        )

        self.assertEqual(
            get_response
            .get_json()[
                "allocation_status"
            ],
            "NEEDS_ASSIGNMENT",
        )


if __name__ == "__main__":
    unittest.main()