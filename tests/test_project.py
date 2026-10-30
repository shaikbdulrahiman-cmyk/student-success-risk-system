from src.risk_engine import calculate_risk
from src.validation import validate_data

def test_risk_score_is_bounded():
    result = calculate_risk(80, 75, 10, 20)
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}

def test_missing_data_is_not_zero_failure():
    result = calculate_risk(None, None, 0, 0)
    assert result["missing_input"] is True
    assert result["risk_score"] == 52.5  # neutral attendance/grade plus neutral engagement contribution

def test_risk_uses_no_future_grade_argument():
    # The public risk function accepts only contemporaneous indicators.
    assert "final_grade" not in calculate_risk.__code__.co_varnames

def test_generated_data_validation():
    result = validate_data("data")
    assert result["passed"], result["errors"]
