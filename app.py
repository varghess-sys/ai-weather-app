import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

## Test changes

st.set_page_config(page_title="Weather Buddy AI", page_icon="🌤️", layout="wide")
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌤️ Weather Buddy AI")
st.caption("Version: City name or coordinates input")

st.caption("Search by city name or coordinates.")


@st.cache_data(ttl=86400)
def geocode_city(city_name):
   ## st.caption("Tip: If the result looks wrong, try the current official city name, for example Mysuru instead of Mysore.")
    """Find latitude and longitude for a city name using Open-Meteo Geocoding API."""

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city_name,
        "count": 10,
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
            "message": f"No matching city or place found for '{city_name}'. "
                        "Enter a specific city or place, not only a state or region. "
                        "Example: Bengaluru, Mysuru, Mangaluru, Delhi, India.",
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
    except Exception as e:
        st.error(f"Something went wrong: {e}")

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
        "past_days": 1,
        "forecast_days": 4,
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

   
def build_weather_advisor(temperature, feels_like, humidity, rain_probability, wind_speed):
    summary_parts = []
    advice_parts = []

    if temperature >= 35:
        summary_parts.append("Very hot")
        advice_parts.append("Avoid long exposure to direct sun and carry water.")
    elif temperature >= 30:
        summary_parts.append("Hot")
        advice_parts.append("It is warm outside, so stay hydrated.")
    elif temperature >= 24:
        summary_parts.append("Warm")
        advice_parts.append("The temperature is comfortable to warm.")
    elif temperature >= 18:
        summary_parts.append("Cool")
        advice_parts.append("The weather is relatively cool.")
    else:
        summary_parts.append("Cold")
        advice_parts.append("You may need an extra layer if going out.")

    if feels_like - temperature >= 3:
        summary_parts.append("Feels warmer")
        advice_parts.append("It may feel warmer than the actual temperature.")

    if humidity >= 80:
        summary_parts.append("Very humid")
        advice_parts.append("High humidity may make it feel sticky and uncomfortable.")
    elif humidity >= 65:
        summary_parts.append("Humid")
        advice_parts.append("Humidity is noticeable, so outdoor activity may feel slightly tiring.")
    else:
        summary_parts.append("Comfortable humidity")

    if rain_probability >= 70:
        summary_parts.append("High rain risk")
        advice_parts.append("Carry an umbrella or rain protection.")
    elif rain_probability >= 40:
        summary_parts.append("Moderate rain risk")
        advice_parts.append("There is some chance of rain, so check before stepping out.")
    else:
        summary_parts.append("Low rain risk")

    if wind_speed >= 25:
        summary_parts.append("Windy")
        advice_parts.append("Expect noticeable wind outside.")
    elif wind_speed >= 15:
        summary_parts.append("Breezy")
    else:
        summary_parts.append("Light wind")

    summary = " • ".join(summary_parts)
    advisor = " ".join(advice_parts)

    return summary, advisor

### place1
def build_forecast_advice(summary):
    advice = []

    if summary["max_rain_probability"] >= 70 or summary["rainfall"] >= 5:
        advice.append("Rain risk is high. Carry an umbrella or rain protection.")
    elif summary["max_rain_probability"] >= 40:
        advice.append("Some rain is possible. Check before stepping out.")
    else:
        advice.append("Rain risk looks low.")

    if summary["max_wind"] >= 25:
        advice.append("It may be windy, so be careful with outdoor plans.")

    if summary["high_temp"] >= 35:
        advice.append("Heat may be uncomfortable. Stay hydrated.")

    return " ".join(advice)
###

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
###

st.subheader("Location Input")

input_method = st.radio(
    "How do you want to search?",
    ["City name", "Coordinates"],
    horizontal=True
)

if "location_results" not in st.session_state:
    st.session_state.location_results = []

if "last_city_search" not in st.session_state:
    st.session_state.last_city_search = ""

city_name = ""
latitude = None
longitude = None
latitude_input = "" 
longitude_input = ""
display_location = ""
selected_location = None

