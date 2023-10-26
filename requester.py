import requests
from datetime import datetime, timedelta, date, time

cook = '67116395-dc55-4cc7-840c-a258f2ac2d28'


def create_scheme(data_, schedule=[]):
    schedule_ = []
    for s in schedule:
        time_ = s[0] * 3600 + s[1] * 60
        schedule_.append(time_)
    data_['schedule'] = schedule_
    url_flask = 'http://192.168.0.105:5000/irrigation/schemes/'
    response = requests.post(url_flask, json=data_, cookies={'token': cook})
    print(response.status_code)
    print(response.json())


def edit_scheme(id_, data_, schedule=[]):
    url_flask = 'http://192.168.0.105:5000/irrigation/schemes/' + id_ + '/'
    schedule_ = []
    for s in schedule:
        time_ = s[0] * 3600 + s[1] * 60
        schedule_.append(time_)
    data_['schedule'] = schedule_
    response = requests.patch(url_flask, json=data_, cookies={'token': cook})
    print(response.status_code)
    print(response.json())


data = {
    'volume': 300,
    'volume_auto': False,
    'schedule_program': 1,
    'area_id': 1,
    'status': True,
}


# create_scheme(data, [[10, 45], [15, 55]])
edit_scheme('1', data, [[10, 10], [11, 52], [16, 27]])

# dt = datetime.now()
# d = datetime.date(dt)
# dt = datetime.combine(d, time(0, 0))
# print(int(dt.timestamp()))
