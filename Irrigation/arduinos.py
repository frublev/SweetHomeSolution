from requests import get
from datetime import datetime, time, timedelta
from requests.exceptions import ConnectTimeout, ConnectionError
from urllib3.exceptions import ProtocolError

from Irrigation.models import WateringModel, ValveModel, WateringSchemeModel


url_ard = 'http://192.168.0.177/'


def request_pin_status(url):
    try:
        response_ard = get(url, timeout=20)
        if response_ard.status_code == 200:
            response_ard = response_ard.text
            response_ard = response_ard[:4]
        else:
            response_ard = 'dddd'
    except ConnectTimeout:
        response_ard = 'dddd'
        print('ConnectTimeout')
    except ConnectionError:
        response_ard = 'dddd'
        print('ConnectionError')
    except ProtocolError:
        response_ard = 'dddd'
        print('ProtocolError')
    return response_ard


def valve_on_off(session, relay, relays_status, timer, token):
    pin = 7 - relay + 1
    start_time = None
    if relays_status[relay - 1] == 'f':
        response = get(url_ard + f'digital_pin={pin}&timer={timer}&pin_high')
        if response.status_code == 200:
            new_watering = WateringModel()
            new_watering.user_id = token.user.id
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


def get_start_time(session, start_, scheme_=None, valves_=(), valve_=0, duration_=0):
    pause_till = start_ + timedelta(seconds=duration_ + 60)
    if len(valves_) > 1:
        i = valves_.index(valve_)
    else:
        i = 100
    if i + 1 < len(valves_):
        start_ = pause_till
        valve_ = valves_[i + 1]
    else:
        start_ = datetime(2021, 1, 1)
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        dt0 = datetime.combine(current_date, time(0, 0))
        next_time = session.query(WateringSchemeModel).filter(WateringSchemeModel.status == True).all()
        if next_time:
            for nt in next_time:
                next_start = nt.schedule
                next_start.sort()
                for ns in next_start:
                    dt1 = dt0 + timedelta(seconds=ns)
                    if dt1 > current_datetime > start_ or start_ > dt1 > current_datetime:
                        start_ = dt1
                        scheme_ = nt
                        break
                else:
                    if (dt0 + timedelta(days=1, seconds=next_start[0])) < start_ or start_ < dt0:
                        start_ = dt0 + timedelta(days=1, seconds=next_start[0])
                        scheme_ = nt
            valves_ = session.query(ValveModel).filter(ValveModel.area_id == scheme_.area_id).all()
            if pause_till - timedelta(seconds=duration_ + 60) < start_ < pause_till:
                start_ = pause_till
            # valves_ = []
            # for v in valves_q:
            #     valves_.append(int(v.id))
            valve_ = valves_[0]
            valves_ = tuple(valves_)
        else:
            start_, scheme_, valves_, valve_, duration_ = datetime(2021, 1, 1), None, (), 0, 0
    print(f'get_start_time {start_, scheme_.area_id, valves_, valve_.id, duration_}')
    return start_, scheme_, valves_, valve_, duration_
