import psycopg
from psycopg.rows import namedtuple_row

from migration import (
    POSTGRES_DB_NAME,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
)


def get_cursor():
    conn = psycopg.connect(
        dbname=POSTGRES_DB_NAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        autocommit=True,
    )

    return conn.cursor(row_factory=namedtuple_row)


def get_db():
    cursor = get_cursor()
    try:
        yield cursor
    finally:
        cursor.close()
