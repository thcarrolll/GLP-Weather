# weather_data.py
import requests
import datetime
import pytz
import re
import os
import base64
from astral.sun import sun
from astral import LocationInfo
from astral.moon import phase

# Function to convert degrees to cardinal direction
def degrees_to_cardinal(degrees):
    if not isinstance(degrees, (int, float)):
        return "N/A"
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

# Function to format time difference
def format_time_diff(future_time, now):
    if future_time < now:
        return "Past"
    delta = future_time - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if delta.days > 0:
        return f"In {delta.days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"In {hours}h {minutes}m"
    else:
        return f"In {minutes}m"

# Function to encode image to base64
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        return None

# Function to calculate moon phase
def get_moon_phase(date):
    new_moon = datetime.datetime(2025, 3, 29, 10, 58, 0, tzinfo=pytz.UTC)
    now_utc = date.astimezone(pytz.UTC)
    diff = now_utc - new_moon
    days_since_new = diff.total_seconds() / (24 * 3600)
    lunar_cycle = 29.530588
    phase_fraction = (days_since_new % lunar_cycle) / lunar_cycle

    if phase_fraction < 0.02 or phase_fraction >= 0.98:
        return "New Moon"
    elif 0.02 <= phase_fraction < 0.23:
        return "Waxing Crescent"
    elif 0.23 <= phase_fraction < 0.27:
        return "First Quarter"
    elif 0.27 <= phase_fraction < 0.48:
        return "Waxing Gibbous"
    elif 0.48 <= phase_fraction < 0.52:
        return "Full Moon"
    elif 0.52 <= phase_fraction < 0.73:
        return "Waning Gibbous"
    elif 0.73 <= phase_fraction < 0.77:
        return "Last Quarter"
    elif 0.77 <= phase_fraction < 0.98:
        return "Waning Crescent"
    return "Unknown"

