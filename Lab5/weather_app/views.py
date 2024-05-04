from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from datetime import datetime
from .models import Country, City, Forecast
from django.core.exceptions import ValidationError
import os


def create_user():
    user = User.objects.create_user("user1", "myemail@example.com", "password1")
    user.first_name = "John"
    user.last_name = "Doe"
    user.save()


def create_superadmin():
    load_dotenv()
    EMAIL = os.getenv("SUPERADMIN_EMAIL")
    PASSWORD = os.getenv("SUPERADMIN_PASSWORD")
    user = User.objects.create_user("superadmin", EMAIL, PASSWORD)
    user.is_superuser = True
    user.is_staff = True
    user.save()


try:
    create_superadmin()
    create_user()
except Exception:
    pass


def index(request):
    if request.method == "GET":
        cities = City.objects.all()
        return render(request, "index.html", {"cities": cities, "user": request.user})


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def access_denied_view(request):
    return error_view(request, '403', 'You do not have sufficient privileges to access this page.')


def error_view(request, code, detail):
    context = {
        'code': code,
        'detail': detail
    }
    return render(request, 'error.html', context)


@csrf_exempt
@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def add_city(request):
    if request.method == "POST":
        country_id = request.POST["country_id"]
        city_name = request.POST["city_name"]
        country = Country.objects.get(id=country_id)
        try:
            city = City(name=city_name, country_id=country)
            city.full_clean()
            city.save()
            return HttpResponseRedirect(reverse("index"))
        except ValidationError as e:
            return error_view(request, '400', e.message_dict['name'][0])
    else:  # Handle 'GET' request
        countries = Country.objects.all()
        return render(
            request,
            "add_city.html",
            {"countries": countries, "user": request.user},
        )


@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def edit_forecast(request, forecast_id):
    if request.method == "GET":
        forecast = Forecast.objects.get(id=forecast_id)
        return render(
            request,
            "edit_forecast.html",
            {"forecast": forecast, "cities": City.objects.all(), "user": request.user},
        )


@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def create_forecast(request):
    if request.method == "GET":
        return render(request, "create_forecast.html", {"cities": City.objects.all(), "user": request.user})
    elif request.method == "POST":
        city_id = request.POST["city_id"]
        forecast_datetime = request.POST["forecast_datetime"]
        forecasted_temperature = request.POST["forecasted_temperature"]
        forecasted_humidity = request.POST["forecasted_humidity"]
        city = City.objects.get(id=city_id)
        try:
            forecast = Forecast(
                city_id=city,
                datetime=forecast_datetime,
                forecasted_temperature=forecasted_temperature,
                forecasted_humidity=forecasted_humidity,
            )
            forecast.full_clean()
            forecast.save()
            return HttpResponseRedirect(reverse("index"))
        except ValidationError as e:
            return error_view(request, '400', str(e))

@csrf_exempt
@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def add_country(request):
    if request.method == "POST":
        country_name = request.POST["country_name"]
        country_code = request.POST["country_code"]
        try:
            country = Country(name=country_name, code=country_code)
            country.full_clean()
            country.save()
            return HttpResponseRedirect(reverse("index"))
        except ValidationError as e:
            return redirect('error_view', code="400", detail=str(e))
    else:
        return render(request, "add_country.html", {"user": request.user})

@login_required
def get_forecast(request, city_name):
    if request.method == "GET":
        city = City.objects.filter(name=city_name).first()
        if not city:
            return redirect('error_view', code="404", detail="City not found")

        datetime_from = request.GET.get('forecast_datetime_from')
        datetime_to = request.GET.get('forecast_datetime_to')

        try:
            if datetime_from:
                datetime_from = datetime.strptime(datetime_from, "%Y-%m-%d").date()
            if datetime_to:
                datetime_to = datetime.strptime(datetime_to, "%Y-%m-%d").date()

            if datetime_from and datetime_to and datetime_from >= datetime_to:
                return redirect('error_view', code="400", detail="Datetime From must be before Datetime To.")
        except ValueError as e:
            return redirect('error_view', code="400", detail="Invalid datetime format")

        if datetime_from and datetime_to:
            forecasts = Forecast.objects.filter(city_id=city.id, datetime__range=[datetime_from, datetime_to])
        elif datetime_from:
            forecasts = Forecast.objects.filter(city_id=city.id, datetime__gte=datetime_from)
        elif datetime_to:
            forecasts = Forecast.objects.filter(city_id=city.id, datetime__lte=datetime_to)
        else:
            forecasts = Forecast.objects.filter(city_id=city.id)
        return render(request, "forecasts.html", {"forecasts": forecasts, "cities": City.objects.all(), "user": request.user})

@csrf_exempt
@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def update_forecast(request, forecast_id):
    if request.method == "POST":
        city_id = request.POST["city_id"]
        forecast_datetime = request.POST["forecast_datetime"]
        forecasted_temperature = request.POST["forecasted_temperature"]
        forecasted_humidity = request.POST["forecasted_humidity"]
        city = City.objects.get(id=city_id)
        forecast = Forecast.objects.get(id=forecast_id)
        forecast.city_id = city
        forecast.datetime = forecast_datetime
        forecast.forecasted_temperature = forecasted_temperature
        forecast.forecasted_humidity = forecasted_humidity
        try:
            forecast.full_clean()
            forecast.save()
            return HttpResponseRedirect(reverse("index"))
        except ValidationError as e:
            return error_view(request, '400', str(e))

@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def delete_forecast(request, forecast_id):
    if request.method == "POST":
        forecast = Forecast.objects.get(id=forecast_id)
        forecast.delete()
        return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")

        if not username or not email or not password or not password_confirm:
            return HttpResponse("All fields are required.", status=400)
        if password != password_confirm:
            return HttpResponse("Passwords do not match.", status=400)
        
        try:
            user = User.objects.create_user(username, email, password)
            login(request, user)
            return redirect("index")
        except Exception as e:
            return error_view(request, '400', str(e))
    else:
        return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "login.html",
                {"message": "Invalid credentials.", "user": request.user},
            )
    return render(
        request,
        "login.html",
        {"user": request.user},
    )


def logout_view(request):
    logout(request)
    return redirect("login")