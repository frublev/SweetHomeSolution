import os

import requests
from datetime import datetime, timedelta, date, time

from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), 'Irrigation/', '.env')
print(dotenv_path)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
cook = os.getenv('COOK')


def create_user(user_name, password, phone_num, email):
    url_flask = 'http://192.168.0.108:5000/create_user/'
    data_ = {
        'user_name': user_name,
        'password': password,
        'phone_num': phone_num,
        'email': email
    }
    response = requests.post(url_flask, json=data_)
    print(response.status_code)
    print(response.json())


def create_scheme(schedule):
    data_ = {
        'volume': 300,
        'volume_auto': False,
        'schedule_program': 1,
        'status': True,
    }
    schedule_ = []
    for s in schedule:
        time_ = s[0] * 3600 + s[1] * 60
        schedule_.append(time_)
    data_['schedule'] = schedule_
    url_flask = 'http://192.168.0.108:5000/irrigation/schemes/'
    response = requests.post(url_flask, json=data_, cookies={'token': cook})
    print(response.status_code)
    print(response.json())


def edit_scheme(id_, schedule):
    data = {
        'volume': 300,
        'volume_auto': False,
        'schedule_program': 1,
        'status': True,
    }
    url_flask = 'http://192.168.0.105:5000/irrigation/schemes/' + id_ + '/'
    schedule_ = []
    for s in schedule:
        time_ = s[0] * 3600 + s[1] * 60
        schedule_.append(time_)
    data['schedule'] = schedule_
    response = requests.patch(url_flask, json=data, cookies={'token': cook})
    print(response.status_code)
    print(response.json())


def edit_unit(id_, hh, mm, unit='area'):
    t = (hh * 60 + mm) * 60
    url_flask = 'http://192.168.0.105:5000/irrigation/' + str(id_) + '/'
    areas = {
        'schedule': [t],
        'duration': 300,
    }
    response = requests.patch(url_flask, json=areas, cookies={'token': cook})
    print(response.status_code)
    print(response.json())


edit_unit(1, 16, 45, unit='area')


# create_scheme([[10, 45], [16, 30]])
# create_scheme([[11, 45], [17, 30]])
# edit_scheme('1', [[10, 45], [16, 30]])
# edit_scheme('2', [[11, 45], [17, 30]])

# create_user('frublev', '12345678', '+421905069102', 'f.rublev@gmail.com')

# dt = datetime.now()
# d = datetime.date(dt)
# dt = datetime.combine(d, time(0, 0))
# print(int(dt.timestamp()))
