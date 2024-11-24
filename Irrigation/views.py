import logging

import time as pause
from datetime import datetime, time, timedelta
from threading import Thread

import requests
from flask import render_template, request, jsonify, make_response, redirect
from flask.views import MethodView
from flask_bcrypt import Bcrypt

from Irrigation import app
from requests import get

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import pydantic
import os

from dotenv import load_dotenv

from requests.exceptions import ConnectTimeout, ConnectionError
from urllib3.exceptions import ProtocolError

from .global_var import settings, alerts_type
from .arduinos import url_ard, valve_on_off, gts
from .loggers import log_handler, get_log, log_for_monitor
from .weather_stat import get_forecast, set_sunrise, COORD, get_weather
from .models import UserModel, Token, AreaModel, Base, SprinklerModel, ValveModel, WateringModel, AlertTypeModel, \
    AlertModel


views_logger = logging.getLogger(__name__)
views_logger.setLevel(logging.INFO)
views_logger.addHandler(log_handler)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(dotenv_path)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

bcrypt = Bcrypt(app)
PG_DSN = os.getenv('PG_DSN')
cook = os.getenv('COOK')
engine = create_engine(PG_DSN)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

g_start = datetime(2021, 1, 1)
g_area = None
g_valves = ()
g_valve = 0
g_duration = 0


class CreateUserValidation(pydantic.BaseModel):
    user_name: str
    password: str
    phone_num: str
    email: str

    @pydantic.field_validator('password')
    def strong_password(cls, value):
        if len(value) < 5:
            raise ValueError('too easy')
        return value


class HTTPError(Exception):
    def __init__(self, status_code: int, message):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HTTPError)
def error_handle(error):
    response = jsonify({"message": error.message})
    response.status_code = error.status_code
    return response


def check_token(session):
    token = (session.query(Token).filter(Token.id == request.cookies.get('token')).first())
    if token is None or token.status == False:
        raise HTTPError(403, 'invalid token')
    return token


class Login(MethodView):
    def get(self):
        response = make_response(render_template('login.html'))
        return response

    def post(self):
        login_data = request.json
        with Session() as session:
            user = (
                session.query(UserModel)
                    .filter(UserModel.user_name == login_data['login'])
                    .first()
            )
            if user is None or not user.check_password(login_data['password'], bcrypt):
                message = {'message': 'incorrect user or password'}
                response = make_response(message, 401)
                return response
            else:
                old_token = (
                    session.query(Token)
                        .filter(Token.user_id == user.id)
                        .first()
                )
                if old_token:
                    session.query(Token).filter(Token.id == old_token.id).update({'status': False})
                token = Token(user_id=user.id, status=True)
                session.add(token)
                session.commit()
                response = make_response({'message': 'Welcome'})
                response.set_cookie(key='token', value=str(token.id), httponly=True, samesite='Strict')
                return response


@app.route('/logout')
def logout():
    with Session() as session:
        token = check_token(session)
        if token:
            session.query(Token).filter(Token.id == token.id).update({'status': False})
            session.commit()
            print(token.id)
            print(token.status)
        return redirect('/', code=302)


@app.route('/')
@app.route('/monitor')
def monitor():
    """Renders the home page."""
    valves_status = request_pin_status()
    if valves_status == 'dddd':
        valves_status = 'No connection!'
    else:
        valves_status = valves_status.replace('f', 'Off-')
        valves_status = valves_status.replace('n', 'On-')
    today = datetime.now().date()
    tod_yest = (str(today), str(today - timedelta(days=1)))
    log_layout = log_for_monitor(tod_yest)
    return render_template(
        'monitor.html',
        valves=valves_status,
        title='Home Page',
        year=datetime.now().year,
        layout=log_layout
    )


@app.route('/logs/')
def logs():
    current_date = datetime.now()
    current_date = str(current_date.date())
    print(current_date)
    log_layout = log_for_monitor()
    return render_template(
        'logs.html',
        title='Logs',
        year=datetime.now().year,
        layout=log_layout
    )


@app.route('/check_token')
def check_token_base():
    with Session() as session:
        token = check_token(session)
        if token:
            return jsonify({'message': token.user.user_name, 'user_id': token.user.id})
        else:
            message = {'message': 'auth error'}
            response = make_response(message, 403)
            return response


