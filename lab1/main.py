from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, insert, update, delete
from sqlalchemy.orm import Session

from authorization import (
    authenticate_user,
    create_access_token,
    create_example_user,
    create_superadmin,
    get_superadmin,
    get_current_user,
)
from models import (
    SessionLocal,
    engine,
    get_db,
    User,
    Forecast,
    Base,
    City,
)
from schemas import (
    ForecastSchema,
    AccessTokenSchema,
    ForecastUpdateSchema,
)


async def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_superadmin(db)
        create_example_user(db)
    finally:
        db.close()


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
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", tags=["Forecasts"], response_class=HTMLResponse)
def index(request: Request, user: Annotated[User | None, Depends(get_current_user)]):
    return templates.TemplateResponse(
        name="index.html", request=request, context={"user": user}
    )


@app.post(
    "/forecasts/",
    tags=["Forecasts"],
    response_model=ForecastSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_forecast(
    forecast: ForecastSchema,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_superadmin)],
):
    if db.scalar(select(City).where(City.id == forecast.city_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    forecast = db.scalar(insert(Forecast).values(**forecast.dict()).returning(Forecast))
    db.commit()
    db.refresh(forecast)
    return forecast


@app.get("/forecasts", tags=["Forecasts"], response_class=HTMLResponse)
def get_forecast(
    request: Request,
    city_name: str,
    forecast_datetime_from: datetime,
    forecast_datetime_to: datetime,
    db: Annotated[Session, Depends(get_db)],
):
    forecasts = db.scalars(
        select(Forecast)
        .join(City, City.id == Forecast.city_id)
        .where(City.name == city_name)
        .where(Forecast.datetime <= forecast_datetime_to)
        .where(Forecast.datetime >= forecast_datetime_from)
    ).all()
    if len(forecasts) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecasts not found"
        )
    return templates.TemplateResponse(
        name="search_forecast.html",
        request=request,
        context={
            "city_name": city_name,
            "forecast_datetime_from": forecast_datetime_from,
            "forecast_datetime_to": forecast_datetime_to,
            "forecasts": forecasts,
        },
    )


@app.put(
    "/forecasts/{forecast_id}",
    tags=["Forecasts"],
    response_model=ForecastSchema,
    status_code=status.HTTP_201_CREATED,
)
async def update_forecast(
    forecast_id: int,
    forecast: ForecastUpdateSchema,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_superadmin)],
):
    db_forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))

    if db_forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    if db.scalar(select(City).where(City.id == forecast.city_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    db.execute(
        update(Forecast).where(Forecast.id == forecast_id).values(**forecast.dict())
    )
    db.commit()
    db.refresh(db_forecast)

    return db_forecast


@app.delete(
    "/forecasts/{forecast_id}", tags=["Forecasts"], response_model=ForecastSchema
)
def delete_forecast(
    forecast_id: int,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_superadmin)],
):
    forecast = db.scalar(
        delete(Forecast).where(Forecast.id == forecast_id).returning(Forecast)
    )
    if forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )
    return forecast


@app.post("/token", tags=["Authorization"], response_model=AccessTokenSchema)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_access_token(data={"sub": user.username})


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
    uvicorn.run(app)
