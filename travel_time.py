import requests
from datetime import datetime, timedelta
import pytz
import WazeRouteCalculator

# Constants
GROTON_ADDRESS = "62 Sound Breeze Ave, Groton, CT 06340"
CHATHAM_ADDRESS = "82 Canterbury Road, Chatham, NJ 07928"
MYSTIC_STATION_CODE = "MYS"
BOSTON_STATION_CODE = "BOS"
REGION = "US"
CURRENT_TIME = datetime.now(pytz.timezone('US/Eastern'))
TODAY = CURRENT_TIME.date().isoformat()

# Drive time from GLP to Chatham
def get_drive_time():
    try:
        route = WazeRouteCalculator.WazeRouteCalculator(GROTON_ADDRESS, CHATHAM_ADDRESS, REGION)
        time, _ = route.calc_route_info()
        hours = int(time // 60)
        minutes = int(time % 60)
        return f"{hours} hours and {minutes} minutes"
    except Exception:
        return "2 hours and 55 minutes"  # Fallback based on typical time

# Next train from Mystic to Boston
def get_next_train():
    static_schedule = [
        {"departure_time": "1:47 PM"},
        {"departure_time": "5:17 PM"},
        {"departure_time": "8:11 PM"},
        {"departure_time": "10:44 PM"}
    ]
    try:
        url = "https://api-v3.amtraker.com/v3/trains"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        trains = response.json()
        for train_list in trains.values():
            for train in train_list:
                stations = train.get("stations", [])
                mystic_stop = next((s for s in stations if s["code"] == MYSTIC_STATION_CODE), None)
                if mystic_stop and BOSTON_STATION_CODE in [s["code"] for s in stations]:
                    mystic_idx = next(i for i, s in enumerate(stations) if s["code"] == MYSTIC_STATION_CODE)
                    boston_idx = next(i for i, s in enumerate(stations) if s["code"] == BOSTON_STATION_CODE)
                    if boston_idx > mystic_idx:
                        dep_time_str = mystic_stop.get("schDep")
                        if dep_time_str:
                            dep_time = datetime.strptime(dep_time_str, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.timezone('US/Eastern'))
                            if dep_time > CURRENT_TIME and dep_time.date() == CURRENT_TIME.date():
                                return dep_time.strftime("%I:%M %p").lstrip("0")
    except Exception as e:
        print(f"API Error: {e}")  # Optional logging for debugging
    # Fallback to static schedule
    for static in static_schedule:
        dep_time = pytz.timezone('US/Eastern').localize(
            datetime.strptime(f"{TODAY} {static['departure_time']}", "%Y-%m-%d %I:%M %p")
        )
        if dep_time > CURRENT_TIME:
            return static["departure_time"]
    return "N/A"

if __name__ == "__main__":
    drive_time = get_drive_time()
    next_train = get_next_train()
    print(f"Drive time from Groton to Chatham: {drive_time}")
    print(f"Next train from Mystic to Boston: {next_train}")