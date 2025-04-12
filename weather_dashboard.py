import streamlit as st
import barometric_app
import moon_app
import tide_app
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import plotly.graph_objects as go
import datetime
import pytz
from io import BytesIO
import requests
from weather_data import (degrees_to_cardinal, format_time_diff, image_to_base64, 
                         get_moon_phase, get_current_conditions, get_wave_height, 
                         get_forecast, get_sun_times, get_next_full_moon, get_current_water_temp)
from compass_rose_gauge import CompassRoseGauge, get_windy_wave_data
from travel_time import get_drive_time, get_next_train
from style_config import TITLE_FONT, PALETTE, FALLBACK_FONTS, FONT_PATH
import os
import importlib
import sys

# Set page config
st.set_page_config(layout="wide", page_title="Groton Long Point", initial_sidebar_state="collapsed")

# Initialize session state with defaults from style_config
if 'palette' not in st.session_state:
    st.session_state.palette = PALETTE.copy()
if 'title_font' not in st.session_state:
    st.session_state.title_font = TITLE_FONT
if 'font_path' not in st.session_state:
    st.session_state.font_path = FONT_PATH
if 'fallback_fonts' not in st.session_state:
    st.session_state.fallback_fonts = FALLBACK_FONTS.copy()

# Function to write style_config.py (for persistence)
def update_style_config(title_font, font_path, fallback_fonts, palette):
    font_path_logic = """
# Use TITLE_FONT directly if no TTF path is provided
if FONT_PATH and os.path.exists(FONT_PATH):
    try:
        fm.fontManager.addfont(FONT_PATH)
        print(f"Loaded custom font: {TITLE_FONT}")
    except:
        print(f"Failed to load {TITLE_FONT}, falling back to {FALLBACK_FONTS[0]}")
        TITLE_FONT = FALLBACK_FONTS[0]
else:
    print(f"No TTF path or not found, using TITLE_FONT as system font: {TITLE_FONT}")

# Validate TITLE_FONT, fall back if needed
if TITLE_FONT not in fm.fontManager.get_font_names():
    print(f"{TITLE_FONT} not found in system fonts, falling back")
    TITLE_FONT = next((f for f in FALLBACK_FONTS if f in fm.fontManager.get_font_names()), "serif")
"""
    config_content = f"""# style_config.py
import matplotlib.font_manager as fm
import os

TITLE_FONT = "{title_font}"
FONT_PATH = "{font_path}"
FALLBACK_FONTS = {fallback_fonts}

{font_path_logic}

PALETTE = {{
    'app_bg': '{palette['app_bg']}',
    'main_bg': '{palette['main_bg']}',
    'card_bg': '{palette['card_bg']}',
    'metric_bg': '{palette['metric_bg']}',
    'plot_bg': '{palette['plot_bg']}',
    'plot_line': '{palette['plot_line']}',
    'text': '{palette['text']}',
    'title': '{palette['title']}',
    'subtitle': '{palette.get('subtitle', palette['title'])}',
    'border': '{palette['border']}',
    'shading': '{palette['shading']}',
    'shading_alpha': {palette['shading_alpha']}
}}

print("Using font:", TITLE_FONT)
print("PALETTE loaded with app_bg:", PALETTE['app_bg'])
"""
    config_path = "C:/Users/teren/Tides/style_config.py"
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"Saved config to {config_path}")
        with open(config_path, "r") as f:
            print("New style_config.py content:", f.read())
        if "style_config" in sys.modules:
            del sys.modules["style_config"]
        importlib.import_module("style_config")
        print("Reloaded style_config successfully")
    except Exception as e:
        st.error(f"Failed to save or reload config: {str(e)}")
        print(f"Save error details: {str(e)}")
        return

# Common Windows fonts
common_fonts = [
    "Arial", "Calibri", "Comic Sans MS", "Courier New", "Georgia",
    "Times New Roman", "Trebuchet MS", "Verdana", "Segoe UI", "Custom"
]

