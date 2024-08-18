import os
from datetime import datetime
import json
import requests


w_path = os.path.join(os.path.dirname(__file__), 'cash/forecast.json')

COORD = {'latitude': 48.0353930, 'longitude': 17.2635956}


def get_forecast(coordinates):
    latitude_f = coordinates['latitude']
    longitude_f = coordinates['longitude']
    response = requests.get(f'https://api.open-meteo.com/v1/forecast?'
                            f'latitude={latitude_f}&longitude={longitude_f}&'
                            f'cell_selection=land&'
                            f'timezone=auto&'
                            f'forecast_days=2&'
                            f'windspeed_unit=ms&'
                            f'hourly=temperature_2m,relativehumidity_2m,dewpoint_2m,'
                            f'pressure_msl,'
                            f'windspeed_10m,winddirection_10m,windgusts_10m,'
                            f'precipitation,precipitation_probability,'
                            f'cloudcover,weathercode,visibility&'
                            f'daily=sunrise,sunset,precipitation_sum,precipitation_hours,precipitation_probability_max,'
                            f'wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant&'
                            f'current=temperature_2m,relative_humidity_2m,rain,showers,snowfall,cloud_cover,'
                            f'surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m')
    with open(w_path, 'w') as f:
        json.dump(response.json(), f)
    return True


def set_sunrise(i):
    with open(w_path) as w_file:
        weather = json.load(w_file)
    h_m = weather['daily']['sunrise'][i][11:]
    h = int(h_m[:2]) * 60 * 60
    m = int(h_m[3:]) * 60
    s = h + m
    ct = weather['current']['time']
    return s, ct


if __name__ == '__main__':
    a = get_forecast(COORD)
    sun, check_time = set_sunrise()
    print(sun)
