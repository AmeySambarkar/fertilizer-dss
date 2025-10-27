import requests
import pandas as pd
from datetime import datetime

def fetch_imd_weather(lat, lon, start_date, end_date):
    """Fetch daily weather data (IMD-style) via Open-Meteo archive API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    if "daily" not in data:
        raise ValueError(f"Unexpected API response: {data}")

    daily = data["daily"]
    df = pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "tmax_c": daily["temperature_2m_max"],
        "tmin_c": daily["temperature_2m_min"],
        "rainfall_mm": daily["precipitation_sum"]
    })
    return df

def summarize_imd(lat, lon, start_date, end_date, base_temp=10):
    df = fetch_imd_weather(lat, lon, start_date, end_date)
    mean_temp = ((df["tmax_c"] + df["tmin_c"]) / 2).mean()
    df["gdd"] = ((df["tmax_c"] + df["tmin_c"]) / 2 - base_temp).clip(lower=0)
    gdd_sum = df["gdd"].sum()
    total_rain = df["rainfall_mm"].sum()
    return {
        "total_rainfall_mm": float(total_rain),
        "gdd": float(gdd_sum),
        "mean_temp": float(mean_temp)
    }

if __name__ == "__main__":
    res = summarize_imd(18.52, 73.85, "2024-06-01", "2024-09-30")
    print(res)