# Sidebar for config input
with st.sidebar:
    st.header("Customize Style")
    font_choice = st.selectbox("Title Font", common_fonts, index=common_fonts.index(st.session_state.title_font) if st.session_state.title_font in common_fonts else len(common_fonts)-1)
    if font_choice == "Custom":
        st.session_state.title_font = st.text_input("Custom Font Name", st.session_state.title_font)
        st.session_state.font_path = st.text_input("Font File Path (TTF)", st.session_state.font_path)
    else:
        st.session_state.title_font = font_choice
        st.session_state.font_path = ""
    fallback_fonts_str = st.text_input("Fallback Fonts (comma-separated)", ", ".join(st.session_state.fallback_fonts))
    st.session_state.fallback_fonts = [f.strip() for f in fallback_fonts_str.split(",")]
    st.session_state.palette['app_bg'] = st.color_picker("App Background", st.session_state.palette['app_bg'])
    st.session_state.palette['main_bg'] = st.color_picker("Main Background", st.session_state.palette['main_bg'])
    st.session_state.palette['card_bg'] = st.color_picker("Card Background", st.session_state.palette['card_bg'])
    st.session_state.palette['metric_bg'] = st.color_picker("Metric Background", st.session_state.palette['metric_bg'])
    st.session_state.palette['plot_bg'] = st.color_picker("Plot Background", st.session_state.palette['plot_bg'])
    st.session_state.palette['plot_line'] = st.color_picker("Plot Line", st.session_state.palette['plot_line'])
    st.session_state.palette['text'] = st.color_picker("Text Color", st.session_state.palette['text'])
    st.session_state.palette['title'] = st.color_picker("Title Color", st.session_state.palette['title'])
    st.session_state.palette['subtitle'] = st.color_picker("Subtitle Color", st.session_state.palette.get('subtitle', st.session_state.palette['title']))
    st.session_state.palette['border'] = st.color_picker("Border Color", st.session_state.palette['border'])
    st.session_state.palette['shading'] = st.color_picker("Shading Color", st.session_state.palette['shading'])
    st.session_state.palette['shading_alpha'] = st.slider("Shading Alpha", 0.0, 1.0, st.session_state.palette['shading_alpha'])
    if st.button("Save Config"):
        update_style_config(st.session_state.title_font, st.session_state.font_path, st.session_state.fallback_fonts, st.session_state.palette)
        st.success("Config saved! Changes applied live; restart to update plots.")

# Build font-family stack
font_stack = f"'{st.session_state.title_font}', " + ", ".join(f"'{f}'" for f in st.session_state.fallback_fonts)

# Apply CSS with advisory styling
font_face_css = f"""
@font-face {{
    font-family: '{st.session_state.title_font}';
    src: url('file:///{st.session_state.font_path}') format('truetype');
}}
""" if st.session_state.font_path and os.path.exists(st.session_state.font_path) else ""

st.markdown(
    f"""
    <style>
    {font_face_css}
    .stApp {{ background-color: {st.session_state.palette['app_bg']}; color: {st.session_state.palette['text']}; }}
    .main-content {{ background-color: {st.session_state.palette['main_bg']}; padding-top: 20px; }}
    .st-emotion-cache-16tyu1 h1 {{ 
        color: {st.session_state.palette['title']} !important; 
        font-family: {font_stack} !important; 
        font-size: 2.75rem; 
    }}
    .st-emotion-cache-16tyu1 h2 {{ 
        color: {st.session_state.palette['subtitle']} !important; 
        font-family: {font_stack} !important; 
        font-size: 1.75rem; 
    }}
    .st-emotion-cache-16tyu1 h3 {{ 
        color: {st.session_state.palette['subtitle']} !important; 
        font-family: {font_stack} !important; 
        font-size: 1.25rem; 
    }}
    h4, h5, h6 {{ color: {st.session_state.palette['subtitle']} !important; }}
    .stText, .stMarkdown, p {{ color: {st.session_state.palette['text']}; }}
    .card {{ background-color: {st.session_state.palette['card_bg']}; border-radius: 10px; padding: 15px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }}
    .metric-box {{ background-color: {st.session_state.palette['metric_bg']} !important; border-radius: 8px; padding: 10px; text-align: center; margin: 5px 0; width: 100%; height: 140px; display: flex; flex-direction: column; justify-content: center; }}
    .metric-box div {{ font-family: {font_stack} !important; color: {st.session_state.palette['title']}; }}
    .metric-label {{ font-size: 16px; }}
    .metric-value {{ font-size: 24px; font-weight: bold; }}
    .metric-extra {{ font-size: 20px; }}
    .chart-container {{ width: 100%; max-width: 480px; margin: 0 auto; }}
    .forecast-container {{ background-color: {st.session_state.palette['card_bg']}; border-radius: 8px; padding: 10px; text-align: center; margin: 5px; width: 140px; min-height: 240px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); display: flex; flex-direction: column; align-items: center; font-family: serif; }}
    .forecast-container div {{ font-size: 14px; line-height: 1.2; color: {st.session_state.palette['text']}; }}
    .forecast-container img {{ width: 80px; margin: 10px auto; display: block; }}
    .sun-tide-moon-container {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; width: 100%; }}
    .sun-column, .tide-column, .moon-column, .travel-column {{ display: flex; flex-direction: column; gap: 5px; }}
    .sun-info, .tide-info, .moon-info, .travel-info {{ display: flex; align-items: center; font-size: 24px; min-width: 200px; }}
    .gauge-container {{ width: 100%; text-align: center; overflow-x: auto; background-color: {st.session_state.palette['app_bg']}; }}
    .advisory-box {{ border-left: 5px solid #b22222; padding-left: 10px; margin-top: 10px; }}
    .advisory-box img {{ vertical-align: middle; margin-right: 8px; }}
    </style>
    """,
    unsafe_allow_html=True
)
print("CSS injected with font stack:", font_stack)

