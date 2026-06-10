import pandas as pd
import requests
import streamlit as st
## Test changes

st.set_page_config(page_title="Weather Buddy AI", page_icon="🌤️", layout="wide")

st.title("🌤️ Weather Buddy AI")
st.caption("Version: City name or coordinates input")

st.write(
    "Enter a city name, or provide latitude and longitude directly. "
    "If latitude and longitude are not provided, the app will find them using Open-Meteo's Geocoding API."
)


@st.cache_data(ttl=86400)
def geocode_city(city_name):
    """Find latitude and longitude for a city name using Open-Meteo Geocoding API."""

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city_name,
        "count": 5,
        "language": "en",
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 429:
        return {
            "error": "rate_limit",
            "message": "The location lookup API is temporarily busy. Please wait a few minutes and try again.",
        }

    response.raise_for_status()
    data = response.json()

    if "results" not in data or not data["results"]:
        return {
            "error": "not_found",
            "message": f"No matching location found for '{city_name}'. Try a more specific name like 'Bangalore, India'.",
        }

    return data["results"]

@st.cache_data(ttl=86400)
def reverse_geocode(latitude, longitude):
    """Find place name from latitude and longitude."""

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 10,
    }

    headers = {
        "User-Agent": "weather-buddy-ai-learning-app"
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)

    if response.status_code == 429:
        return "Place lookup is temporarily busy. Showing coordinates only."

    if response.status_code == 404:
        return "Unknown place"

    response.raise_for_status()
    data = response.json()

    if data.get("display_name"):
        return data["display_name"]

    return "Unknown place"


def validate_coordinates(latitude_text, longitude_text):
    """Validate latitude and longitude entered as text."""

    latitude_text = latitude_text.strip()
    longitude_text = longitude_text.strip()

    if not latitude_text and not longitude_text:
        return None, None, "Please enter both latitude and longitude."

    if latitude_text and not longitude_text:
        return None, None, "Please enter longitude also, or use city name instead."

    if longitude_text and not latitude_text:
        return None, None, "Please enter latitude also, or use city name instead."

    try:
        latitude = float(latitude_text)
        longitude = float(longitude_text)
    except ValueError:
        return None, None, "Latitude and longitude must be valid numbers. Example: 12.9716 and 77.5946."

    if latitude < -90 or latitude > 90:
        return None, None, "Latitude must be between -90 and 90."

    if longitude < -180 or longitude > 180:
        return None, None, "Longitude must be between -180 and 180."

    return latitude, longitude, None


