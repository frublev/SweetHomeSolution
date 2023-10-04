from datetime import datetime

from flask import render_template, request, jsonify, make_response, redirect
from flask.views import MethodView
from flask_bcrypt import Bcrypt

from Irrigation import app
from requests import get

from sqlalchemy import create_engine, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import pydantic
import os

from dotenv import load_dotenv

from .arduinos import request_pin_status, url_ard
from .models import UserModel, Token, AreaModel, Base, SprinklerModel, ValveModel, WateringModel

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(dotenv_path)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

bcrypt = Bcrypt(app)
PG_DSN = os.getenv('PG_DSN')
engine = create_engine(PG_DSN)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)


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
    return render_template(
        'monitor.html',
        title='Home Page',
        year=datetime.now().year,
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

                relays_status = request_pin_status(url_ard)
                print(relays_status)
                valves = []
                valves_str = ''
                start_time = 0
                active_valve = None
                for valve_ in valves_:
                    valve = valve_.to_dict_short()
                    valve['relay'] = valve_.relay
                    if relays_status[valve_.relay - 1] == 'n':
                        valve['button'] = ['On', 'btn btn-danger']
                        active_valve = valve['relay']
                        watering_session = session.query(WateringModel).filter(WateringModel.valve_id == valve_.id,
                                                                               WateringModel.status == True).first()
                        start_time = watering_session.creation_time
                        start_time = start_time.timestamp()
                    elif relays_status[valve_.relay - 1] == 'f':
                        valve['button'] = ['Off', 'btn btn-success']
                    else:
                        valve['button'] = ['Unknown', 'btn btn-secondary disabled']
                    valves.append(valve)
                    valves_str += str(valve['relay']) + ';'

                response = make_response(render_template('irrigation_area.html',
                                                         head=area.head,
                                                         description=description,
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
                return jsonify(upd_area.to_dict())


@app.route('/valve_manual', methods=['POST'])
def valve_manual():
    relays_status = request_pin_status(url_ard)
    if relays_status == 'dddd':
        js_json = {'fn': 'dddd'}
    else:
        request_data = request.get_json()
        with Session() as session:
            token = check_token(session)
            if token:
                relay = int(request_data['relay'])
                pin = 7 - relay + 1
                if relays_status[relay - 1] == 'f':
                    response = get(url_ard + f'digital_pin={pin}&pin_high')
                    if response.status_code == 200:
                        new_watering = WateringModel()
                        new_watering.user_id = token.user.id
                        valve = session.query(ValveModel).filter(ValveModel.relay == relay).first()
                        new_watering.valve_id = valve.id
                        new_watering.status = True
                        session.add(new_watering)
                        session.commit()
                else:
                    response = get(url_ard + f'digital_pin={pin}&pin_low')
        response = response.text
        js_json = {'fn': response}
    return jsonify(js_json)


@app.route('/watering_stopped/<rs_status>')
def watering_stopped(rs_status):
    relay = 0
    for index, value in enumerate(rs_status):
        if value == 'n':
            relay = index + 1
            with Session() as session:
                valve = session.query(ValveModel).filter(ValveModel.relay == relay).first()
                watering_session = session.query(WateringModel).filter(WateringModel.valve_id == valve.id,
                                                                       WateringModel.status == True).all()
                print(watering_session)
                for w_s in watering_session:
                    print(w_s.creation_time)
                    w_s.stop_time = datetime.now()
                    w_s.status = False
                session.commit()
    print(relay)
    return rs_status


@app.route('/relay_status')
def relay_status_check():
    relays_status = request_pin_status(url_ard)
    js_json = {'fn': relays_status}
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


app.add_url_rule('/irrigation/<int:area_id>/', view_func=AreaView.as_view('view_area'), methods=['GET'])
app.add_url_rule('/irrigation/<int:area_id>/', view_func=AreaView.as_view('edit_area'), methods=['PATCH'])
app.add_url_rule('/irrigation/areas/', view_func=AreaView.as_view('create_area'), methods=['POST'])
app.add_url_rule('/irrigation/valves/', view_func=ValveView.as_view('create_valve'), methods=['POST'])
app.add_url_rule('/irrigation/sprinklers/', view_func=SprinklerView.as_view('create_sprinkler'), methods=['POST'])
app.add_url_rule('/create_user/', view_func=UserView.as_view('create_user'), methods=['POST'])
app.add_url_rule('/login/', view_func=Login.as_view('show_login_form'), methods=['GET'])
app.add_url_rule('/login/', view_func=Login.as_view('login'), methods=['POST'])
app.add_url_rule('/welcome/', view_func=WelcomeView.as_view('show_welcome'), methods=['GET'])
app.add_url_rule('/user/<int:user_id>/', view_func=UserView.as_view('get_user'), methods=['GET'])

# 13:30 30/08 два куска мыла, яйца, пакеты для мусора
