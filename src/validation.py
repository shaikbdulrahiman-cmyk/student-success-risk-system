"""Data-quality checks for generated student records."""
from pathlib import Path
import pandas as pd

def validate_data(data_dir="data"):
    folder = Path(data_dir)
    errors, warnings = [], []
    required = {
        "students": ["student_id"],
        "courses": ["course_id"],
        "enrollments": ["enrollment_id", "student_id", "course_id"],
        "attendance_events": ["attendance_event_id", "enrollment_id"],
        "assessments": ["assessment_id"],
        "assessment_results": ["assessment_result_id", "enrollment_id", "assessment_id"],
        "lms_activity": ["lms_activity_id", "enrollment_id"],
        "support_cases": ["support_case_id", "student_id", "enrollment_id"],
        "interventions": ["intervention_id", "support_case_id"],
        "outcomes": ["outcome_id", "enrollment_id"]
    }
    data = {}
    for table, cols in required.items():
        path = folder / f"{table}.csv"
        if not path.exists():
            errors.append(f"Missing file: {path.name}")
            continue
        df = pd.read_csv(path)
        data[table] = df
        for col in cols:
            if col not in df.columns:
                errors.append(f"{table}: missing column {col}")
        pk = cols[0]
        if pk in df and df[pk].duplicated().any():
            errors.append(f"{table}: duplicate primary key in {pk}")

    def fk(child, col, parent, pk):
        if child not in data or parent not in data:
            return
        invalid = set(data[child][col].dropna()) - set(data[parent][pk].dropna())
        if invalid:
            errors.append(f"{child}.{col}: {len(invalid)} invalid foreign keys")

    fk("enrollments", "student_id", "students", "student_id")
    fk("enrollments", "course_id", "courses", "course_id")
    fk("attendance_events", "enrollment_id", "enrollments", "enrollment_id")
    fk("assessment_results", "enrollment_id", "enrollments", "enrollment_id")
    fk("assessment_results", "assessment_id", "assessments", "assessment_id")
    fk("lms_activity", "enrollment_id", "enrollments", "enrollment_id")
    fk("support_cases", "student_id", "students", "student_id")
    fk("support_cases", "enrollment_id", "enrollments", "enrollment_id")
    fk("interventions", "support_case_id", "support_cases", "support_case_id")
    fk("outcomes", "enrollment_id", "enrollments", "enrollment_id")

    if "attendance_events" in data:
        allowed = {"PRESENT", "APPROVED_ABSENCE", "LATE", "ABSENT"}
        bad = set(data["attendance_events"].status.dropna()) - allowed
        if bad:
            errors.append(f"attendance_events: invalid statuses {bad}")
    if "assessment_results" in data:
        marks = data["assessment_results"].marks_obtained.dropna()
        if ((marks < 0) | (marks > 100)).any():
            errors.append("assessment_results: marks outside 0..100")
        if (data["assessment_results"].result_status == "MISSING").sum() and \
           data["assessment_results"].loc[
               data["assessment_results"].result_status == "MISSING", "marks_obtained"
           ].notna().any():
            warnings.append("Some MISSING results have marks; inspect source.")
    if "enrollments" in data and "students" in data:
        merged = data["enrollments"].merge(
            data["students"][["student_id", "student_status"]], on="student_id", how="left")
        bad = merged[(merged.student_status == "WITHDRAWN") &
                     (merged.enrollment_status == "ACTIVE")]
        if len(bad):
            errors.append(f"{len(bad)} withdrawn students have ACTIVE enrollments")
    if "interventions" in data and "support_cases" in data:
        merged = data["interventions"].merge(
            data["support_cases"][["support_case_id", "opened_date"]],
            on="support_case_id", how="left")
        if (pd.to_datetime(merged.assigned_date) < pd.to_datetime(merged.opened_date)).any():
            errors.append("An intervention is dated before its support case was opened")

    return {"passed": not errors, "errors": errors, "warnings": warnings,
            "tables_checked": len(data),
            "total_rows": sum(len(x) for x in data.values())}

if __name__ == "__main__":
    import json
    print(json.dumps(validate_data(), indent=2))
