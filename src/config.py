from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SEED = 20261022

TABLES = [
    "students", "courses", "enrollments", "attendance_events",
    "assessments", "assessment_results", "lms_activity",
    "support_cases", "interventions", "outcomes"
]