# Fetch travel data with short TTL cache
@st.cache_data(ttl=60)
def get_travel_data(_timestamp):
    try:
        drive_time = get_drive_time()
        next_train = get_next_train()
        return drive_time, next_train
    except Exception as e:
        st.error(f"Error fetching travel data: {e}")
        return "N/A", "N/A"

timestamp = datetime.datetime.now().timestamp()
drive_time, next_train = get_travel_data(timestamp)

# Fetch conditions with caching
@st.cache_data(ttl=3600)
def cached_current_conditions():
    return get_current_conditions()
conditions = cached_current_conditions()

# Fetch wave height with caching
@st.cache_data(ttl=3600)
def cached_wave_height():
    return get_wave_height()
wave_height, wave_timestamp = cached_wave_height()

# Fetch tide data for high/low times
_, _, _, next_high_time, next_low_time = tide_app.get_tide_plot()

# Fetch barometric pressure data
@st.cache_data(ttl=3600)
def get_historical_baro_pressure():
    fig, current_pressure, trend, pressure_3h_ago = barometric_app.get_barometric_plot_with_history()
    if pressure_3h_ago is None:
        pressure_3h_ago = current_pressure - 0.1
    print(f"Current Pressure: {current_pressure:.2f} inHg, 3h Ago: {pressure_3h_ago:.2f} inHg")
    return pressure_3h_ago

baro_pressure_3h_ago = get_historical_baro_pressure()

# Get barometric pressure for gauge
fig, baro_pressure, _, _ = barometric_app.get_barometric_plot_with_history()

# Cache the CompassRoseGauge rendering
@st.cache_data(ttl=3600)
def render_gauge(wind_direction, wind_speed, wind_gusts, temperature, precip_24h, 
                 baro_pressure, baro_pressure_3h_ago, humidity, water_temp, wave_height, swell_height):
    gauge = CompassRoseGauge(width=50, height=18.75)
    gauge.fig.set_dpi(150)
    gauge.draw_compass_rose(
        wind_direction=wind_direction,
        wind_speed=wind_speed,
        wind_gusts=wind_gusts,
        temperature=temperature,
        precip_24h=precip_24h,
        baro_pressure=baro_pressure,
        baro_pressure_3h_ago=baro_pressure_3h_ago,
        humidity=humidity,
        water_temp=water_temp,
        wave_height=wave_height,
        swell_height=swell_height
    )
    buf = BytesIO()
    gauge.fig.savefig(buf, format="png", dpi=150, bbox_inches='tight')
    buf.seek(0)
    return buf

# Prepare gauge data
wind_direction = conditions["wind_direction"] if isinstance(conditions["wind_direction"], (int, float)) else 0
wind_speed = conditions["wind_speed"] if isinstance(conditions["wind_speed"], (int, float)) else 0
wind_gusts = conditions["wind_gust"] if isinstance(conditions["wind_gust"], (int, float)) else 0
temperature = conditions["temperature"] if isinstance(conditions["temperature"], (int, float)) else 0
precip_24h = conditions["precipitation_totals"]["24h"] if isinstance(conditions["precipitation_totals"]["24h"], (int, float)) else 0
humidity = conditions["humidity"] if isinstance(conditions["humidity"], (int, float)) else 0
water_temp = get_current_water_temp()
wave_height_value, swell_height_value = get_windy_wave_data()

# Render and display gauge
gauge_buf = render_gauge(
    wind_direction, wind_speed, wind_gusts, temperature, precip_24h,
    baro_pressure, baro_pressure_3h_ago, humidity, water_temp, wave_height_value, swell_height_value
)
st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
st.image(gauge_buf, width=2000)
st.markdown('</div>', unsafe_allow_html=True)

