"""Explainable risk calculation using only information available at prediction time."""
import numpy as np
import pandas as pd

def calculate_risk(attendance_pct, average_marks, lms_events, support_history_score=0):
    """Return risk score 0..100 and level. Missing values are not treated as failure."""
    # Missing data is handled neutrally and flagged for review, not converted to zero.
    attendance_risk = 100 - attendance_pct if pd.notna(attendance_pct) else 50
    grade_risk = 100 - average_marks if pd.notna(average_marks) else 50
    engagement_risk = np.clip(100 - (lms_events or 0) * 4, 0, 100)
    support_risk = np.clip(support_history_score, 0, 100)
    score = round(.40*attendance_risk + .35*grade_risk +
                  .15*engagement_risk + .10*support_risk, 2)
    level = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
    return {"risk_score": score, "risk_level": level,
            "missing_input": pd.isna(attendance_pct) or pd.isna(average_marks)}

def build_risk_report(data_dir="data"):
    from pathlib import Path
    folder = Path(data_dir)
    attendance = pd.read_csv(folder / "attendance_events.csv")
    results = pd.read_csv(folder / "assessment_results.csv")
    assessments = pd.read_csv(folder / "assessments.csv")
    lms = pd.read_csv(folder / "lms_activity.csv")
    enrollments = pd.read_csv(folder / "enrollments.csv")

    cutoff = pd.Timestamp("2026-11-30")
    att = attendance[pd.to_datetime(attendance.event_date) <= cutoff].copy()
    att["present"] = att.status.isin(["PRESENT", "LATE"]).astype(int)
    att = att[att.is_countable == True]
    att_agg = att.groupby("enrollment_id").agg(present=("present", "sum"),
                                                eligible=("present", "size"))
    att_agg["attendance_pct"] = 100 * att_agg.present / att_agg.eligible.replace(0, np.nan)

    res = results.merge(assessments[["assessment_id", "week_number"]], on="assessment_id")
    res = res[res.week_number <= 20]
    grade = res.groupby("enrollment_id").marks_obtained.mean()
    lms = lms[pd.to_datetime(lms.activity_timestamp) <= cutoff]
    activity = lms.groupby("enrollment_id").size()

    report = enrollments[["enrollment_id", "student_id"]].copy()
    report["attendance_pct"] = report.enrollment_id.map(att_agg.attendance_pct)
    report["average_marks"] = report.enrollment_id.map(grade)
    report["lms_events"] = report.enrollment_id.map(activity).fillna(0)
    # Support history as of cutoff is unavailable in this simplified generator;
    # neutral value is explicit and can be replaced with dated case history.
    report["support_history_score"] = 0
    calculated = report.apply(lambda r: calculate_risk(
        r.attendance_pct, r.average_marks, r.lms_events, r.support_history_score), axis=1)
    report["risk_score"] = [x["risk_score"] for x in calculated]
    report["risk_level"] = [x["risk_level"] for x in calculated]
    report["missing_input"] = [x["missing_input"] for x in calculated]
    report["prediction_cutoff"] = cutoff.date().isoformat()
    return report
