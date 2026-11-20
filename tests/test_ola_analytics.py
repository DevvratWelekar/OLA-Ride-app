import unittest

import pandas as pd

from app.ola_analytics import build_recommendations, clean_ride_data, summarize_rides


class CleanRideDataTests(unittest.TestCase):
    def test_normalizes_nulls_and_adds_booking_time_fields(self):
        raw = pd.DataFrame(
            {
                "Date": ["2024-07-01", "2024-07-02"],
                "Time": ["08:15:00", "17:45:00"],
                "Booking_ID": ["B1", "B2"],
                "Booking_Status": ["Success", "Canceled by Driver"],
                "Customer_ID": ["C1", "C2"],
                "Vehicle_Type": ["Mini", "Bike"],
                "Booking_Value": ["100", "null"],
                "Ride_Distance": ["10", "0"],
                "Payment_Method": ["UPI", "null"],
                "Canceled_Rides_by_Customer": ["null", "null"],
                "Canceled_Rides_by_Driver": ["null", "Personal & Car related issue"],
                "Incomplete_Rides": ["No", "null"],
                "Incomplete_Rides_Reason": ["null", "null"],
                "Driver_Ratings": ["4.5", "null"],
                "Customer_Rating": ["4", "null"],
            }
        )

        cleaned = clean_ride_data(raw)

        self.assertEqual(cleaned.loc[0, "Hour"], 8)
        self.assertEqual(cleaned.loc[1, "Hour"], 17)
        self.assertTrue(pd.isna(cleaned.loc[1, "Payment_Method"]))
        self.assertEqual(cleaned.loc[0, "Booking_Value"], 100)
        self.assertNotIn("Vehicle Images", cleaned.columns)

    def test_summary_counts_successful_revenue_and_completed_distance(self):
        raw = pd.DataFrame(
            {
                "Date": ["2024-07-01", "2024-07-01"],
                "Time": ["08:00:00", "09:00:00"],
                "Booking_ID": ["B1", "B2"],
                "Booking_Status": ["Success", "Canceled by Customer"],
                "Customer_ID": ["C1", "C2"],
                "Vehicle_Type": ["Mini", "Mini"],
                "Booking_Value": [100, 50],
                "Ride_Distance": [12, 0],
                "Payment_Method": ["UPI", "null"],
                "Driver_Ratings": [4.5, "null"],
                "Customer_Rating": [4.0, "null"],
            }
        )
        summary = summarize_rides(clean_ride_data(raw))

        self.assertEqual(summary["bookings"], 2)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["success_rate"], 0.5)
        self.assertEqual(summary["revenue"], 100)
        self.assertEqual(summary["completed_distance"], 12)

    def test_recommendations_handle_empty_filtered_data(self):
        raw = pd.DataFrame(
            columns=[
                "Date",
                "Time",
                "Booking_ID",
                "Booking_Status",
                "Customer_ID",
                "Vehicle_Type",
                "Booking_Value",
                "Ride_Distance",
            ]
        )
        cleaned = clean_ride_data(raw)
        self.assertTrue(build_recommendations(cleaned))


if __name__ == "__main__":
    unittest.main()
