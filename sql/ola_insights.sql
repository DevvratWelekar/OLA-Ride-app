-- Q01: Retrieve all successful bookings
SELECT *
FROM rides
WHERE Booking_Status = 'Success';

-- Q02: Average completed ride distance for each vehicle type
SELECT
    Vehicle_Type,
    ROUND(AVG(Ride_Distance), 2) AS average_ride_distance_km
FROM rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY average_ride_distance_km DESC;

-- Q03: Number of rides cancelled by customers
SELECT
    COUNT(*) AS customer_cancelled_rides
FROM rides
WHERE Booking_Status = 'Canceled by Customer';

-- Q04: Top 5 customers by number of bookings
SELECT
    Customer_ID,
    COUNT(*) AS ride_count
FROM rides
GROUP BY Customer_ID
ORDER BY ride_count DESC, Customer_ID
LIMIT 5;

-- Q05: Driver cancellations due to personal and car-related issues
SELECT
    COUNT(*) AS personal_or_car_issue_cancellations
FROM rides
WHERE Booking_Status = 'Canceled by Driver'
  AND Canceled_Rides_by_Driver = 'Personal & Car related issue';

-- Q06: Maximum and minimum driver ratings for Prime Sedan completed bookings
SELECT
    MAX(Driver_Ratings) AS maximum_driver_rating,
    MIN(Driver_Ratings) AS minimum_driver_rating
FROM rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Booking_Status = 'Success';

-- Q07: Rides paid using UPI
SELECT *
FROM rides
WHERE Payment_Method = 'UPI';

-- Q08: Average customer rating by vehicle type
SELECT
    Vehicle_Type,
    ROUND(AVG(Customer_Rating), 2) AS average_customer_rating
FROM rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY average_customer_rating DESC;

-- Q09: Total booking value for successfully completed rides
SELECT
    ROUND(SUM(Booking_Value), 2) AS successful_booking_value
FROM rides
WHERE Booking_Status = 'Success';

-- Q10: Incomplete rides and their reported reasons
SELECT
    Booking_ID,
    Customer_ID,
    Vehicle_Type,
    Incomplete_Rides_Reason
FROM rides
WHERE Incomplete_Rides = 'Yes'
ORDER BY Incomplete_Rides_Reason, Booking_ID;
