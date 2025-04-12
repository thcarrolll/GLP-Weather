import requests
import datetime
import pytz

def test_tide_api():
    utc_now = datetime.datetime.now(pytz.UTC)
    local_tz = pytz.timezone('America/New_York')
    local_now = utc_now.astimezone(local_tz)
    start_date = local_now - datetime.timedelta(days=1)
    end_date = local_now + datetime.timedelta(days=4)
    
    url = (
        f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
        f"begin_date={start_date.strftime('%Y%m%d')}&end_date={end_date.strftime('%Y%m%d')}&"
        f"station=8461490&product=predictions&datum=MLLW&time_zone=gmt&interval=6&units=english&format=json"
    )
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        predictions = data.get("predictions", [])
        print(f"Predictions count: {len(predictions)}")
        if predictions:
            print(f"First prediction: {predictions[0]}")
            print(f"Last prediction: {predictions[-1]}")
        else:
            print("No predictions in response.")
    except requests.RequestException as e:
        print(f"API error: {e}")
    except ValueError as e:
        print(f"JSON decode error: {e}")

if __name__ == "__main__":
    test_tide_api()