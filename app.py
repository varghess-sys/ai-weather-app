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

@st.cache_data(ttl=600)

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
    "wind_speed_10m"
),
"hourly": (
    "temperature_2m,"
    "precipitation_probability,"
    "precipitation"
),
"daily": (
    "temperature_2m_max,"
    "temperature_2m_min,"
    "precipitation_probability_max"
),
"forecast_days": 1,
"timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 429:
       return {
           "error": "rate_limit",
           "message": "The weather API is temporarily busy. Please wait a few minutes and try again."
       }

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
                if "error" in weather_data:
                    st.warning(weather_data["message"])
                    st.stop()
                if weather_data is None:
                    st.stop()
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