@app.route('/irrigation/')
@app.route('/irrigation')
def irrigation():
    with Session() as session:
        token = check_token(session)
        if token:
            areas = session.query(AreaModel).order_by(AreaModel.id).all()
            layout = []
            for ar in areas:
                area = ar.to_dict()
                # area['volume_auto'] = ar.scheme.volume_auto
                # area['schedule_program'] = ar.scheme.schedule_program
                layout.append(area)
    return render_template(
        'irrigation.html',
        layout=layout,
        year=datetime.now().year
    )


class WelcomeView(MethodView):
    def get(self):
        with Session() as session:
            token = check_token(session)
            if token:
                return render_template(
                    'welcome.html',
                    message=f'Welcome {token.user.user_name}!',
                    year=datetime.now().year,
                )
            else:
                message = {'message': 'auth error'}
                response = make_response(message, 403)
                return response


@app.route('/security')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )


@app.route('/irrigation_old', methods=['GET', 'POST'])
def irrigation_old():
    response = get(url_ard)
    response = response.text
    print(response)

    if request.method == 'POST':
        request_data = request.get_json()
        valve = int(request_data['valve'])
        pin = 7 - valve + 1
        print(pin)
        if response[valve - 1] == 'f':
            response = get(url_ard + f'digital_pin={pin}&pin_high')
        else:
            response = get(url_ard + f'digital_pin={pin}&pin_low')
        response = response.text
        js_json = {'fn': response}
        return jsonify(js_json)

    else:
        button = []
        valve_status = []
        for i in range(3):
            if response[i] == 'f':
                print(i)
                valve_status.append('off')
                button.append('btn btn-success')
            else:
                valve_status.append('on')
                button.append('btn btn-danger')
        return render_template(
            'irrigation_old.html',
            title='Irrigation System',
            year=datetime.now().year,
            button1=button[0],
            valve_status1=valve_status[0],
            button2=button[1],
            valve_status2=valve_status[1],
            button3=button[2],
            valve_status3=valve_status[2],
        )


class UserView(MethodView):
    def get(self, user_id: int):
        with Session() as session:
            token = check_token(session)
            if token.user.id != user_id:
                raise HTTPError(403, "auth error")
            else:
                response = make_response(render_template('profile.html',
                                                         user_name=token.user.user_name,
                                                         email=token.user.email,
                                                         phone_num=token.user.phone_num
                                                         ))
            return response

    def post(self):
        try:
            validated_data = CreateUserValidation(**request.json).model_dump()
        except pydantic.ValidationError as err:
            val_error = err.errors()
            raise HTTPError(400, val_error[0]['msg'])
        with Session() as session:
            validated_data['password'] = bcrypt.generate_password_hash(validated_data['password'].encode()).decode()
            new_user = UserModel(**validated_data)
            print(new_user)
            session.add(new_user)
            try:
                session.commit()
                return jsonify(new_user.to_dict())
            except IntegrityError:
                user_name = validated_data['user_name']
                session.rollback()
                return jsonify({'error': f'Username {user_name} already exists'})


