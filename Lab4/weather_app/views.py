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
import os

COUNTRIES = [
    {"id": 1, "name": "Ukraine", "code": "UA"},
    {"id": 2, "name": "Poland", "code": "PL"},
]

CITIES = [
    {"id": 1, "name": "Kyiv", "country_id": 1},
    {"id": 2, "name": "Lviv", "country_id": 1},
    {"id": 3, "name": "Krakow", "country_id": 2},
]

FORECASTS = [
    {
        "id": 1,
        "city_id": 1,
        "datetime": "2021-10-10",
        "forecasted_temperature": "20",
        "forecasted_humidity": "50",
    },
    {
        "id": 2,
        "city_id": 1,
        "datetime": "2021-10-11",
        "forecasted_temperature": "21",
        "forecasted_humidity": "51",
    },
    {
        "id": 3,
        "city_id": 2,
        "datetime": "2021-10-10",
        "forecasted_temperature": "22",
        "forecasted_humidity": "52",
    },
    {
        "id": 4,
        "city_id": 2,
        "datetime": "2021-10-11",
        "forecasted_temperature": "23",
        "forecasted_humidity": "53",
    },
    {
        "id": 5,
        "city_id": 3,
        "datetime": "2021-10-10",
        "forecasted_temperature": "24",
        "forecasted_humidity": "54",
    },
    {
        "id": 6,
        "city_id": 3,
        "datetime": "2021-10-11",
        "forecasted_temperature": "25",
        "forecasted_humidity": "55",
    },
]


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
        return render(request, "index.html", {"cities": CITIES, "user": request.user})
    
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
        country = next(
            (country for country in COUNTRIES if country["id"] == int(country_id)), None
        )
        city_id = len(CITIES) + 1
        city = {"id": city_id, "name": city_name, "country_id": country["id"]}
        CITIES.append(city)
        return HttpResponseRedirect(reverse("index"))
    else:  # Handle 'GET' request
        return render(
            request,
            "add_city.html",
            {"countries": COUNTRIES, "user": request.user},
        )


@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def edit_forecast(request, forecast_id):
    if request.method == "GET":
        forecast = next(
            (forecast for forecast in FORECASTS if forecast["id"] == int(forecast_id)),
            None,
        )
        return render(
            request,
            "edit_forecast.html",
            {"forecast": forecast, "cities": CITIES, "user": request.user},
        )


@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def create_forecast(request):
    if request.method == "GET":
        return render(request, "create_forecast.html", {"cities": CITIES})
    elif request.method == "POST":
        city_id = request.POST["city_id"]
        forecast_datetime = request.POST["forecast_datetime"]
        forecasted_temperature = request.POST["forecasted_temperature"]
        forecasted_humidity = request.POST["forecasted_humidity"]
        city = next((city for city in CITIES if city["id"] == int(city_id)), None)
        city_id = len(FORECASTS) + 1
        forecast = {
            "id": city_id,
            "city_id": city["id"],
            "datetime": forecast_datetime,
            "forecasted_temperature": forecasted_temperature,
            "forecasted_humidity": forecasted_humidity,
        }
        FORECASTS.append(forecast)
        return HttpResponseRedirect(reverse("index"))


@csrf_exempt
@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def add_country(request):
    if request.method == "POST":
        country_name = request.POST["country_name"]
        country_code = request.POST["country_code"]
        city_id = len(COUNTRIES) + 1
        country = {"id": city_id, "name": country_name, "code": country_code}
        COUNTRIES.append(country)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "add_country.html", {"user": request.user})


@login_required
def get_forecast(request, city_name):
    if request.method == "GET":
        city = next((city for city in CITIES if city["name"] == city_name), None)
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

        forecasts = [
            forecast for forecast in FORECASTS if forecast["city_id"] == city["id"] and
            (not datetime_from or datetime.strptime(forecast["datetime"], "%Y-%m-%d").date() >= datetime_from) and
            (not datetime_to or datetime.strptime(forecast["datetime"], "%Y-%m-%d").date() <= datetime_to)
        ]
        return render(request, "forecasts.html", {"forecasts": forecasts, "cities": CITIES, "user": request.user})


@csrf_exempt
@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def update_forecast(request, forecast_id):
    if request.method == "POST":
        city_id = request.POST["city_id"]
        forecast_datetime = request.POST["forecast_datetime"]
        forecasted_temperature = request.POST["forecasted_temperature"]
        forecasted_humidity = request.POST["forecasted_humidity"]
        city = next((city for city in CITIES if city["id"] == int(city_id)), None)
        forecast = next(
            (forecast for forecast in FORECASTS if forecast["id"] == int(forecast_id)),
            None,
        )
        forecast["city"] = city
        forecast["datetime"] = forecast_datetime
        forecast["forecasted_temperature"] = forecasted_temperature
        forecast["forecasted_humidity"] = forecasted_humidity
        return HttpResponseRedirect(reverse("index"))


@login_required
@user_passes_test(is_staff_user, login_url='/access_denied/')
def delete_forecast(request, forecast_id):
    if request.method == "POST":
        forecast = next(
            (forecast for forecast in FORECASTS if forecast["id"] == int(forecast_id)),
            None,
        )
        FORECASTS.remove(forecast)
        return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("index")
        else:
            return render(request, "register.html", {"form": form})
    else:
        form = UserCreationForm()
        return render(request, "register.html", {"form": form, "user": request.user})


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
