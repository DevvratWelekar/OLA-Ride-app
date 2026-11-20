from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from app.ola_analytics import (
    DATA_PATH,
    build_recommendations,
    load_query_catalog,
    load_ride_data,
    run_sql_query,
    summarize_rides,
)


st.set_page_config(
    page_title="Ola Ride Insights",
    page_icon=":material/local_taxi:",
    layout="wide",
)


@st.cache_data(show_spinner="Loading and cleaning the July ride data...")
def get_rides() -> pd.DataFrame:
    return load_ride_data(DATA_PATH)


@st.cache_data
def get_queries() -> dict[str, dict[str, str]]:
    return load_query_catalog()


try:
    rides = get_rides()
except (FileNotFoundError, ValueError, OSError) as exc:
    st.error(f"Could not load the ride dataset: {exc}", icon=":material/error:")
    st.stop()

with st.sidebar:
    st.title("OLA", icon=":material/local_taxi:")
    st.caption("Ride insights · Bengaluru")
    st.subheader("Explore")
    views = [
        "Overall",
        "Vehicle type",
        "Revenue",
        "Cancellation",
        "Ratings",
        "SQL insights",
        "Recommendations",
        "Power BI report",
    ]
    view = st.radio(
        "Dashboard sections",
        options=views,
        label_visibility="collapsed",
        key="dashboard_view",
    )

    st.subheader("Filters")
    date_min = rides["Date"].min().date()
    date_max = rides["Date"].max().date()
    selected_dates = st.date_input(
        "Booking date range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )
    vehicle_types = sorted(rides["Vehicle_Type"].dropna().unique().tolist())
    selected_vehicles = st.multiselect(
        "Vehicle types",
        options=vehicle_types,
        default=vehicle_types,
    )
    st.caption(f"Source: July 2024 · {len(rides):,} bookings")

filtered = rides.loc[rides["Vehicle_Type"].isin(selected_vehicles)].copy()
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    if start_date and end_date:
        filtered = filtered.loc[
            filtered["Date"].between(
                pd.Timestamp(start_date), pd.Timestamp(end_date), inclusive="both"
            )
        ]

if filtered.empty:
    st.warning("No rides match the selected filters. Choose a wider date range or more vehicles.")
    st.stop()

metrics = summarize_rides(filtered)

st.badge("July 2024 snapshot", icon=":material/calendar_month:", color="blue")
st.title("Ola Ride Insights", icon=":material/analytics:")
st.caption("A clear view of ride demand, service quality, and completed-trip value.")

metric_columns = st.columns(3, border=True)
metric_columns[0].metric("Bookings", f"{metrics['bookings']:,}")
metric_columns[1].metric("Successful rides", f"{metrics['successful']:,}")
metric_columns[2].metric("Success rate", f"{metrics['success_rate']:.1%}")
metric_columns = st.columns(2, border=True)
metric_columns[0].metric("Completed revenue", f"₹{metrics['revenue']:,.0f}")
metric_columns[1].metric("Completed distance", f"{metrics['completed_distance']:,.0f} km")

if view == "Overall":
    st.header("Overall", icon=":material/space_dashboard:")
    st.caption("Track daily demand and see how bookings resolve.")
    by_day = (
        filtered.groupby("Date", as_index=False)
        .agg(Bookings=("Booking_ID", "count"))
        .sort_values("Date")
    )
    statuses = (
        filtered["Booking_Status"]
        .value_counts()
        .rename_axis("Booking status")
        .reset_index(name="Bookings")
    )
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Ride volume over time")
            st.line_chart(
                by_day,
                x="Date",
                y="Bookings",
                alt="Daily booking volume across the selected date range",
            )
    with right:
        with st.container(border=True):
            st.subheader("Booking status breakdown")
            st.bar_chart(
                statuses,
                x="Booking status",
                y="Bookings",
                horizontal=True,
                alt="Booking counts by ride status",
            )

elif view == "Vehicle type":
    st.header("Vehicle type", icon=":material/directions_car:")
    st.caption("Compare completed distance and trip ratings across the fleet.")
    completed = filtered.loc[filtered["Is_Successful"]]
    vehicle_distance = (
        completed.groupby("Vehicle_Type", as_index=False)
        .agg(**{"Ride distance (km)": ("Ride_Distance", "sum")})
        .nlargest(5, "Ride distance (km)")
    )
    vehicle_ratings = (
        completed.groupby("Vehicle_Type", as_index=False)
        .agg(
            **{
                "Customer rating": ("Customer_Rating", "mean"),
                "Driver rating": ("Driver_Ratings", "mean"),
            }
        )
        .round(2)
    )
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Top 5 vehicle types by completed ride distance")
            st.bar_chart(
                vehicle_distance,
                x="Vehicle_Type",
                y="Ride distance (km)",
                horizontal=True,
                alt="Five vehicle types with the greatest completed ride distance",
            )
    with right:
        with st.container(border=True):
            st.subheader("Average ratings by vehicle type")
            st.bar_chart(
                vehicle_ratings,
                x="Vehicle_Type",
                y=["Customer rating", "Driver rating"],
                alt="Average customer and driver ratings for each vehicle type",
            )
    st.caption("Ride distance and ratings include successful bookings only.")

elif view == "Revenue":
    st.header("Revenue", icon=":material/payments:")
    st.caption("Completed trips only · booking value shown in ₹.")
    completed = filtered.loc[filtered["Is_Successful"]]
    payment = (
        completed.groupby("Payment_Method", as_index=False, dropna=False)
        .agg(Revenue=("Booking_Value", "sum"))
        .sort_values("Revenue", ascending=False)
    )
    top_customers = (
        completed.groupby("Customer_ID", as_index=False)
        .agg(**{"Booking value": ("Booking_Value", "sum")})
        .nlargest(5, "Booking value")
    )
    daily_distance = (
        completed.groupby("Date", as_index=False)
        .agg(**{"Ride distance (km)": ("Ride_Distance", "sum")})
        .sort_values("Date")
    )
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Revenue by payment method")
            st.bar_chart(
                payment,
                x="Payment_Method",
                y="Revenue",
                horizontal=True,
                alt="Completed booking revenue grouped by payment method",
            )
    with col2:
        with st.container(border=True):
            st.subheader("Top 5 customers by completed booking value")
            st.bar_chart(
                top_customers,
                x="Customer_ID",
                y="Booking value",
                horizontal=True,
                alt="Five customers with the highest completed booking value",
            )
    with st.container(border=True):
        st.subheader("Completed ride distance per day")
        st.area_chart(
            daily_distance,
            x="Date",
            y="Ride distance (km)",
            alt="Daily distance traveled on completed rides",
        )
    st.caption("Revenue is the sum of Booking_Value for successful bookings only.")

elif view == "Cancellation":
    st.header("Cancellation", icon=":material/cancel:")
    st.caption("Separate reported customer and driver reasons; incomplete rides are shown below.")
    reason_columns = (
        ("Canceled_Rides_by_Customer", "Customer cancellation reasons"),
        ("Canceled_Rides_by_Driver", "Driver cancellation reasons"),
    )
    col1, col2 = st.columns(2)
    for column, (reason_field, title) in zip((col1, col2), reason_columns):
        with column:
            with st.container(border=True):
                st.subheader(title)
                reasons = (
                    filtered[reason_field]
                    .dropna()
                    .value_counts()
                    .rename_axis("Reason")
                    .reset_index(name="Bookings")
                )
                if reasons.empty:
                    st.info("No cancellation reasons in the selected data.")
                else:
                    st.bar_chart(
                        reasons,
                        x="Reason",
                        y="Bookings",
                        horizontal=True,
                        alt=f"Reported reasons for {title.lower()}",
                    )
    incomplete = (
        filtered.loc[filtered["Incomplete_Rides"].eq("Yes"), "Incomplete_Rides_Reason"]
        .dropna()
        .value_counts()
        .rename_axis("Incomplete ride reason")
        .reset_index(name="Bookings")
    )
    with st.container(border=True):
        st.subheader("Incomplete ride reasons")
        if incomplete.empty:
            st.info("No incomplete rides with a recorded reason in the selected data.")
        else:
            st.bar_chart(
                incomplete,
                x="Incomplete ride reason",
                y="Bookings",
                horizontal=True,
                alt="Reported reasons for incomplete rides",
            )

elif view == "Ratings":
    st.header("Ratings", icon=":material/star:")
    st.caption("Completed bookings only · source ratings are on a five-point scale.")
    completed = filtered.loc[filtered["Is_Successful"]]
    rating_bins = [0, 1, 2, 3, 4, 5]
    rating_labels = ["0–1", "1–2", "2–3", "3–4", "4–5"]
    driver_ratings = completed["Driver_Ratings"].dropna()
    customer_ratings = completed["Customer_Rating"].dropna()
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Driver ratings distribution")
            distribution = (
                pd.cut(driver_ratings, bins=rating_bins, labels=rating_labels, include_lowest=True)
                .value_counts(sort=False)
                .rename_axis("Rating")
                .reset_index(name="Bookings")
            )
            st.bar_chart(
                distribution,
                x="Rating",
                y="Bookings",
                alt="Distribution of driver ratings on completed rides",
            )
    with col2:
        with st.container(border=True):
            st.subheader("Customer ratings distribution")
            distribution = (
                pd.cut(
                    customer_ratings,
                    bins=rating_bins,
                    labels=rating_labels,
                    include_lowest=True,
                )
                .value_counts(sort=False)
                .rename_axis("Rating")
                .reset_index(name="Bookings")
            )
            st.bar_chart(
                distribution,
                x="Rating",
                y="Bookings",
                alt="Distribution of customer ratings on completed rides",
            )
    st.metric("Average driver rating", f"{metrics['avg_driver_rating']:.2f} / 5")
    st.metric("Average customer rating", f"{metrics['avg_customer_rating']:.2f} / 5")
    rating_comparison = pd.DataFrame(
        {
            "Rating type": ["Driver rating", "Customer rating"],
            "Average rating": [
                metrics["avg_driver_rating"],
                metrics["avg_customer_rating"],
            ],
        }
    )
    with st.container(border=True):
        st.subheader("Customer vs. driver ratings")
        st.bar_chart(
            rating_comparison,
            x="Rating type",
            y="Average rating",
            alt="Average customer and driver ratings for completed rides",
        )

elif view == "SQL insights":
    st.header("SQL insights", icon=":material/database:")
    st.caption("Choose one of the ten SQLite queries from the project query library.")
    catalog = get_queries()
    query_key = st.selectbox(
        "Insight query",
        options=list(catalog),
        format_func=lambda key: f"{key}: {catalog[key]['title']}",
    )
    if st.button("Run query", type="primary", icon=":material/play_arrow:"):
        try:
            result = run_sql_query(filtered, catalog[query_key]["query"])
        except (ValueError, KeyError, pd.errors.DatabaseError) as exc:
            st.error(f"Query failed: {exc}")
        else:
            st.success(f"Returned {len(result):,} rows.")
            if len(result) > 1_000:
                st.caption("Showing the first 1,000 rows. Download the complete result below.")
            st.dataframe(
                result.head(1_000),
                hide_index=True,
                alt=f"Results for {catalog[query_key]['title']}",
            )
            st.download_button(
                "Download complete query result",
                data=result.to_csv(index=False).encode("utf-8"),
                file_name=f"{query_key.lower()}_results.csv",
                mime="text/csv",
                icon=":material/download:",
            )

elif view == "Recommendations":
    st.header("Recommendations", icon=":material/lightbulb:")
    st.caption(
        "Suggestions are generated from the currently selected dates and vehicle types. "
        "They are hypotheses to validate with driver availability, wait-time, and support data."
    )
    for index, recommendation in enumerate(build_recommendations(filtered), start=1):
        with st.container(border=True):
            st.markdown(f"**Priority {index}**")
            st.write(recommendation)

elif view == "Power BI report":
    st.header("Power BI report", icon=":material/monitoring:")
    embed_url = os.getenv("POWER_BI_EMBED_URL", "").strip()
    if embed_url:
        st.iframe(embed_url, height=720, scrolling=True, tab_index=0, alt="Embedded Ola Power BI report")
    else:
        st.info(
            "No Power BI embed URL is configured. Build the report from the cleaned CSV "
            "or connect Power BI to the generated SQLite database, then set "
            "POWER_BI_EMBED_URL as described in README.md.",
            title="Connect a Power BI report",
        )
        st.caption(
            "The supplied Ola-Slides.pptx defines the dashboard sections; it is a design "
            "reference, not a published Power BI report."
        )

with st.expander("Data quality and definitions"):
    st.write(
        f"Source: `OLA_DataSet.xlsx` → `July` worksheet · "
        f"{len(rides):,} rows · {rides['Booking_ID'].nunique():,} unique booking IDs."
    )
    st.write(
        "Text `null` values are treated as missing; numeric measures are coerced to numbers; "
        "vehicle-image URLs are omitted. Revenue, distance, and ratings use successful rides "
        "unless a chart says otherwise."
    )
    st.write(
        "Booking success rate = successful bookings ÷ all filtered bookings. "
        "Cancellation reasons are counted from their respective reason columns. "
        "A ride with no payment method is not assigned to a payment-method revenue group."
    )
