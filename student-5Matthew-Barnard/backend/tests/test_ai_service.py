import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from ai_service import _extract_json, _validate_recommendation


class AiOutputValidationTests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "staffID": 101,
            "developmentGoals": [{"goalID": 3, "title": "Improve leadership"}],
            "availableTrainingPrograms": [
                {"trainingID": 8, "title": "Academic Leadership Essentials"}
            ],
        }

    def test_valid_catalogue_recommendation_becomes_pending_record(self):
        record = _validate_recommendation({
            "goalID": 3,
            "recommendationType": "Training",
            "recommendation": "Complete Academic Leadership Essentials.",
            "rationale": "This supports the existing leadership goal.",
        }, self.context)

        self.assertEqual(record["staffID"], 101)
        self.assertEqual(record["goalID"], 3)
        self.assertEqual(record["status"], "Pending")

    def test_hallucinated_training_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not in the catalogue"):
            _validate_recommendation({
                "goalID": 3,
                "recommendationType": "Training",
                "recommendation": "Complete an invented executive course.",
                "rationale": "This supports the leadership goal.",
            }, self.context)

    def test_goal_from_another_staff_member_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not belong"):
            _validate_recommendation({
                "goalID": 99,
                "recommendationType": "Mentoring",
                "recommendation": "Arrange monthly mentoring.",
                "rationale": "This supports the leadership goal.",
            }, self.context)

    def test_json_can_be_extracted_from_minor_model_wrapping(self):
        result = _extract_json('Response: {"goalID": 3, "recommendationType": "Goal"}')
        self.assertEqual(result["goalID"], 3)


if __name__ == "__main__":
    unittest.main()
