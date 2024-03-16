from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Integer, String, create_engine, ForeignKey
from sqlalchemy.orm import (
    sessionmaker,
    Mapped,
    mapped_column,
    DeclarativeBase,
    MappedAsDataclass,
)

DATABASE_URL = "sqlite:///./sqlite.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(engine, autoflush=False)


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str]
    role: Mapped[str] = mapped_column(String, default="user")


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    code: Mapped[str] = mapped_column(String, unique=True)


class City(Base):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    country_id: Mapped[int] = mapped_column(Integer, ForeignKey("countries.id"))


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id"), name="city_id_fk"
    )
    datetime: Mapped[datetime]
    forecasted_temperature: Mapped[float]
    forecasted_humidity: Mapped[float]


class ForecastResponse(BaseModel):
    city_id: int
    datetime: datetime
    forecasted_temperature: float
    forecasted_humidity: float


class ForecastMessage(BaseModel):
    message: str
