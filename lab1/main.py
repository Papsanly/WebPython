from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends, status, Form
from fastapi.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
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


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return templates.TemplateResponse(
        name="error.html",
        request=request,
        context={"code": exc.status_code, "detail": exc.detail},
    )


@app.get("/", tags=["Forecasts"], response_class=HTMLResponse)
def index(request: Request, user: Annotated[User | None, Depends(get_current_user)]):
    return templates.TemplateResponse(
        name="index.html", request=request, context={"user": user}
    )


@app.get("/create-forecast", tags=["Forecasts"], response_class=HTMLResponse)
def create_forecast(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_superadmin)],
):
    cities = db.scalars(select(City)).all()
    return templates.TemplateResponse(
        name="create_forecast.html",
        request=request,
        context={"user": user, "cities": cities},
    )


@app.get(
    "/edit-forecast/{forecast_id}", tags=["Forecasts"], response_class=HTMLResponse
)
def edit_forecast(
    request: Request,
    forecast_id: int,
    user: Annotated[User, Depends(get_superadmin)],
    db: Annotated[Session, Depends(get_db)],
):
    forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))
    return templates.TemplateResponse(
        name="edit_forecast.html",
        request=request,
        context={"user": user, "forecast": forecast},
    )


@app.post(
    "/forecasts",
    tags=["Forecasts"],
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_forecast(
    request: Request,
    city_id: Annotated[int, Form()],
    forecast_datetime: Annotated[datetime, Form()],
    forecasted_temperature: Annotated[int, Form()],
    forecasted_humidity: Annotated[int, Form()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_superadmin)],
):
    if db.scalar(select(City).where(City.id == city_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    forecast = db.scalar(
        insert(Forecast)
        .values(
            city_id=city_id,
            datetime=forecast_datetime,
            forecasted_temperature=forecasted_temperature,
            forecasted_humidity=forecasted_humidity,
        )
        .returning(Forecast)
    )
    db.commit()
    db.refresh(forecast)
    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast created successfully"},
    )


@app.get("/forecasts", tags=["Forecasts"], response_class=HTMLResponse)
def get_forecast(
    request: Request,
    city_name: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    forecast_datetime_from: datetime | None = None,
    forecast_datetime_to: datetime | None = None,
):
    forecasts = db.scalars(
        select(Forecast)
        .join(City, City.id == Forecast.city_id)
        .where(City.name == city_name.lower())
        .where(Forecast.datetime <= (forecast_datetime_to or datetime.max))
        .where(Forecast.datetime >= (forecast_datetime_from or datetime.min))
        .order_by(Forecast.datetime)
    ).all()
    if len(forecasts) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecasts not found"
        )
    return templates.TemplateResponse(
        name="forecasts.html",
        request=request,
        context={
            "user": user,
            "city_name": city_name,
            "forecast_datetime_from": forecast_datetime_from,
            "forecast_datetime_to": forecast_datetime_to,
            "forecasts": forecasts,
        },
    )


@app.post(
    "/forecasts/{forecast_id}",
    tags=["Forecasts"],
    response_model=ForecastSchema,
    status_code=status.HTTP_201_CREATED,
)
async def update_forecast(
    request: Request,
    forecast_id: int,
    city_id: Annotated[int, Form()],
    forecast_datetime: Annotated[datetime, Form()],
    forecasted_temperature: Annotated[int, Form()],
    forecasted_humidity: Annotated[int, Form()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_superadmin)],
):
    db_forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))

    if db_forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    if db.scalar(select(City).where(City.id == city_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    db.execute(
        update(Forecast)
        .where(Forecast.id == forecast_id)
        .values(
            city_id=city_id,
            datetime=forecast_datetime,
            forecasted_temperature=forecasted_temperature,
            forecasted_humidity=forecasted_humidity,
        )
    )
    db.commit()
    db.refresh(db_forecast)

    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast updated successfully"},
    )


@app.delete(
    "/forecasts/{forecast_id}", tags=["Forecasts"], response_model=ForecastSchema
)
def delete_forecast(
    request: Request,
    forecast_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_superadmin)],
):
    forecast = db.scalar(
        delete(Forecast).where(Forecast.id == forecast_id).returning(Forecast)
    )
    db.commit()
    if forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )
    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast deleted successfully"},
    )


@app.get("/login", tags=["Authorization"], response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(
        name="login.html",
        request=request,
    )


@app.get("/logout", tags=["Authorization"], response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("token")
    return response


@app.post("/token", tags=["Authorization"], response_class=RedirectResponse)
async def get_token(
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
    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="token", value=token.access_token)
    return response


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
    openapi_schema["paths"]["/forecasts"]["post"][
        "summary"
    ] = "Create a new forecast for the weather system"
    openapi_schema["paths"]["/forecasts/{forecast_id}"]["post"][
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
