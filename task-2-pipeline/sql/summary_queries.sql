-- =============================================================
-- Weather Pipeline — Summary Queries
-- Run these in the BigQuery Console after your pipeline loads data.
-- Replace `your-project-id` with your actual GCP project ID.
-- =============================================================


-- -----------------------------------------------------------
-- Query 1: Daily temperature summary per city (last 7 days)
-- Shows avg, min, max — useful for spotting trends at a glance
-- -----------------------------------------------------------
SELECT
    city,
    date,
    ROUND(AVG(temperature_c), 1)  AS avg_temp_c,
    ROUND(MIN(temperature_c), 1)  AS min_temp_c,
    ROUND(MAX(temperature_c), 1)  AS max_temp_c,
    ROUND(SUM(precipitation_mm), 1) AS total_rain_mm,
    COUNTIF(is_raining)            AS rainy_hours
FROM
    `your-project-id.weather_pipeline.hourly_weather`
WHERE
    date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY
    city, date
ORDER BY
    city, date DESC;


-- -----------------------------------------------------------
-- Query 2: Hourly average temperature by city
-- Good for understanding diurnal (day/night) patterns
-- -----------------------------------------------------------
SELECT
    city,
    hour_of_day,
    ROUND(AVG(temperature_c), 1)         AS avg_temp_c,
    ROUND(AVG(thermal_discomfort_delta), 2) AS avg_feels_like_delta
FROM
    `your-project-id.weather_pipeline.hourly_weather`
GROUP BY
    city, hour_of_day
ORDER BY
    city, hour_of_day;


-- -----------------------------------------------------------
-- Query 3: Wind category distribution per city
-- Shows what % of hours fall into each wind category
-- -----------------------------------------------------------
SELECT
    city,
    wind_category,
    COUNT(*)                                              AS hour_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY city), 1) AS pct_of_hours
FROM
    `your-project-id.weather_pipeline.hourly_weather`
GROUP BY
    city, wind_category
ORDER BY
    city, hour_count DESC;


-- -----------------------------------------------------------
-- Query 4: Wettest days (top 10 by total rainfall across all cities)
-- -----------------------------------------------------------
SELECT
    city,
    date,
    ROUND(SUM(precipitation_mm), 2) AS total_rain_mm,
    COUNTIF(is_raining)             AS rainy_hours_count
FROM
    `your-project-id.weather_pipeline.hourly_weather`
GROUP BY
    city, date
HAVING
    total_rain_mm > 0
ORDER BY
    total_rain_mm DESC
LIMIT 10;


-- -----------------------------------------------------------
-- Query 5: Most common weather conditions per city
-- Uses the human-readable WMO weather description
-- -----------------------------------------------------------
SELECT
    city,
    weather_description,
    COUNT(*) AS hour_count
FROM
    `your-project-id.weather_pipeline.hourly_weather`
GROUP BY
    city, weather_description
ORDER BY
    city, hour_count DESC;