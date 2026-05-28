# Task 2: Data Pipeline — Open-Meteo → BigQuery

## What This Is

A Python data pipeline that does 3 things in sequence:

1. **Fetch** — Calls the Open-Meteo API and gets hourly weather data for cities you choose
2. **Transform** — Cleans the raw JSON and adds useful derived fields
3. **Load** — Saves the clean data into Google BigQuery

---

## Why Open-Meteo?

- No API key required — anyone can run this without any account setup
- Returns nested JSON — good for showing real data transformation work
- Free and reliable — no rate limits for a demo pipeline
- Hourly granularity gives enough rows to make SQL queries meaningful

---

## Repository Structure

```
task-2-pipeline/
├── pipeline.py             # Main pipeline script — fetch → transform → load
├── test_pipeline.py        # 13 unit tests for the transform logic
├── requirements.txt        # Python dependencies
├── sql/
│   └── summary_queries.sql # 5 BigQuery SQL queries with sample output
└── README.md               # This file
```

---

## How to Run — Step by Step

### Step 1 — Install Python dependencies

Open your terminal, go to the task-2-pipeline folder, and run:

```bash
cd task-2-pipeline
pip install -r requirements.txt
```

This installs: `requests`, `pandas`, `google-cloud-bigquery`, `pyarrow`, and related packages.

---

### Step 2 — Set up BigQuery (one time only)

You need a free Google BigQuery Sandbox account:

1. Go to [console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery)
2. Sign in with any Google account
3. Your **project ID** appears in the top bar — note it down (e.g. `poised-honor-428405-n6`)
4. In the left panel, click your project → **Create dataset**
   - Dataset ID: `weather_pipeline`
   - Click **Create dataset**

> The BigQuery Sandbox is completely free. No credit card needed. It has some limitations (no UPDATE/DELETE queries) but everything this pipeline does is fully supported.

---

### Step 3 — Authenticate with Google Cloud (one time only)

Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) for your OS.

Then open the **Google Cloud SDK Shell** and run:

```bash
gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,openid" --no-browser
```

This gives you a `--remote-bootstrap` URL. Copy it and run it in PowerShell:

```powershell
gcloud auth application-default login --remote-bootstrap='PASTE_URL_HERE'
```

Type `y`, sign in with your browser, copy the `localhost:8085` URL it gives back, paste it into the SDK Shell prompt, press Enter.

Then set your quota project:

```bash
gcloud auth application-default set-quota-project your-project-id
```

You should see: `Credentials saved to file: [...]`

---

### Step 4 — Run the pipeline

```bash
python pipeline.py --project your-project-id
```

**What you will see in the terminal:**

```
2026-05-28 07:30:58 [INFO] Fetching weather data for London (2026-05-22 → 2026-05-28)
2026-05-28 07:31:00 [INFO]   ✓ Received 168 hourly records for London
2026-05-28 07:31:00 [INFO]   ✓ Transformed 168 rows for London
2026-05-28 07:31:00 [INFO] Fetching weather data for New York (2026-05-22 → 2026-05-28)
2026-05-28 07:31:02 [INFO]   ✓ Received 168 hourly records for New York
2026-05-28 07:31:02 [INFO]   ✓ Transformed 168 rows for New York
2026-05-28 07:31:02 [INFO] Fetching weather data for Tokyo (2026-05-22 → 2026-05-28)
2026-05-28 07:31:04 [INFO]   ✓ Received 168 hourly records for Tokyo
2026-05-28 07:31:04 [INFO]   ✓ Transformed 168 rows for Tokyo
2026-05-28 07:31:04 [INFO] Total rows to load: 504 across 3 cities
2026-05-28 07:31:08 [INFO]   ✓ Load complete. Table: weather_pipeline.hourly_weather
2026-05-28 07:31:08 [INFO] Pipeline complete.
```

**504 rows loaded** — 168 hourly records × 3 cities × 7 days.

---

### Step 5 — Verify in BigQuery Console

1. Go to [console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery)
2. In the left panel: expand your project → `weather_pipeline` → `hourly_weather`
3. Click the table → **Preview** tab to see your data
4. Click **+ New Query** and run:

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

---

## Optional — Custom Parameters

### Run with different cities
```bash
python pipeline.py --project your-project-id --cities "Chennai,Mumbai,Delhi"
```

### Run for a specific date range
```bash
python pipeline.py --project your-project-id --start-date 2026-05-01 --end-date 2026-05-07
```

### Dry run — fetch and transform only, no BigQuery write
```bash
python pipeline.py --dry-run
```

### Available cities
London, New York, Tokyo, Mumbai, Sydney, Paris, Dubai, Singapore, Chennai

To add a new city, add its latitude and longitude to `CITY_COORDS` in `pipeline.py`:
```python
"Salem": {"latitude": 11.6643, "longitude": 78.1460},
```

