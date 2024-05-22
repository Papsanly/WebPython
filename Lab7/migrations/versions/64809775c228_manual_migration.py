"""Manual migration

Revision ID: 64809775c228
Revises: 
Create Date: 2024-05-20 20:49:05.838620

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '64809775c228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('country',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('code', sa.String(length=2), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('city',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('country_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['country_id'], ['country.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('forecast',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('city_id', sa.Integer(), nullable=False),
                    sa.Column('datetime', sa.Date(), nullable=False),
                    sa.Column('forecasted_temperature', sa.Integer(), nullable=False),
                    sa.Column('forecasted_humidity', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['city_id'], ['city.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('user',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('username', sa.String(length=64), nullable=True),
                    sa.Column('email', sa.String(length=120), nullable=True),
                    sa.Column('password_hash', sa.String(length=128), nullable=True),
                    sa.Column('is_staff', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('username')
                    )

    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    old_user_data = bind.execute("SELECT * FROM users")
    for user in old_user_data:
        session.execute(
            sa.text(
                "INSERT INTO user (id, username, email, password_hash, is_staff) "
                "VALUES (:id, :username, :email, :hashed_password, :is_staff)"
            ),
            {"id": user.id, "username": user.username, "email": user.email, "hashed_password": user.hashed_password,
             "is_staff": False}
        )

    old_country_data = bind.execute("SELECT * FROM countries")
    for country in old_country_data:
        session.execute(
            sa.text(
                "INSERT INTO country (id, name, code) "
                "VALUES (:id, :name, :code)"
            ),
            {"id": country.id, "name": country.name, "code": country.code}
        )

    old_city_data = bind.execute("SELECT * FROM cities")
    for city in old_city_data:
        session.execute(
            sa.text(
                "INSERT INTO city (id, name, country_id) "
                "VALUES (:id, :name, :country_id)"
            ),
            {"id": city.id, "name": city.name, "country_id": city.country_id}
        )

    old_forecast_data = bind.execute("SELECT * FROM forecasts")
    for forecast in old_forecast_data:
        session.execute(
            sa.text(
                "INSERT INTO forecast (id, city_id, datetime, forecasted_temperature, forecasted_humidity) "
                "VALUES (:id, :city_id, :datetime, :forecasted_temperature, :forecasted_humidity)"
            ),
            {"id": forecast.id, "city_id": forecast.city_id, "datetime": forecast.datetime,
             "forecasted_temperature": forecast.forecasted_temperature,
             "forecasted_humidity": forecast.forecasted_humidity}
        )

    session.commit()


def downgrade():
    op.drop_table('forecast')
    op.drop_table('city')
    op.drop_table('country')
    op.drop_table('user')
