"""Load generated CSV files into a local SQLite database."""
from pathlib import Path
import sqlite3
import pandas as pd

def load_csvs_to_sqlite(data_dir="data", db_path="student_success.db"):
    folder = Path(data_dir)
    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {folder.resolve()}. Generate data first.")
    with sqlite3.connect(db_path) as conn:
        for csv_file in csv_files:
            table = csv_file.stem
            df = pd.read_csv(csv_file)
            df.to_sql(table, conn, if_exists="replace", index=False)
    return len(csv_files)

if __name__ == "__main__":
    count = load_csvs_to_sqlite()
    print(f"Loaded {count} CSV files into student_success.db")