# Start main content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Weather condition icon mapping
weather_icon_map = {
    "Clear": "icons/1530392_weather_sun_sunny_temperature.png",
    "Sunny": "icons/1530392_weather_sun_sunny_temperature.png",
    "Fair": "icons/1530391_fair.png",
    "Partly Cloudy": "icons/1530391_partly_sunny_partly_cloudy.png",
    "Mostly Cloudy": "icons/1530369_cloudy.png",
    "Cloudy": "icons/1530369_cloudy.png",
    "Rain": "icons/1530362_cloudy_rain.png",
    "Light Rain": "icons/1530365_rain_cloud_drizzle_.png",
    "Drizzle": "icons/1530365_rain_cloud_drizzle_.png",
    "Showers": "icons/1530364_rain_storm_shower.png",
    "Thunderstorms": "icons/1530363_thunderstorm_lightning_clouds.png",
    "Thunderstorm": "icons/1530363_thunderstorm_lightning_clouds.png",
    "Snow": "icons/1530371_winter_snow_clouds_blowing_snow.png",
    "Sleet": "icons/1530370_hail_weather_hailstone_sleet_freezing_rain_clouds_snow_rainandsnow.png",
    "Freezing Rain": "icons/1530370_hail_weather_hailstone_sleet_freezing_rain_clouds_snow_rainandsnow.png",
    "Hail": "icons/1530370_hail_weather_hailstone_sleet_freezing_rain_clouds_snow_rainandsnow.png",
    "Rain and Snow": "icons/1530370_hail_weather_hailstone_sleet_freezing_rain_clouds_snow_rainandsnow.png",
    "Fog": "icons/1530368_foggy_weather_fog_clouds_cloudy_mist.png",
    "Mist": "icons/1530368_foggy_weather_fog_clouds_cloudy_mist.png",
    "Haze": "icons/1530386_weather_clouds_fog_foggy.png",
    "Windy": "icons/1530361_windy_cloudy.png",
    "Blowing Snow": "icons/1530371_winter_snow_clouds_blowing_snow.png",
    "Tornado": "icons/1530366_hurricane_tornado_storm.png",
    "Hurricane": "icons/1530366_hurricane_tornado_storm.png",
    "Dust": "icons/1530372_sand_weather_storm_sandstorm.png",
    "Sandstorm": "icons/1530372_sand_weather_storm_sandstorm.png",
    "Partly Sunny with Showers": "icons/1530385_partly sunny_thunder_clouds_rain.png",
    "Sunny with Rain": "icons/1530390_sunny_rain_cloudy_weather_clouds_partlysunny.png",
}

# Function to select weather icon with fuzzy matching
def get_weather_icon(condition_description, icon_map):
    condition_lower = condition_description.lower()
    if condition_description in icon_map:
        return image_to_base64(icon_map[condition_description])
    if "thunder" in condition_lower:
        return image_to_base64(icon_map["Thunderstorms"])
    elif "rain" in condition_lower or "drizzle" in condition_lower:
        return image_to_base64(icon_map["Light Rain"])
    elif "snow" in condition_lower:
        return image_to_base64(icon_map["Snow"])
    elif "fog" in condition_lower or "mist" in condition_lower:
        return image_to_base64(icon_map["Fog"])
    elif "cloud" in condition_lower:
        return image_to_base64(icon_map["Cloudy"])
    elif "sun" in condition_lower or "clear" in condition_lower:
        return image_to_base64(icon_map["Sunny"])
    return image_to_base64("icons/1530391_partly_sunny_partly_cloudy.png")