if input_method == "City name":
    city_name = st.text_input(
        "Enter city name or specific place name",
        value="Bengaluru, India",
        help="Example: Bengaluru, Mysuru, Kochi, Delhi, London. Do not enter only a state like Karnataka."
    )

    st.caption(
        "Tip: If the result looks wrong, try a more specific name. "
        "Example: Bengaluru, India or Mysuru, India."
    )

    search_text = city_name.strip()

    if search_text and search_text != st.session_state.last_city_search:
        location_results = geocode_city(search_text)

        if isinstance(location_results, dict) and "error" in location_results:
            st.warning(location_results["message"])
            st.session_state.location_results = []
            st.session_state.last_city_search = search_text
        else:
            st.session_state.location_results = location_results
            st.session_state.last_city_search = search_text

    if st.session_state.location_results:
        st.write(f"Showing matches for: {st.session_state.last_city_search}")

        location_options = {}

        for index, location in enumerate(st.session_state.location_results, start=1):
            name = location.get("name", "")
            admin1 = location.get("admin1", "")
            country = location.get("country", "")
            latitude_value = location.get("latitude")
            longitude_value = location.get("longitude")

            label_parts = [name]

            if admin1:
                label_parts.append(admin1)

            if country:
                label_parts.append(country)

            label = ", ".join(label_parts)
            label = f"{index}. {label} | Lat: {latitude_value}, Lon: {longitude_value}"

            location_options[label] = location

        selected_location_label = st.selectbox(
            "Select the correct location",
            list(location_options.keys())
        )

        selected_location = location_options[selected_location_label]

else:
    st.session_state.location_results = []
    st.session_state.last_city_search = ""

    col_a, col_b = st.columns(2)

    with col_a:
        latitude_input = st.text_input(
            "Enter latitude",
            value="",
            help="Example for Bengaluru: 12.9716"
        )

    with col_b:
        longitude_input = st.text_input(
            "Enter longitude",
            value="",
            help="Example for Bengaluru: 77.5946"
        )


