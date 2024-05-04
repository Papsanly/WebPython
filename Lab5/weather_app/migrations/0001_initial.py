# Generated by Django 5.0.4 on 2024-05-04 08:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('country_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather_app.country')),
            ],
        ),
        migrations.CreateModel(
            name='Forecast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateField()),
                ('forecasted_temperature', models.IntegerField()),
                ('forecasted_humidity', models.PositiveIntegerField()),
                ('city_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather_app.city')),
            ],
        ),
    ]
