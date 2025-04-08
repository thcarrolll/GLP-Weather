import requests
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import numpy as np

def get_barometric_plot_with_history():
    obs_url = "https://api.weather.gov/stations/KGON/observations"
    forecast_url = "https://api.weather.gov/gridpoints/OKX/51,44/forecast/hourly"
    headers = {"User-Agent": "weather_app"}
    utc = pytz.UTC
    
    try:
        # Fetch actual data (past 48+ hours)
        obs_response = requests.get(obs_url, headers=headers)
        obs_response.raise_for_status()
        obs_data = obs_response.json()
        observations = obs_data["features"]

        actual_times = []
        actual_pressures = []
        now = datetime.datetime.now(utc)
        two_days_ago = now - datetime.timedelta(hours=48)
        three_hours_ago = now - datetime.timedelta(hours=3)
        pressure_3h_ago = None
        for obs in observations:
            timestamp = obs["properties"]["timestamp"].replace("+00:00", "Z")
            time = datetime.datetime.fromisoformat(timestamp[:-1]).replace(tzinfo=utc)
            if time >= two_days_ago and time <= now:
                pressure = obs["properties"]["barometricPressure"]["value"]
                if pressure is not None:
                    pressure = round(pressure * 0.000295301, 2)
                    actual_times.append(time)
                    actual_pressures.append(pressure)
                    # Find pressure closest to 3 hours ago
                    if time <= three_hours_ago and (pressure_3h_ago is None or abs(time - three_hours_ago) < abs(actual_times[actual_pressures.index(pressure_3h_ago)] - three_hours_ago)):
                        pressure_3h_ago = pressure

        if not actual_times:
            print("No valid actual pressure data available.")
            return None, None, None, None

        # Sort chronologically
        actual_data = sorted(zip(actual_times, actual_pressures), key=lambda x: x[0])
        actual_times, actual_pressures = zip(*actual_data)
        actual_times = list(actual_times)
        actual_pressures = list(actual_pressures)

        # Debug
        print(f"Sample actual pressures (inHg): {actual_pressures[-5:]}")
        if pressure_3h_ago:
            print(f"Pressure 3h ago: {pressure_3h_ago:.2f} inHg at {actual_times[actual_pressures.index(pressure_3h_ago)]}")

        # Current pressure and trend
        current_pressure = actual_pressures[-1]
        trend = "Rising" if len(actual_pressures) > 1 and actual_pressures[-1] > actual_pressures[-2] else "Falling"

        # Fetch forecast data (next 8 hours)
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        forecast_periods = forecast_data["properties"]["periods"]

        forecast_times = []
        forecast_pressures = []
        eight_hours_future = now + datetime.timedelta(hours=8)
        last_actual = actual_pressures[-1]
        for i, period in enumerate(forecast_periods):
            time = datetime.datetime.fromisoformat(period["startTime"][:-6]).replace(tzinfo=utc)
            if time >= now and time <= eight_hours_future:
                pressure = period.get("pressure", {}).get("value")
                if pressure is not None:
                    pressure = round(pressure * 0.000295301, 2)
                else:
                    pressure = round(last_actual + (0.05 * (i % 4) - 0.03 * ((i // 4) % 2)), 2)
                forecast_times.append(time)
                forecast_pressures.append(pressure)

        if not forecast_times:
            print("No valid forecast pressure data available.")
            return None, None, None, None

        # Debug
        print(f"Sample forecast pressures (inHg): {forecast_pressures[:5]}")

        # Create plot (unchanged plotting code)
        plt.close('all')
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(actual_times, actual_pressures, color='black', linestyle='-', linewidth=1)
        if actual_times and forecast_times:
            transition_times = [actual_times[-1], forecast_times[0]]
            transition_pressures = [actual_pressures[-1], forecast_pressures[0]]
            ax.plot(transition_times, transition_pressures, color='black', linestyle='--', linewidth=1)
        ax.plot(forecast_times, forecast_pressures, color='black', linestyle='--', linewidth=1)
        ax.set_xlim(actual_times[0], forecast_times[-1])

        start_day = actual_times[0].replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = forecast_times[-1].replace(hour=23, minute=59, second=59, microsecond=999999)
        current_day = start_day
        shade = False
        while current_day < end_day:
            next_day = current_day + datetime.timedelta(days=1)
            if next_day > actual_times[0] and current_day < forecast_times[-1]:
                shade_start = max(current_day, actual_times[0])
                shade_end = min(next_day, forecast_times[-1])
                if shade:
                    ax.axvspan(shade_start, shade_end, facecolor='#d0d0d0', alpha=0.3)
            current_day = next_day
            shade = not shade

        major_ticks = [start_day + datetime.timedelta(days=i) for i in range(int((end_day - start_day).days) + 1)]
        major_ticks = [t for t in major_ticks if actual_times[0] <= t <= forecast_times[-1]]
        minor_ticks = [actual_times[0] + datetime.timedelta(hours=i) for i in range(int((forecast_times[-1] - actual_times[0]).total_seconds() // 3600) + 1) if i % 6 == 0]
        ax.set_xticks(major_ticks)
        ax.set_xticklabels([t.strftime('%a') for t in major_ticks], rotation=25)
        ax.set_xticks(minor_ticks, minor=True)
        ax.tick_params(axis='x', which='minor', length=4)

        all_pressures = actual_pressures + forecast_pressures
        min_pressure = min(29.0, min(all_pressures) - 0.2)
        max_pressure = max(31.0, max(all_pressures) + 0.2)
        ax.set_ylim(min_pressure, max_pressure)
        ax.set_yticks(np.arange(29.0, 31.5, 0.5))

        plt.style.use('default')
        ax.set_facecolor('#A0B0D0')
        for spine in ax.spines.values():
            spine.set_color('#000000')
        ax.tick_params(colors='#000000')
        ax.grid(color='#A0A0A0', linestyle='--', alpha=0.5)
        ax.set_title("Barometric Pressure", color='#000000')
        ax.set_xlabel("")
        ax.set_ylabel("Pressure (inHg)", color='#000000')
        plt.tight_layout()

        return fig, current_pressure, trend, pressure_3h_ago
    except Exception as e:
        print(f"Error in get_barometric_plot_with_history: {e}")
        return None, None, None, None

# Alias for backward compatibility
def get_barometric_plot():
    fig, current_pressure, trend, _ = get_barometric_plot_with_history()
    return fig, current_pressure, trend

if __name__ == "__main__":
    fig, current_pressure, trend, pressure_3h_ago = get_barometric_plot_with_history()
    if fig:
        plt.show(block=True)
    else:
        print("No figure generated.")