####
if st.button("Get Weather"):
    try:
        if input_method == "City name":
            if selected_location is None:
                st.error("Please click Find Locations and select the correct location first.")
                st.stop()

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

        st.info(
            f"Using location: {display_location} | "
            f"Latitude {latitude}, Longitude {longitude}"
        )

        with st.expander("View location map"):
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

        # Calculate high and low temperature so far today
                
        current_time = pd.to_datetime(current["time"])

        so_far_df = pd.DataFrame(
            {
                "Time": pd.to_datetime(hourly["time"]),
                "Temperature °C": hourly["temperature_2m"],
            }
        )

        so_far_df = so_far_df[so_far_df["Time"] <= current_time]

        if so_far_df.empty:
            so_far_df = pd.DataFrame(
                {
                    "Time": [pd.to_datetime(current["time"])],
                    "Temperature °C": [temperature],
                }
            )

        high_so_far = so_far_df["Temperature °C"].max()
        low_so_far = so_far_df["Temperature °C"].min()

        high_so_far_time = so_far_df.loc[
            so_far_df["Temperature °C"].idxmax(), "Time"
        ].strftime("%I:%M %p").lstrip("0")

        low_so_far_time = so_far_df.loc[
            so_far_df["Temperature °C"].idxmin(), "Time"
        ].strftime("%I:%M %p").lstrip("0")

        st.subheader(f"Weather dashboard: {display_location}")

        st.caption(
            f"Latitude {latitude}, Longitude {longitude}"
        )

        # Compact top metrics
        st.markdown(
            f"""
            <div style="
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 6px;
                margin-top: 12px;
                margin-bottom: 12px;
            ">
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Temp</div>
                    <div style="font-size:20px; font-weight:700;color:white;">{temperature:.1f} °C</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Feels</div>
                    <div style="font-size:20px; font-weight:700;color:white;">{feels_like:.1f} °C</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Humidity</div>
                    <div style="font-size:20px; font-weight:700;color:white;">{humidity}%</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Rain</div>
                    <div style="font-size:20px; font-weight:700;color:white;">{rain_probability_max}%</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Wind</div>
                    <div style="font-size:20px; font-weight:700;color:white;">{wind_speed:.1f} km/h</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Today H/L</div>
                    <div style="font-size:20px; font-weight:700;color:white;">{high_so_far:.1f} / {low_so_far:.1f} °C</div>
                    <div style="font-size:11px; color:#cbd5e1;">H: {high_so_far_time} | L: {low_so_far_time}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Advisor section
        weather_summary, advisor_text = build_weather_advisor(
            temperature,
            feels_like,
            humidity,
            rain_probability_max,
            wind_speed,
        )

        advisor_col1, advisor_col2 = st.columns(2)



        with advisor_col1:
            st.info(f"Weather Summary: {weather_summary}")

        with advisor_col2:
            st.info(f"Advisor: {advisor_text}")

        # Hourly dataframe
        hourly_df = pd.DataFrame(
            {
                "Time": pd.to_datetime(hourly["time"]),
                "Temperature °C": hourly["temperature_2m"],
                "Rain Probability %": hourly["precipitation_probability"],
                "Rain mm": hourly["precipitation"],
                "Wind Speed km/h": hourly["wind_speed_10m"],
            }
        )

        hourly_df["Hour"] = hourly_df["Time"].dt.strftime("%I %p")
        hourly_df = pd.DataFrame(
    {
        "Time": pd.to_datetime(hourly["time"]),
        "Temperature °C": hourly["temperature_2m"],
        "Rain Probability %": hourly["precipitation_probability"],
        "Rain mm": hourly["precipitation"],
        "Wind Speed km/h": hourly["wind_speed_10m"],
    }
)

        hourly_df["Hour"] = hourly_df["Time"].dt.strftime("%I %p")

        # Rolling time windows
        current_time = pd.to_datetime(current["time"])

        last_24h_df = hourly_df[
            (hourly_df["Time"] >= current_time - pd.Timedelta(hours=24)) &
            (hourly_df["Time"] <= current_time)
        ]

        next_24h_df = hourly_df[
            (hourly_df["Time"] > current_time) &
            (hourly_df["Time"] <= current_time + pd.Timedelta(hours=24))
        ]

        next_48h_df = hourly_df[
            (hourly_df["Time"] > current_time) &
            (hourly_df["Time"] <= current_time + pd.Timedelta(hours=48))
        ]

        next_72h_df = hourly_df[
            (hourly_df["Time"] > current_time) &
            (hourly_df["Time"] <= current_time + pd.Timedelta(hours=72))
        ]

        def calculate_forecast_summary(window_df):
            if window_df.empty:
                return {
                    "rainfall": 0,
                    "max_rain_probability": 0,
                    "high_temp": 0,
                    "low_temp": 0,
                    "max_wind": 0,
                }

            return {
                "rainfall": window_df["Rain mm"].sum(),
                "max_rain_probability": window_df["Rain Probability %"].max(),
                "high_temp": window_df["Temperature °C"].max(),
                "low_temp": window_df["Temperature °C"].min(),
                "max_wind": window_df["Wind Speed km/h"].max(),
            }

        next_24h_summary = calculate_forecast_summary(next_24h_df)
        next_48h_summary = calculate_forecast_summary(next_48h_df)
        next_72h_summary = calculate_forecast_summary(next_72h_df)


        last_24h_rain = last_24h_df["Rain mm"].sum()
        last_24h_high = last_24h_df["Temperature °C"].max()
        last_24h_low = last_24h_df["Temperature °C"].min()
        last_24h_max_wind = last_24h_df["Wind Speed km/h"].max()

  # Last 24 hours summary
        current_time = pd.to_datetime(current["time"])
        last_24_start = current_time - pd.Timedelta(hours=24)

        last_24_df = hourly_df[
            (hourly_df["Time"] >= last_24_start) &
            (hourly_df["Time"] <= current_time)
        ]

        if last_24_df.empty:
            last_24_df = hourly_df.head(1)

        rain_last_24h = last_24_df["Rain mm"].sum()
        high_last_24h = last_24_df["Temperature °C"].max()
        low_last_24h = last_24_df["Temperature °C"].min()
        max_wind_last_24h = last_24_df["Wind Speed km/h"].max()

        high_last_24h_time = last_24_df.loc[
            last_24_df["Temperature °C"].idxmax(), "Time"
        ].strftime("%I:%M %p").lstrip("0")

        low_last_24h_time = last_24_df.loc[
            last_24_df["Temperature °C"].idxmin(), "Time"
        ].strftime("%I:%M %p").lstrip("0")

        max_wind_last_24h_time = last_24_df.loc[
            last_24_df["Wind Speed km/h"].idxmax(), "Time"
        ].strftime("%I:%M %p").lstrip("0")

        ####

        st.subheader("Rolling Last 24 Hours Summary")

        st.markdown(
            f"""
            <div style="
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 6px;
                margin-top: 10px;
                margin-bottom: 18px;
            ">
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Rainfall</div>
                    <div style="font-size:20px; font-weight:700; color:white;">{rain_last_24h:.1f} mm</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Highest Temp</div>
                    <div style="font-size:20px; font-weight:700; color:white;">{high_last_24h:.1f} °C</div>
                    <div style="font-size:11px; color:#cbd5e1;">At {high_last_24h_time}</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Lowest Temp</div>
                    <div style="font-size:20px; font-weight:700; color:white;">{low_last_24h:.1f} °C</div>
                    <div style="font-size:11px; color:#cbd5e1;">At {low_last_24h_time}</div>
                </div>
                <div style="background-color:#0f172a; padding:6px; min-height:44px; border-radius:7px;">
                    <div style="font-size:11px; color:#cbd5e1;">Max Wind</div>
                    <div style="font-size:20px; font-weight:700; color:white;">{max_wind_last_24h:.1f} km/h</div>
                    <div style="font-size:11px; color:#cbd5e1;">At {max_wind_last_24h_time}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

            
        ####
        st.subheader("Forecast Summary")

        components.html(
            f"""
            <div style="
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 6px;
                margin-top: 10px;
                margin-bottom: 18px;
            ">

                <div style="background-color:#0f172a;padding:8px;border-radius:8px;line-height:1.25;">
                    <div style="font-size:14px;font-weight:700;color:white;margin-bottom:8px;">Next 24 Hours</div>

                    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px;">
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Rainfall</div>
                            <div style="font-size:18px;font-weight:700;color:white;">{next_24h_summary['rainfall']:.1f} mm</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Rain Chance</div>
                            <div style="font-size:18px;font-weight:700;color:white;">{next_24h_summary['max_rain_probability']:.0f}%</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">High / Low</div>
                            <div style="font-size:16px;font-weight:700;color:white;">{next_24h_summary['high_temp']:.1f} / {next_24h_summary['low_temp']:.1f} °C</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Wind</div>
                            <div style="font-size:16px;font-weight:700;color:white;">{next_24h_summary['max_wind']:.1f} km/h</div>
                        </div>
                    </div>

                    <div style="font-size:11px;color:#93c5fd;margin-top:8px;">
                        {build_forecast_advice(next_24h_summary)}
                    </div>
                </div>

                <div style="background-color:#0f172a;padding:8px;border-radius:8px;line-height:1.25;">
                    <div style="font-size:14px;font-weight:700;color:white;margin-bottom:8px;">Next 48 Hours</div>

                    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px;">
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Rainfall</div>
                            <div style="font-size:18px;font-weight:700;color:white;">{next_48h_summary['rainfall']:.1f} mm</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Rain Chance</div>
                            <div style="font-size:18px;font-weight:700;color:white;">{next_48h_summary['max_rain_probability']:.0f}%</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">High / Low</div>
                            <div style="font-size:16px;font-weight:700;color:white;">{next_48h_summary['high_temp']:.1f} / {next_48h_summary['low_temp']:.1f} °C</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Wind</div>
                            <div style="font-size:16px;font-weight:700;color:white;">{next_48h_summary['max_wind']:.1f} km/h</div>
                        </div>
                    </div>

                    <div style="font-size:11px;color:#93c5fd;margin-top:8px;">
                        {build_forecast_advice(next_48h_summary)}
                    </div>
                </div>
                <div style="background-color:#0f172a;padding:8px;border-radius:8px;line-height:1.25;">
                    <div style="font-size:14px;font-weight:700;color:white;margin-bottom:8px;">Next 72 Hours</div>

                    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px;">
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Rainfall</div>
                            <div style="font-size:18px;font-weight:700;color:white;">{next_72h_summary['rainfall']:.1f} mm</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Rain Chance</div>
                            <div style="font-size:18px;font-weight:700;color:white;">{next_72h_summary['max_rain_probability']:.0f}%</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">High / Low</div>
                            <div style="font-size:16px;font-weight:700;color:white;">{next_72h_summary['high_temp']:.1f} / {next_72h_summary['low_temp']:.1f} °C</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#cbd5e1;">Wind</div>
                            <div style="font-size:16px;font-weight:700;color:white;">{next_72h_summary['max_wind']:.1f} km/h</div>
                        </div>
                    </div>

                    <div style="font-size:11px;color:#93c5fd;margin-top:8px;">
                        {build_forecast_advice(next_72h_summary)}
                    </div>
                </div>

            </div>
            """,
            height=230,
        )
        
        # Keep charts compact by showing only the next 12 hours
        current_time = pd.to_datetime(current["time"])
      
        compact_hourly_df = hourly_df[hourly_df["Time"] >= current_time].head(12)

        if compact_hourly_df.empty:
            compact_hourly_df = hourly_df.head(12)
        
        st.subheader("Next 12 hours Trend")

        chart_col1, chart_col2, chart_col3 = st.columns(3)

        with chart_col1:
            st.write("Temperature")
            st.line_chart(
                compact_hourly_df,
                x="Time",
                y="Temperature °C",
                height=180,
            )

        with chart_col2:
            st.write("Rain probability")
            st.line_chart(
                compact_hourly_df,
                x="Time",
                y="Rain Probability %",
                height=180,
            )

        with chart_col3:
            st.write("Wind speed")
            st.line_chart(
                compact_hourly_df,
                x="Time",
                y="Wind Speed km/h",
                height=180,
            )

        with st.expander("View hourly data table"):
            st.dataframe(hourly_df)

        with st.expander("Raw API Response"):
            st.json(current)

    except Exception as e:
        st.error(f"Something went wrong: {e}")


