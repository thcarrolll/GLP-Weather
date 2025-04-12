import requests

def get_wave_height_openweathermap(lat=41.314, lon=-72.007):
    api_key = "f720f4f80ec9d02a5e54f6938bf55d8b"  # Your key
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        data = response.json()
        print("Full API Response:", data)  # Debug: see the raw response
        
        # Check if wave data exists (might not be in free tier)
        wave_height_ft = data.get("hourly", [{}])[0].get("waves", {}).get("height", 1.0)
        timestamp = data["hourly"][0]["dt"]
        return wave_height_ft, timestamp
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return 1.0, "N/A"
    except Exception as e:
        print(f"Other Error: {e}")
        return 1.0, "N/A"

# Call the function and print the result
if __name__ == "__main__":
    wave_height, timestamp = get_wave_height_openweathermap()
    print(f"Wave Height: {wave_height} ft at {timestamp}")