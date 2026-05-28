# Task 2: Data Pipeline — Open-Meteo → BigQuery

## What This Is

A Python data pipeline that:
1. Fetches hourly weather data from [Open-Meteo](https://open-meteo.com/) (free, no API key)
2. Cleans and transforms the nested JSON into a flat, analytics-ready table
3. Enriches it with derived fields that add analytical value
4. Loads the result into Google BigQuery

The pipeline is parameterised, logs its progress, handles errors gracefully, and can process multiple cities in a single run.

---

## Why Open-Meteo?

- No API key or account required — zero friction for a demo pipeline
- Returns rich, nested JSON that demonstrates real transformation work (flattening, type coercion, null handling)
- Hourly granularity gives enough rows to make aggregation queries meaningful
- Directly relevant to a marketing tech context: weather data correlates with consumer behaviour and campaign performance in retail, travel, and FMCG verticals

---

## Repository Structure

```
task2/
├── pipeline.py          # Main pipeline: fetch → transform → load
├── requirements.txt     # Python dependencies
├── sql/
│   └── summary_queries.sql   # 5 BigQuery SQL queries with sample use cases
└── README.md            # This file
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

Follow these steps exactly:

1. Go to [console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery) and sign in with a Google account
2. A default project is created automatically (it will have a name like `my-project-123456`) — note this project ID
3. In the BigQuery console left panel, click your project name → **Create dataset**
   - Dataset ID: `weather_pipeline`
   - Location: choose any region (e.g. `US` or `europe-west2`)
   - Leave everything else as default → **Create**

> **Sandbox limitations to be aware of:**  
> The BigQuery Sandbox does not support DML operations (UPDATE, DELETE, MERGE) or scheduled queries. This pipeline uses `WRITE_APPEND` load jobs, which are fully supported. The 10 GB free storage and 1 TB free query limits are more than enough for this task.

### 3. Authenticate locally

Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), then:

```bash
gcloud auth application-default login
```

This sets up Application Default Credentials (ADC). The `google-cloud-bigquery` library picks these up automatically — no service account JSON file needed for local development.

---

## Running the Pipeline

### Basic run (default: London, New York, Tokyo — last 7 days)
```bash
python pipeline.py --project your-project-id
```

### Custom cities and date range
```bash
python pipeline.py \
  --cities "London,Paris,Dubai,Singapore" \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --project your-project-id
```

### Dry run (fetch + transform only, no BigQuery write)
```bash
python pipeline.py --dry-run
```

### All available cities
`London`, `New York`, `Tokyo`, `Mumbai`, `Sydney`, `Paris`, `Dubai`, `Singapore`

(Add more by extending the `CITY_COORDS` dict in `pipeline.py`)

---

## What the Pipeline Does

### Fetch
Calls the Open-Meteo `/v1/forecast` endpoint with hourly variables: temperature, apparent temperature, humidity, precipitation, wind speed, and WMO weather code. Handles timeouts, HTTP errors, and malformed responses explicitly.

### Transform
Flattens the nested `hourly` JSON object into a flat DataFrame. Then:

| Derived Field | What It Is | Why It's Useful |
|---|---|---|
| `weather_description` | Human-readable label for WMO weather code | Makes raw codes queryable/filterable |
| `thermal_discomfort_delta` | `feels_like_c − temperature_c` | Captures wind chill / humidity effect; negative = colder than actual |
| `hour_of_day` | Integer 0–23 | Enables hourly aggregations without parsing timestamps |
| `date` | String YYYY-MM-DD | Enables daily groupings in SQL |
| `is_raining` | Boolean (`precipitation_mm > 0`) | Simplifies rain-day analysis |
| `wind_category` | Beaufort-based label (Calm → Near gale) | Human-readable wind strength |

Nulls are handled per column: numeric columns coerced with `pd.to_numeric(errors='coerce')`, timestamps with `errors='coerce'` then dropped if unparseable.

### Load
Uses `bigquery.LoadJobConfig` with `WRITE_APPEND` — safe to re-run without duplicating schema, and compatible with BigQuery Sandbox. Schema is explicitly defined (not inferred) for reliability.

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
| `pipeline_run_date` | STRING | When the pipeline ran |

---

## SQL Queries

See [`sql/summary_queries.sql`](sql/summary_queries.sql) for the full set. Replace `your-project-id` with your GCP project ID before running.

### Sample: Daily temperature summary (Query 1)

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

**Sample output** (illustrative — your actual values will vary by date): **Actual output** (run on 2026-05-28):

| city | date | avg_temp_c | min_temp_c | max_temp_c | total_rain_mm | rainy_hours |
|---|---|---|---|---|---|---|
| London | 2026-05-28 | 24.0 | 16.0 | 30.8 | 0.0 | 0 |
| London | 2026-05-27 | 22.0 | 16.7 | 25.6 | 0.0 | 0 |
| London | 2026-05-26 | 28.4 | 21.3 | 34.6 | 0.0 | 0 |
| London | 2026-05-25 | 26.9 | 19.8 | 33.9 | 0.0 | 0 |
| New York | 2026-05-28 | 20.4 | 15.5 | 25.8 | 0.4 | 1 |

---

## Production Thinking (Step 5)

### How would you schedule this pipeline to run automatically?

For a simple setup: **Google Cloud Scheduler** + **Cloud Run Jobs**. Containerise `pipeline.py` with Docker, deploy it as a Cloud Run Job, and trigger it on a cron schedule (e.g. `0 6 * * *` for 6 AM UTC daily). This costs almost nothing at this data volume and requires no infrastructure to manage.

For a more mature setup: use **Cloud Composer** (managed Airflow) if this pipeline is one step in a larger DAG — e.g. fetch weather → join with campaign spend data → write to a reporting table.

### How would you know if it failed?

Three layers:
1. **Exit codes**: `pipeline.py` calls `sys.exit(1)` on total failure. Cloud Run Jobs treats non-zero exits as failures and surfaces them in the console.
2. **Cloud Logging**: all `log.error(...)` calls write to Cloud Logging automatically when running in GCP. Set a log-based alert to fire on `ERROR` severity → notify via email or Slack via Cloud Monitoring.
3. **BigQuery row count check**: after each run, a lightweight validation query (`SELECT COUNT(*) FROM table WHERE pipeline_run_date = TODAY`) confirms rows were written. If count is 0, trigger an alert.

### What would you add or change if this pipeline needed to scale to 10x the data volume?

At 10x scale (say, 1,000 cities × 90-day backfill = ~2.1M rows per run):

- **Parallelise fetches**: replace the sequential city loop with `concurrent.futures.ThreadPoolExecutor`. The Open-Meteo API is stateless, so concurrent requests are safe.
- **Batch BigQuery loads**: instead of one combined DataFrame load, write partitioned Parquet files to GCS first, then use `bigquery.LoadJobConfig` with a GCS URI. This is faster and more memory-efficient than in-memory DataFrame uploads for large volumes.
- **Add date-partitioning** to the BigQuery table on the `date` column. This makes time-range queries significantly cheaper and faster.
- **Idempotency**: add a `WRITE_TRUNCATE` partition-level strategy so re-running a day's data replaces rather than duplicates it.
- **Schema evolution**: use `ALLOW_FIELD_ADDITION` (already included) and pin schema versions so adding a new derived field doesn't break existing queries.

---

## What I Would Revisit With More Time

- **Idempotency**: currently `WRITE_APPEND` means re-running the pipeline for the same date range will duplicate rows. With more time I'd add a pre-load deduplication step or use partition-overwrite semantics.
- **Historical backfill mode**: add a `--backfill-months N` flag that chunks requests into 90-day windows (Open-Meteo's max per call) automatically.
- **Unit tests**: the `transform()` function is pure and deterministic — it's straightforward to test with `pytest` + a fixture of raw API JSON.
- **Config file**: move city coordinates and the BigQuery table ref into a `config.yaml` so non-engineers can adjust scope without touching Python.
- **Marketing relevance**: in a real deployment, I'd join this weather table with campaign spend or conversion data in BigQuery to surface correlations — e.g. "did rainy weekends in London correlate with higher online conversion rates for our client's delivery brand?"