import sqlite3

from dotenv import load_dotenv

from models import User, Country, City, Forecast, connect

SQLITE_DB_PATH = "../lab1/sqlite.db"

load_dotenv()


def transform(data, class_name):
    transformed_data = []
    for entry in data:
        obj = class_name(*(entry[1:]))
        obj_dict = obj.__dict__
        transformed_data.append(obj_dict)
    return transformed_data


if __name__ == "__main__":
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    db = connect()
    users_collection = db["users"]
    countries_collection = db["countries"]
    cities_collection = db["cities"]
    forecasts_collection = db["forecasts"]

    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = sqlite_cursor.fetchall()

    for table in tables:
        table_name = table[0]

        sqlite_cursor.execute(f"SELECT * FROM {table_name};")
        rows = sqlite_cursor.fetchall()
        if table_name == "users":
            users_collection.insert_many(transform(rows, User))
        elif table_name == "countries":
            countries_collection.insert_many(transform(rows, Country))
        elif table_name == "cities":
            newRows = []
            sqlite_cursor.execute(f"SELECT * FROM countries;")
            countryRows = sqlite_cursor.fetchall()
            for i in rows:
                sqlite_cursor.execute(f"SELECT name FROM countries WHERE id={i[2]};")
                countryName = sqlite_cursor.fetchone()
                print(countryName)
                countryId = db["countries"].find_one({"name": countryName[0]})
                newRows.append((i[0], i[1], countryId["_id"]))
            cities_collection.insert_many(transform(newRows, City))
        elif table_name == "forecasts":
            newRows = []
            sqlite_cursor.execute(f"SELECT * FROM cities;")
            cityRows = sqlite_cursor.fetchall()
            for i in rows:
                print(i)
                sqlite_cursor.execute(f"SELECT name FROM cities WHERE id={i[1]};")
                cityName = sqlite_cursor.fetchone()
                cityId = db["cities"].find_one({"name": cityName[0]})
                newRows.append((i[0], cityId["_id"], i[2], i[3], i[4]))
            forecasts_collection.insert_many(transform(newRows, Forecast))
