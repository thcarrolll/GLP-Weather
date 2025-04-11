# weather_data.py
import requests
import datetime
import pytz
import base64
import os
import csv
from astral import LocationInfo
from astral.sun import sun
from math import floor, sin, pi

# Function to convert degrees to cardinal direction (e.g., 0° = N, 90° = E)
def degrees_to_cardinal(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(degrees / (360. / len(directions)))
    return directions[ix % len(directions)]

# Function to format time difference (e.g., "in 2h 30m")
def format_time_diff(target_time, current_time):
    diff = target_time - current_time
    total_seconds = int(diff.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"in {hours}h {minutes}m"
    elif minutes > 0:
        return f"in {minutes}m"
    else:
        return "now"

# Function to convert image file to base64 string for dashboard display
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    except Exception as e:
        print(f"[DEBUG] Image Error: {e}")
        return None

# Function to get current weather conditions from NWS API
def get_current_conditions():
    nws_url = "https://api.weather.gov/stations/KGON/observations"  # Weather station KGON (Groton, CT)
    headers = {"User-Agent": "weather_app"}  # Identify our app to the API
    now = datetime.datetime.now(pytz.UTC)  # Current time in UTC
    
    try:
        # Fetch the latest observation from NWS API
        nws_response = requests.get(nws_url, headers=headers, params={"limit": 1})
        nws_response.raise_for_status()  # Raise an error if the request fails
        nws_data = nws_response.json()["features"][0]["properties"]
        
        # Try to use textDescription if available and non-empty
        text_description = nws_data["textDescription"] or None
        
        # If textDescription is empty, construct a verbose description
        if not text_description:
            # Gather data from API response
            precip_last_hour = nws_data.get("precipitationLastHour", {}).get("value", 0)  # mm
            cloud_layers = nws_data.get("cloudLayers", [])
            wind_speed_kmh = nws_data["windSpeed"]["value"] if nws_data["windSpeed"]["value"] is not None else 0
            wind_speed_mph = round(wind_speed_kmh * 0.621371)  # Convert km/h to mph
            visibility_m = nws_data["visibility"]["value"] if nws_data["visibility"]["value"] is not None else 16093.4
            visibility_mi = round(visibility_m / 1609.34, 1)  # Convert meters to miles
            present_weather = nws_data.get("presentWeather", [])
            
            # Initialize description components
            weather_terms = []
            cloud_term = ""
            qualifier = ""
            
            # Check for precipitation in the last hour
            if precip_last_hour > 0:
                if precip_last_hour < 2.5:
                    weather_terms.append("Light Rain")
                elif precip_last_hour < 7.6:
                    weather_terms.append("Moderate Rain")
                else:
                    weather_terms.append("Heavy Rain")
            
            # Check presentWeather codes (e.g., RA=rain, FG=fog)
            for pw in present_weather:
                code = pw.get("weather", "").upper()
                if code.startswith("RA"):
                    if "Light Rain" not in weather_terms:
                        weather_terms.append("Light Rain" if "-RA" in code else "Rain")
                elif code.startswith("SN"):
                    weather_terms.append("Snow")
                elif code in ("FG", "BR"):
                    weather_terms.append("Fog")
                elif code == "HZ":
                    weather_terms.append("Haze")
            
            # Determine cloud cover
            if cloud_layers:
                top_layer = cloud_layers[-1]["amount"]
                cloud_map = {
                    "CLR": "Clear",
                    "FEW": "Mostly Clear",
                    "SCT": "Partly Cloudy",
                    "BKN": "Mostly Cloudy",
                    "OVC": "Overcast"
                }
                cloud_term = cloud_map.get(top_layer, "Cloudy")
            else:
                # Infer cloud cover if no cloud data
                cloud_term = "Clear" if visibility_mi > 5 and not weather_terms else "Cloudy"
            
            # Add wind qualifier
            if wind_speed_mph > 15:
                qualifier = "Breezy"
            elif wind_speed_mph > 25:
                qualifier = "Windy"
            
            # Construct verbose description
            if weather_terms:
                # Use precipitation or weather events if present
                main_term = weather_terms[0]  # First weather condition (e.g., "Light Rain")
                if cloud_term in ("Cloudy", "Mostly Cloudy", "Overcast"):
                    text_description = f"{main_term} with {cloud_term} Skies"
                else:
                    text_description = main_term
            else:
                # No precipitation; use cloud cover
                text_description = f"{cloud_term} Conditions"
            
            # Add qualifier if applicable
            if qualifier:
                text_description = f"{qualifier} {text_description}"
            
            # Add "Likely" for precipitation if recent but not current
            if precip_last_hour > 0 and not any(t in weather_terms for t in ["Rain", "Snow"]):
                text_description = f"{text_description} Likely"
            
            # Handle fog based on visibility
            if visibility_mi < 1 and "Fog" not in text_description:
                text_description = f"Foggy with {text_description}"
            
            # Default if still empty
            if not text_description:
                text_description = "Clear Conditions"
        
        # Calculate remaining weather metrics
        temperature_c = nws_data["temperature"]["value"] if nws_data["temperature"]["value"] is not None else 0
        temperature_f = round((temperature_c * 9/5) + 32, 1)  # Convert Celsius to Fahrenheit
        wind_speed_kmh = nws_data["windSpeed"]["value"] if nws_data["windSpeed"]["value"] is not None else 0
        wind_speed_mph = round(wind_speed_kmh * 0.621371)
        wind_direction_deg = nws_data["windDirection"]["value"] if nws_data["windDirection"]["value"] is not None else 0
        wind_gust_kmh = nws_data["windGust"]["value"] if nws_data["windGust"]["value"] is not None else 0
        wind_gust_mph = round(wind_gust_kmh * 0.621371) if wind_gust_kmh else "N/A"
        humidity = nws_data["relativeHumidity"]["value"] if nws_data["relativeHumidity"]["value"] is not None else 50.0
        visibility_m = nws_data["visibility"]["value"] if nws_data["visibility"]["value"] is not None else 16093.4
        visibility_mi = round(visibility_m / 1609.34, 1)
        baro_pressure_pa = nws_data["barometricPressure"]["value"] if nws_data["barometricPressure"]["value"] is not None else 101325
        baro_pressure_inhg = round(baro_pressure_pa / 3386.39, 2)  # Convert Pa to inHg
        
        # Calculate cloud cover percentage for gauge
        cloud_layers = nws_data.get("cloudLayers", [])
        cloud_cover = 0
        if cloud_layers:
            top_layer = cloud_layers[-1]["amount"]
            cloud_cover_map = {"CLR": 0, "FEW": 25, "SCT": 50, "BKN": 75, "OVC": 100}
            cloud_cover = cloud_cover_map.get(top_layer, 0)
        else:
            cloud_cover = 100 if "Cloudy" in text_description.lower() or "overcast" in text_description.lower() else (50 if "partly" in text_description.lower() else 0)

        # Get precipitation totals
        precip_totals = get_nws_precipitation()

        # Build the result dictionary
        result = {
            "temperature": temperature_f,
            "wind_speed": wind_speed_mph,
            "wind_direction": wind_direction_deg,
            "wind_gust": wind_gust_mph,
            "humidity": humidity,
            "precipitation": precip_totals["1h"],
            "precipitation_totals": precip_totals,
            "visibility": visibility_mi,
            "cloud_cover": cloud_cover,
            "timestamp": nws_data["timestamp"],
            "text_description": text_description,
            "barometric_pressure": baro_pressure_inhg
        }

        # Debug output to see what’s happening
        print(f"[DEBUG] NWS Raw Data: {nws_data}")
        print(f"[DEBUG] NWS textDescription: {text_description}")
        print(f"[DEBUG] NWS Cloud Cover: {cloud_cover}%")
        print(f"[DEBUG] NWS Returned Conditions: {result}")

        return result

    except Exception as e:
        print(f"[DEBUG] NWS Error: {e}")
        # Default values if the API fails
        result = {
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
            "text_description": "Clear Conditions",  # Verbose default
            "barometric_pressure": 30.0
        }
        print(f"[DEBUG] NWS Default Conditions: {result}")
        return result

# Function to get precipitation totals from NWS API
def get_nws_precipitation():
    nws_url = "https://api.weather.gov/stations/KGON/observations"
    headers = {"User-Agent": "weather_app"}
    try:
        nws_response = requests.get(nws_url, headers=headers, params={"limit": 24})
        nws_response.raise_for_status()
        observations = nws_response.json()["features"]
        
        precip_totals = {"1h": 0.0, "3h": 0.0, "6h": 0.0, "12h": 0.0, "24h": 0.0}
        now = datetime.datetime.now(pytz.UTC)
        
        for obs in observations:
            props = obs["properties"]
            timestamp = datetime.datetime.fromisoformat(props["timestamp"].replace("Z", "+00:00"))
            precip = props.get("precipitationLastHour", {}).get("value", 0) or 0
            time_diff = (now - timestamp).total_seconds() / 3600  # Hours ago
            
            if time_diff <= 1:
                precip_totals["1h"] += precip
            if time_diff <= 3:
                precip_totals["3h"] += precip
            if time_diff <= 6:
                precip_totals["6h"] += precip
            if time_diff <= 12:
                precip_totals["12h"] += precip
            if time_diff <= 24:
                precip_totals["24h"] += precip
        
        # Convert mm to inches
        for key in precip_totals:
            precip_totals[key] = round(precip_totals[key] / 25.4, 2)
        
        return precip_totals
    except Exception as e:
        print(f"[DEBUG] NWS Precip Error: {e}")
        return {"1h": 0.0, "3h": 0.0, "6h": 0.0, "12h": 0.0, "24h": 0.0}

# Function to get wave height (placeholder, replace with your actual implementation)
def get_wave_height():
    try:
        response = requests.get("https://api.example.com/wave_height", headers={"User-Agent": "weather_app"})
        response.raise_for_status()
        data = response.json()
        wave_height = data.get("waveHeight", 0)
        timestamp = data.get("timestamp", "N/A")
        return wave_height, timestamp
    except Exception as e:
        print(f"[DEBUG] Wave Height Error: {e}")
        return 0, "N/A"

# Function to get upcoming weather forecast from NWS API
def get_forecast():
    url = "https://api.weather.gov/gridpoints/OKX/32,34/forecast/hourly"  # Forecast for grid OKX/32,34
    headers = {"User-Agent": "weather_app"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        forecast_data = response.json()["properties"]["periods"]
        
        # Set up time periods for forecast (e.g., This Afternoon, Tomorrow Morning)
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
            (day_after_tomorrow.strftime('%A') + " Afternoon", day_after_tomorrow, 9),  # Note: Should be 15?
            (day_after_tomorrow.strftime('%A') + " Evening", day_after_tomorrow, 21)
        ])
        
        # Directory for weather icons
        icon_dir = "icons"
        available_icons = [f for f in os.listdir(icon_dir) if f.endswith('.png')]
        
        # Function to match weather condition to an icon
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
        
        # Build forecast periods
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
                        condition = period["shortForecast"]  # Keep verbose description
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
                print(f"[DEBUG] Forecast Period: {closest_period['label']}, Conditions: {closest_period['conditions']}")
        
        return forecast_periods
    except Exception as e:
        print(f"[DEBUG] Forecast Error: {e}")
        return []

# Function to get sunrise and sunset times for Groton, CT
def get_sun_times():
    try:
        # Define location: Groton, CT (latitude 41.3148, longitude -72.0076)
        location = LocationInfo("Groton", "USA", "US/Eastern", 41.3148, -72.0076)
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        # Calculate sun times for today
        s = sun(location.observer, date=now.date(), tzinfo=pytz.timezone('US/Eastern'))
        sunrise = s['sunrise']
        sunset = s['sunset']
        print(f"[DEBUG] Sunrise: {sunrise}, Sunset: {sunset}")
        return sunrise, sunset
    except Exception as e:
        print(f"[DEBUG] Sun Times Error: {e}")
        return None, None

# Function to calculate days since last new moon (approximation)
def days_since_new_moon(date):
    # Reference new moon: January 6, 2000 (approximate)
    reference_date = datetime.date(2000, 1, 6)
    delta = (date - reference_date).days
    lunar_cycle = 29.530588  # Average length of lunar cycle in days
    days_since = delta % lunar_cycle
    return days_since

# Function to get moon phase
def get_moon_phase(date):
    try:
        days = days_since_new_moon(date.date())
        cycle_length = 29.530588
        phase_fraction = days / cycle_length
        phase_degrees = phase_fraction * 360
        phase = floor((phase_degrees + 22.5) / 45) % 8  # Divide into 8 phases
        
        phase_names = [
            "New Moon",
            "Waxing Crescent",
            "First Quarter",
            "Waxing Gibbous",
            "Full Moon",
            "Waning Gibbous",
            "Last Quarter",
            "Waning Crescent"
        ]
        phase_name = phase_names[phase]
        print(f"[DEBUG] Moon Phase for {date}: {phase_name} (Days since new moon: {days:.2f})")
        return phase_name
    except Exception as e:
        print(f"[DEBUG] Moon Phase Error: {e}")
        return "Unknown"

# Function to get the next full moon
def get_next_full_moon():
    try:
        now = datetime.datetime.now(pytz.timezone('US/Eastern')).date()
        days_since = days_since_new_moon(now)
        lunar_cycle = 29.530588
        # Full moon is roughly at 14.765 days into the cycle
        days_to_full = (14.765 - days_since) % lunar_cycle
        if days_to_full < 0:
            days_to_full += lunar_cycle
        full_moon_date = now + datetime.timedelta(days=days_to_full)
        full_moon_str = full_moon_date.strftime('%Y-%m-%d')
        print(f"[DEBUG] Next Full Moon: {full_moon_str} (Days to full: {days_to_full:.2f})")
        return full_moon_str
    except Exception as e:
        print(f"[DEBUG] Next Full Moon Error: {e}")
        return "Unknown"

# Function to get current weather advisories from NWS API for Groton, CT
def get_weather_advisories():
    url = "https://api.weather.gov/alerts/active?point=41.3148,-72.0076"  # Groton, CT coordinates
    headers = {"User-Agent": "weather_app"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        alerts = data.get("features", [])
        if not alerts:
            return [{"message": "No active weather advisories for Groton, CT."}]
        
        # Process active alerts
        advisories = []
        for alert in alerts:
            props = alert.get("properties", {})
            event = props.get("event", "Unknown Alert")
            severity = props.get("severity", "Unknown")
            headline = props.get("headline", "No headline available")
            description = props.get("description", "No description available").strip()
            effective = props.get("effective", "N/A")
            expires = props.get("expires", "N/A")
            # Convert UTC times to Eastern Time
            if effective != "N/A":
                effective_dt = datetime.datetime.fromisoformat(effective.replace("Z", "+00:00")).astimezone(pytz.timezone('US/Eastern'))
                effective = effective_dt.strftime("%I:%M %p on %b %d").lstrip("0")
            if expires != "N/A":
                expires_dt = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00")).astimezone(pytz.timezone('US/Eastern'))
                expires = expires_dt.strftime("%I:%M %p on %b %d").lstrip("0")
            
            advisories.append({
                "event": event,
                "severity": severity,
                "headline": headline,
                "description": description,
                "effective": effective,
                "expires": expires
            })
            print(f"[DEBUG] Advisory: {event} - {headline} (Effective: {effective}, Expires: {expires})")
        return advisories
    except Exception as e:
        print(f"[DEBUG] Weather Advisories Error: {e}")
        return [{"message": "Unable to fetch weather advisories at this time."}]

# Function to get current water temperature near Groton, CT (New London station)
# Replace the existing get_current_water_temp function
# Replace the existing get_current_water_temp function
# Function to get current water temperature near Groton, CT (New London station)
def get_current_water_temp():
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "station": "8461490",  # New London, CT
        "product": "water_temperature",
        "date": "today",
        "units": "english",
        "format": "json",
        "time_zone": "gmt",  # Added required time zone
        "application": "weather_dashboard"
    }
    headers = {"User-Agent": "weather_app"}
    try:
        full_url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        print(f"[DEBUG] Water Temp URL: {full_url}")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "data" not in data or not data["data"]:
            print(f"[DEBUG] No water temp data available for today")
            return 45.0
        temp = float(data["data"][-1]["v"])  # Most recent value
        timestamp = data["data"][-1]["t"]
        print(f"[DEBUG] Current Water Temp: {temp}°F at {timestamp}")
        return temp
    except Exception as e:
        print(f"[DEBUG] Water Temp Error: {e}")
        return 45.0  # Fallback to approximate April average

# Function to get average water temperature for the current month
def get_average_water_temp():
    csv_path = "water_temps.csv"
    current_month = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%B")
    try:
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            print(f"[DEBUG] CSV Headers: {reader.fieldnames}")  # Debug headers
            for row in reader:
                if row["Month"] == current_month:
                    return float(row["Average_Temp_F"])
        print(f"[DEBUG] No average temp found for {current_month}")
        return 45.0  # Fallback
    except Exception as e:
        print(f"[DEBUG] Average Water Temp Error: {e}")
        return 45.0

# Main block to test the script standalone
if __name__ == "__main__":
    conditions = get_current_conditions()
    print(f"Current Precipitation (1h): {conditions['precipitation']} inches")
    print(f"Precipitation Totals: {conditions['precipitation_totals']}")
    print(f"Text Description: {conditions['text_description']}")
    print(f"Wind Direction: {conditions['wind_direction']}° ({degrees_to_cardinal(conditions['wind_direction'])})")
    print(f"Wind Speed: {conditions['wind_speed']} MPH")
    print(f"Temperature: {conditions['temperature']}°F")
    print(f"Barometric Pressure: {conditions['barometric_pressure']:.2f} inHg")
    
    sunrise, sunset = get_sun_times()
    print(f"Sunrise: {sunrise}, Sunset: {sunset}")
    
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    moon_phase = get_moon_phase(now)
    print(f"Moon Phase: {moon_phase}")
    
    next_full_moon = get_next_full_moon()
    print(f"Next Full Moon: {next_full_moon}")
    
    forecast = get_forecast()
    for period in forecast:
        print(f"Forecast: {period['label']} - {period['conditions']} at {period['time']}")
    
    water_temp = get_current_water_temp()
    avg_temp = get_average_water_temp()
    print(f"Current Water Temperature: {water_temp}°F")
    print(f"Average Water Temperature for {datetime.datetime.now().strftime('%B')}: {avg_temp}°F")