from datetime import datetime

from pydantic import BaseModel


class ForecastSchema(BaseModel):
    city_id: int
    datetime: datetime
    forecasted_temperature: float
    forecasted_humidity: float


class ForecastUpdateSchema(BaseModel):
    city_id: int | None
    datetime: datetime | None
    forecasted_temperature: float | None
    forecasted_humidity: float | None


class MessageSchema(BaseModel):
    message: str


class AccessTokenSchema(BaseModel):
    access_token: str
    token_type: str
