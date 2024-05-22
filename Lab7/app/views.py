from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest

from . import login_manager
from .models import db, User, Country, City, Forecast
from .forms import LoginForm, RegisterForm, CityForm, CountryForm, ForecastForm, CSRFProtectForm, EditUserForm

main = Blueprint('main', __name__)

@main.route('/')
def index():
    cities = City.query.all()
    return render_template('index.html', cities=cities)

@main.route('/create_forecast', methods=['GET', 'POST'])
@login_required
def create_forecast():
    form = ForecastForm()
    if form.validate_on_submit():
        forecast = Forecast(city_id=form.city_id.data, datetime=form.forecast_datetime.data,
                            forecasted_temperature=form.forecasted_temperature.data,
                            forecasted_humidity=form.forecasted_humidity.data)
        db.session.add(forecast)
        try:
            db.session.commit()
            return redirect(url_for('main.index'))
        except IntegrityError:
            db.session.rollback()
            return "Error: Unable to create forecast"
    else:
        cities = City.query.all()
        return render_template('create_forecast.html', form=form, cities=cities)

@main.route('/add-city', methods=['GET', 'POST'])
@login_required
def add_city():
    form = CityForm()
    if form.validate_on_submit():
        country = Country.query.get(form.country_id.data)
        if country is None:
            raise BadRequest('Invalid country ID')
        city = City(name=form.name.data, country_id=country.id)
        db.session.add(city)
        try:
            db.session.commit()
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            return main.error_view('400', str(e))
    else:
        countries = Country.query.all()
        return render_template('add_city.html', countries=countries, user=current_user, form=form)

@main.route('/add-country', methods=['GET', 'POST'])
@login_required
def add_country():
    form = CountryForm()
    if form.validate_on_submit():
        country = Country(name=form.name.data, code=form.code.data)
        db.session.add(country)
        try:
            db.session.commit()
            return redirect(url_for('main.index'))
        except IntegrityError:
            db.session.rollback()
            return "Error: Unable to add country"
    return render_template('add_country.html', form=form)

@main.route('/edit_forecast/<int:forecast_id>', methods=['GET', 'POST'])
@login_required
def edit_forecast(forecast_id):
    forecast = Forecast.query.get(forecast_id)
    form = ForecastForm(obj=forecast)
    if form.validate_on_submit():
        city_name = forecast.city.name
        form.populate_obj(forecast)
        db.session.commit()
        return redirect(url_for('main.get_forecast', city_name=city_name))
    cities = City.query.all()
    return render_template('edit_forecast.html', form=form, forecast=forecast, cities=cities)

@main.route('/forecasts/city/<city_name>/', methods=['GET'])
@login_required
def get_forecast(city_name):
    city = City.query.filter_by(name=city_name).first()
    if city is None:
        return "Error: City not found"

    datetime_from = request.args.get('forecast_datetime_from')
    datetime_to = request.args.get('forecast_datetime_to')

    if datetime_from and datetime_to:
        forecasts = Forecast.query.filter(Forecast.city_id == city.id,
                                          Forecast.datetime.between(datetime_from, datetime_to)).all()
    elif datetime_from:
        forecasts = Forecast.query.filter(Forecast.city_id == city.id, Forecast.datetime >= datetime_from).all()
    elif datetime_to:
        forecasts = Forecast.query.filter(Forecast.city_id == city.id, Forecast.datetime <= datetime_to).all()
    else:
        forecasts = Forecast.query.filter_by(city_id=city.id).all()
    form = ForecastForm()
    return render_template('forecasts.html', forecasts=forecasts, city_name=city_name,
                           forecast_datetime_from=datetime_from, forecast_datetime_to=datetime_to, form=form)

@main.route('/forecasts/id/<int:forecast_id>/', methods=['GET', 'POST'])
@login_required
def update_forecast(forecast_id):
    forecast = Forecast.query.get_or_404(forecast_id)
    form = ForecastForm(obj=forecast)
    if form.validate_on_submit():
        form.populate_obj(forecast)
        db.session.commit()
        city_name = forecast.city.name
        return redirect(url_for('main.get_forecast', city_name=city_name))
    return render_template('edit_forecast.html', form=form)

@main.route('/forecasts/<int:forecast_id>/delete/', methods=['POST'])
@login_required
def delete_forecast(forecast_id):
    forecast = Forecast.query.get(forecast_id)
    if forecast:
        city_name = forecast.city.name
        db.session.delete(forecast)
        db.session.commit()
    return redirect(url_for('main.get_forecast', city_name=city_name))

@main.route('/accounts/login', methods=['GET', 'POST'])
def login_view():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            return "Invalid credentials"
    return render_template('login.html', form=form)

@main.route('/accounts/logout', methods=['GET'])
@login_required
def logout_view():
    logout_user()
    return redirect(url_for('main.login_view'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            return redirect(url_for('main.login_view'))
        except IntegrityError:
            db.session.rollback()
            return "Error: Unable to register user"
    return render_template('register.html', form=form)

@main.route('/access_denied/')
def access_denied_view():
    return main.error_view('403', 'You do not have sufficient privileges to access this page.')

@main.route('/error/<code>/<detail>/')
def error_view(code, detail):
    return render_template('error.html', code=code, detail=detail)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/users')
@login_required
def users_view():
    users = User.query.all()
    form = CSRFProtectForm()
    return render_template('users.html', users=users, form=form)

@main.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.id == user_id:
        abort(403)
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('main.users_view'))

@main.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.id == user_id:
        abort(403)
    user = User.query.get(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        return redirect(url_for('main.users_view'))
    return render_template('edit_user.html', form=form, user=user)

@main.route('/countries')
@login_required
def countries():
    countries = Country.query.all()
    form = CSRFProtectForm()
    return render_template('countries.html', countries=countries, form=form)

@main.route('/countries/delete/<int:country_id>', methods=['POST'])
@login_required
def delete_country(country_id):
    country = Country.query.get(country_id)
    if country:
        db.session.delete(country)
        db.session.commit()
    return redirect(url_for('main.countries'))

@main.route('/countries/edit/<int:country_id>', methods=['GET', 'POST'])
@login_required
def edit_country(country_id):
    country = Country.query.get(country_id)
    if country is None:
        return redirect(url_for('main.error_view', code=404, detail='Country not found'))
    form = CountryForm(obj=country)
    if form.validate_on_submit():
        form.populate_obj(country)
        db.session.commit()
        return redirect(url_for('main.countries'))
    return render_template('edit_country.html', form=form, country=country)

@main.route('/cities')
@login_required
def cities():
    cities = City.query.all()
    form = CSRFProtectForm()
    return render_template('cities.html', cities=cities, form=form)

@main.route('/cities/delete/<int:city_id>', methods=['POST'])
@login_required
def delete_city(city_id):
    city = City.query.get(city_id)
    if city:
        db.session.delete(city)
        db.session.commit()
    return redirect(url_for('main.cities'))

@main.route('/cities/edit/<int:city_id>', methods=['GET', 'POST'])
@login_required
def edit_city(city_id):
    city = City.query.get(city_id)
    if city is None:
        return redirect(url_for('main.error_view', code=404, detail='City not found'))
    form = CityForm(obj=city)
    if form.validate_on_submit():
        form.populate_obj(city)
        db.session.commit()
        return redirect(url_for('main.cities'))
    countries = Country.query.all()
    return render_template('edit_city.html', form=form, city=city, countries=countries)
