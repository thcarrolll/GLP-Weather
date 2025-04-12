# test_windy.py (just for testing)
import requests
import json
from datetime import datetime

url = "https://api.windy.com/api/point-forecast/v2"
payload = {
    "lat": 41.311,
    "lon": -72.014,
    "model": "gfsWave",
    "parameters": ["waves", "swell1"],
    "key": "qcEK39VJSgSjX9I0oLAxmXAjPeGnG2eh",
    "levels": ["surface"],
    "time": "now"
}
headers = {"Content-Type": "application/json"}
try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        wave_height_m = data.get("waves_height-surface", [0])[0]
        wave_height_ft = round(wave_height_m * 3.28084, 1)
        swell_height_m = data.get("swell1_height-surface", [0])[0]
        swell_height_ft = round(swell_height_m * 3.28084, 1)
        swell_direction = data.get("swell1_direction-surface", [0])[0]
        swell_period = data.get("swell1_period-surface", [0])[0]
        ts_ms = data.get("ts", [0])[0]
        timestamp = datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts_ms else "N/A"
        print(f"Wave Height: {wave_height_ft} ft, Swell Height: {swell_height_ft} ft, "
              f"Swell Direction: {swell_direction}°, Swell Period: {swell_period}s, Timestamp: {timestamp}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
except Exception as e:
    print(f"Request Failed: {e}")