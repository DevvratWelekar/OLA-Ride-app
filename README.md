# Ola Ride Insights

An interactive ride-operations and revenue project for the supplied Ola July
workbook. The Streamlit dashboard follows the five sections in
`data/Ola-Slides.pptx` (Overall, Vehicle type, Revenue, Cancellation, and Ratings),
and adds a SQL query browser, evidence-based recommendations, and an optional
Power BI embed.

## Project structure

```text
OLA Ride/
├── app/
│   ├── streamlit_app.py
│   └── ola_analytics.py
├── data/
│   ├── OLA_DataSet.xlsx
│   └── Ola-Slides.pptx
├── sql/
│   └── ola_insights.sql
├── tests/
│   └── test_ola_analytics.py
├── prepare_data.py
├── requirements.txt
└── README.md
```

## Project contents

- `data/OLA_DataSet.xlsx` — supplied source workbook; the app reads the `July` sheet.
- `data/Ola-Slides.pptx` — supplied reference for dashboard sections and vehicle types.
- `app/streamlit_app.py` — interactive dashboard and SQL results browser.
- `app/ola_analytics.py` — cleaning, summary, recommendation, and SQLite query helpers.
- `sql/ola_insights.sql` — the ten requested, runnable SQLite queries.
- `prepare_data.py` — exports the cleaned dataset and a SQLite database for Power BI
  or standalone SQL work.
- `tests/test_ola_analytics.py` — focused data cleaning and metric tests.

## Run locally

Python 3.10 or later is recommended.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py
```

Keep the source workbook at `data/OLA_DataSet.xlsx`. Filters for booking
date and vehicle type apply to the dashboard, recommendations, and SQL query
browser. SQL query results display at most 1,000 rows in the app; the download
button returns the complete selected result.

## Data preparation and SQL

The cleaner converts the literal text `null` to missing values, normalizes date
and time, coerces numeric measures, removes the decorative vehicle-image URL,
and adds booking datetime, hour, weekday, and success fields. Missing values are
not imputed: they commonly mean a metric does not apply to a canceled or
unmatched booking.

Generate Power BI-friendly CSV, Excel, and SQLite files:

```powershell
python prepare_data.py
```

This creates `data/OLA_DataSet_Clean.csv`, `data/OLA_DataSet_Clean.xlsx`, and
`data/ola_rides.db`.
The SQL file expects a table named `rides`, as created by the script. It uses
SQLite syntax and can also be run in the dashboard's SQL insights view.

## Dashboard definitions

- **Overall:** daily booking volume and booking-status breakdown.
- **Vehicle type:** top five vehicle types by distance from successful rides and
  average customer/driver ratings by vehicle.
- **Revenue:** completed booking value by payment method, top five customers by
  completed booking value, and completed distance by day.
- **Cancellation:** customer and driver reason fields are counted separately;
  incomplete ride reasons are shown as a third chart.
- **Ratings:** distributions for driver and customer ratings, plus their means.
- **SQL insights:** the ten requested SQL questions, evaluated against current
  dashboard filters.

Revenue, distance, and ratings are restricted to `Booking_Status = 'Success'`
so canceled bookings do not inflate completed-trip metrics. Customer and driver
ratings are scored from 0 to 5 in the source. Cancellation reason columns are
counted as recorded; they are not inferred from free text.

## Power BI

Use **Get data → Excel workbook** to load `data/OLA_DataSet_Clean.xlsx`, or
**Get data → Text/CSV** for the CSV, or connect to `data/ola_rides.db` with an
available SQLite connector. The Power BI report can
recreate the five sections and measures above. The supplied PPT is a view
outline, not a `.pbix` report.

To display a published report in the app, set `POWER_BI_EMBED_URL` in the
environment where Streamlit runs. The URL must be embeddable and accessible to
the app's viewers; follow your organization's Power BI sharing and data
protection policy. Without a configured URL, the app continues to show its
native dashboard.

Suggested Power BI measures:

```DAX
Bookings = COUNTROWS(rides)
Successful Bookings =
    CALCULATE([Bookings], rides[Booking_Status] = "Success")
Success Rate = DIVIDE([Successful Bookings], [Bookings])
Completed Revenue =
    CALCULATE(SUM(rides[Booking_Value]), rides[Booking_Status] = "Success")
Completed Distance (km) =
    CALCULATE(SUM(rides[Ride_Distance]), rides[Booking_Status] = "Success")
```

Use a date slicer, vehicle-type slicer, and booking-status slicer. Keep the
calendar/date field related to `rides[Date]`.

## July 2024 baseline observations

These are descriptive results from the supplied data, not causal findings:

- 103,024 bookings; 63,967 succeeded (62.1%).
- Driver cancellations: 18,434 (17.9%); customer cancellations: 10,499 (10.2%);
  `Driver Not Found`: 10,124 (9.8%).
- Successful booking value totals ₹35,080,467; cash and UPI are the largest
  recorded completed-ride payment groups.
- Among customer cancellation reasons, “Driver is not moving towards pickup
  location” appears most often (3,175). For driver reasons, “Personal & Car
  related issue” appears most often (6,542).
- Booking volume is highest at 12:00 in the supplied hourly distribution. This
  should be compared with driver availability and wait-time data before making
  a staffing decision.

### Recommendations to investigate

1. Review driver dispatch and cancellation workflows first, since driver
   cancellations are the largest unsuccessful booking status.
2. Test pickup-progress alerts and timely reassignment for rides where the
   driver is not moving toward pickup; measure impact on cancellations and
   pickup wait time.
3. Investigate vehicle readiness and driver support for personal/car-related
   cancellation reports; validate whether preventive checks can reduce these
   events.
4. Compare booking volume by hour with driver-online supply and wait times
   before moving driver coverage toward peak hours.
5. Link low-rating trips to pickup, route, and vehicle feedback before
   introducing vehicle-specific service interventions.

The workbook does not include driver-online supply, wait times at trip level,
surge multipliers, or a fraud label. It therefore supports demand and outcome
descriptions, but not causal surge-pricing effectiveness or confirmed fraud
detection.

## Validate

```powershell
python -m unittest discover -s tests -v
```
