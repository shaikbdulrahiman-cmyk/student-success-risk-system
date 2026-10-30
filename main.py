"""One-command setup: generate data, validate it, and load SQLite."""
import argparse
from src.data_generator import generate_data
from src.validation import validate_data
from src.database import load_csvs_to_sqlite

def main():
    parser = argparse.ArgumentParser(description="Student Success Risk System setup")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    generate_data(scale=args.scale, seed=args.seed)
    result = validate_data()
    print("\nVALIDATION")
    print(result)
    if not result["passed"]:
        raise SystemExit("Validation failed. Fix errors before using the dashboard.")
    count = load_csvs_to_sqlite()
    print(f"\nSQLite ready: {count} tables loaded.")
    print("Next: streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()
