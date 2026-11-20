from __future__ import annotations

import sqlite3

from app.ola_analytics import DATA_DIR, DATA_PATH, load_ride_data, sql_compatible_frame


CSV_PATH = DATA_DIR / "OLA_DataSet_Clean.csv"
EXCEL_PATH = DATA_DIR / "OLA_DataSet_Clean.xlsx"
DATABASE_PATH = DATA_DIR / "ola_rides.db"

DATA_DIR.mkdir(exist_ok=True)
data = load_ride_data(DATA_PATH)
data.to_csv(CSV_PATH, index=False, encoding="utf-8")
data.to_excel(EXCEL_PATH, index=False, engine="openpyxl")

with sqlite3.connect(DATABASE_PATH) as connection:
    sql_compatible_frame(data).to_sql(
        "rides", connection, index=False, if_exists="replace", chunksize=5_000
    )

print(f"Cleaned {len(data):,} rides.")
print(f"CSV: {CSV_PATH}")
print(f"Excel workbook: {EXCEL_PATH}")
print(f"SQLite database: {DATABASE_PATH}")
