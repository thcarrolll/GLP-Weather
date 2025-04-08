import requests
from datetime import datetime, timedelta
import pytz
import re

def get_nws_precipitation():
    url = "https://api.weather.gov/stations/KGON/observations"
    headers = {"User-Agent": "weather_app"}
    now = datetime.now(pytz.UTC)
    start_time = now - timedelta(hours=36)  # Extend to catch all 24h+
    params = {
        "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": 100  # More observations
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()["features"]
        
        precip_totals = {"3h": 0, "6h": 0, "12h": 0, "24h": 0}
        hourly_precip = []
        
        for obs in data:
            timestamp = datetime.fromisoformat(obs["properties"]["timestamp"].replace("+00:00", "Z"))
            raw = obs["properties"]["rawMessage"]
            
            precip_1h = re.search(r'\bP(\d{4})\b', raw)
            precip_in = int(precip_1h.group(1)) / 100 if precip_1h else 0.0
            
            hours_ago = (now - timestamp).total_seconds() / 3600
            hourly_precip.append((timestamp, precip_in))
            print(f"{timestamp} ({hours_ago:.1f}h ago): {precip_in:.2f} in, METAR: {raw}")
        
        # Sum hourly precip
        for ts, precip in sorted(hourly_precip, reverse=True):
            hours_ago = (now - ts).total_seconds() / 3600
            if hours_ago <= 3:
                precip_totals["3h"] += precip
            if hours_ago <= 6:
                precip_totals["6h"] += precip
            if hours_ago <= 12:
                precip_totals["12h"] += precip
            precip_totals["24h"] += precip
        
        for period, total_in in precip_totals.items():
            print(f"Total {period}: {total_in:.2f} inches")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_nws_precipitation()