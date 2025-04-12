import requests

def get_nws_alerts(zone_id="ANZ332"):
    """Fetch active weather alerts for a given NWS zone (e.g., ANZ332)."""
    url = f"https://api.weather.gov/alerts/active/zone/{zone_id}"
    headers = {
        "User-Agent": "WeatherDashboard (your.email@example.com)",  # NWS requires a contact
        "Accept": "application/geo+json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("features", [])
            if not alerts:
                print(f"No active alerts for {zone_id}.")
                return None
            for alert in alerts:
                props = alert.get("properties", {})
                event = props.get("event", "Unknown")
                headline = props.get("headline", "No headline")
                description = props.get("description", "No description")
                effective = props.get("effective", "Unknown")
                expires = props.get("expires", "Unknown")
                print(f"Alert: {event}")
                print(f"Headline: {headline}")
                print(f"Effective: {effective}")
                print(f"Expires: {expires}")
                print(f"Description:\n{description}")
                print("-" * 50)
            return alerts
        else:
            print(f"NWS API Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"NWS Request Failed: {e}")
        return None

if __name__ == "__main__":
    get_nws_alerts("ANZ332")