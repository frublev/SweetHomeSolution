"""
Routes and views for the flask application.
"""

from datetime import datetime

from flask import render_template, request, jsonify, make_response, redirect
from flask.views import MethodView
from flask_bcrypt import Bcrypt

from Irrigation import app
from requests import get

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
    Boolean
)
from sqlalchemy_utils import EmailType
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import uuid
import pydantic
import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(dotenv_path)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

bcrypt = Bcrypt(app)
PG_DSN = os.getenv('PG_DSN')
engine = create_engine(PG_DSN)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    registration_time = Column(DateTime, server_default=func.now())
    email = Column(EmailType, nullable=False, unique=True)
    phone_num = Column(String(20), nullable=False, unique=True)

    def to_dict(self):
        return {
            'user_name': self.user_name,
            'email': self.email,
            'registration_time': int(self.registration_time.timestamp()),
            'id': self.id,
        }

    def check_password(self, password: str):
        return bcrypt.check_password_hash(self.password.encode(), password.encode())


class Token(Base):
    __tablename__ = "tokens"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    creation_time = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Boolean, nullable=True)
    user = relationship(UserModel, lazy="joined")


class ValveModel(Base):
    __tablename__ = "valves"
    id = Column(Integer, primary_key=True)
    head = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    jet = Column(Integer, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship(UserModel, lazy="joined")

    def to_dict(self):
        return {
            'head': self.head,
            'description': self.description,
            'jet': self.jet,
            'creation_time': int(self.creation_time.timestamp()),
            'id': self.id,
            'user_id': self.user_id
        }


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
    print(token.status)
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
            if user is None or not user.check_password(login_data['password']):
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
    url_ard = 'http://192.168.0.177/'
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


class ValveView(MethodView):
    def get(self, valve_id: int):
        area = f'Irrigation area {valve_id}'
        url_ard = 'http://192.168.0.177/'
        response = get(url_ard)
        response = response.text
        print(response)
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
            'irrigation_valve.html',
            title=area,
            year=datetime.now().year,
            button1=button[0],
            valve_status1=valve_status[0],
            button2=button[1],
            valve_status2=valve_status[1],
            button3=button[2],
            valve_status3=valve_status[2],

        )


app.add_url_rule('/irrigation/<int:valve_id>/', view_func=ValveView.as_view('view_valve'), methods=['GET'])
app.add_url_rule('/create_user/', view_func=UserView.as_view('create_user'), methods=['POST'])
app.add_url_rule('/login/', view_func=Login.as_view('show_login_form'), methods=['GET'])
app.add_url_rule('/login/', view_func=Login.as_view('login'), methods=['POST'])
app.add_url_rule('/welcome/', view_func=WelcomeView.as_view('show_welcome'), methods=['GET'])
app.add_url_rule('/user/<int:user_id>/', view_func=UserView.as_view('get_user'), methods=['GET'])
