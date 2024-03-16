from datetime import datetime

from pydantic import BaseModel


class ForecastSchema(BaseModel):
    city_id: int
    datetime: datetime
    forecasted_temperature: float
    forecasted_humidity: float


class AccessTokenSchema(BaseModel):
    access_token: str
    token_type: str