# Function to generate Time-of-Day Progression summary
def get_weather_summary(forecast_periods, conditions, sunrise, sunset):
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    is_day = sunrise <= now <= sunset if sunrise and sunset else now.hour < 18
    period_start = now.replace(hour=6, minute=0, second=0, microsecond=0) if is_day else now.replace(hour=18, minute=0, second=0, microsecond=0)
    period_end = period_start.replace(hour=18) if is_day else period_start.replace(hour=6) + datetime.timedelta(days=1)
    if is_day:
        morning_end = period_start.replace(hour=12)
        afternoon_start = morning_end
        first_period, second_period = "Morning", "Afternoon"
    else:
        evening_end = period_start.replace(hour=23, minute=59, second=59)
        overnight_start = evening_end + datetime.timedelta(seconds=1)
        first_period, second_period = "Evening", "Overnight"
    morning_periods = [p for p in forecast_periods if period_start <= p['time'] < (morning_end if is_day else evening_end)]
    afternoon_periods = [p for p in forecast_periods if (afternoon_start if is_day else overnight_start) <= p['time'] <= period_end]
    current_desc = conditions.get('text_description', 'Unknown').lower()
    current_temp = conditions.get('temperature', 60)
    current_humidity = conditions.get('humidity', 50)
    current_wind = conditions.get('wind_speed', 0)
    def get_dominant_condition(periods, default="Cloudy"):
        if not periods:
            return default
        conditions_count = {}
        for p in periods:
            cond = p['conditions']
            conditions_count[cond] = conditions_count.get(cond, 0) + 1
        for keyword in ["Thunder", "Rain", "Snow", "Fog", "Cloud", "Clear", "Sunny"]:
            for cond in conditions_count:
                if keyword.lower() in cond.lower():
                    return cond
        return max(conditions_count, key=conditions_count.get, default=default)
    def simplify_condition(cond):
        cond_lower = cond.lower()
        if "thunder" in cond_lower:
            return "Stormy"
        elif "rain" in cond_lower or "drizzle" in cond_lower or "showers" in cond_lower:
            return "Rainy"
        elif "snow" in cond_lower:
            return "Snowy"
        elif "fog" in cond_lower or "mist" in cond_lower:
            return "Misty"
        elif "cloud" in cond_lower:
            return "Cloudy"
        elif "clear" in cond_lower or "sun" in cond_lower:
            return "Sunny" if is_day else "Starry"
        return "Cloudy"
    first_cond = simplify_condition(get_dominant_condition(morning_periods, "Cloudy" if is_day else "Starry"))
    second_cond = simplify_condition(get_dominant_condition(afternoon_periods, "Cloudy" if is_day else "Starry"))
    temp_qualifier = ""
    if current_temp > 75:
        temp_qualifier = "Hot"
    elif current_temp < 60:
        temp_qualifier = "Cool"
    else:
        temp_qualifier = "Warm"
    humidity_qualifier = "Humid" if current_humidity > 70 else ""
    wind_qualifier = "Breezy" if current_wind > 15 else ""
    avg_first_temp = sum(p['temp'] for p in morning_periods) / len(morning_periods) if morning_periods else current_temp
    avg_second_temp = sum(p['temp'] for p in afternoon_periods) / len(afternoon_periods) if afternoon_periods else current_temp
    if avg_second_temp - avg_first_temp > 5:
        temp_qualifier = "Warming"
    elif avg_first_temp - avg_second_temp > 5:
        temp_qualifier = "Cooling"
    current_keywords = ["thunder", "rain", "snow", "fog", "mist"]
    if any(k in current_desc for k in current_keywords):
        first_cond = simplify_condition(conditions.get('text_description', 'Cloudy'))
    summary_parts = []
    if first_cond:
        if second_cond == first_cond:
            summary_parts.append(f"{temp_qualifier} {first_cond} {first_period} & {second_period}".strip())
        else:
            summary_parts.append(f"{temp_qualifier} {first_cond} {first_period}".strip())
            if second_cond:
                summary_parts.append(f"{second_cond} {second_period}")
    qualifiers = [q for q in [humidity_qualifier, wind_qualifier] if q]
    if qualifiers:
        if len(qualifiers) > 1:
            qualifier_str = ", ".join(qualifiers[:-1]) + f" {qualifiers[-1]}"
        else:
            qualifier_str = qualifiers[0]
        summary_parts.append(f"with {qualifier_str}")
    summary_parts.append("Skies")
    summary = ", ".join(summary_parts[:-1]) + f" {summary_parts[-1]}" if len(summary_parts) > 1 else summary_parts[0]
    if len(summary) > 80:
        summary = summary[:77] + "..."
    if not summary.strip() or not forecast_periods:
        summary = f"{temp_qualifier} {current_desc.title()} {'Day' if is_day else 'Night'}"
    icon_condition = first_cond
    if "Stormy" in icon_condition:
        icon_condition = "Thunderstorms"
    elif "Rainy" in icon_condition:
        icon_condition = "Light Rain"
    elif "Snowy" in icon_condition:
        icon_condition = "Snow"
    elif "Misty" in icon_condition:
        icon_condition = "Fog"
    elif "Cloudy" in icon_condition:
        icon_condition = "Cloudy"
    elif "Sunny" in icon_condition or "Starry" in icon_condition:
        icon_condition = "Sunny"
    title = "Today's Weather" if is_day else "Tonight's Weather"
    return title, summary, icon_condition

# Get weather summary and icon
forecast_periods = get_forecast()
sunrise, sunset = get_sun_times()
weather_title, weather_summary, icon_condition = get_weather_summary(forecast_periods, conditions, sunrise, sunset)
weather_icon = get_weather_icon(icon_condition, weather_icon_map)

# Title and Weather Summary
st.markdown(
    f"""
    <h1>Groton Long Point</h1>
    <h2>{weather_title}: <img src="{weather_icon}" width="64"> {weather_summary}</h2>
    """,
    unsafe_allow_html=True
)

# Sunrise/Sunset, Tides, Moon, Travel
now = datetime.datetime.now(pytz.timezone('US/Eastern'))
today_str = now.strftime('%Y-%m-%d')

sunrise_str = sunset_str = next_event = first_time = second_time = None
if sunrise and sunset:
    sunrise_str = sunrise.strftime('%I:%M %p').lstrip('0')
    sunset_str = sunset.strftime('%I:%M %p').lstrip('0')
    next_event = "Sunset" if now < sunset else "Sunrise"
    first_time = sunset_str if next_event == "Sunset" else sunrise_str
    second_time = sunrise_str if next_event == "Sunset" else sunset_str
else:
    sunrise_str = sunset_str = "N/A"
    next_event = "N/A"
    first_time = second_time = "N/A"

