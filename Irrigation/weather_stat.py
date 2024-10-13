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


def set_sunrise():
    with open(w_path) as w_file:
        weather = json.load(w_file)
    sun_rise_time = []
    for i in weather['daily']['sunrise']:
        h_m = i[11:]
        h = int(h_m[:2]) * 60 * 60
        m = int(h_m[3:]) * 60
        s = h + m
        sun_rise_time.append(s)
    ct = weather['current']['time']
    return sun_rise_time, ct


def get_weather():
    with open(w_path) as w_file:
        weather = json.load(w_file)
    temperature = [str(round(weather['current']["temperature_2m"])) + '\u00A0' + '°C']
    next_hour = datetime.now()
    next_hour = next_hour.hour
    temp_for = [weather['hourly']['temperature_2m'][next_hour:25], weather['hourly']['temperature_2m'][25:]]
    for t in temp_for:
        t.sort()
        t_min, t_max = t[0], t[-1]
        if t_min == t_max:
            temperature.append(str(round(t_min)) + '\u00A0' + '°C')
        else:
            temperature.append(str(round(t_min)) + '...' + str(round(t_max)) + '\u00A0' + '°C')
    return temperature


if __name__ == '__main__':
    a = get_forecast(COORD)
    sun, check_time = set_sunrise()
    print(sun)
