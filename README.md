# Student Success & Risk Prediction System

A beginner-friendly, end-to-end synthetic-data project for the YottaFlex.ai 72-hour code challenge.

## Features
- Deterministic synthetic data generator (starter and full scale)
- 10 related data entities plus a separate ground-truth file
- Attendance, assessments, LMS activity, support cases and interventions
- Explainable rule-based risk scoring
- Streamlit dashboard with filters, charts and CSV download
- SQLite database export
- Validation checks and starter tests

## Requirements
Python 3.10 or newer is recommended.

## Setup (Windows)
Open Command Prompt in this project folder:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Generate a small dataset first
```bash
python main.py --scale starter
```

This creates CSV files in `data/`, validates them, and loads `student_success.db`.

## Run the dashboard
```bash
streamlit run dashboard/app.py
```

## Generate the full challenge dataset
After checking the starter dataset and dashboard:

```bash
python main.py --scale full
```

Full scale targets 5,000 students, 200 courses, and 20,000 enrollments, with one academic year's attendance and assessment events.

## Run tests
```bash
pytest -q
```

## Risk score
The score is a transparent rule-based indicator from 0 to 100:

`risk = 0.40 × attendance_risk + 0.35 × grade_risk + 0.15 × engagement_risk + 0.10 × support_history_risk`

- LOW: 0–29
- MEDIUM: 30–59
- HIGH: 60–100

The current generator uses a neutral support-history value in the prediction report because the demo does not model pre-cutoff case history in detail. This is documented and should not be described as a trained AI model. Missing attendance/grade data is flagged for review and is not automatically treated as failure.

## Reproducibility
Default seed: `20261022`. Use the same seed and scale to regenerate the same synthetic records.

## Privacy and limitations
All records are synthetic. Do not upload real student personal data. Risk levels are decision-support signals, not final decisions. Authorized staff should review cases and consider context before acting.

## Repository checklist
- [ ] Run starter setup and dashboard
- [ ] Run tests
- [ ] Run full data generation
- [ ] Inspect validation report
- [ ] Add prompt history (see `PROMPT_HISTORY_TEMPLATE.md`)
- [ ] Review files for secrets/private data
- [ ] Push to a public GitHub repository
- [ ] Submit repository URL before deadline
