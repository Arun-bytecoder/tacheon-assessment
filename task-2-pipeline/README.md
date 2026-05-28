# Task 2: Data Pipeline — Open-Meteo → BigQuery

## What This Is

A Python data pipeline that:
1. Fetches hourly weather data from [Open-Meteo](https://open-meteo.com/) (free, no API key needed)
2. Cleans and transforms the raw JSON into a flat, analytics-ready table
3. Adds derived fields that go beyond what the API returns
4. Loads the result into Google BigQuery

---

## Why Open-Meteo?

- No API key required — easy for anyone to run without setup
- Returns nested JSON — good for demonstrating real transformation work
- Free and reliable — no rate limit issues for a demo pipeline
- Hourly data gives enough rows to make SQL aggregations meaningful

---

## Repository Structure

```
task-2-pipeline/
├── pipeline.py            # Main pipeline: fetch → transform → load
├── test_pipeline.py       # 13 unit tests for transform logic
├── requirements.txt       # Python dependencies
├── sql/
│   └── summary_queries.sql   # 5 BigQuery SQL queries
└── README.md              # This file
```

---

## Setup

### 1. Python environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. BigQuery Sandbox (free, no credit card)

1. Go to [console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery) and sign in with a Google account
2. Note your project ID shown in the top bar (e.g. `poised-honor-428405-n6`)
3. Click your project → **Create dataset**
   - Dataset ID: `weather_pipeline`
   - Leave everything else as default → **Create**

> **Sandbox limitations:** No DML (UPDATE/DELETE/MERGE), no scheduled queries. This pipeline uses WRITE_APPEND load jobs which are fully supported in the Sandbox.

### 3. Authenticate locally

Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), then:

```bash
gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,openid"
gcloud auth application-default set-quota-project your-project-id
```

---

## Running the Pipeline

### Default run (London, New York, Tokyo — last 7 days)
```bash
python pipeline.py --project your-project-id
```

### Custom cities and date range
```bash
python pipeline.py \
  --cities "London,Paris,Chennai" \
  --start-date 2026-05-01 \
  --end-date 2026-05-28 \
  --project your-project-id
```

### Dry run (no BigQuery write)
```bash
python pipeline.py --dry-run
```

### Available cities
London, New York, Tokyo, Mumbai, Sydney, Paris, Dubai, Singapore, Chennai

To add a new city, add its latitude and longitude to the `CITY_COORDS` dictionary in `pipeline.py`.

---

## How It Works

### Step 1 — Fetch
Calls Open-Meteo API with city coordinates and date range. Returns hourly JSON data for 6 variables. Handles timeouts, HTTP errors, and unexpected responses — if one city fails, the others still run.

### Step 2 — Transform
Flattens nested JSON into a flat DataFrame. Handles nulls and bad values. Adds 6 derived fields:

| Derived Field | What It Is | Why It's Useful |
|---|---|---|
| `weather_description` | Human-readable label for WMO weather code | Makes codes like 61 readable as "Slight rain" |
| `thermal_discomfort_delta` | Feels-like minus actual temperature | Shows wind chill or humidity effect |
| `hour_of_day` | Integer 0–23 | Enables hourly trend analysis in SQL |
| `date` | YYYY-MM-DD string | Enables daily grouping in SQL |
| `is_raining` | Boolean — True if precipitation > 0 | Simple flag for rain-day filtering |
| `wind_category` | Beaufort scale label | Human-readable wind strength |

### Step 3 — Load
Writes the clean DataFrame to BigQuery using an explicitly defined schema. Uses `WRITE_APPEND` — safe to re-run without duplicating schema, compatible with BigQuery Sandbox.

---

## BigQuery Schema

| Field | Type | Notes |
|---|---|---|
| `timestamp` | TIMESTAMP | UTC |
| `city` | STRING | |
| `latitude` / `longitude` | FLOAT64 | |
| `temperature_c` | FLOAT64 | |
| `feels_like_c` | FLOAT64 | |
| `humidity_pct` | FLOAT64 | 0–100 |
| `precipitation_mm` | FLOAT64 | |
| `windspeed_kmh` | FLOAT64 | |
| `weather_code` | INT64 | WMO code |
| `weather_description` | STRING | Derived |
| `thermal_discomfort_delta` | FLOAT64 | Derived |
| `hour_of_day` | INT64 | Derived |
| `date` | STRING | Derived |
| `is_raining` | BOOL | Derived |
| `wind_category` | STRING | Derived |
| `pipeline_run_date` | STRING | When pipeline ran |

