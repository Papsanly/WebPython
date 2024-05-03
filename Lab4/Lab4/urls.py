from django.urls import path

from weather_app import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create-forecast/", views.create_forecast, name="create_forecast"),
    path("add-city/", views.add_city, name="add_city"),
    path("add-country/", views.add_country, name="add_country"),
    path("edit-forecast/<int:forecast_id>/", views.edit_forecast, name="edit_forecast"),
    path("forecasts/", views.create_forecast, name="create_forecast"),
    path("countries/", views.add_country, name="add_country"),
    path("cities/", views.add_city, name="add_city"),
    path("forecasts/<str:city_name>/", views.get_forecast, name="get_forecast"),
    path("forecasts/<int:forecast_id>/", views.update_forecast, name="update_forecast"),
    path(
        "forecasts/<int:forecast_id>/delete/",
        views.delete_forecast,
        name="delete_forecast",
    ),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path('access_denied/', views.access_denied_view, name='access_denied'),
    path('error/<str:code>/<str:detail>/', views.error_view, name='error_view'),
]
