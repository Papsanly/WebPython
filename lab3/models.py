from pymongo import MongoClient

MONGO_DB_HOST = "localhost"
MONGO_DB_PORT = "27017"
MONGO_DB_NAME = "lab3"

def connect():
    client = MongoClient(f'mongodb://{MONGO_DB_HOST}:{MONGO_DB_PORT}/')
    db = client[MONGO_DB_NAME]
    return db

class User:
    def __init__(self, username, email, hashed_password, role='user'):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.role = role


class Country:
    def __init__(self, name, code):
        self.name = name
        self.code = code


class City:
    def __init__(self, name, country_id):
        self.name = name
        self.country_id = country_id


class Forecast:
    def __init__(self, city_id, datetime, forecasted_temperature, forecasted_humidity):
        self.city_id = city_id
        self.datetime = datetime
        self.forecasted_temperature = forecasted_temperature
        self.forecasted_humidity = forecasted_humidity