high_icon = image_to_base64("icons/7984977_high_tide_icon.png")
low_icon = image_to_base64("icons/7984975_low_tide_icon.png")
first_tide_label = first_tide_time = first_tide_icon = second_tide_label = second_tide_time = second_tide_icon = None

if next_high_time != "N/A" and next_low_time != "N/A":
    try:
        high_time = datetime.datetime.strptime(f"{today_str} {next_high_time}", '%Y-%m-%d %a %I:%M %p')
        low_time = datetime.datetime.strptime(f"{today_str} {next_low_time}", '%Y-%m-%d %a %I:%M %p')
        high_dt = pytz.timezone('US/Eastern').localize(high_time)
        low_dt = pytz.timezone('US/Eastern').localize(low_time)
        if high_dt < now:
            high_dt += datetime.timedelta(days=1)
        if low_dt < now:
            low_dt += datetime.timedelta(days=1)
        if high_dt < low_dt:
            first_tide_label = "High Tide"
            first_tide_time = high_dt.strftime('%I:%M %p').lstrip('0')
            first_tide_icon = high_icon
            second_tide_label = "Low Tide"
            second_tide_time = low_dt.strftime('%I:%M %p').lstrip('0')
            second_tide_icon = low_icon
        else:
            first_tide_label = "Low Tide"
            first_tide_time = low_dt.strftime('%I:%M %p').lstrip('0')
            first_tide_icon = low_icon
            second_tide_label = "High Tide"
            second_tide_time = high_dt.strftime('%I:%M %p').lstrip('0')
            second_tide_icon = high_icon
    except ValueError as e:
        first_tide_label = "High Tide"
        first_tide_time = next_high_time
        first_tide_icon = high_icon
        second_tide_label = "Low Tide"
        second_tide_time = next_low_time
        second_tide_icon = low_icon
else:
    first_tide_label = "High Tide"
    first_tide_time = "N/A"
    first_tide_icon = high_icon
    second_tide_label = "Low Tide"
    second_tide_time = "N/A"
    second_tide_icon = low_icon

moon_phase_name = get_moon_phase(now)
moon_phase_icon_map = {
    "New Moon": "icons/icons8-new-moon-50.png",
    "Waxing Crescent": "icons/icons8-waxing-crescent-moon-48.png",
    "First Quarter": "icons/icons8-first-quarter-moon-48.png",
    "Waxing Gibbous": "icons/icons8-waxing-gibbous-moon-48.png",
    "Full Moon": "icons/icons8-full-moon-48.png",
    "Waning Gibbous": "icons/icons8-waning-gibbous-moon-48.png",
    "Last Quarter": "icons/icons8-third-quarter-moon-48.png",
    "Waning Crescent": "icons/icons8-waning-crescent-moon-48.png",
    "Unknown": "icons/icons8-new-moon-50.png"
}
moon_phase_icon = image_to_base64(moon_phase_icon_map.get(moon_phase_name, "icons/icons8-new-moon-50.png"))
full_moon_icon = image_to_base64("icons/icons8-full-moon-48.png")
next_full_moon_date = get_next_full_moon()
if next_full_moon_date == "Unknown":
    next_full_moon_date = "N/A"

drive_icon = image_to_base64("icons/icons8-car-100.png")
train_icon = image_to_base64("icons/icons8-train-100.png")
sunrise_icon = image_to_base64("icons/icons8-sunrise-48.png")
sunset_icon = image_to_base64("icons/icons8-sunset-48.png")

sun_tide_moon_html = '<div class="sun-tide-moon-container">'
sun_tide_moon_html += '<div class="sun-column">'
sun_tide_moon_html += (
    f'<div class="sun-info"><img src="{sunset_icon if next_event == "Sunset" else sunrise_icon}" width="24"> {next_event}: {first_time}</div>'
    f'<div class="sun-info"><img src="{sunrise_icon if next_event == "Sunset" else sunset_icon}" width="24"> {"Sunrise" if next_event == "Sunset" else "Sunset"}: {second_time}</div>'
)
sun_tide_moon_html += '</div>'
sun_tide_moon_html += '<div class="tide-column">'
sun_tide_moon_html += (
    f'<div class="tide-info"><img src="{first_tide_icon}" width="36"> {first_tide_label}: {first_tide_time}</div>'
    f'<div class="tide-info"><img src="{second_tide_icon}" width="36"> {second_tide_label}: {second_tide_time}</div>'
)
sun_tide_moon_html += '</div>'
sun_tide_moon_html += '<div class="moon-column">'
sun_tide_moon_html += (
    f'<div class="moon-info"><img src="{moon_phase_icon}" width="36"> Current: {moon_phase_name}</div>'
    f'<div class="moon-info"><img src="{full_moon_icon}" width="36"> Next Full Moon: {next_full_moon_date}</div>'
)
sun_tide_moon_html += '</div>'
sun_tide_moon_html += '<div class="travel-column">'
sun_tide_moon_html += (
    f'<div class="travel-info"><img src="{drive_icon}" width="36"> Drive time to Chatham, NJ: {drive_time}</div>'
    f'<div class="travel-info"><img src="{train_icon}" width="36"> Next train Mystic to Boston: {next_train}</div>'
)
sun_tide_moon_html += '</div>'
sun_tide_moon_html += '</div>'

