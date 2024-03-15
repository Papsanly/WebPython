from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")

    def __init__(self, username, email, hashed_password, role="user"):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.role = role

    def __repr__(self):
        return self.username


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    code = Column(String, unique=True)

    def __init__(self, name, code):
        self.code = code
        self.name = name

    def __repr__(self):
        return self.name


class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    country_id = Column(Integer, ForeignKey("countries.id"))

    def __init__(self, name, country_id):
        self.name = name
        self.country_id = country_id

    def __repr__(self):
        return f"City(name={self.name}, country_id={self.country_id})"


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), name="city_id_fk")
    datetime = Column(DateTime)
    forecasted_temperature = Column(Float)
    forecasted_humidity = Column(Float)

    def __init__(self, datetime, city_id, forecasted_temperature, forecasted_humidity):
        self.datetime = datetime
        self.city_id = city_id
        self.forecasted_temperature = forecasted_temperature
        self.forecasted_humidity = forecasted_humidity


from pydantic import BaseModel
from datetime import datetime


class ForecastResponse(BaseModel):
    city_id: int
    datetime: datetime
    forecasted_temperature: float
    forecasted_humidity: float


class ForecastMessage(BaseModel):
    message: str


from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
