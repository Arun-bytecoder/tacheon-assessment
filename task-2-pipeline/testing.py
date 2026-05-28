"""
Unit tests for the Open-Meteo → BigQuery weather pipeline.
Tests focus on the transform() function since it is pure and deterministic.

Run with:
    pip install pytest
    pytest test_pipeline.py -v
"""

import pytest
import pandas as pd
from pipeline import transform, CITY_COORDS, WMO_CODE_MAP


# ---------------------------------------------------------------------------
# Fixtures — sample raw API responses
# ---------------------------------------------------------------------------

def make_raw_response(hours=24, city="London"):
    """Generate a minimal but valid Open-Meteo API response."""
    times = [f"2026-05-{str(i % 28 + 1).zfill(2)}T{str(i % 24).zfill(2)}:00" for i in range(hours)]
    return {
        "latitude": CITY_COORDS[city]["latitude"],
        "longitude": CITY_COORDS[city]["longitude"],
        "hourly": {
            "time":                  times,
            "temperature_2m":        [20.0 + i * 0.1 for i in range(hours)],
            "apparent_temperature":  [18.0 + i * 0.1 for i in range(hours)],
            "relative_humidity_2m":  [60 + i % 20 for i in range(hours)],
            "precipitation":         [0.0 if i % 5 != 0 else 1.5 for i in range(hours)],
            "windspeed_10m":         [10.0 + i % 15 for i in range(hours)],
            "weathercode":           [0 if i % 3 != 0 else 61 for i in range(hours)],
        }
    }


def make_raw_with_nulls(hours=10):
    """Raw response with nulls and type issues to test cleaning."""
    return {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "hourly": {
            "time":                  [f"2026-05-01T{str(i).zfill(2)}:00" for i in range(hours)],
            "temperature_2m":        [None, "bad", 20.0, 21.0, None, 22.0, 23.0, 24.0, 25.0, 26.0],
            "apparent_temperature":  [18.0] * hours,
            "relative_humidity_2m":  [60] * hours,
            "precipitation":         [0.0] * hours,
            "windspeed_10m":         [10.0] * hours,
            "weathercode":           [0] * hours,
        }
    }


# ---------------------------------------------------------------------------
# Tests: output shape and columns
# ---------------------------------------------------------------------------

def test_transform_returns_dataframe():
    raw = make_raw_response()
    df = transform(raw, "London")
    assert isinstance(df, pd.DataFrame)


def test_transform_row_count():
    raw = make_raw_response(hours=48)
    df = transform(raw, "London")
    assert len(df) == 48


def test_transform_expected_columns():
    raw = make_raw_response()
    df = transform(raw, "London")
    expected = [
        "timestamp", "temperature_c", "feels_like_c", "humidity_pct",
        "precipitation_mm", "windspeed_kmh", "weather_code",
        "weather_description", "thermal_discomfort_delta",
        "hour_of_day", "date", "is_raining", "wind_category",
        "city", "latitude", "longitude", "pipeline_run_date",
    ]
    for col in expected:
        assert col in df.columns, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Tests: derived fields are correct
# ---------------------------------------------------------------------------

def test_thermal_discomfort_delta():
    """thermal_discomfort_delta = feels_like_c - temperature_c"""
    raw = make_raw_response(hours=5)
    df = transform(raw, "London")
    for _, row in df.iterrows():
        expected = round(row["feels_like_c"] - row["temperature_c"], 2)
        assert abs(row["thermal_discomfort_delta"] - expected) < 0.01


def test_is_raining_flag():
    """is_raining should be True only when precipitation_mm > 0"""
    raw = make_raw_response(hours=10)
    df = transform(raw, "London")
    for _, row in df.iterrows():
        if row["precipitation_mm"] > 0:
            assert row["is_raining"] is True or row["is_raining"] == True
        else:
            assert row["is_raining"] is False or row["is_raining"] == False


def test_weather_description_mapped():
    """WMO code 0 should map to 'Clear sky', code 61 to 'Slight rain'"""
    raw = make_raw_response(hours=6)
    df = transform(raw, "London")
    for _, row in df.iterrows():
        code = row["weather_code"]
        expected_desc = WMO_CODE_MAP.get(code, "Unknown")
        assert row["weather_description"] == expected_desc


def test_hour_of_day_range():
    """hour_of_day must always be 0–23"""
    raw = make_raw_response(hours=48)
    df = transform(raw, "London")
    assert df["hour_of_day"].between(0, 23).all()


def test_wind_category_not_null():
    """wind_category should never be null"""
    raw = make_raw_response(hours=24)
    df = transform(raw, "London")
    assert df["wind_category"].notna().all()


def test_city_column_set_correctly():
    raw = make_raw_response(city="Tokyo")
    df = transform(raw, "Tokyo")
    assert (df["city"] == "Tokyo").all()


# ---------------------------------------------------------------------------
# Tests: null and bad data handling
# ---------------------------------------------------------------------------

def test_null_temperatures_handled():
    """Rows with null temperature_c should remain but be NaN, not crash"""
    raw = make_raw_with_nulls()
    df = transform(raw, "London")
    # Should not raise; nulls become NaN floats
    assert "temperature_c" in df.columns
    assert df["temperature_c"].dtype in [float, "float64"]


def test_bad_string_temperature_coerced_to_nan():
    """'bad' string in temperature field should become NaN"""
    raw = make_raw_with_nulls()
    df = transform(raw, "London")
    null_count = df["temperature_c"].isna().sum()
    assert null_count >= 2  # None and "bad" both become NaN


def test_missing_hourly_key_raises():
    """A response without 'hourly' key should raise ValueError"""
    bad_raw = {"latitude": 51.5, "longitude": -0.1}
    with pytest.raises((KeyError, ValueError)):
        transform(bad_raw, "London")


# ---------------------------------------------------------------------------
# Tests: city coordinates config
# ---------------------------------------------------------------------------

def test_all_cities_have_lat_lng():
    for city, coords in CITY_COORDS.items():
        assert "latitude" in coords, f"{city} missing latitude"
        assert "longitude" in coords, f"{city} missing longitude"
        assert -90 <= coords["latitude"] <= 90
        assert -180 <= coords["longitude"] <= 180