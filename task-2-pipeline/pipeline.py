"""
Weather Data Pipeline — Open-Meteo → BigQuery
Fetches hourly weather data for one or more cities, transforms it,
and loads the result into a BigQuery table.

Usage:
    python pipeline.py                          # defaults
    python pipeline.py --cities "London,Paris" --days 7
    python pipeline.py --cities "Tokyo" --days 3 --table my_dataset.weather
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from typing import Optional

import requests
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# City coordinates (extend as needed)
# ---------------------------------------------------------------------------
CITY_COORDS: dict[str, dict] = {
    "London":    {"latitude": 51.5074, "longitude": -0.1278},
    "New York":  {"latitude": 40.7128, "longitude": -74.0060},
    "Tokyo":     {"latitude": 35.6895, "longitude": 139.6917},
    "Mumbai":    {"latitude": 19.0760, "longitude": 72.8777},
    "Sydney":    {"latitude": -33.8688, "longitude": 151.2093},
    "Paris":     {"latitude": 48.8566, "longitude": 2.3522},
    "Dubai":     {"latitude": 25.2048, "longitude": 55.2708},
    "Singapore": {"latitude": 1.3521,  "longitude": 103.8198},
    "Chennai":   {"latitude": 12.9856, "longitude": 80.2614},
    "Salem":  {"latitude": 11.6643, "longitude": 78.1460},
    "Delhi":  {"latitude": 28.6139, "longitude": 77.2090},
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def fetch_weather(city: str, latitude: float, longitude: float,
                  start_date: str, end_date: str) -> dict:
    """
    Call Open-Meteo API for hourly weather variables.
    Returns raw JSON. Raises on HTTP or parse errors.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "windspeed_10m",
            "apparent_temperature",
            "weathercode",
        ],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC",
    }

    log.info(f"Fetching weather data for {city} ({start_date} → {end_date})")
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        log.error(f"Request timed out for {city}")
        raise
    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP error for {city}: {e}")
        raise
    except requests.exceptions.RequestException as e:
        log.error(f"Network error for {city}: {e}")
        raise

    data = response.json()
    if "hourly" not in data:
        raise ValueError(f"Unexpected API response for {city}: 'hourly' key missing. Got: {list(data.keys())}")

    log.info(f"  ✓ Received {len(data['hourly']['time'])} hourly records for {city}")
    return data


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------
WMO_CODE_MAP = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ slight hail",
    99: "Thunderstorm w/ heavy hail",
}


