import requests
response = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 13.0827,  # Chennai
        "longitude": 80.2707,
        "hourly": "temperature_2m,relative_humidity_2m",
        "days": 1
    }
)
data = response.json()