---

## SQL Queries

See [`sql/summary_queries.sql`](sql/summary_queries.sql) for all 5 queries. Replace `your-project-id` before running.

### Query 1 — Daily temperature summary

```sql
SELECT
    city,
    date,
    ROUND(AVG(temperature_c), 1)    AS avg_temp_c,
    ROUND(MIN(temperature_c), 1)    AS min_temp_c,
    ROUND(MAX(temperature_c), 1)    AS max_temp_c,
    ROUND(SUM(precipitation_mm), 1) AS total_rain_mm,
    COUNTIF(is_raining)             AS rainy_hours
FROM `your-project-id.weather_pipeline.hourly_weather`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY city, date
ORDER BY city, date DESC;
```

**Actual output (run on 2026-05-28):**

| city | date | avg_temp_c | min_temp_c | max_temp_c | total_rain_mm | rainy_hours |
|---|---|---|---|---|---|---|
| London | 2026-05-28 | 24.0 | 16.0 | 30.8 | 0.0 | 0 |
| London | 2026-05-27 | 22.0 | 16.7 | 25.6 | 0.0 | 0 |
| London | 2026-05-26 | 28.4 | 21.3 | 34.6 | 0.0 | 0 |
| London | 2026-05-25 | 26.9 | 19.8 | 33.9 | 0.0 | 0 |
| New York | 2026-05-28 | 20.4 | 15.5 | 25.8 | 0.4 | 1 |

---

## Running the Tests

```bash
pip install pytest
pytest test_pipeline.py -v
```

**Result: 13 passed**

Tests cover:
- Output shape and column names are correct
- Derived field calculations are accurate
- Null and bad string values are handled without crashing
- City coordinates config is valid

---

## Production Thinking

### How would you schedule this pipeline to run automatically?

Use **Google Cloud Scheduler** to trigger a **Cloud Run Job** on a daily cron (e.g. `0 6 * * *`). Package `pipeline.py` into a Docker container, deploy as a Cloud Run Job. No servers to manage, costs almost nothing at this data volume.

For a more complex setup with multiple dependent pipelines, **Cloud Composer** (managed Airflow) would be the right choice.

### How would you know if it failed?

Three layers:
1. **Exit codes** — `pipeline.py` exits with code 1 on failure. Cloud Run Jobs treat non-zero exits as failures and surface them in the console.
2. **Cloud Logging** — all `log.error()` calls write to Cloud Logging automatically in GCP. Set a log-based alert on ERROR severity to notify via email or Slack.
3. **Row count check** — after each run, a validation query checks `SELECT COUNT(*) WHERE pipeline_run_date = TODAY`. If count is 0, trigger an alert.

### What would you add if this pipeline needed to scale to 10x the data volume?

- **Parallel city fetches** — replace the sequential loop with `ThreadPoolExecutor`. Each city's API call is independent so parallel requests are safe.
- **GCS-based loads** — write Parquet files to Google Cloud Storage first, then load from GCS URI instead of uploading a DataFrame directly. Faster and more memory-efficient at scale.
- **Date partitioning** — add `time_partitioning` on the `date` column in BigQuery. Makes time-range queries significantly cheaper.
- **Idempotency** — add partition-level overwrite so re-running a day replaces rather than duplicates data.

---

## What I Would Revisit With More Time

- **Idempotency** — currently WRITE_APPEND means re-running the same date range duplicates rows. I would add a deduplication step or partition-overwrite strategy.
- **Unit tests for fetch** — the `fetch_weather` function makes a real HTTP call. With more time I'd mock the API response with `unittest.mock` to test error handling without hitting the network.
- **Config file** — move city coordinates and BigQuery table ref into a `config.yaml` so non-engineers can adjust scope without editing Python.
- **Marketing context** — in a real deployment I'd join this weather table with campaign spend or conversion data in BigQuery to find correlations — e.g. do rainy days drive higher online conversions for a delivery brand?