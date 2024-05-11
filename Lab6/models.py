from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from flask_login import UserMixin

db = SQLAlchemy()


class Country(db.Model):
    __tablename__ = 'country'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(2), nullable=False)

    @validates('name', 'code')
    def validate_name(self, key, value):
        assert value.isalpha(), f"{key} must be Alphabetic"
        return value


class City(db.Model):
    __tablename__ = 'city'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)

    @validates('name')
    def validate_name(self, key, value):
        assert value.isalpha(), f"{key} must be Alphabetic"
        return value


class Forecast(db.Model):
    __tablename__ = 'forecast'
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    datetime = db.Column(db.Date, nullable=False)
    forecasted_temperature = db.Column(db.Integer, nullable=False)
    forecasted_humidity = db.Column(db.Integer, nullable=False)

    @validates('forecasted_humidity')
    def validate_forecasted_humidity(self, key, forecasted_humidity):
        assert forecasted_humidity >= 0, "forecasted_humidity must be >= 0"
        return forecasted_humidity


from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_staff = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
