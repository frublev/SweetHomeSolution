import json

import requests
from requests import get, post, patch, delete


def arduino_test(hl):
    url_ard = 'http://192.168.0.177/' + hl
    response = get(url_ard)
    print(response.text)
    return response


def login_test(user_name, password, phone_num, email):
    url_flask = 'http://192.168.0.104:5000/create_user/'
    data_ = {
        'user_name': user_name,
        'password': password,
        'phone_num': phone_num,
        'email': email
    }
    response = requests.post(url_flask, json=data_)
    print(response.status_code)
    print(response.json())


def create_area(data_):
    url_flask = 'http://192.168.0.104:5000/irrigation/area/'
    response = requests.post(url_flask, json=data_, cookies={'token': 'f57022f2-169f-4752-bf02-a9520f4d3009'})
    print(response.status_code)
    print(response.json())


def edit_valve(id, data_):
    url_flask = 'http://192.168.0.104:5000/irrigation/' + id + '/'
    response = requests.patch(url_flask, json=data_, cookies={'token': 'bde14bfe-e862-4719-bf24-f8276ce2e59c'})
    print(response.status_code)
    print(response.json())


def create_unit(data_, unit):
    url_flask = 'http://192.168.0.104:5000/irrigation/' + unit + '/'
    response = requests.post(url_flask, json=data_, cookies={'token': 'ab34ef69-235c-4b5c-92d8-01fabef87a16'})
    print(response.status_code)
    print(response.json())


def create_areas():
    area1 = {
        'head': 'Northern square',
        'description': 'North of plot',
        'square': 52.5,
        'auto': True,
        'on_off': True,
        'schedule': [43200],
        'duration': [900]
    }

    area2 = {
        'head': 'Southern rectangle',
        'description': 'South of plot',
        'square': 41.5,
        'auto': True,
        'on_off': True,
        'schedule': [43200],
        'duration': [600]
    }

    areas = [area1, area2]

    for a in areas:
        create_unit(a, 'areas')


def create_valves():
    valve1 = {
        'head': '#1',
        'description': 'Northern square',
        'model': 'Hunter PGV-100MM-B-DC',
        'jet': 16.2,
        'relay': 1,
        'area_id': 1,
    }

    valve2 = {
        'head': '#2',
        'description': 'Southern rectangle: West',
        'model': 'Hunter PGV-100MM-B-DC',
        'relay': 2,
        'jet': 26.1,
        'area_id': 2,
    }

    valve3 = {
        'head': '#3',
        'description': 'Northern square: East',
        'model': 'Hunter PGV-100MM-B-DC',
        'relay': 3,
        'jet': 25.3,
        'area_id': 2,
    }

    valves = [valve1, valve2, valve3]

    for v in valves:
        create_unit(v, 'valves')


def create_sprinklers():
    description = ['South West', 'North West', 'South East', 'North East',
                   'West 1', 'West 2', 'West 3', 'West 4', 'West 5', 'West 6',
                   'East 1', 'East 2', 'East 3', 'East 4', 'East 5']
    for d in description:
        if d[0] == 'W':
            area_id = 2
            valve_id = 2
            model = 'Hunter PSU-04-10A'
        elif d[0] == 'E':
            area_id = 2
            valve_id = 3
            model = 'Hunter PSU-02-8A'
        else:
            area_id = 1
            valve_id = 1
            model = 'Gargena T100'
        if d == 'West 5' or d == 'West 6':
            sector = 90
        elif d == 'East 1':
            sector = 270
            model = 'Hunter PSU-02-10A'
        else:
            sector = 180
        sprinklers = {
            'model': model,
            'description': d,
            'sector': sector,
            'area_id': area_id,
            'valve_id': valve_id,
        }
        create_unit(sprinklers, 'sprinklers')


# create_areas()
# create_valves()
# create_sprinklers()
# login_test('frublev', '1234567', '+123456789', 'f.rublev@gmail.com')