def transform(raw: dict, city: str) -> pd.DataFrame:
    """
    Flatten nested hourly JSON into a tidy DataFrame.
    Adds derived fields for analytical value.
    """
    hourly = raw["hourly"]

    df = pd.DataFrame({
        "timestamp":           hourly["time"],
        "temperature_c":       hourly["temperature_2m"],
        "feels_like_c":        hourly["apparent_temperature"],
        "humidity_pct":        hourly["relative_humidity_2m"],
        "precipitation_mm":    hourly["precipitation"],
        "windspeed_kmh":       hourly["windspeed_10m"],
        "weather_code":        hourly["weathercode"],
    })

    # ---- Parse & clean ----
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])

    numeric_cols = ["temperature_c", "feels_like_c", "humidity_pct",
                    "precipitation_mm", "windspeed_kmh"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["weather_code"] = df["weather_code"].fillna(-1).astype(int)

    # ---- Derived fields ----
    # 1. Human-readable weather description
    df["weather_description"] = df["weather_code"].map(WMO_CODE_MAP).fillna("Unknown")

    # 2. Thermal comfort index: difference between actual and feels-like temp
    #    Negative = feels colder (wind chill); Positive = feels hotter (humidity)
    df["thermal_discomfort_delta"] = (df["feels_like_c"] - df["temperature_c"]).round(2)

    # 3. Hour of day (useful for aggregations like "average temp by hour")
    df["hour_of_day"] = df["timestamp"].dt.hour

    # 4. Date column (for daily aggregations in SQL)
    df["date"] = df["timestamp"].dt.date.astype(str)

    # 5. Is it raining? Boolean flag
    df["is_raining"] = df["precipitation_mm"] > 0

    # 6. Wind category
    df["wind_category"] = pd.cut(
        df["windspeed_kmh"],
        bins=[-1, 5, 19, 38, 61, 88, float("inf")],
        labels=["Calm", "Light breeze", "Moderate breeze", "Fresh breeze", "Strong breeze", "Near gale"],
    ).astype(str)

    # ---- Metadata ----
    df["city"] = city
    df["latitude"] = raw["latitude"]
    df["longitude"] = raw["longitude"]
    df["pipeline_run_date"] = date.today().isoformat()

    log.info(f"  ✓ Transformed {len(df)} rows for {city}")
    return df


# ---------------------------------------------------------------------------
# Load to BigQuery
# ---------------------------------------------------------------------------
def load_to_bigquery(df: pd.DataFrame, table_ref: str,
                     project_id: Optional[str] = None) -> None:
    """
    Append DataFrame to a BigQuery table, creating it if it doesn't exist.
    table_ref format: "dataset.table" or "project.dataset.table"
    """
    client = bigquery.Client(project=project_id)

    schema = [
        bigquery.SchemaField("timestamp",                "TIMESTAMP",  mode="REQUIRED"),
        bigquery.SchemaField("city",                     "STRING",     mode="REQUIRED"),
        bigquery.SchemaField("latitude",                 "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("longitude",                "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("temperature_c",            "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("feels_like_c",             "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("humidity_pct",             "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("precipitation_mm",         "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("windspeed_kmh",            "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("weather_code",             "INT64",      mode="NULLABLE"),
        bigquery.SchemaField("weather_description",      "STRING",     mode="NULLABLE"),
        bigquery.SchemaField("thermal_discomfort_delta", "FLOAT64",    mode="NULLABLE"),
        bigquery.SchemaField("hour_of_day",              "INT64",      mode="NULLABLE"),
        bigquery.SchemaField("date",                     "STRING",     mode="NULLABLE"),
        bigquery.SchemaField("is_raining",               "BOOL",       mode="NULLABLE"),
        bigquery.SchemaField("wind_category",            "STRING",     mode="NULLABLE"),
        bigquery.SchemaField("pipeline_run_date",        "STRING",     mode="NULLABLE"),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        # Skip rows with schema errors rather than failing the whole load
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
    )

    log.info(f"Loading {len(df)} rows → {table_ref}")
    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for completion
        log.info(f"  ✓ Load complete. Table: {table_ref}")
    except GoogleAPIError as e:
        log.error(f"BigQuery load failed: {e}")
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    today = date.today()
    default_start = (today - timedelta(days=6)).isoformat()
    default_end = today.isoformat()

    parser = argparse.ArgumentParser(description="Open-Meteo → BigQuery weather pipeline")
    parser.add_argument(
        "--cities",
        default="London,New York,Tokyo",
        help="Comma-separated city names. Available: " + ", ".join(CITY_COORDS.keys()),
    )
    parser.add_argument("--start-date", default=default_start, help="YYYY-MM-DD (default: 7 days ago)")
    parser.add_argument("--end-date",   default=default_end,   help="YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--table",
        default="weather_pipeline.hourly_weather",
        help="BigQuery table as dataset.table or project.dataset.table",
    )
    parser.add_argument("--project", default=None, help="GCP project ID (optional, uses ADC default)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch & transform only; skip BigQuery load")
    return parser.parse_args()


def main():
    args = parse_args()
    cities = [c.strip() for c in args.cities.split(",")]

    all_dfs = []
    errors = []

    for city in cities:
        if city not in CITY_COORDS:
            log.warning(f"Unknown city '{city}' — skipping. Add it to CITY_COORDS to include it.")
            continue

        coords = CITY_COORDS[city]
        try:
            raw = fetch_weather(
                city=city,
                latitude=coords["latitude"],
                longitude=coords["longitude"],
                start_date=args.start_date,
                end_date=args.end_date,
            )
            df = transform(raw, city)
            all_dfs.append(df)
        except Exception as e:
            log.error(f"Failed to process {city}: {e}")
            errors.append(city)
            continue  # Don't let one city failure kill the whole run

    if not all_dfs:
        log.error("No data collected. Exiting.")
        sys.exit(1)

    combined = pd.concat(all_dfs, ignore_index=True)
    log.info(f"Total rows to load: {len(combined)} across {len(all_dfs)} cities")

    if args.dry_run:
        log.info("Dry run — skipping BigQuery. Sample output:")
        print(combined.head(10).to_string(index=False))
    else:
        load_to_bigquery(combined, args.table, project_id=args.project)

    if errors:
        log.warning(f"The following cities failed and were skipped: {errors}")

    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()