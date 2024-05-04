from django.db import models
from django.core.validators import RegexValidator

class Country(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z]*$',
                message='Name must be Alphabetic',
                code='invalid_name'
            )
        ]
    )
    code = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z]*$',
                message='Code must be Alphabetic',
                code='invalid_code'
            )
        ]
    )

class City(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z]*$',
                message='Name must be Alphabetic',
                code='invalid_name'
            )
        ]
    )
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE)

class Forecast(models.Model):
    city_id = models.ForeignKey(City, on_delete=models.CASCADE)
    datetime = models.DateField()
    forecasted_temperature = models.IntegerField()
    forecasted_humidity = models.PositiveIntegerField()