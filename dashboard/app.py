import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
from src.validation import validate_data
from src.risk_engine import build_risk_report

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

st.set_page_config(page_title="Student Success Dashboard", page_icon="🎓",
                   layout="wide")
st.title("🎓 Student Success & Risk Dashboard")
st.caption("Synthetic demonstration data | Prediction cutoff: 30 Nov 2026")

if not (DATA / "students.csv").exists():
    st.warning("No data found. Run `python main.py --scale starter` from the project folder first.")
    st.stop()

students = pd.read_csv(DATA / "students.csv")
courses = pd.read_csv(DATA / "courses.csv")
enrollments = pd.read_csv(DATA / "enrollments.csv")
risk = build_risk_report(DATA)
support = pd.read_csv(DATA / "support_cases.csv")
interventions = pd.read_csv(DATA / "interventions.csv")

st.sidebar.header("Filters")
programs = ["All"] + sorted(students.program.dropna().unique().tolist())
program = st.sidebar.selectbox("Program", programs)
levels = st.sidebar.multiselect("Risk level", ["HIGH", "MEDIUM", "LOW"],
                                default=["HIGH", "MEDIUM", "LOW"])
view = risk.merge(enrollments[["enrollment_id", "enrollment_status"]], on="enrollment_id")
view = view.merge(students[["student_id", "program"]], on="student_id")
if program != "All":
    view = view[view.program == program]
view = view[view.risk_level.isin(levels)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Students", f"{students.student_id.nunique():,}")
c2.metric("Courses", f"{courses.course_id.nunique():,}")
c3.metric("Enrollments", f"{enrollments.enrollment_id.nunique():,}")
c4.metric("High-risk enrollments", f"{(view.risk_level == 'HIGH').sum():,}")

left, right = st.columns(2)
with left:
    counts = view.risk_level.value_counts().reindex(["HIGH", "MEDIUM", "LOW"], fill_value=0)
    st.plotly_chart(px.pie(names=counts.index, values=counts.values,
                           title="Risk level distribution", hole=.45), use_container_width=True)
with right:
    st.plotly_chart(px.histogram(view, x="risk_score", nbins=20,
                                 color="risk_level", title="Risk score distribution"),
                    use_container_width=True)

st.subheader("Students requiring attention")
display = view.sort_values("risk_score", ascending=False).merge(
    students[["student_id", "first_name", "last_name", "program"]],
    on=["student_id", "program"], how="left")
st.dataframe(display[["student_id", "first_name", "last_name", "program",
                      "attendance_pct", "average_marks", "lms_events",
                      "risk_score", "risk_level", "missing_input"]],
             use_container_width=True, hide_index=True)

st.subheader("Support and intervention overview")
a, b = st.columns(2)
a.metric("Support cases", f"{len(support):,}")
b.metric("Interventions", f"{len(interventions):,}")
if len(interventions):
    st.plotly_chart(px.histogram(interventions, x="intervention_type",
                                 color="intervention_status",
                                 title="Interventions by type and status"),
                    use_container_width=True)

st.subheader("Data quality")
validation = validate_data(DATA)
if validation["passed"]:
    st.success(f"Validation passed: {validation['tables_checked']} tables, "
               f"{validation['total_rows']:,} rows checked.")
else:
    st.error("Validation found issues.")
    for error in validation["errors"]:
        st.write("•", error)
for warning in validation["warnings"]:
    st.warning(warning)

st.download_button("Download filtered risk report (CSV)",
                   view.to_csv(index=False).encode("utf-8"),
                   file_name="filtered_risk_report.csv", mime="text/csv")
st.caption("Decision support only. Risk flags should be reviewed by authorized staff; "
           "they are not automatic judgments about a learner.")