---

## How It Works Internally

### Fetch (`fetch_weather` function)
- Calls `https://api.open-meteo.com/v1/forecast` with city coordinates and date range
- Requests 6 hourly variables: temperature, feels-like temperature, humidity, precipitation, wind speed, weather code
- If the API is down or returns bad data — logs the error and skips that city. Other cities still run.

### Transform (`transform` function)
Raw API response looks like this (nested JSON):
```json
{
  "hourly": {
    "time": ["2026-05-22T00:00", "2026-05-22T01:00", ...],
    "temperature_2m": [18.2, 17.9, ...],
    "precipitation": [0.0, 1.5, ...]
  }
}
```

After transform — flat table, one row per hour:

| timestamp | city | temperature_c | is_raining | weather_description | wind_category |
|---|---|---|---|---|---|
| 2026-05-22 00:00 UTC | London | 18.2 | False | Clear sky | Light breeze |
| 2026-05-22 01:00 UTC | London | 17.9 | True | Slight rain | Light breeze |

**6 derived fields added:**

| Field | What It Is | Why Useful |
|---|---|---|
| `weather_description` | Human label for WMO weather code | Turns code 61 into "Slight rain" |
| `thermal_discomfort_delta` | Feels-like minus actual temp | Captures wind chill / humidity effect |
| `hour_of_day` | Integer 0–23 | Enables hourly trend queries in SQL |
| `date` | YYYY-MM-DD string | Enables daily grouping in SQL |
| `is_raining` | Boolean, True if precipitation > 0 | Simple flag for rain-day analysis |
| `wind_category` | Beaufort scale label | Readable wind strength |

### Load (`load_to_bigquery` function)
- Schema is explicitly defined — field names and types, nothing inferred
- Uses `WRITE_APPEND` — safe to re-run, compatible with BigQuery Sandbox
- Logs how many rows were loaded and confirms success

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

## SQL Summary Queries

All 5 queries are in [`sql/summary_queries.sql`](sql/summary_queries.sql).

**Actual output from Query 1 (run on 2026-05-28):**

| city | date | avg_temp_c | min_temp_c | max_temp_c | total_rain_mm | rainy_hours |
|---|---|---|---|---|---|---|
| London | 2026-05-28 | 24.0 | 16.0 | 30.8 | 0.0 | 0 |
| London | 2026-05-27 | 22.0 | 16.7 | 25.6 | 0.0 | 0 |
| London | 2026-05-26 | 28.4 | 21.3 | 34.6 | 0.0 | 0 |
| London | 2026-05-25 | 26.9 | 19.8 | 33.9 | 0.0 | 0 |
| New York | 2026-05-28 | 20.4 | 15.5 | 25.8 | 0.4 | 1 |
| Tokyo | 2026-05-28 | 19.5 | 14.2 | 24.8 | 0.0 | 0 |

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
- Null and bad string values handled without crashing
- City coordinates config is valid

---

## Production Thinking

### How would you schedule this pipeline automatically?

Use **Google Cloud Scheduler** to trigger a **Cloud Run Job** on a daily cron schedule (e.g. `0 6 * * *` = 6 AM UTC every day). Package `pipeline.py` in a Docker container, deploy as a Cloud Run Job. No servers to manage, costs almost nothing at this scale.

### How would you know if it failed?

Three layers:
1. **Exit codes** — `pipeline.py` exits with code 1 on total failure. Cloud Run Jobs detect this automatically.
2. **Cloud Logging alerts** — all `log.error()` calls go to Cloud Logging. Set an alert on ERROR severity → notify via email or Slack.
3. **Row count check** — after each run, verify `SELECT COUNT(*) WHERE pipeline_run_date = TODAY`. If 0 rows, trigger an alert.

### What would change at 10x data volume?

- **Parallel city fetches** — use `ThreadPoolExecutor` to fetch all cities at the same time instead of one by one
- **GCS-based loads** — write Parquet files to Cloud Storage first, then load from there. Faster than uploading a DataFrame directly for large volumes
- **Date partitioning** — partition the BigQuery table by `date` so time-range queries scan less data and cost less
- **Idempotency** — switch to partition-level overwrite so re-running a day replaces data instead of duplicating it

---

## What I Would Revisit With More Time

- **Idempotency** — WRITE_APPEND duplicates rows if you re-run the same date range. I would add a deduplication step or partition-overwrite strategy to fix this
- **Mocked tests for fetch** — the `fetch_weather` function makes a real HTTP call. With more time I would use `unittest.mock` to test error handling without hitting the network
- **Config file** — move city coordinates and BigQuery table ref into a `config.yaml` so anyone can change the scope without editing Python
- **Marketing connection** — in a real deployment I would join this weather data with campaign spend or conversion data in BigQuery to find patterns — for example, do rainy days increase online orders for a delivery brand?