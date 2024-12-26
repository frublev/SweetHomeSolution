import logging

import os
from datetime import datetime, timedelta
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
    status = response.status_code
    if response:
        with open(w_path, 'w') as f:
            try:
                json.dump(response.json(), f)
            except requests.exceptions.JSONDecodeError:
                msg = f'Error dumping to json. Status code {status}'
                weather_logger.error(msg)
    else:
        msg = f'Weather forecast is empty. Status code {status}'
        weather_logger.error(msg)
    return status


def to_second(full_date):
    h_m = full_date[11:]
    h = int(h_m[:2]) * 60 * 60
    m = int(h_m[3:]) * 60
    s = h + m
    return s


def set_sunrise():
    with open(w_path) as w_file:
        weather = json.load(w_file)
    sun_rise_time = []
    for i in weather['daily']['sunrise']:
        s = to_second(i)
        sun_rise_time.append(s)
    ct = weather['current']['time']
    return sun_rise_time, ct


def wind_dir_str(wind_dir):
    if 22.5 <= wind_dir < 67.5:
        w_dir_str = ('SW', '\u2197')
    elif 67.5 <= wind_dir < 112.5:
        w_dir_str = ('W', '\u2192')
    elif 112.5 <= wind_dir < 157.5:
        w_dir_str = ('NW', '\u2198')
    elif 157.5 <= wind_dir < 202.5:
        w_dir_str = ('N', '\u2193')
    elif 202.5 <= wind_dir < 247.5:
        w_dir_str = ('NE', '\u2199')
    elif 247.5 <= wind_dir < 292.5:
        w_dir_str = ('E', '\u2190')
    elif 292.5 <= wind_dir < 337.5:
        w_dir_str = ('SE', '\u2196')
    else:
        w_dir_str = ('S', '\u2191')
    return w_dir_str


def get_weather_icon(cloudcover, precipitation, night=True):
    if cloudcover < 10:
        cloud_icon = '\u2600'
        if night:
            cloud_icon = '\N{CRESCENT MOON}'
    elif 10 <= cloudcover < 30:
        cloud_icon = '\N{WHITE SUN WITH SMALL CLOUD}'
        if night:
            cloud_icon = '\u2601'
        if precipitation > 0.3:
            cloud_icon = '\N{WHITE SUN BEHIND CLOUD WITH RAIN}'
            if night:
                cloud_icon = '\N{CLOUD WITH RAIN}'
    elif 30 <= cloudcover < 70:
        cloud_icon = '\N{WHITE SUN BEHIND CLOUD}'
        if night:
            cloud_icon = '\u2601'
        if precipitation > 0.3:
            cloud_icon = '\N{WHITE SUN BEHIND CLOUD WITH RAIN}'
            if night:
                cloud_icon = '\N{CLOUD WITH RAIN}'
    else:
        cloud_icon = '\u2601'
        if precipitation > 0.3:
            cloud_icon = '\N{CLOUD WITH RAIN}'
    return cloud_icon


def get_weather(t=100):
    with open(w_path) as w_file:
        try:
            weather = json.load(w_file)
        except:
            msg = f'Error in json-file'
            weather_logger.error(msg)
    if weather:
        actuality = weather['current']["time"].replace("T", " ")
        ct = datetime.now()
        next_hour = ct.hour
        weather_data = []
        if t == 100:
            weather_data = [str(round(weather['current']["temperature_2m"])) + '\u00A0' + '°C']
            day = 'today'
            temp_for = [weather['hourly']['temperature_2m'][next_hour:25], weather['hourly']['temperature_2m'][25:]]
            for t in temp_for:
                t.sort()
                t_min, t_max = t[0], t[-1]
                if t_min == t_max:
                    weather_data.append(str(round(t_min)) + '\u00A0' + '°C')
                else:
                    weather_data.append(str(round(t_min)) + '...' + str(round(t_max)) + '\u00A0' + '°C')
        elif t == 101:
            day = 'now'
            wind = wind_dir_str(weather['current']["wind_direction_10m"])
            weather_data = {'time': weather['current']['time'][-5:],
                            'temperature': str(weather['current']["temperature_2m"]) + " \u00b0C",
                            'humidity': str(weather['current']["relative_humidity_2m"]) + " %",
                            'surface_pressure': str(weather['current']["surface_pressure"]) + 'hPa',
                            'wind': str(wind)}
        else:
            if t == 0:
                day = 'today'
            elif t == 1:
                day = 'tomorrow'
            else:
                day = ct.date() + timedelta(days=t)
            hours = t * 24
            for h in range(hours, hours + 24):
                if t < 2:
                    if to_second(weather['daily']['sunrise'][t]) <= to_second(weather['hourly']['time'][h]) < to_second(
                            weather['daily']['sunset'][t]):
                        night = False
                    else:
                        night = True
                    wind = wind_dir_str(weather['hourly']["winddirection_10m"][h])
                    weather_data.append({
                        'time': weather['hourly']['time'][h][-5:],
                        't': weather['hourly']['temperature_2m'][h],
                        'p': get_weather_icon(
                            weather['hourly']['cloudcover'][h],
                            weather['hourly']['precipitation'][h],
                            night
                        ) + ' ' + str(weather['hourly']['precipitation'][h]),
                        'h': weather['hourly']['relativehumidity_2m'][h],
                        'w': wind[1] + ' ' + str(round(weather['hourly']['windspeed_10m'][h], 1)),
                        })
        return weather_data, day, actuality


if __name__ == '__main__':
    a = get_forecast(COORD)
    # sun, check_time = set_sunrise()
    a, b, c = get_weather(2)
    print(b, c, a)
