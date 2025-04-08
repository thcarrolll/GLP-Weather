import streamlit as st
import barometric_app
import moon_app
import tide_app
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import datetime
import pytz
from io import BytesIO
from weather_data import (degrees_to_cardinal, format_time_diff, image_to_base64, 
                         get_moon_phase, get_current_conditions, get_wave_height, 
                         get_forecast, get_sun_times, get_next_full_moon)
from compass_rose_gauge import CompassRoseGauge
import os

# Set page config
st.set_page_config(layout="wide", page_title="Groton Long Point", initial_sidebar_state="collapsed")

# Apply custom CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #333333;
    }
    .main-content {
        background-color: #F5F5F5;
        padding-top: 20px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }
    .stText, .stMarkdown, p {
        color: #333333;
    }
    .card {
        background-color: #E8E8E8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .metric-box {
        background-color: #6ABBB5 !important;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin: 5px 0;
        width: 100%;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-label {
        font-size: 16px;
        color: #000000;
        font-family: serif;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #000000;
        font-family: serif;
    }
    .metric-extra {
        font-size: 20px;
        color: #000000;
        font-family: serif;
    }
    .chart-container {
        width: 100%;
        max-width: 480px;
        margin: 0 auto;
    }
    .forecast-container {
        background-color: #E8E8E8;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin: 5px;
        width: 140px;
        min-height: 240px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        font-family: serif;
    }
    .forecast-container div {
        font-size: 14px;
        line-height: 1.2;
    }
    .forecast-container img {
        width: 80px;
        margin: 10px auto;
        display: block;
    }
    .sun-tide-moon-container {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 20px;
        width: 100%;
    }
    .sun-column, .tide-column, .moon-column {
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    .sun-info, .tide-info, .moon-info {
        display: flex;
        align-items: center;
        font-size: 24px;
        min-width: 200px;
    }
    .gauge-container {
        width: 100%;
        text-align: center;
        overflow-x: auto;
        background-color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

# Fetch barometric pressure data (current and historical)
@st.cache_data(ttl=3600)
def get_historical_baro_pressure():
    fig, current_pressure, trend, pressure_3h_ago = barometric_app.get_barometric_plot_with_history()
    if pressure_3h_ago is None:
        pressure_3h_ago = current_pressure - 0.1  # Fallback
    print(f"Current Pressure: {current_pressure:.2f} inHg, 3h Ago: {pressure_3h_ago:.2f} inHg")
    return pressure_3h_ago

baro_pressure_3h_ago = get_historical_baro_pressure()

# Get barometric pressure for gauge
fig, baro_pressure, _, _ = barometric_app.get_barometric_plot_with_history()

# CompassRoseGauge with larger size
gauge = CompassRoseGauge(width=50, height=18.75)
gauge.fig.set_dpi(200)
wind_direction = conditions["wind_direction"] if isinstance(conditions["wind_direction"], (int, float)) else 0
wind_speed = conditions["wind_speed"] if isinstance(conditions["wind_speed"], (int, float)) else 0
wind_gusts = conditions["wind_gust"] if isinstance(conditions["wind_gust"], (int, float)) else 0
temperature = conditions["temperature"] if isinstance(conditions["temperature"], (int, float)) else 0
precip_24h = conditions["precipitation_totals"]["24h"] if isinstance(conditions["precipitation_totals"]["24h"], (int, float)) else 0
humidity = conditions["humidity"] if isinstance(conditions["humidity"], (int, float)) else 0
cloud_cover = conditions["cloud_cover"] if isinstance(conditions["cloud_cover"], (int, float)) else 0
wave_height_value = wave_height if isinstance(wave_height, (int, float)) else 0

gauge.draw_compass_rose(
    wind_direction=wind_direction,
    wind_speed=wind_speed,
    wind_gusts=wind_gusts,
    temperature=temperature,
    precip_24h=precip_24h,
    baro_pressure=baro_pressure,
    baro_pressure_3h_ago=baro_pressure_3h_ago,
    humidity=humidity,
    cloud_cover=cloud_cover,
    wave_height=wave_height_value
)

# Save and display gauge
buf = BytesIO()
gauge.fig.savefig(buf, format="png", dpi=200, bbox_inches='tight')
buf.seek(0)
st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
st.image(buf, width=2000)
st.markdown('</div>', unsafe_allow_html=True)

# Start main content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Title and Current Conditions
st.title("Groton Long Point")
st.subheader(f"Current Conditions: {conditions['text_description']}")

# Sunrise/Sunset, Tides, and Moon
sunrise, sunset = get_sun_times()
now = datetime.datetime.now(pytz.timezone('US/Eastern'))
today_str = now.strftime('%Y-%m-%d')

sunrise_str = sunset_str = next_event = first_time = second_time = first_icon = second_icon = None
if sunrise and sunset:
    sunrise_str = sunrise.strftime('%I:%M %p').lstrip('0')
    sunset_str = sunset.strftime('%I:%M %p').lstrip('0')
    next_event = "Sunset" if now < sunset else "Sunrise"
    first_time = sunset_str if next_event == "Sunset" else sunrise_str
    second_time = sunrise_str if next_event == "Sunset" else sunset_str
    first_icon = "https://cdn-icons-png.flaticon.com/512/1146/1146885.png" if next_event == "Sunset" else "https://cdn-icons-png.flaticon.com/512/1163/1163624.png"
    second_icon = "https://cdn-icons-png.flaticon.com/512/1163/1163624.png" if next_event == "Sunset" else "https://cdn-icons-png.flaticon.com/512/1146/1146885.png"

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

moon_phase_name = get_moon_phase(now)
moon_phase_icon_map = {
    "New Moon": "icons/icons8-new-moon-50.png",
    "Waxing Crescent": "icons/icons8-waxing-crescent-moon-48.png",
    "First Quarter": "icons/icons8-first-quarter-moon-48.png",
    "Waxing Gibbous": "icons/icons8-waxing-gibbous-moon-48.png",
    "Full Moon": "icons/icons8-full-moon-48.png",
    "Waning Gibbous": "icons/icons8-waning-gibbous-moon-48.png",
    "Last Quarter": "icons/icons8-third-quarter-moon-48.png",
    "Waning Crescent": "icons/icons8-waning-crescent-moon-48.png"
}
moon_phase_icon = image_to_base64(moon_phase_icon_map.get(moon_phase_name, "icons/icons8-new-moon-50.png"))
full_moon_icon = image_to_base64("icons/icons8-full-moon-48.png")
next_full_moon_date = get_next_full_moon()

sun_tide_moon_html = '<div class="sun-tide-moon-container">'
sun_tide_moon_html += '<div class="sun-column">'
if sunrise_str and sunset_str:
    sun_tide_moon_html += (
        f'<div class="sun-info"><img src="{first_icon}" width="24"> {next_event}: {first_time}</div>'
        f'<div class="sun-info"><img src="{second_icon}" width="24"> {"Sunrise" if next_event == "Sunset" else "Sunset"}: {second_time}</div>'
    )
sun_tide_moon_html += '</div>'
sun_tide_moon_html += '<div class="tide-column">'
if first_tide_label and first_tide_time and second_tide_label and second_tide_time:
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
sun_tide_moon_html += '</div>'

st.markdown(sun_tide_moon_html, unsafe_allow_html=True)

# Upcoming Weather Section
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Upcoming Weather")
forecast_periods = get_forecast()
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
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Weather Advisory")
    st.markdown("**Current Advisory:** No active weather advisories for Groton, CT.")
    st.markdown('</div>', unsafe_allow_html=True)

# Grid layout for remaining sections
row1_col1, row1_col2 = st.columns([1, 1])

# Define color scheme
TIFFANY_BLUE = '#81D8D0'
PLOT_FIELD_COLOR = '#6ABBB5'
PLOT_LINE_COLOR = '#3C8D88'

# Barometric Pressure Plot
with row1_col1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Barometric Pressure")
        fig, current_pressure, trend, _ = barometric_app.get_barometric_plot_with_history()
        if fig:
            fig.patch.set_facecolor('white')
            for ax in fig.get_axes():
                ax.set_facecolor(PLOT_FIELD_COLOR)
                ax.spines['top'].set_color('#333333')
                ax.spines['right'].set_color('#333333')
                ax.spines['left'].set_color('#333333')
                ax.spines['bottom'].set_color('#333333')
                ax.tick_params(axis='x', colors='#333333')
                ax.tick_params(axis='y', colors='#333333')
                ax.xaxis.label.set_color('#333333')
                ax.yaxis.label.set_color('#333333')
                ax.xaxis.label.set_fontfamily('serif')
                ax.yaxis.label.set_fontfamily('serif')
                for tick in ax.get_xticklabels() + ax.get_yticklabels():
                    tick.set_fontfamily('serif')
                for line in ax.get_lines():
                    line.set_color(PLOT_LINE_COLOR)
                if ax.get_title():
                    ax.title.set_color('#333333')
                    ax.title.set_fontfamily('serif')
            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-value">Current Pressure</div>
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
        st.subheader("Tides")
        fig, current_height, trend, next_high_time, next_low_time = tide_app.get_tide_plot()
        if fig:
            fig.patch.set_facecolor('white')
            for ax in fig.get_axes():
                ax.set_facecolor(PLOT_FIELD_COLOR)
                ax.spines['top'].set_color('#333333')
                ax.spines['right'].set_color('#333333')
                ax.spines['left'].set_color('#333333')
                ax.spines['bottom'].set_color('#333333')
                ax.tick_params(axis='x', colors='#333333')
                ax.tick_params(axis='y', colors='#333333')
                ax.xaxis.label.set_color('#333333')
                ax.yaxis.label.set_color('#333333')
                ax.xaxis.label.set_fontfamily('serif')
                ax.yaxis.label.set_fontfamily('serif')
                for tick in ax.get_xticklabels() + ax.get_yticklabels():
                    tick.set_fontfamily('serif')
                for line in ax.get_lines():
                    line.set_color(PLOT_LINE_COLOR)
                if ax.get_title():
                    ax.title.set_color('#333333')
                    ax.title.set_fontfamily('serif')
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
                        <div class="metric-value">Current Tide</div>
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
                        <div class="metric-value">Current Tide</div>
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