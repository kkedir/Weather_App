import datetime
import requests
import string
from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.getenv("OWM_API_KEY")

OWM_ENDPOINT = "https://api.openweathermap.org/data/3.0/weather"
OWM_FORECAST_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_API_ENDPOINT = "http://api.openweathermap.org/geo/1.0/direct"


app = Flask(__name__)

# Display home page and get city name entered into search form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("search")
        if city.lower() == "favicon.ico":
            return redirect(url_for("home"))
        return redirect(url_for("get_weather", city=city))
    return render_template("index.html")


# Display weather forecast for specific city using data from OpenWeather API

@app.route("/<city>", methods=["GET", "POST"])
def get_weather(city):
    if not api_key:
        print("Error: API key is missing")
        return redirect(url_for("error"))

    # Format city name and get current date to display on page
    city_name = string.capwords(city)
    today = datetime.datetime.now()
    current_date = today.strftime("%A, %B %d")

    # Get latitude and longitude for city
    location_params = {
        "q": city_name,
        "appid": api_key,
        "limit": 3,
    }

    try:
        location_response = requests.get(GEOCODING_API_ENDPOINT, params=location_params)
        location_response.raise_for_status()
        location_data = location_response.json()

        # Prevent IndexError if no location data is returned
        if not location_data:
            return redirect(url_for("error"))
        lat = location_data[0].get('lat')
        lon = location_data[0].get('lon')

    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching location data: {e}")
        return redirect(url_for("error"))

    # Get OpenWeather API data
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",  # Metric for Celsius
    }

    try:
        # Fetch both current and forecast weather data
        forecast_response = requests.get(OWM_FORECAST_ENDPOINT, weather_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Extract current weather data from forecast
        current_data = forecast_data['list'][0]
        current_temp = round((current_data['main']['temp']) * 9/5 + 32)  
        current_weather = current_data['weather'][0]['main']
        min_temp = round((current_data['main']['temp_min']) * 9/5 + 32)  
        max_temp = round((current_data['main']['temp_max']) * 9/5 + 32) 
        wind_speed = current_data['wind']['speed']

        # Get five-day weather forecast data at noon and convert to Fahrenheit
        five_day_temp_list = [round((item['main']['temp']) * 9/5 + 32) for item in forecast_data['list'] if '12:00:00' in item['dt_txt']]
        five_day_weather_list = [item['weather'][0]['main'] for item in forecast_data['list']
                                 if '12:00:00' in item['dt_txt']]

        # Get next four weekdays to show user alongside weather data
        five_day_unformatted = [today + datetime.timedelta(days=i) for i in range(5)]
        five_day_dates_list = [date.strftime("%a") for date in five_day_unformatted]

    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"Error fetching weather data: {e}")
        return redirect(url_for("error"))

    return render_template("city.html", city_name=city_name, current_date=current_date, current_temp=current_temp,
                           current_weather=current_weather, min_temp=min_temp, max_temp=max_temp, wind_speed=wind_speed,
                           five_day_temp_list=five_day_temp_list, five_day_weather_list=five_day_weather_list,
                           five_day_dates_list=five_day_dates_list)


# Display error page for invalid input
@app.route("/error")
def error():
    return render_template("error.html")


if __name__ == "__main__":
    app.run(debug=True)
