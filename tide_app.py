import requests
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import numpy as np
import matplotlib
matplotlib.use('Agg')

  # Use TkAgg for interactive plots; requires tkinter

def get_tide_plot():
    # Dynamically set date range: yesterday to 5 days forward (6 days total)
    utc_now = datetime.datetime.now(pytz.UTC)
    local_tz = pytz.timezone('America/New_York')  # EDT
    local_now = utc_now.astimezone(local_tz)
    start_date = local_now - datetime.timedelta(days=1)  # Yesterday
    end_date = local_now + datetime.timedelta(days=4)    # Today + 4 = 5 days forward
    
    url = (
        f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
        f"begin_date={start_date.strftime('%Y%m%d')}&end_date={end_date.strftime('%Y%m%d')}&"
        f"station=8461490&product=predictions&datum=MLLW&time_zone=gmt&interval=6&units=english&format=json"
    )
    print(f"Request URL: {url}")  # Debug URL
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        predictions = data.get("predictions", [])

        times = []
        heights = []
        for pred in predictions:
            timestamp = pred["t"]
            time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.UTC)
            height = float(pred["v"])
            times.append(time)
            heights.append(height)

        if not times:
            print("No valid tide data available.")
            return None, None, None, None, None

        # Debug: Print first and last data points
        print(f"First data point: {times[0].astimezone(local_tz).strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"Last data point: {times[-1].astimezone(local_tz).strftime('%Y-%m-%d %I:%M %p %Z')}")

        tide_data = sorted(zip(times, heights), key=lambda x: x[0])
        times, heights = zip(*tide_data)
        times = list(times)
        heights = list(heights)
        times_local = [t.astimezone(local_tz) for t in times]

        # Current tide height and trend
        current_height = None
        trend = None
        for i, time in enumerate(times):
            if time >= utc_now:
                if i > 0:
                    current_height = heights[i-1]
                    trend = "Rising" if i > 1 and heights[i-1] > heights[i-2] else "Falling"
                else:
                    current_height = heights[0]
                    trend = "Rising" if heights[1] > heights[0] else "Falling"
                break
        if current_height is None:
            current_height = heights[-1]
            trend = "Rising" if len(heights) > 1 and heights[-1] > heights[-2] else "Falling"

        # Find highs and lows with relaxed detection
        heights_array = np.array(heights)
        highs = []
        lows = []
        window = 5  # ~30 minutes
        expected_tides = 10  # Min 2 per day over 5+ days
        for i in range(window, len(heights) - window):
            if heights[i] == max(heights[i-window:i+window+1]):
                highs.append((times[i], heights[i]))
            if heights[i] == min(heights[i-window:i+window+1]):
                lows.append((times[i], heights[i]))

        # Fallback if too few tides detected
        if len(highs) < expected_tides or len(lows) < expected_tides:
            highs = []
            lows = []
            for i in range(1, len(heights) - 1):
                if heights[i] > heights[i-1] and heights[i] > heights[i+1]:
                    highs.append((times[i], heights[i]))
                if heights[i] < heights[i-1] and heights[i] < heights[i+1]:
                    lows.append((times[i], heights[i]))

        # Find next high and low after now
        next_high = None
        next_low = None
        for time, height in highs:
            if time > utc_now:
                next_high = (time, height)
                break
        for time, height in lows:
            if time > utc_now:
                next_low = (time, height)
                break

        # Fallback: Shift to next cycle if no next tide
        tidal_period = datetime.timedelta(hours=12, minutes=25)  # Approx semi-diurnal period
        if not next_high and highs:
            next_high = (highs[0][0] + tidal_period, highs[0][1])
            while next_high[0] <= utc_now:
                next_high = (next_high[0] + tidal_period, next_high[1])
        if not next_low and lows:
            next_low = (lows[0][0] + tidal_period, lows[0][1])
            while next_low[0] <= utc_now:
                next_low = (next_low[0] + tidal_period, next_low[1])

        next_high_time = next_high[0].astimezone(local_tz).strftime('%a %I:%M %p').replace(' 0', ' ').lstrip('0') if next_high else "N/A"
        next_low_time = next_low[0].astimezone(local_tz).strftime('%a %I:%M %p').replace(' 0', ' ').lstrip('0') if next_low else "N/A"

        # Create plot
        plt.close('all')
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(times_local, heights, color='black', linestyle='-', linewidth=1)
        ax.axvline(local_now, color='red', linestyle='--', linewidth=1)

        # Annotate highs and lows with smaller font
        min_height = min(heights) - 0.5
        max_height = max(heights) + 0.5
        for high_time, high_height in highs:
            high_time_local = high_time.astimezone(local_tz)
            time_str = high_time_local.strftime('%I:%M %p').lstrip('0')
            y_pos = min(high_height + 0.3, max_height - 0.2)
            ax.text(high_time_local, y_pos, time_str, ha='center', va='bottom', color='#000000', fontsize=4)
        for low_time, low_height in lows:
            low_time_local = low_time.astimezone(local_tz)
            time_str = low_time_local.strftime('%I:%M %p').lstrip('0')
            y_pos = max(low_height - 0.3, min_height + 0.2)
            ax.text(low_time_local, y_pos, time_str, ha='center', va='top', color='#000000', fontsize=4)

        # Shading for each day, aligned with data
        start_time = times_local[0].replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = times_local[-1].replace(hour=23, minute=59, second=59, microsecond=999999)
        current_day = start_time
        day_count = 0
        while current_day < end_time:
            next_day = current_day + datetime.timedelta(days=1)
            if day_count % 2 == 0:
                ax.axvspan(current_day, next_day, facecolor='#d0d0d0', alpha=0.3)
            current_day = next_day
            day_count += 1

        # Set x-axis limits to actual data range
        ax.set_xlim(times_local[0], times_local[-1])
        tick_times = [times_local[0] + datetime.timedelta(days=i) for i in range(int((times_local[-1] - times_local[0]).days) + 1)]
        ax.set_xticks(tick_times)
        ax.set_xticklabels([t.strftime('%a') for t in tick_times], rotation=25)
        ax.set_ylim(min_height, max_height)

        ax.set_facecolor('#A0B0D0')
        for spine in ax.spines.values():
            spine.set_color('#000000')
        ax.tick_params(colors='#000000')
        ax.grid(color='#A0A0A0', linestyle='--', alpha=0.5)
        ax.set_title("Tide Height", color='#000000')
        ax.set_xlabel("")
        ax.set_ylabel("Height (ft)", color='#000000')
        plt.tight_layout()

        return fig, current_height, trend, next_high_time, next_low_time
    except Exception as e:
        print(f"Error in get_tide_plot: {e}")
        return None, None, None, None, None

if __name__ == "__main__":
    fig, current_height, trend, next_high_time, next_low_time = get_tide_plot()
    if fig:
        plt.show()
    else:
        print("No figure generated.")