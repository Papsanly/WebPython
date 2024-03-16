from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, insert, update, delete
from sqlalchemy.orm import Session

from authorization import (
    get_current_user,
    authenticate_user,
    create_access_token,
    create_user,
    create_superadmin,
)
from models import (
    engine,
    ForecastResponse,
    get_db,
    User,
    Forecast,
    ForecastMessage,
    Base,
)


async def startup_event():
    Base.metadata.create_all(bind=engine)


app = FastAPI(
    openapi_tags=[
        {"name": "Forecasts", "description": "Endpoints related to weather forecasts"},
        {
            "name": "Authentication",
            "description": "Endpoints related to user authentication",
        },
    ]
)

app.add_event_handler("startup", startup_event)

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(engine)
    db = Session()
    try:
        create_superadmin(db)
        create_user(db)
    finally:
        db.close()


@app.get("/", tags=["Forecasts"])
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/forecasts/", tags=["Forecasts"], response_model=ForecastResponse)
async def create_forecast(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    data = await request.json()
    city_id = data.get("city_id")
    datetime_str = data.get("datetime")
    forecasted_temperature = data.get("forecasted_temperature")
    forecasted_humidity = data.get("forecasted_humidity")

    if (
        not city_id
        or not datetime_str
        or forecasted_temperature is None
        or forecasted_humidity is None
    ):
        raise HTTPException(
            status_code=400, detail="Missing one or more required fields"
        )

    forecast_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    stmt = (
        insert(Forecast)
        .values(
            city_id=city_id,
            datetime=forecast_datetime,
            forecasted_temperature=forecasted_temperature,
            forecasted_humidity=forecasted_humidity,
        )
        .returning(Forecast)
    )
    forecast = db.scalar(stmt)

    return {
        "city_id": forecast.city_id,
        "datetime": forecast.datetime,
        "forecasted_temperature": forecast.forecasted_temperature,
        "forecasted_humidity": forecast.forecasted_humidity,
    }


@app.get(
    "/forecasts/{forecast_id}", tags=["Forecasts"], response_model=ForecastResponse
)
def get_forecast(forecast_id: int, db: Session = Depends(get_db)):
    forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))
    if forecast is None:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return {
        "city_id": forecast.city_id,
        "datetime": forecast.datetime,
        "forecasted_temperature": forecast.forecasted_temperature,
        "forecasted_humidity": forecast.forecasted_humidity,
    }


@app.put("/forecasts/{forecast_id}", tags=["Forecasts"], response_model=ForecastMessage)
async def update_forecast(
    forecast_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    data = await request.json()
    forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))

    if forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    update_data = {}
    if "city_id" in data:
        update_data[Forecast.city_id] = data["city_id"]
    if "datetime" in data:
        datetime_str = data["datetime"]
        update_data[Forecast.datetime] = datetime.strptime(
            datetime_str, "%Y-%m-%d %H:%M:%S"
        )
    if "forecasted_temperature" in data:
        update_data[Forecast.forecasted_temperature] = data["forecasted_temperature"]
    if "forecasted_humidity" in data:
        update_data[Forecast.forecasted_humidity] = data["forecasted_humidity"]

    if update_data:
        db.execute(
            update(Forecast).where(Forecast.id == forecast.id).values(**update_data)
        )

    return {"message": "Forecast updated successfully"}


@app.delete(
    "/forecasts/{forecast_id}", tags=["Forecasts"], response_model=ForecastMessage
)
def delete_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    forecast = db.scalar(
        delete(Forecast).where(Forecast.id == forecast_id).returning(Forecast)
    )
    if forecast is None:
        raise HTTPException(status_code=404, detail="Forecast not found")

    return {"message": "Forecast deleted successfully"}


@app.post("/token", tags=["Authorization"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Weather API",
        version="1.0",
        summary="This is a custom API schema for our Weather API.",
        description="This API provides weather forecasts and allows users to authenticate to access protected "
        "endpoints."
        "This wonderful app is made by Andriy, Dmytro and Vladyslav.",
        routes=app.routes,
    )
    openapi_schema["paths"]["/forecasts/"]["post"][
        "summary"
    ] = "Create a new forecast for the weather system"
    openapi_schema["paths"]["/forecasts/{forecast_id}"]["get"][
        "summary"
    ] = "Get Weather Forecast by ID"
    openapi_schema["paths"]["/forecasts/{forecast_id}"]["put"][
        "summary"
    ] = "Update Weather Forecast by ID"
    openapi_schema["paths"]["/forecasts/{forecast_id}"]["delete"][
        "summary"
    ] = "Delete Weather Forecast by ID"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    load_dotenv()

    uvicorn.run(app, host="127.0.0.1", port=8000)