@st.cache_data(ttl=600)
def get_weather(latitude, longitude):
    """Get weather details from Open-Meteo Forecast API."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
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
            "precipitation,"
            "wind_speed_10m"
        ),
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "forecast_days": 1,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 429:
        return {
            "error": "rate_limit",
            "message": "The weather API is temporarily busy. Please wait a few minutes and try again.",
        }

    response.raise_for_status()
    return response.json()


def make_simple_advice(temperature, humidity, rain_probability, wind_speed):
    advice = []

    if temperature >= 32:
        advice.append("It is quite hot. Carry water and avoid too much direct sun.")
    elif temperature >= 25:
        advice.append("The temperature is warm.")
    else:
        advice.append("The weather is relatively cool.")

    if humidity >= 70:
        advice.append("Humidity is high, so it may feel sticky or uncomfortable.")
    else:
        advice.append("Humidity is moderate.")

    if rain_probability >= 60:
        advice.append("There is a good chance of rain today, so carry an umbrella.")
    elif rain_probability >= 30:
        advice.append("There is some chance of rain today.")
    else:
        advice.append("Rain chance looks low for now.")

    if wind_speed >= 20:
        advice.append("It may feel windy outside.")

    return " ".join(advice)


with st.expander("How this app works"):
    st.write(
        """
        1. The user enters a city name.
        2. If latitude and longitude are provided, the app uses them directly.
        3. If coordinates are not provided, the app uses Open-Meteo Geocoding API to find them.
        4. The app calls the Open-Meteo Weather API using latitude and longitude.
        5. The app displays weather cards, rain probability, weather advice, and hourly trends.
        """
    )


st.subheader("Location Input")

input_method = st.radio(
    "How do you want to search?",
    ["City name", "Coordinates"],
    horizontal=True
)

latitude = None
longitude = None
latitude_input = ""
longitude_input = ""
display_location = ""

if input_method == "City name":
    city_name = st.text_input(
        "Enter city name",
        value="Bangalore",
        help="Example: Bangalore, Kochi, London, New York, Paris"
    )

else:
    col_a, col_b = st.columns(2)

    with col_a:
        latitude_input = st.text_input(
            "Enter latitude",
            value="",
            help="Example for Bangalore: 12.9716"
        )

    with col_b:
        longitude_input = st.text_input(
            "Enter longitude",
            value="",
            help="Example for Bangalore: 77.5946"
        )


if st.button("Get Weather"):
    try:
        if input_method == "City name":
            if not city_name.strip():
                st.error("Please enter a city name.")
                st.stop()

            location_results = geocode_city(city_name.strip())

            if isinstance(location_results, dict) and "error" in location_results:
                st.warning(location_results["message"])
                st.stop()

            selected_location = location_results[0]

            latitude = selected_location["latitude"]
            longitude = selected_location["longitude"]

            display_location_parts = [selected_location.get("name", "")]

            if selected_location.get("admin1"):
                display_location_parts.append(selected_location["admin1"])

            if selected_location.get("country"):
                display_location_parts.append(selected_location["country"])

            display_location = ", ".join(display_location_parts)

        else:
            latitude, longitude, coordinate_error = validate_coordinates(
                latitude_input,
                longitude_input
            )

            if coordinate_error:
                st.error(coordinate_error)
                st.stop()

            place_name = reverse_geocode(latitude, longitude)
            display_location = place_name

        st.info(f"Using location: {display_location} | "
                f"Latitude {latitude}, Longitude {longitude}"
            )

        st.map(
            {
                "lat": [latitude],
                "lon": [longitude],
            }
        )

        weather_data = get_weather(latitude, longitude)

        if "error" in weather_data:
            st.warning(weather_data["message"])
            st.stop()

        current = weather_data["current"]
        hourly = weather_data["hourly"]
        daily = weather_data["daily"]

        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        feels_like = current["apparent_temperature"]
        rain_now = current["precipitation"]
        wind_speed = current["wind_speed_10m"]

        today_high = daily["temperature_2m_max"][0]
        today_low = daily["temperature_2m_min"][0]
        rain_probability_max = daily["precipitation_probability_max"][0]

        st.subheader(f"Current weather in {display_location}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Temperature", f"{temperature} °C")

        with col2:
            st.metric("Feels Like", f"{feels_like} °C")

        with col3:
            st.metric("Humidity", f"{humidity}%")

        with col4:
            st.metric("Wind Speed", f"{wind_speed} km/h")

        st.subheader("Today's Weather Range")

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            st.metric("Today's High", f"{today_high} °C")

        with col6:
            st.metric("Today's Low", f"{today_low} °C")

        with col7:
            st.metric("Rain Now", f"{rain_now} mm")

        with col8:
            st.metric("Max Rain Chance", f"{rain_probability_max}%")

        st.subheader("Simple Weather Advice")
        advice = make_simple_advice(
            temperature,
            humidity,
            rain_probability_max,
            wind_speed,
        )
        st.info(advice)



        st.subheader("Hourly Trends for Today")

        hourly_df = pd.DataFrame({
            "Time": pd.to_datetime(hourly["time"]),
            "Temperature °C": hourly["temperature_2m"],
            "Rain Probability %": hourly["precipitation_probability"],
            "Rain mm": hourly["precipitation"],
            "Wind Speed km/h": hourly["wind_speed_10m"],
        })

        hourly_df["Hour"] = hourly_df["Time"].dt.strftime("%I %p")

        st.write("Temperature trend")
        st.line_chart(hourly_df,x="Hour", y="Temperature °C")

        st.write("Rain probability trend")
        st.line_chart(hourly_df, x="Hour",y="Rain Probability %")
        

        st.write("Wind speed trend")
        st.line_chart(hourly_df,x="Hour",y="Wind Speed km/h")
        

        with st.expander("View hourly data table"):
             st.dataframe(hourly_df)

        with st.expander("Raw API Response"):
             st.json(current)

    except ValueError:
        st.error("Latitude and longitude must be valid numbers. Example: 12.9716 and 77.5946")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
