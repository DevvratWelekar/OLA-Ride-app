from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
DATA_PATH = DATA_DIR / "OLA_DataSet.xlsx"
SQL_PATH = PROJECT_DIR / "sql" / "ola_insights.sql"
NULL_TEXT = re.compile(r"^\s*null\s*$", re.IGNORECASE)
IMAGE_COLUMN = "Vehicle Images"

NUMERIC_COLUMNS = (
    "V_TAT",
    "C_TAT",
    "Booking_Value",
    "Ride_Distance",
    "Driver_Ratings",
    "Customer_Rating",
)


def clean_ride_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize the July sheet and add reusable date/time fields."""
    data = raw.copy()
    data.columns = [str(column).strip() for column in data.columns]
    data = data.drop(columns=[IMAGE_COLUMN], errors="ignore")

    for column in data.select_dtypes(include=["object", "string"]).columns:
        values = data[column].astype("string").str.strip()
        data[column] = values.mask(values.str.fullmatch(NULL_TEXT, na=False), pd.NA)

    if "Date" not in data or "Time" not in data:
        raise ValueError("The workbook must include Date and Time columns.")

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce").dt.normalize()
    time_values = pd.to_datetime(
        data["Time"].astype("string"), format="%H:%M:%S", errors="coerce"
    )
    missing_time = time_values.isna()
    if missing_time.any():
        time_values.loc[missing_time] = pd.to_datetime(
            data.loc[missing_time, "Time"].astype("string"),
            format="%H:%M",
            errors="coerce",
        )
    data["Booking_Datetime"] = data["Date"] + (
        time_values - time_values.dt.normalize()
    )
    data["Hour"] = data["Booking_Datetime"].dt.hour.astype("Int64")
    data["Day_Of_Week"] = data["Booking_Datetime"].dt.day_name()

    for column in NUMERIC_COLUMNS:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    for column in (
        "Booking_Status",
        "Vehicle_Type",
        "Payment_Method",
        "Canceled_Rides_by_Customer",
        "Canceled_Rides_by_Driver",
        "Incomplete_Rides",
        "Incomplete_Rides_Reason",
    ):
        if column in data:
            data[column] = data[column].astype("string").str.strip()

    if "Booking_Status" not in data:
        raise ValueError("The workbook must include a Booking_Status column.")
    data["Is_Successful"] = data["Booking_Status"].eq("Success")
    return data


def load_ride_data(path: Path = DATA_PATH) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Could not find the ride workbook: {path}")
    raw = pd.read_excel(path, sheet_name="July", engine="openpyxl")
    if raw.empty:
        raise ValueError("The July worksheet has no ride records.")
    return clean_ride_data(raw)


def summarize_rides(data: pd.DataFrame) -> dict[str, Any]:
    total = len(data)
    successful = data.loc[data["Is_Successful"]]
    cancelled = data["Booking_Status"].isin(
        ["Canceled by Customer", "Canceled by Driver"]
    )
    return {
        "bookings": total,
        "successful": len(successful),
        "success_rate": len(successful) / total if total else 0.0,
        "cancelled": int(cancelled.sum()),
        "revenue": float(successful["Booking_Value"].sum()),
        "completed_distance": float(successful["Ride_Distance"].sum()),
        "avg_customer_rating": float(successful["Customer_Rating"].mean()),
        "avg_driver_rating": float(successful["Driver_Ratings"].mean()),
    }


def build_recommendations(data: pd.DataFrame) -> list[str]:
    if data.empty:
        return ["No rides match the current filters. Expand the date or vehicle selection."]

    notes: list[str] = []
    summary = summarize_rides(data)
    outcomes = data.loc[~data["Is_Successful"], "Booking_Status"].value_counts()
    if not outcomes.empty:
        status = str(outcomes.index[0])
        count = int(outcomes.iloc[0])
        share = count / len(data)
        notes.append(
            f"{status} is the largest non-success outcome ({count:,} bookings, "
            f"{share:.1%} of filtered bookings). Review the dispatch and cancellation "
            "workflow for this outcome before changing driver allocation."
        )

    for column, audience in (
        ("Canceled_Rides_by_Customer", "customer cancellations"),
        ("Canceled_Rides_by_Driver", "driver cancellations"),
    ):
        reasons = data[column].dropna().value_counts() if column in data else pd.Series(dtype=int)
        if not reasons.empty:
            reason = str(reasons.index[0])
            count = int(reasons.iloc[0])
            action = (
                "test pickup-progress alerts and reassignment rules"
                if "moving towards pickup" in reason.lower()
                else "review the relevant support, vehicle-readiness, or dispatch process"
            )
            notes.append(
                f"The leading reason for {audience} is “{reason}” ({count:,}). "
                f"Prioritize a small operational review and {action}."
            )

    if "Hour" in data and data["Hour"].notna().any():
        peak_hour = int(data["Hour"].value_counts().idxmax())
        peak_count = int(data["Hour"].value_counts().max())
        notes.append(
            f"Booking volume peaks around {peak_hour:02d}:00 "
            f"({peak_count:,} bookings). Compare this demand pattern with driver-online "
            "and wait-time data before adjusting coverage."
        )

    if summary["successful"] and summary["avg_customer_rating"] < 4:
        notes.append(
            f"Completed-ride customer ratings average {summary['avg_customer_rating']:.2f}/5. "
            "Inspect low-rating trips and pickup/vehicle feedback to identify recurring issues."
        )

    return notes[:5]


def load_query_catalog(path: Path = SQL_PATH) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Could not find the SQL query file: {path}")
    catalog: dict[str, dict[str, str]] = {}
    current_key: str | None = None
    current_title = ""
    current_lines: list[str] = []

    def save_current() -> None:
        if current_key is not None:
            query = "\n".join(
                line for line in current_lines if not line.lstrip().startswith("--")
            ).strip()
            catalog[current_key] = {"title": current_title, "query": query}

    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"^\s*--\s*(Q\d+):\s*(.+?)\s*$", line)
        if marker:
            save_current()
            current_key, current_title = marker.groups()
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)
    save_current()
    if not catalog:
        raise ValueError(f"No numbered queries were found in {path}.")
    return catalog


def sql_compatible_frame(data: pd.DataFrame) -> pd.DataFrame:
    sql_data = data.copy()
    for column in sql_data.select_dtypes(include=["datetime", "datetimetz"]).columns:
        sql_data[column] = sql_data[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return sql_data.astype(object).where(pd.notna(sql_data), None)


def run_sql_query(data: pd.DataFrame, query: str) -> pd.DataFrame:
    """Execute a trusted project query against the currently filtered dataset."""
    sql_data = sql_compatible_frame(data)
    with sqlite3.connect(":memory:") as connection:
        sql_data.to_sql(
            "rides", connection, index=False, if_exists="replace", chunksize=5_000
        )
        return pd.read_sql_query(query, connection)

