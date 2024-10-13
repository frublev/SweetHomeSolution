from requests import get
from datetime import datetime, time, timedelta
from requests.exceptions import ConnectTimeout, ConnectionError
from urllib3.exceptions import ProtocolError

from Irrigation.global_var import settings
from Irrigation.models import WateringModel, ValveModel, AreaModel, AlertModel
from Irrigation.weather_stat import set_sunrise

url_ard = 'http://192.168.0.177/'


# def request_pin_status(url='http://192.168.0.177/'):
#     try:
#         response_ard = get(url, timeout=20)
#         if response_ard.status_code == 200:
#             response_ard = response_ard.text
#             response_ard = response_ard[:4]
#         else:
#             response_ard = 'dddd'
#     except ConnectTimeout:
#         response_ard = 'dddd'
#         print('ConnectTimeout')
#     except ConnectionError:
#         response_ard = 'dddd'
#         print('ConnectionError')
#     except ProtocolError:
#         response_ard = 'dddd'
#         print('ProtocolError')
#     if response_ard == 'dddd':
#         alert_write(1, True)
#     return response_ard


def valve_on_off(session, relay, relays_status, timer, token=None):
    pin = 7 - relay + 1
    start_time = None
    if relays_status[relay - 1] == 'f':
        response = get(url_ard + f'digital_pin={pin}&timer={timer}&pin_high')
        if response.status_code == 200:
            new_watering = WateringModel()
            if token:
                new_watering.user_id = token.user.id
            else:
                new_watering.user_id = 1
            new_watering.creation_time = datetime.now()
            start_time = new_watering.creation_time
            valve = session.query(ValveModel).filter(ValveModel.relay == relay).first()
            new_watering.valve_id = valve.id
            new_watering.status = True
            session.add(new_watering)
            session.commit()
    else:
        response = get(url_ard + f'digital_pin={pin}&pin_low')
    return response, start_time


def set_duration(sq, jet, v=5.5):
    duration = sq * v / jet * 60
    duration = round(duration, 0)
    return duration


def gts(session):
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    dt0 = datetime.combine(current_date, time(0, 0))
    areas = session.query(AreaModel).order_by(AreaModel.id).all()
    alerts = session.query(AlertModel).all()
    alerts_types = []
    for at in alerts:
        alerts_types.append(at.id)
    durations = []
    ar_start = []
    start_time = None
    for ar in areas:
        if ar.auto:
            t_delta = timedelta(seconds=set_sunrise()[0][0])
            if dt0 + t_delta < current_datetime:
                t_delta = timedelta(seconds=set_sunrise()[0][1])
            valves_ = session.query(ValveModel).filter(ValveModel.area_id == ar.id).all()
            j = 0
            for v in valves_:
                j += v.jet
            j = j / len(valves_)
            duration = set_duration(ar.square, j)
            print(duration)
        else:
            t_delta = timedelta(seconds=ar.schedule[0])
            duration = ar.duration[0]
        dt1 = dt0 + t_delta
        if dt1 < current_datetime:
            dt1 = dt1 + timedelta(days=1)
        ar_start.append({'area': ar.id, 'start_time': dt1, 'duration': duration})
        ar_start = sorted(ar_start, key=lambda x: x['start_time'])
    if ar_start[0]:
        start_time = ar_start[0]['start_time']
        areas = [ar_start[0]['area']]
        durations = [ar_start[0]['duration']]
    for i in range(1, len(ar_start)):
        if ar_start[i]['start_time'] <= ar_start[i - 1]['start_time'] + timedelta(seconds=ar_start[i - 1]['duration']):
            areas.append(ar_start[i]['area'])
            durations.append(ar_start[i]['duration'])
    return start_time, areas, durations, alerts_types
