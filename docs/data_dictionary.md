# Data dictionary

All generated records are synthetic. IDs are deterministic for a fixed seed.

| Entity / CSV | Primary key | Purpose |
|---|---|---|
| students | student_id | Learner master records |
| courses | course_id | Course master records |
| enrollments | enrollment_id | Student-course relationship |
| attendance_events | attendance_event_id | Weekly attendance events |
| assessments | assessment_id | Assessment definitions |
| assessment_results | assessment_result_id | Marks for an enrollment and assessment |
| lms_activity | lms_activity_id | Timestamped learning-platform activity |
| support_cases | support_case_id | Academic/engagement support cases |
| interventions | intervention_id | Actions assigned to a support case |
| outcomes | outcome_id | Future evaluation label; never a risk input |
| ground_truth | anomaly_id | Documented anomaly/edge-case expectations |
| risk_snapshot | enrollment_id | Risk calculation output at the stated cutoff |

## Important rules
- `student_id`, `course_id`, and all event IDs are unique within their entity.
- Child records reference valid parent IDs.
- Attendance percentage = count of PRESENT and LATE events / countable attendance events × 100.
- APPROVED_ABSENCE has `is_countable=false` and is excluded from the denominator.
- Missing assessment marks remain null; they are not changed to zero.
- The risk prediction cutoff is 2026-11-30. Only events on or before this cutoff may be features.
- `outcomes.csv` contains future evaluation information and must not be joined into model input features.
- `ground_truth.csv` documents edge-case expectations separately from model features.
