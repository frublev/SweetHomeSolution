import logging

import os
from datetime import datetime
import json
import requests

from .loggers import log_handler

weather_logger = logging.getLogger(__name__)
weather_logger.setLevel(logging.INFO)
weather_logger.addHandler(log_handler)

w_path = os.path.join(os.path.dirname(__file__), 'cash/forecast.json')
print('PATH!!!!!!!!', w_path)

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
    if response:
        with open(w_path, 'w') as f:
            try:
                json.dump(response.json(), f)
            except requests.exceptions.JSONDecodeError:
                msg = 'Error dumping to json'
                weather_logger.error(msg)
    else:
        msg = 'Weather forecast is empty'
        weather_logger.error(msg)
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


def wind_dir_str(wind_dir):
    if 22.5 <= wind_dir < 67.5:
        w_dir_str = 'SW'
    elif 67.5 <= wind_dir < 112.5:
        w_dir_str = 'W'
    elif 112.5 <= wind_dir < 157.5:
        w_dir_str = 'NW'
    elif 157.5 <= wind_dir < 202.5:
        w_dir_str = 'N'
    elif 202.5 <= wind_dir < 247.5:
        w_dir_str = 'NE'
    elif 247.5 <= wind_dir < 292.5:
        w_dir_str = 'E'
    elif 292.5 <= wind_dir < 337.5:
        w_dir_str = 'SE'
    else:
        w_dir_str = 'S'
    return w_dir_str


def get_weather(t='base'):
    with open(w_path) as w_file:
        weather = json.load(w_file)
    next_hour = datetime.now()
    next_hour = next_hour.hour
    if t == 'base':
        temperature = [str(round(weather['current']["temperature_2m"])) + '\u00A0' + '°C']
        temp_for = [weather['hourly']['temperature_2m'][next_hour:25], weather['hourly']['temperature_2m'][25:]]
        for t in temp_for:
            t.sort()
            t_min, t_max = t[0], t[-1]
            if t_min == t_max:
                temperature.append(str(round(t_min)) + '\u00A0' + '°C')
            else:
                temperature.append(str(round(t_min)) + '...' + str(round(t_max)) + '\u00A0' + '°C')
        return temperature
    elif t == 'now':
        wind = wind_dir_str(weather['current']["wind_direction_10m"])
        weather_data = {'time': weather['current']['time'][-5:],
                        'temperature': str(weather['current']["temperature_2m"]) + " \u00b0C",
                        'humidity': str(weather['current']["relative_humidity_2m"]) + " %",
                        'surface_pressure': str(weather['current']["surface_pressure"]) + 'hPa',
                        'wind': str(wind)}
        return weather_data


if __name__ == '__main__':
    a = get_forecast(COORD)
    # sun, check_time = set_sunrise()
    b = get_weather('now')
    print(b)
