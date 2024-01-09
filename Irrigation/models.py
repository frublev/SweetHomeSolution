from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
    func,
    Boolean
)

from sqlalchemy.types import ARRAY
from sqlalchemy_utils import EmailType
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


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

    def check_password(self, password: str, bcrypt):
        return bcrypt.check_password_hash(self.password.encode(), password.encode())


class Token(Base):
    __tablename__ = "tokens"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    creation_time = Column(DateTime, server_default=func.now())
    status = Column(Boolean, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(UserModel, lazy='joined')


class WateringSchemeModel(Base):
    __tablename__ = "schemes"
    id = Column(Integer, primary_key=True)
    creation_time = Column(DateTime, server_default=func.now())
    volume = Column(Float)
    volume_auto = Column(Boolean, nullable=True)
    schedule = Column(ARRAY(Integer), nullable=True)
    schedule_program = Column(Integer, nullable=True)
    status = Column(Boolean, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(UserModel, lazy='joined')

    def to_dict(self):
        return {
            'creation_time': self.creation_time,
            'volume': self.volume,
            'volume_auto': self.volume_auto,
            'schedule': self.schedule,
            'schedule_program': self.schedule_program,
            'status': self.status,
            'user_id': self.user_id
        }


class AreaModel(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True)
    head = Column(String(200), nullable=False, unique=True)
    description = Column(String(1000), nullable=False)
    square = Column(Float, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    scheme_id = Column(Integer, ForeignKey('schemes.id'))
    scheme = relationship(WateringSchemeModel, lazy='joined')
    status = Column(Boolean, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(UserModel, lazy='joined')

    def to_dict(self):
        return {
            'head': self.head,
            'description': self.description,
            'square': self.square,
            'creation_time': int(self.creation_time.timestamp()),
            'status': self.status,
            'id': self.id,
            'user_id': self.user_id,
            'scheme_id': self.scheme_id
        }


class ValveModel(Base):
    __tablename__ = "valves"
    id = Column(Integer, primary_key=True)
    head = Column(String(200), nullable=False, unique=True)
    description = Column(String(1000), nullable=False)
    model = Column(String(100), nullable=False)
    jet = Column(Float, nullable=False)
    relay = Column(Integer, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    area_id = Column(Integer, ForeignKey('areas.id'))
    area = relationship(AreaModel, lazy='joined')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(UserModel, lazy='joined')

    def to_dict_full(self):
        return {
            'head': self.head,
            'description': self.description,
            'model': self.model,
            'jet': self.jet,
            'relay': self.relay,
            'creation_time': int(self.creation_time.timestamp()),
            'id': self.id,
            'area_id': self.area_id,
            'user_id': self.user_id
        }

    def to_dict_short(self):
        return {
            'head': self.head,
            'description': self.description,
            'model': self.model,
            'jet': self.jet,
        }


class SprinklerModel(Base):
    __tablename__ = "sprinklers"
    id = Column(Integer, primary_key=True)
    model = Column(String(200), nullable=False)
    description = Column(String(1000))
    sector = Column(Integer)
    creation_time = Column(DateTime, server_default=func.now())
    area_id = Column(Integer, ForeignKey('areas.id'))
    area = relationship(AreaModel, lazy='joined')
    valve_id = Column(Integer, ForeignKey('valves.id'))
    valve = relationship(ValveModel, lazy='joined')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(UserModel, lazy='joined')

    def to_dict(self):
        return {
            'model': self.model,
            'description': self.description,
            'sector': self.sector,
            'creation_time': int(self.creation_time.timestamp()),
            'id': self.id,
            'area_id': self.area_id,
            'user_id': self.user_id,
            'valve_id': self.valve_id
        }


class WateringModel(Base):
    __tablename__ = "watering"
    id = Column(Integer, primary_key=True)
    creation_time = Column(DateTime, nullable=True)
    stop_time = Column(DateTime)
    volume = Column(Float)
    status = Column(Boolean, nullable=True)
    valve_id = Column(Integer, ForeignKey('valves.id'))
    valve = relationship(ValveModel, lazy='joined')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(UserModel, lazy='joined')

    def to_dict_full(self):
        return {
            'creation_time': int(self.creation_time.timestamp()),
            'stop_time': self.stop_time,
            'status': self.status,
            'volume': self.volume,
            'id': self.id,
            'valve_id': self.valve_id,
            'user_id': self.user_id
        }

    def to_dict_short(self):
        return {
            'head': self.head,
            'description': self.description,
            'model': self.model,
            'jet': self.jet,
        }
