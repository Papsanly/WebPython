from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class CityForm(FlaskForm):
    country_id = IntegerField('Country ID', validators=[DataRequired()])
    city_name = StringField('City Name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CountryForm(FlaskForm):
    country_name = StringField('Country Name', validators=[DataRequired()])
    country_code = StringField('Country Code', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ForecastForm(FlaskForm):
    city_id = IntegerField('City ID', validators=[DataRequired()])
    forecast_datetime = DateField('Forecast Datetime', validators=[DataRequired()])
    forecasted_temperature = FloatField('Forecasted Temperature', validators=[DataRequired()])
    forecasted_humidity = FloatField('Forecasted Humidity', validators=[DataRequired()])
    submit = SubmitField('Submit')