class AreaView(MethodView):
    def get(self, area_id: int):
        with Session() as session:
            token = check_token(session)
            if token:
                area = session.query(AreaModel).filter(AreaModel.id == area_id).first()
                valves_ = session.query(ValveModel).filter(ValveModel.area_id == area_id).all()
                valves_count = len(valves_)
                sprinklers = session.query(SprinklerModel).filter(SprinklerModel.area_id == area_id).all()
                sprinklers = len(sprinklers)
                description = {
                    'Area': area.description,
                    'Square': area.square,
                    'Valves quantity': valves_count,
                    'Sprinklers quantity': sprinklers
                }
                try:
                    settings = {
                        'set_start_time_h': (area.schedule[0] / 1800) // 2,
                        'set_start_time_m': (area.schedule[0] / 1800) % 2 * 30,
                        'duration_m': (area.duration[0] / 30) // 60,
                        'duration_s': (area.duration[0] / 30) % 60 * 30
                    }
                except TypeError:
                    settings = {
                        'set_start_time_h': 24,
                        'set_start_time_m': 0,
                        'duration_m': 0,
                        'duration_s': 0
                    }

                relays_status = request_pin_status(url_ard)
                print(relays_status)
                valves = []
                valves_str = ''
                start_time = 0
                active_valve = None
                active_class = ["nav-link active", "tab-pane fade show active", "nav-link", "tab-pane fade"]
                for valve_ in valves_:
                    valve = valve_.to_dict_full()
                    valve['relay'] = valve_.relay
                    if relays_status[valve_.relay - 1] == 'n':
                        valve['button'] = ['On', 'btn btn-danger']
                        active_valve = valve['relay']
                        active_class = ["nav-link", "tab-pane fade", "nav-link active", "tab-pane fade show active"]
                        watering_session = session.query(WateringModel).filter(WateringModel.valve_id == valve_.id,
                                                                               WateringModel.status == True).first()
                        start_time = watering_session.creation_time
                        start_time = start_time.timestamp() * 1000
                        volume = (datetime.now().timestamp() * 1000 - start_time) / 60000 * valve_.jet
                        volume = round(volume, 1)
                        valve['button'] = [volume, 'btn btn-danger']
                    elif relays_status[valve_.relay - 1] == 'f':
                        valve['button'] = ['Off', 'btn btn-success']
                    else:
                        valve['button'] = ['Unknown', 'btn btn-secondary disabled']
                    valves.append(valve)
                    valves_str += str(valve['relay']) + ';'

                response = make_response(render_template('irrigation_area.html',
                                                         id=area.id,
                                                         head=area.head,
                                                         auto=area.auto,
                                                         on_off=area.on_off,
                                                         active_class=active_class,
                                                         description=description,
                                                         settings=settings,
                                                         valves=valves,
                                                         valves_str=valves_str,
                                                         active_valve=active_valve,
                                                         rs=relays_status,
                                                         start_time=start_time,
                                                         year=datetime.now().year,
                                                         ))
                return response

    def post(self):
        area_data = request.json
        with Session() as session:
            token = check_token(session)
            if token:
                new_area = AreaModel(**area_data)
                new_area.user_id = token.user.id
                session.add(new_area)
                try:
                    session.commit()
                    return jsonify(new_area.to_dict())
                except IntegrityError:
                    head = area_data['head']
                    session.rollback()
                    return jsonify({'error': f'Area {head} already exists'})

    def patch(self, area_id: int):
        area_data = request.json
        with Session() as session:
            token = check_token(session)
            if token:
                session.query(AreaModel).filter(AreaModel.id == area_id).update(area_data)
                session.commit()
                upd_area = session.query(AreaModel).get(area_id)
                settings.charts = gts(session)
                return jsonify(upd_area.to_dict())


@app.route('/valve_manual', methods=['POST'])
def valve_manual(timer='1800'):
    relays_status = request_pin_status(url_ard)
    if relays_status == 'dddd':
        js_json = {'fn': 'dddd'}
    else:
        request_data = request.get_json()
        relay = int(request_data['relay'])
        with Session() as session:
            token = check_token(session)
            if token:
                response, start_time = valve_on_off(session, relay, relays_status, timer, token)
        response = response.text
        if start_time:
            start_time = start_time.timestamp() * 1000
        js_json = {'fn': response, 'start_time_': start_time}
    return jsonify(js_json)


@app.route('/watering_stopped/<rs_status>')
def watering_stopped(rs_status):
    for index, value in enumerate(rs_status):
        if value == 'n':
            relay = index + 1
            with Session() as session:
                valve = session.query(ValveModel).filter(ValveModel.relay == relay).first()
                watering_session = session.query(WateringModel).filter(WateringModel.valve_id == valve.id,
                                                                       WateringModel.status == True).all()
                for w_s in watering_session:
                    w_s.stop_time = datetime.now()
                    w_s.volume = (w_s.stop_time.timestamp() - w_s.creation_time.timestamp()) / 60 * valve.jet
                    w_s.status = False
                session.commit()
    return rs_status


@app.route('/relay_status')
def relay_status_check():
    relays_status = request_pin_status(url_ard)
    js_json = {'fn': relays_status}
    return jsonify(js_json)


@app.route('/get_weather')
def get_weather_info():
    try:
        temperature = get_weather()
    except:
        temperature = ['No data', 'No data', 'No data']
    js_json = {'message': temperature}
    print('weather', js_json)
    return jsonify(js_json)


class ValveView(MethodView):
    def post(self):
        valve_data = request.json
        with Session() as session:
            token = check_token(session)
            if token:
                new_valve = ValveModel(**valve_data)
                new_valve.user_id = token.user.id
                session.add(new_valve)
                session.commit()
                return jsonify(new_valve.to_dict_full())


class SprinklerView(MethodView):
    def post(self):
        sprinkler_data = request.json
        with Session() as session:
            token = check_token(session)
            if token:
                new_sprinkler = SprinklerModel(**sprinkler_data)
                new_sprinkler.user_id = token.user.id
                session.add(new_sprinkler)
                session.commit()
                return jsonify(new_sprinkler.to_dict())


