from django.urls import path

from weather_app import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create-forecast/", views.create_forecast, name="create_forecast"),
    path("add-city/", views.add_city, name="add_city"),
    path("add-country/", views.add_country, name="add_country"),
    path("edit-forecast/<int:forecast_id>/", views.edit_forecast, name="edit_forecast"),
    path("forecasts/", views.create_forecast, name="create_forecast"),
    path("countries/add_country", views.add_country, name="add_country"),
    path("cities/add_city", views.add_city, name="add_city"),
    path("forecasts/city/<str:city_name>/", views.get_forecast, name="get_forecast"),
    path(
        "forecasts/id/<int:forecast_id>/", views.update_forecast, name="update_forecast"
    ),
    path(
        "forecasts/<int:forecast_id>/delete/",
        views.delete_forecast,
        name="delete_forecast",
    ),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("access_denied/", views.access_denied_view, name="access_denied"),
    path("error/<str:code>/<str:detail>/", views.error_view, name="error_view"),
    path("users/", views.users_view, name="users"),
    path("users/delete_user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("users/edit_user/<int:user_id>/", views.edit_user, name="edit_user"),
    path("countries/", views.countries, name="countries"),
    path(
        "countries/delete_country/<int:country_id>/",
        views.delete_country,
        name="delete_country",
    ),
    path(
        "countries/edit_country/<int:country_id>/",
        views.edit_country,
        name="edit_country",
    ),
]
