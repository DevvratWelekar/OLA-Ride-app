# Ola Ride Insights

An interactive dashboard for analyzing Ola ride bookings from July 2024. Built
with Python, Pandas, SQLite, and Streamlit.

## Run the dashboard

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py
```

Open the local URL printed in the terminal.

## Dashboard

Explore booking trends, vehicle types, revenue, cancellations, ratings, SQL
insights, and recommendations. Use the sidebar filters to select dates and
vehicle types.

## Data and SQL

The app reads the `July` sheet in `data/OLA_DataSet.xlsx`. Run this command to
create cleaned CSV, Excel, and SQLite files for analysis or Power BI:

```powershell
python prepare_data.py
```

SQL queries are in `sql/ola_insights.sql`. The generated SQLite database uses
the table `rides`.

## Power BI (optional)

Import `data/OLA_DataSet_Clean.xlsx` or `data/OLA_DataSet_Clean.csv` into Power
BI Desktop to create a report. To show a published report in the app, set the
`POWER_BI_EMBED_URL` environment variable to an accessible, secure embed URL.
The Streamlit dashboard works without Power BI.

## Tests

```powershell
python -m unittest discover -s tests -v
```