# Function to fetch cumulative precipitation from NWS API
def get_nws_precipitation():
    url = "https://api.weather.gov/stations/KGON/observations"
    headers = {"User-Agent": "weather_app"}
    now = datetime.datetime.now(pytz.UTC)
    start_time = now - datetime.timedelta(hours=36)  # Look back 36h to ensure 24h coverage
    params = {
        "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()["features"]
        
        precip_totals = {"1h": 0, "3h": 0, "6h": 0, "12h": 0, "24h": 0}
        hourly_precip = []
        
        for obs in data:
            timestamp = datetime.datetime.fromisoformat(obs["properties"]["timestamp"].replace("+00:00", "Z"))
            raw = obs["properties"]["rawMessage"]
            precip_1h = re.search(r'\bP(\d{4})\b', raw)
            precip_in = int(precip_1h.group(1)) / 100 if precip_1h else 0.0
            hours_ago = (now - timestamp).total_seconds() / 3600
            hourly_precip.append((timestamp, precip_in))
        
        # Sum precipitation over time periods
        for ts, precip in sorted(hourly_precip, reverse=True):
            hours_ago = (now - ts).total_seconds() / 3600
            if hours_ago <= 1:
                precip_totals["1h"] += precip
            if hours_ago <= 3:
                precip_totals["3h"] += precip
            if hours_ago <= 6:
                precip_totals["6h"] += precip
            if hours_ago <= 12:
                precip_totals["12h"] += precip
            if hours_ago <= 24:
                precip_totals["24h"] += precip
        
        return precip_totals
    except Exception as e:
        print(f"Error fetching NWS precipitation: {e}")
        return {"1h": 0.0, "3h": 0.0, "6h": 0.0, "12h": 0.0, "24h": 0.0}

# Function to fetch and parse METAR data for KGON with NWS precipitation
def get_current_conditions():
    # Fetch METAR data
    metar_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
    now = datetime.datetime.now(datetime.UTC)
    params = {
        "station": "KGON",
        "data": "all",
        "year1": now.year,
        "month1": now.month,
        "day1": now.day,
        "year2": now.year,
        "month2": now.month,
        "day2": now.day,
        "tz": "Etc/UTC",
        "format": "onlycomma",
        "latlon": "no",
        "direct": "no",
        "report_type": "1,2",
        "hours": "1"
    }
    headers = {"User-Agent": "weather_app"}
    
    try:
        response = requests.get(metar_url, headers=headers, params=params)
        response.raise_for_status()
        lines = response.text.splitlines()
        if len(lines) < 2:
            raise ValueError("No METAR data returned")
        
        latest_line = lines[-1].split(',')
        metar = latest_line[-2].strip()
        timestamp = latest_line[1]
        
        # Add output for raw METAR data
        print(f"Raw METAR: {metar}")
        
        wind_match = re.search(r'(\d{3})(\d{2})(G(\d{2}))?KT', metar)
        temp_match = re.search(r'(\d{2})/(M?\d{2})', metar)
        vis_match = re.search(r'(\d{1,2})SM', metar)
        sky_match = re.search(r'(CLR|FEW|SCT|BKN|OVC)', metar)
        pressure_match = re.search(r'A(\d{4})', metar)  # Look for altimeter setting (e.g., A2986)
        
        wind_speed_kt = 0
        wind_direction_deg = 0
        wind_gust_kt = 0
        if wind_match:
            wind_direction_deg = float(wind_match.group(1))
            wind_speed_kt = float(wind_match.group(2))
            if wind_match.group(4):
                wind_gust_kt = float(wind_match.group(4))
        wind_speed_mph = round(wind_speed_kt * 1.15078)
        wind_gust_mph = round(wind_gust_kt * 1.15078) if wind_gust_kt > 0 else "N/A"
        
        temperature_c = 0
        if temp_match:
            temp_str = temp_match.group(1)
            dew_str = temp_match.group(2).replace("M", "-")
            temperature_c = float(temp_str)
            dewpoint_c = float(dew_str)
            temperature_f = (temperature_c * 9/5) + 32
            humidity = 100 * (dewpoint_c / temperature_c) if temperature_c != 0 else 50.0
            humidity = min(max(humidity, 0), 100)
        else:
            temperature_f = 50.0
            humidity = 50.0
        
        visibility_mi = float(vis_match.group(1)) if vis_match else 10.0
        cloud_cover = {"CLR": 0, "FEW": 25, "SCT": 50, "BKN": 75, "OVC": 100}.get(sky_match.group(1) if sky_match else "CLR", 0)
        
        # Parse barometric pressure from altimeter setting
        baro_pressure_inhg = 30.0  # Default value
        if pressure_match:
            altimeter_hpa = float(pressure_match.group(1)) / 100  # e.g., A2986 -> 29.86 inHg
            baro_pressure_inhg = altimeter_hpa
            print(f"Parsed Altimeter: A{pressure_match.group(1)} -> {baro_pressure_inhg:.2f} inHg")
        else:
            print("No altimeter setting found in METAR, using default 30.00 inHg")
        
        text_description = "Fair"
        if "TS" in metar:
            text_description = "Thunderstorm"
        elif "RA" in metar:
            text_description = "Rain" if "-RA" in metar else "Heavy Rain"
        elif "SN" in metar:
            text_description = "Snow"
        
        wind_dir_text = degrees_to_cardinal(wind_direction_deg)
        severe_weather = "TS" in metar or "SQ" in metar
        if wind_speed_mph > 25 and not severe_weather:
            if wind_gust_mph == "N/A" or (isinstance(wind_gust_mph, int) and wind_gust_mph <= wind_speed_mph):
                wind_speed_mph = 15
        
        # Fetch cumulative precipitation from NWS API
        precip_totals = get_nws_precipitation()
        
        return {
            "temperature": temperature_f,
            "wind_speed": wind_speed_mph,
            "wind_direction": wind_direction_deg,
            "wind_gust": wind_gust_mph,
            "humidity": humidity,
            "precipitation": precip_totals["1h"],
            "precipitation_totals": precip_totals,
            "visibility": visibility_mi,
            "cloud_cover": cloud_cover,
            "timestamp": timestamp,
            "text_description": text_description,
            "barometric_pressure": baro_pressure_inhg  # Add barometric pressure to the return dict
        }
    except Exception as e:
        print(f"Error fetching METAR data: {e}")
        return {
            "temperature": 50.0,
            "wind_speed": 8,
            "wind_direction": 0,
            "wind_gust": "N/A",
            "humidity": 50.0,
            "precipitation": 0.0,
            "precipitation_totals": {"1h": 0.0, "3h": 0.0, "6h": 0.0, "12h": 0.0, "24h": 0.0},
            "visibility": 10.0,
            "cloud_cover": 0,
            "timestamp": "N/A",
            "text_description": "N/A",
            "barometric_pressure": 30.0  # Default in case of error
        }

# Function to fetch wave height from NDBC Station 44097
def get_wave_height():
    url = "https://www.ndbc.noaa.gov/data/realtime2/44097.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        lines = response.text.splitlines()
        latest_data = lines[2]
        columns = latest_data.split()
        wave_height_m = float(columns[8])
        wave_height_ft = wave_height_m * 3.28084
        timestamp = f"{columns[0]}-{columns[1]}-{columns[2]} {columns[3]}:{columns[4]} UTC"
        return wave_height_ft, timestamp
    except Exception as e:
        return 1.0, "N/A"

# Function to fetch forecast
def get_forecast():
    url = "https://api.weather.gov/gridpoints/OKX/32,34/forecast/hourly"
    headers = {"User-Agent": "weather_app"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        forecast_data = response.json()["properties"]["periods"]
        
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        day_after_tomorrow = today + datetime.timedelta(days=2)
        is_morning = now.hour < 12
        
        periods = []
        if is_morning:
            periods.append(("This Morning", today, 9))
        periods.extend([
            ("This Afternoon", today, 15),
            ("This Evening", today, 21),
            ("Early Morning", tomorrow, 3),
            ("Tomorrow Morning", tomorrow, 9),
            ("Tomorrow Afternoon", tomorrow, 15),
            ("Tomorrow Evening", tomorrow, 21),
            (day_after_tomorrow.strftime('%A') + " Morning", day_after_tomorrow, 9),
            (day_after_tomorrow.strftime('%A') + " Afternoon", day_after_tomorrow, 15),
            (day_after_tomorrow.strftime('%A') + " Evening", day_after_tomorrow, 21)
        ])
        
        icon_dir = "icons"
        available_icons = [f for f in os.listdir(icon_dir) if f.endswith('.png')]
        
        def match_icon(condition):
            condition = condition.lower()
            if "thunderstorm" in condition:
                icon_path = "icons/1530363_thunderstorm_lightning_clouds.png"
            elif "partly sunny" in condition or "partly cloudy" in condition:
                icon_path = "icons/1530391_partly_sunny_partly_cloudy.png"
            elif "rain" in condition or "showers" in condition:
                icon_path = "icons/1530362_cloudy_rain.png"
            elif "snow" in condition:
                icon_path = "icons/1530371_winter_snow_clouds.png"
            elif "cloudy" in condition:
                icon_path = "icons/1530369_cloudy.png"
            elif "fog" in condition:
                icon_path = "icons/1530368_foggy_weather_fog_clouds_cloudy.png"
            elif "clear" in condition:
                icon_path = "icons/1530375_night_clear.png"
            else:
                icon_path = "icons/1530392_weather_sun_sunny_temperature.png"
            base64_icon = image_to_base64(icon_path)
            return base64_icon if base64_icon else icon_path
        
        forecast_periods = []
        for label, target_date, target_hour in periods:
            closest_period = None
            min_diff = float('inf')
            for period in forecast_data:
                start_time = datetime.datetime.fromisoformat(period["startTime"].replace("Z", "+00:00"))
                start_time_edt = start_time.astimezone(pytz.timezone('US/Eastern'))
                if start_time_edt.date() == target_date:
                    diff = abs(start_time_edt.hour - target_hour)
                    if diff < min_diff:
                        min_diff = diff
                        condition = period["shortForecast"]
                        icon = match_icon(condition)
                        closest_period = {
                            "label": label,
                            "time": start_time_edt,
                            "temp": period["temperature"],
                            "conditions": condition,
                            "icon": icon
                        }
            if closest_period:
                forecast_periods.append(closest_period)
        
        return forecast_periods
    except Exception as e:
        return []

# Function to fetch sunrise and sunset times
def get_sun_times():
    try:
        location = LocationInfo("Groton", "USA", "US/Eastern", 41.35, -72.08)
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        s = sun(location.observer, date=now.date(), tzinfo=pytz.timezone('US/Eastern'))
        
        sunrise = s["sunrise"]
        sunset = s["sunset"]
        
        if now > sunset:
            tomorrow = now.date() + datetime.timedelta(days=1)
            s_tomorrow = sun(location.observer, date=tomorrow, tzinfo=pytz.timezone('US/Eastern'))
            sunrise = s_tomorrow["sunrise"]
            sunset = s_tomorrow["sunset"]
        
        return sunrise, sunset
    except Exception as e:
        return None, None

# Function to get next full moon
def get_next_full_moon():
    try:
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        current_date = now.date()
        while True:
            moon_phase = phase(current_date)
            if 13.5 <= moon_phase <= 14.5:
                full_moon_datetime = datetime.datetime.combine(current_date, datetime.time(0, 0), tzinfo=pytz.timezone('US/Eastern'))
                if full_moon_datetime >= now:
                    return full_moon_datetime.strftime('%Y-%m-%d')
                else:
                    current_date += datetime.timedelta(days=1)
            else:
                current_date += datetime.timedelta(days=1)
    except Exception as e:
        return "N/A"

if __name__ == "__main__":
    conditions = get_current_conditions()
    print(f"Current Precipitation (1h): {conditions['precipitation']} inches")
    print(f"Precipitation Totals: {conditions['precipitation_totals']}")
    print(f"Text Description: {conditions['text_description']}")
    print(f"Wind Direction: {conditions['wind_direction']}° ({degrees_to_cardinal(conditions['wind_direction'])})")
    print(f"Wind Speed: {conditions['wind_speed']} MPH")
    print(f"Temperature: {conditions['temperature']}°F")
    print(f"Barometric Pressure: {conditions['barometric_pressure']:.2f} inHg")  # Added for verification