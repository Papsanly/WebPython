import os
import sqlite3

import psycopg
from dotenv import load_dotenv

SQLITE_DB_PATH = "../lab1/sqlite.db"

load_dotenv()

POSTGRES_DB_NAME = "webpython"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = "localhost"

if __name__ == "__main__":
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    pg_conn = psycopg.connect(
        dbname=POSTGRES_DB_NAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
    )

    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = sqlite_cursor.fetchall()

    for table in tables:
        all_info = {}
        table_name = table[0]
        sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = sqlite_cursor.fetchall()
        all_info[table_name] = [i[1] for i in columns_info]

        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        for column_info in columns_info:
            column_name = column_info[1]
            column_type = column_info[2]
            if column_name == "id":
                column_type = "SERIAL"
            if column_type == "DATETIME":
                column_type = "TIMESTAMP"
            create_table_query += f"{column_name} {column_type} "
            if column_name == ("name" or "username" or "email"):
                create_table_query += f"UNIQUE, "
            else:
                create_table_query += ", "

        create_table_query += "PRIMARY KEY (id)"
        if table_name == "forecasts":
            create_table_query += ", FOREIGN KEY (city_id) REFERENCES cities(id)"
        if table_name == "cities":
            create_table_query += ", FOREIGN KEY (country_id) REFERENCES countries(id)"
        create_table_query += ");"
        pg_cursor.execute(create_table_query)
        pg_conn.commit()

        sqlite_cursor.execute(f"SELECT * FROM {table_name};")
        rows = sqlite_cursor.fetchall()
        for row in rows:
            names = ", ".join(all_info[table_name][1:])
            placeholders = ", ".join(["%s" for _ in range(len(row) - 1)])
            pg_cursor.execute(
                f"INSERT INTO {table_name}({names}) VALUES ({placeholders});", row[1:]
            )
        pg_conn.commit()

    sqlite_cursor.close()
    sqlite_conn.close()
    pg_cursor.close()
    pg_conn.close()