def check_time():
    checked = True
    while app:
        ct = datetime.now()
        if ct.minute in [1, 16, 31, 46]:
            if checked:
                check_forecast()
                checked = False
        else:
            checked = True
        if settings.charts[0] + timedelta(seconds=60) > ct >= settings.charts[0]:
            with Session() as session:
                indx = 0
                print(ct)
                for ar in settings.charts[1]:
                    msg = f'Trying to start watering Area {ar}...'
                    views_logger.info(msg)
                    print(msg)
                    valves_ = session.query(ValveModel).filter(ValveModel.area_id == ar).all()
                    for v in valves_:
                        d = settings.charts[2][indx] / len(valves_)
                        relay_status = request_pin_status()
                        if relay_status == 'dddd':
                            msg = f'Can not open valve {v.head}, cause irrigation controller does not respond'
                            views_logger.warning(msg)
                            break
                        valve_on_off(session, v.relay, relay_status, d)
                        print('Valve', v.head, 'was opened at', datetime.now(), 'for', d, 'seconds')
                        pause.sleep(d)
                        relay_status = request_pin_status()
                        if relay_status != 'ffff':
                            valve_on_off(session, v.relay, relay_status, 0)
                        print('Valve', v.head, 'closed at', datetime.now())
                        pause.sleep(3)
                    indx += 1
                settings.charts = gts(session)
                print('Next watering: area', settings.charts[1], 'at', settings.charts[0])
        else:
            print(ct)
            print(settings.charts)
            print(request_pin_status())
            pause.sleep(30)


def request_pin_status(url='http://192.168.0.177/'):
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
    if response_ard == 'dddd':
        alert_write(1, True)
    return response_ard


def alert_write(alert_id, start):
    globvar = list(settings.charts)
    if alert_id not in globvar[3] and start:
        globvar[3].append(alert_id)
        settings.charts = tuple(globvar)
        with Session() as session:
            new_at = AlertModel()
            new_at.alert_id = alert_id
            new_at.user_id = 1
            session.add(new_at)
            session.commit()


def start_timer():
    my_thread = Thread(target=check_time, daemon=True)
    my_thread.start()


def check_forecast():
    try:
        forecast = get_forecast(COORD)
        if forecast:
            sun, forecast_time = set_sunrise()
            print('Forecast refreshed at', forecast_time)
    except requests.exceptions.ConnectionError:
        print('Forecast was not loaded')


def check_alerts_type():
    with Session() as session:
        alert_heads = []
        alert_types = session.query(AlertTypeModel).all()
        if alert_types:
            for at in alert_types:
                alert_heads.append(at.head)
            for at in alerts_type:
                if at['head'] not in alert_heads:
                    new_at = AlertTypeModel(**at)
                    new_at.user_id = 1
                    session.add(new_at)
                    session.commit()
        else:
            for at in alerts_type:
                new_at = AlertTypeModel(**at)
                new_at.user_id = 1
                session.add(new_at)
                session.commit()


check_alerts_type()
check_forecast()
with Session() as session:
    settings.charts = gts(session)
start_timer()
views_logger.info('Server is loaded')

app.add_url_rule('/irrigation/<int:area_id>/', view_func=AreaView.as_view('view_area'), methods=['GET'])
app.add_url_rule('/irrigation/<int:area_id>/', view_func=AreaView.as_view('edit_area'), methods=['PATCH'])  # добавить area
app.add_url_rule('/irrigation/areas/', view_func=AreaView.as_view('create_area'), methods=['POST'])
app.add_url_rule('/irrigation/valves/', view_func=ValveView.as_view('create_valve'), methods=['POST'])
app.add_url_rule('/irrigation/sprinklers/', view_func=SprinklerView.as_view('create_sprinkler'), methods=['POST'])
app.add_url_rule('/create_user/', view_func=UserView.as_view('create_user'), methods=['POST'])
app.add_url_rule('/login/', view_func=Login.as_view('show_login_form'), methods=['GET'])
app.add_url_rule('/login/', view_func=Login.as_view('login'), methods=['POST'])
app.add_url_rule('/welcome/', view_func=WelcomeView.as_view('show_welcome'), methods=['GET'])
app.add_url_rule('/user/<int:user_id>/', view_func=UserView.as_view('get_user'), methods=['GET'])
