import csv
from pathlib import Path

import requests
import streamlit as st


st.set_page_config(page_title="Weather Buddy AI", page_icon="🌤️")

st.title("🌤️ Weather Buddy AI")
st.write("This app reads demo city data from a CSV file, calls a weather API, and displays live weather data.")


DATA_FILE = Path("data/cities_demo.csv")


def load_cities_from_csv(file_path):
    cities = {}

    with open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            city_name = row["city_name"]
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])

            cities[city_name] = {
                "latitude": latitude,
                "longitude": longitude
            }

    return cities


def get_weather(city_name, cities):
    location = cities[city_name]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": (
    "temperature_2m,"
    "relative_humidity_2m,"
    "apparent_temperature,"
    "precipitation,"
    "rain,"
    "showers,"
    "weather_code,"
    "cloud_cover,"
    "pressure_msl,"
    "wind_speed_10m,"
    "wind_direction_10m,"
    "wind_gusts_10m"
),
"hourly": (
    "temperature_2m,"
    "relative_humidity_2m,"
    "apparent_temperature,"
    "precipitation_probability,"
    "precipitation,"
    "rain,"
    "showers,"
    "cloud_cover,"
    "wind_speed_10m,"
    "wind_gusts_10m,"
    "visibility"
),
"daily": (
    "temperature_2m_max,"
    "temperature_2m_min,"
    "precipitation_probability_max,"
    "precipitation_sum,"
    "rain_sum,"
    "wind_speed_10m_max,"
    "wind_gusts_10m_max,"
    "sunrise,"
    "sunset"
),
"past_days": 2,
"forecast_days": 2,
        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


try:
    cities = load_cities_from_csv(DATA_FILE)

    if not cities:
        st.error("No cities found in the demo data file.")
    else:
        city = st.selectbox("Choose a city", list(cities.keys()))

        if st.button("Get Weather"):
            try:
                weather_data = get_weather(city, cities)
                current = weather_data["current"]

                st.subheader(f"Current weather in {city}")

                st.write(f"Temperature: {current['temperature_2m']} °C")
                st.write(f"Humidity: {current['relative_humidity_2m']}%")
                st.write(f"Wind Speed: {current['wind_speed_10m']} km/h")

                st.subheader("Raw API Response")
                st.json(current)

            except Exception as e:
                st.error(f"Something went wrong while calling the weather API: {e}")

except FileNotFoundError:
    st.error("The demo data file was not found. Please check that data/cities_demo.csv exists.")

except Exception as e:
    st.error(f"Something went wrong while loading the demo data: {e}")
