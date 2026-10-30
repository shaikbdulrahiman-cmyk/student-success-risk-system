"""Deterministic synthetic data generator for the student-risk challenge."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

SEED_DEFAULT = 20261022
ACADEMIC_YEAR = "2026-2027"

def generate_data(scale="starter", output_dir="data", seed=SEED_DEFAULT):
    """Generate linked CSV files. 'starter' is quick; 'full' matches the brief."""
    n_students, n_courses, n_enrollments = (
        (250, 30, 800) if scale == "starter" else (5000, 200, 20000)
    )
    rng = np.random.default_rng(seed)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Parent/master entities
    first_names = np.array(["Aarav", "Diya", "Ishaan", "Meera", "Kabir", "Anaya",
                            "Rohan", "Sara", "Arjun", "Nisha", "Vihaan", "Tara"])
    last_names = np.array(["Sharma", "Reddy", "Khan", "Patel", "Rao", "Das",
                           "Singh", "Gupta", "Iyer", "Verma"])
    students = pd.DataFrame({
        "student_id": [f"STU-2026-{i:06d}" for i in range(1, n_students + 1)],
        "first_name": rng.choice(first_names, n_students),
        "last_name": rng.choice(last_names, n_students),
        "program": rng.choice(["ECE", "CSE", "EEE", "ME", "CE"], n_students),
        "year_of_study": rng.integers(1, 5, n_students),
        "admission_date": pd.to_datetime("2023-06-01") + pd.to_timedelta(
            rng.integers(0, 900, n_students), unit="D"),
        "student_status": rng.choice(["ACTIVE", "ACTIVE", "ACTIVE", "TRANSFERRED", "WITHDRAWN"],
                                     n_students, p=[.78, .08, .06, .04, .04])
    })
    courses = pd.DataFrame({
        "course_id": [f"CRS-{i:06d}" for i in range(1, n_courses + 1)],
        "course_name": [f"Course {i:03d}" for i in range(1, n_courses + 1)],
        "department": rng.choice(["ECE", "CSE", "EEE", "ME", "CE"], n_courses),
        "credits": rng.choice([2, 3, 4], n_courses),
        "semester": rng.choice(["ODD", "EVEN"], n_courses)
    })

    # Enrollments link students to courses (many-to-many relationship).
    student_idx = rng.integers(0, n_students, n_enrollments)
    course_idx = rng.integers(0, n_courses, n_enrollments)
    enrollments = pd.DataFrame({
        "enrollment_id": [f"ENR-{s+1:06d}-{c+1:04d}" for s, c in zip(student_idx, np.arange(n_enrollments))],
        "student_id": students.loc[student_idx, "student_id"].to_numpy(),
        "course_id": courses.loc[course_idx, "course_id"].to_numpy(),
        "academic_year": ACADEMIC_YEAR,
        "start_date": pd.Timestamp("2026-07-01"),
        "end_date": pd.Timestamp("2027-04-30"),
        "enrollment_status": "ACTIVE"
    })
    # Explicit lifecycle exception: withdrawn students must not remain active.
    withdrawn_ids = set(students.loc[students.student_status == "WITHDRAWN", "student_id"])
    withdrawn_mask = enrollments.student_id.isin(withdrawn_ids)
    enrollments.loc[withdrawn_mask, "enrollment_status"] = "WITHDRAWN"

    # 2. Attendance events: 30 teaching weeks per enrollment.
    n_weeks = 30
    enr_idx = np.repeat(np.arange(n_enrollments), n_weeks)
    week = np.tile(np.arange(1, n_weeks + 1), n_enrollments)
    latent = rng.beta(2.2, 2.0, n_enrollments)  # student/course difficulty signal
    p_present = np.clip(.94 - latent[enr_idx] * .42, .35, .96)
    draw = rng.random(len(enr_idx))
    status = np.where(draw < p_present, "PRESENT",
             np.where(draw < p_present + .035, "APPROVED_ABSENCE",
             np.where(draw < p_present + .035 + .025, "LATE", "ABSENT")))
    attendance = pd.DataFrame({
        "attendance_event_id": [f"ATT-{i+1:09d}" for i in range(len(enr_idx))],
        "enrollment_id": enrollments.enrollment_id.to_numpy()[enr_idx],
        "event_date": pd.Timestamp("2026-07-06") + pd.to_timedelta((week-1)*7, unit="D"),
        "week_number": week,
        "status": status,
        "is_countable": True
    })
    # Approved absences are excluded from the attendance denominator.
    attendance.loc[attendance.status == "APPROVED_ABSENCE", "is_countable"] = False

    # 3. Assessments and results: four assessments per enrollment.
    assess_rows = []
    result_rows = []
    assess_types = ["QUIZ", "ASSIGNMENT", "MIDTERM", "PROJECT"]
    for j, typ in enumerate(assess_types, start=1):
        aid = f"ASM-{j:03d}"
        assess_rows.append({"assessment_id": aid, "course_id": None,
                            "assessment_name": typ.title(), "assessment_type": typ,
                            "max_marks": 100, "week_number": [5, 10, 16, 25][j-1]})
        marks = np.clip(88 - latent * 55 + rng.normal(0, 12, n_enrollments), 0, 100)
        result_rows.append(pd.DataFrame({
            "assessment_result_id": [f"ARS-{j:03d}-{i+1:06d}" for i in range(n_enrollments)],
            "enrollment_id": enrollments.enrollment_id,
            "assessment_id": aid,
            "marks_obtained": marks.round(1),
            "max_marks": 100,
            "result_status": np.where(rng.random(n_enrollments) < .025, "MISSING", "SUBMITTED")
        }))
    assessments = pd.DataFrame(assess_rows)
    assessment_results = pd.concat(result_rows, ignore_index=True)
    missing_mask = assessment_results.result_status == "MISSING"
    assessment_results.loc[missing_mask, "marks_obtained"] = np.nan

    # 4. LMS activity, with timestamps and event types.
    per_enr = 8
    lms_enr_idx = np.repeat(np.arange(n_enrollments), per_enr)
    lms_seq = np.tile(np.arange(per_enr), n_enrollments)
    lms_week = rng.integers(1, 25, len(lms_enr_idx))
    lms = pd.DataFrame({
        "lms_activity_id": [f"LMS-{i+1:09d}" for i in range(len(lms_enr_idx))],
        "enrollment_id": enrollments.enrollment_id.to_numpy()[lms_enr_idx],
        "activity_timestamp": pd.Timestamp("2026-07-01") + pd.to_timedelta(lms_week*7 + lms_seq, unit="D"),
        "activity_type": rng.choice(["LOGIN", "CONTENT_VIEW", "ASSIGNMENT_VIEW", "FORUM_POST"],
                                    len(lms_enr_idx), p=[.35, .35, .2, .1]),
        "duration_minutes": rng.integers(1, 91, len(lms_enr_idx))
    })

    # 5. Build early risk indicators using information available by week 20 only.
    early_att = attendance[attendance.week_number <= 20].copy()
    early_att["present_value"] = early_att.status.isin(["PRESENT", "LATE"]).astype(int)
    att_agg = early_att.groupby("enrollment_id").agg(
        present_count=("present_value", "sum"),
        eligible_count=("is_countable", "sum")
    )
    att_pct = (100 * att_agg.present_count / att_agg.eligible_count.replace(0, np.nan)).fillna(0)

    early_results = assessment_results.merge(assessments[["assessment_id", "week_number"]], on="assessment_id")
    early_results = early_results[early_results.week_number <= 20]
    grade_pct = early_results.groupby("enrollment_id").marks_obtained.mean().reindex(
        enrollments.enrollment_id).fillna(50)

    early_lms = lms[pd.to_datetime(lms.activity_timestamp) <= pd.Timestamp("2026-11-30")]
    lms_count = early_lms.groupby("enrollment_id").size().reindex(enrollments.enrollment_id).fillna(0)

    attendance_risk = 100 - att_pct.reindex(enrollments.enrollment_id).to_numpy()
    grade_risk = 100 - grade_pct.to_numpy()
    engagement_risk = np.clip(100 - lms_count.to_numpy() * 4, 0, 100)
    support_history_risk = rng.choice([0, 25, 50, 75], n_enrollments, p=[.55, .25, .15, .05])
    risk_score = (.40*attendance_risk + .35*grade_risk +
                  .15*engagement_risk + .10*support_history_risk).round(2)
    risk_level = np.where(risk_score >= 60, "HIGH",
                 np.where(risk_score >= 30, "MEDIUM", "LOW"))

    # 6. Support cases and interventions are created after the risk snapshot.
    support_mask = risk_level != "LOW"
    support_idx = np.where(support_mask)[0]
    support_cases = pd.DataFrame({
        "support_case_id": [f"SUP-{i+1:06d}" for i in range(len(support_idx))],
        "student_id": enrollments.student_id.to_numpy()[support_idx],
        "enrollment_id": enrollments.enrollment_id.to_numpy()[support_idx],
        "opened_date": pd.Timestamp("2026-12-01"),
        "issue_type": np.where(risk_level[support_idx] == "HIGH", "ACADEMIC_RISK", "ENGAGEMENT"),
        "priority": risk_level[support_idx],
        "case_status": rng.choice(["OPEN", "IN_PROGRESS", "CLOSED"], len(support_idx),
                                  p=[.35, .4, .25])
    })
    interventions = pd.DataFrame({
        "intervention_id": [f"INT-2026-{i+1:06d}" for i in range(len(support_idx))],
        "support_case_id": support_cases.support_case_id,
        "intervention_type": rng.choice(["MENTOR_MEETING", "TUTORING", "PARENT_CONTACT",
                                         "STUDY_PLAN"], len(support_idx)),
        "assigned_date": pd.Timestamp("2026-12-03"),
        "due_date": pd.Timestamp("2026-12-17"),
        "intervention_status": rng.choice(["ASSIGNED", "COMPLETED", "CANCELLED"],
                                          len(support_idx), p=[.4, .5, .1])
    })

    # 7. Future outcomes are kept separate from risk input features.
    outcome_success_prob = np.clip(.95 - risk_score/125, .08, .9)
    success = rng.random(n_enrollments) < outcome_success_prob
    outcomes = pd.DataFrame({
        "outcome_id": [f"OUT-{i+1:06d}" for i in range(n_enrollments)],
        "enrollment_id": enrollments.enrollment_id,
        "outcome_date": pd.Timestamp("2027-04-30"),
        "outcome_label": np.where(success, "SUCCESS", "AT_RISK"),
        "final_grade": np.clip(100 - risk_score*.65 + rng.normal(0, 10, n_enrollments),
                               0, 100).round(1)
    })

    # 8. Deliberately labelled anomaly cases. Do not silently corrupt source records.
    ground_truth = pd.DataFrame([
        {"anomaly_id": "ANOM-001", "issue_type": "FUTURE_GRADE_LEAKAGE",
         "entity_id": "OUT-000001", "ground_truth": "A risk model must not use final_grade."},
        {"anomaly_id": "ANOM-002", "issue_type": "WRONG_ATTENDANCE_DENOMINATOR",
         "entity_id": "ATTENDANCE", "ground_truth": "Approved absences are not countable."},
        {"anomaly_id": "ANOM-003", "issue_type": "WITHDRAWN_STUDENT_ACTIVE",
         "entity_id": "ENROLLMENT", "ground_truth": "Withdrawn students must not remain active."},
        {"anomaly_id": "ANOM-004", "issue_type": "INTERVENTION_BEFORE_TRIGGER",
         "entity_id": "INTERVENTION", "ground_truth": "Intervention date must not precede case opening."},
        {"anomaly_id": "ANOM-005", "issue_type": "MISSING_DATA_AS_FAILURE",
         "entity_id": "ASSESSMENT_RESULT", "ground_truth": "Missing marks must remain missing, not become zero."}
    ])

    tables = {
        "students": students, "courses": courses, "enrollments": enrollments,
        "attendance_events": attendance, "assessments": assessments,
        "assessment_results": assessment_results, "lms_activity": lms,
        "support_cases": support_cases, "interventions": interventions,
        "outcomes": outcomes, "ground_truth": ground_truth
    }
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False)

    # Risk snapshot is a model output; it contains no future outcome fields.
    risk_snapshot = pd.DataFrame({
        "enrollment_id": enrollments.enrollment_id,
        "student_id": enrollments.student_id,
        "attendance_pct_as_of_week20": np.round(att_pct.reindex(enrollments.enrollment_id).to_numpy(), 2),
        "average_marks_as_of_week20": np.round(grade_pct.to_numpy(), 2),
        "lms_events_as_of_cutoff": lms_count.to_numpy(),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "prediction_cutoff": "2026-11-30"
    })
    risk_snapshot.to_csv(out / "risk_snapshot.csv", index=False)

    print(f"Generated {scale} dataset in: {out.resolve()}")
    for name, frame in tables.items():
        print(f"{name:22s} {len(frame):>9,} rows")
    return tables

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--output", default="data")
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = parser.parse_args()
    generate_data(args.scale, args.output, args.seed)