st.markdown(sun_tide_moon_html, unsafe_allow_html=True)

# Upcoming Weather Section
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("<h2>Upcoming Weather</h2>", unsafe_allow_html=True)
if forecast_periods:
    cols = st.columns(len(forecast_periods))
    for i, period in enumerate(forecast_periods):
        with cols[i]:
            timestamp = period["time"].strftime('%a %I %p').replace(' 0', ' ').lstrip('0')
            icon_html = f'<img src="{period["icon"]}" width="80">' if period["icon"].startswith("data:image") else '<div>Icon unavailable</div>'
            conditions = period['conditions']
            if len(conditions.split()) > 3:
                mid = len(conditions) // 2
                space_index = conditions.find(' ', mid)
                if space_index != -1:
                    conditions_part1 = conditions[:space_index]
                    conditions_part2 = conditions[space_index+1:]
                else:
                    conditions_part1 = conditions
                    conditions_part2 = ""
            else:
                conditions_part1 = conditions
                conditions_part2 = " "
            label = period['label'] + '<br>' if 'Afternoon' not in period['label'] else period['label']
            st.markdown(
                f"""
                <div class="forecast-container">
                    <div>{label}</div>
                    <div>{timestamp}</div>
                    <div>{period['temp']}°F</div>
                    {icon_html}
                    <div>{conditions_part1}</div>
                    <div>{conditions_part2}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.markdown("No forecast data available.")
st.markdown('</div>', unsafe_allow_html=True)

# Weather Advisory
def get_nws_alerts(zone_id="ANZ332"):
    """Fetch active weather alerts for ANZ332 from NWS API."""
    url = f"https://api.weather.gov/alerts/active/zone/{zone_id}"
    headers = {
        "User-Agent": "WeatherDashboard (your.email@example.com)",
        "Accept": "application/geo+json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("features", [])
            formatted_alerts = []
            for alert in alerts:
                props = alert.get("properties", {})
                event = props.get("event", "Unknown")
                severity = props.get("severity", "Unknown")
                description = props.get("description", "").split("\n")
                # Map event to marine warning flag
                flag_map = {
                    "Small Craft Advisory": "icons/small_craft.png",
                    "Gale Warning": "icons/gale.png",
                    "Storm Warning": "icons/storm.png",
                    "Hurricane Warning": "icons/hurricane.png"
                }
                flag_file = flag_map.get(event, "icons/small_craft.png")
                # Encode flag as base64
                try:
                    flag_base64 = image_to_base64(flag_file)
                except Exception as e:
                    flag_base64 = ""
                    print(f"Failed to load flag {flag_file}: {e}")
                # Extract key details, skip WHERE
                details = ""
                for line in description:
                    if line.startswith("* WHAT"):
                        details = line.replace("* WHAT...", "").strip()
                    elif line.startswith("* WHEN"):
                        details += f" until {line.replace('* WHEN...', '').strip()}"
                expires = props.get("expires", "Unknown")
                try:
                    expires_dt = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00"))
                    expires_str = expires_dt.astimezone(pytz.timezone('US/Eastern')).strftime("%I:%M %p EDT").lstrip("0")
                    details = details.replace("until further notice", f"until {expires_str}")
                except:
                    expires_str = "Unknown"
                formatted_alerts.append({
                    "event": event,
                    "severity": severity,
                    "description": details,
                    "flag": flag_base64
                })
            return formatted_alerts if formatted_alerts else [{"description": "No active alerts.", "flag": ""}]
        else:
            return [{"description": f"NWS API Error: {response.status_code}", "flag": ""}]
    except Exception as e:
        return [{"description": f"NWS Request Failed: {e}", "flag": ""}]

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>Weather Advisory</h2>", unsafe_allow_html=True)
    advisories = get_nws_alerts()
    for advisory in advisories:
        flag = advisory.get("flag", "")
        event = advisory.get("event", "")
        description = advisory.get("description", "No details available.")
        flag_html = f'<img src="{flag}" width="24" alt="{event} flag">' if flag else ""
        st.markdown(
            f"""
            <div class="advisory-box">
                {flag_html} <strong>{event}</strong><br>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

# Grid layout for remaining sections
row1_col1, row1_col2 = st.columns([1, 1])

# Barometric Pressure Plot
with row1_col1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h2>Barometric Pressure</h2>", unsafe_allow_html=True)
        fig, current_pressure, trend, _ = barometric_app.get_barometric_plot_with_history()
        if fig:
            fig.patch.set_facecolor(PALETTE['app_bg'])
            for ax in fig.get_axes():
                ax.set_facecolor(PALETTE['plot_bg'])
                for spine in ax.spines.values():
                    spine.set_color(PALETTE['border'])
                ax.tick_params(axis='x', colors=PALETTE['border'])
                ax.tick_params(axis='y', colors=PALETTE['border'])
                ax.xaxis.label.set_color(PALETTE['text'])
                ax.yaxis.label.set_color(PALETTE['text'])
                ax.xaxis.label.set_fontfamily('serif')
                ax.yaxis.label.set_fontfamily('serif')
                for tick in ax.get_xticklabels() + ax.get_yticklabels():
                    tick.set_fontfamily('serif')
                for line in ax.get_lines():
                    line.set_color(PALETTE['plot_line'])
                if ax.get_title():
                    ax.title.set_color(PALETTE['title'])
                    ax.title.set_fontfamily(TITLE_FONT)
            st.markdown(
                f"""
                <div class="metric-box">
                    <h3>Current Pressure</h3>
                    <div class="metric-extra">{current_pressure:.2f} inHg ({trend})</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Failed to load barometric data")
        st.markdown('</div>', unsafe_allow_html=True)

# Tide Plot
with row1_col2:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h2>Tides</h2>", unsafe_allow_html=True)
        fig, current_height, trend, next_high_time, next_low_time = tide_app.get_tide_plot()
        if fig:
            fig.patch.set_facecolor(PALETTE['app_bg'])
            for ax in fig.get_axes():
                ax.set_facecolor(PALETTE['plot_bg'])
                for spine in ax.spines.values():
                    spine.set_color(PALETTE['border'])
                ax.tick_params(axis='x', colors=PALETTE['border'])
                ax.tick_params(axis='y', colors=PALETTE['border'])
                ax.xaxis.label.set_color(PALETTE['text'])
                ax.yaxis.label.set_color(PALETTE['text'])
                ax.xaxis.label.set_fontfamily('serif')
                ax.yaxis.label.set_fontfamily('serif')
                for tick in ax.get_xticklabels() + ax.get_yticklabels():
                    tick.set_fontfamily('serif')
                for line in ax.get_lines():
                    line.set_color(PALETTE['plot_line'])
                if ax.get_title():
                    ax.title.set_color(PALETTE['title'])
                    ax.title.set_fontfamily(TITLE_FONT)
            now = datetime.datetime.now(pytz.timezone('US/Eastern'))
            today_str = now.strftime('%Y-%m-%d')
            try:
                high_time = datetime.datetime.strptime(f"{today_str} {next_high_time}", '%Y-%m-%d %a %I:%M %p')
                low_time = datetime.datetime.strptime(f"{today_str} {next_low_time}", '%Y-%m-%d %a %I:%M %p')
                high_dt = pytz.timezone('US/Eastern').localize(high_time)
                low_dt = pytz.timezone('US/Eastern').localize(low_time)
                if high_dt < now:
                    high_dt += datetime.timedelta(days=1)
                if low_dt < now:
                    low_dt += datetime.timedelta(days=1)
                next_tide_label = "Next High" if high_dt < low_dt else "Next Low"
                next_tide_time = high_dt.strftime('%a %I:%M %p') if high_dt < low_dt else low_dt.strftime('%a %I:%M %p')
                other_tide_label = "Next Low" if high_dt < low_dt else "Next High"
                other_tide_time = low_dt.strftime('%a %I:%M %p') if high_dt < low_dt else high_dt.strftime('%a %I:%M %p')
                next_tide_diff = format_time_diff(high_dt if high_dt < low_dt else low_dt, now)
                other_tide_diff = format_time_diff(low_dt if high_dt < low_dt else high_dt, now)
                st.markdown(
                    f"""
                    <div class="metric-box">
                        <h3>Current Tide</h3>
                        <div class="metric-extra">{current_height:.2f} ft ({trend})</div>
                        <div class="metric-extra">{next_tide_label}: {next_tide_time} ({next_tide_diff})</div>
                        <div class="metric-extra">{other_tide_label}: {other_tide_time} ({other_tide_diff})</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except ValueError as e:
                st.markdown(
                    f"""
                    <div class="metric-box">
                        <h3>Current Tide</h3>
                        <div class="metric-extra">{current_height:.2f} ft ({trend})</div>
                        <div class="metric-extra">Next High: {next_high_time}</div>
                        <div class="metric-extra">Next Low: {next_low_time}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Failed to load tide data")
        st.markdown('</div>', unsafe_allow_html=True)

# Close main-content div
st.markdown('</div>', unsafe_allow_html=True)