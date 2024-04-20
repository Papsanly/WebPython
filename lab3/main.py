from datetime import datetime
from typing import Annotated

import pymongo
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends, status, Form
from fastapi.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo.database import Database

from authorization import (
    authenticate_user,
    create_access_token,
    create_example_user,
    create_superadmin,
    get_superadmin,
    get_current_user,
    get_password_hash
)
from models import connect, get_db


async def startup_event():
    db = connect()
    try:
        create_superadmin(db)
        create_example_user(db)
    finally:
        pass


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
def index(
    request: Request,
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_current_user),
):
    cities = list(db["cities"].find({}))
    return templates.TemplateResponse(
        name="index.html", request=request, context={"user": user, "cities": cities}
    )


@app.get("/create-forecast", tags=["Forecasts"], response_class=HTMLResponse)
def create_forecast(
    request: Request,
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    cities = list(db["cities"].find({}))
    return templates.TemplateResponse(
        name="create_forecast.html",
        request=request,
        context={"user": user, "cities": cities},
    )


@app.get("/add-city", response_class=HTMLResponse)
def add_city(
    request: Request,
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    countries = list(db["countries"].find({}))
    return templates.TemplateResponse(
        name="add_city.html",
        request=request,
        context={"user": user, "countries": countries},
    )


@app.get("/add-country", response_class=HTMLResponse)
def add_country(
    request: Request,
    user=Depends(get_superadmin),
):
    return templates.TemplateResponse(
        name="add_country.html",
        request=request,
        context={"user": user},
    )


@app.get(
    "/edit-forecast/{forecast_id}", tags=["Forecasts"], response_class=HTMLResponse
)
def edit_forecast(
    request: Request,
    forecast_id: str,
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    forecast = db["forecasts"].find_one(
        {"_id": ObjectId(forecast_id)}
    )  # Знайти прогноз за його ідентифікатором
    cities = list(db["cities"].find({}))  # Отримати всі міста
    return templates.TemplateResponse(
        name="edit_forecast.html",
        request=request,
        context={"user": user, "forecast": forecast, "cities": cities},
    )


@app.post(
    "/forecasts",
    tags=["Forecasts"],
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_forecast(
    request: Request,
    city_id: Annotated[str, Form()],
    forecast_datetime: Annotated[datetime, Form()],
    forecasted_temperature: Annotated[float, Form()],
    forecasted_humidity: Annotated[float, Form()],
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    city = db["cities"].find_one({"_id": ObjectId(city_id)})
    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    forecast_data = {
        "city_id": ObjectId(city_id),
        "datetime": forecast_datetime,
        "forecasted_temperature": forecasted_temperature,
        "forecasted_humidity": forecasted_humidity,
    }
    db["forecasts"].insert_one(forecast_data)

    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast created successfully"},
    )


@app.post(
    "/countries",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_country(
    request: Request,
    country_name: Annotated[str, Form()],
    country_code: Annotated[str, Form()],
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    country_data = {"name": country_name.lower(), "code": country_code.lower()}
    db["forecasts"].insert_one(country_data)

    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Country added successfully"},
    )


@app.post(
    "/cities",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_city(
    request: Request,
    country_id: Annotated[str, Form()],
    city_name: Annotated[str, Form()],
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    country = db["countries"].find_one({"_id": ObjectId(country_id)})
    if country is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Country not found"
        )

    city_data = {
        "name": city_name.lower(),
        "country_id": ObjectId(country_id),
    }
    db["cities"].insert_one(city_data)

    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "City added successfully"},
    )


@app.get("/forecasts", tags=["Forecasts"], response_class=HTMLResponse)
def get_forecast(
    request: Request,
    city_name: str,
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_current_user),
    forecast_datetime_from: datetime | None = None,
    forecast_datetime_to: datetime | None = None,
):
    city = db["cities"].find_one(
        {"name": {"$regex": f"^{city_name}$", "$options": "i"}}
    )
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )

    # Отримання прогнозів за містом та датами
    forecasts = (
        db["forecasts"]
        .find(
            {
                "city_id": ObjectId(city["_id"]),
                "datetime": {
                    "$gte": (
                        forecast_datetime_from
                        if forecast_datetime_from is not None
                        else datetime.min
                    ),
                    "$lte": (
                        forecast_datetime_to
                        if forecast_datetime_to is not None
                        else datetime.max
                    ),
                },
            }
        )
        .sort("datetime", pymongo.ASCENDING)
    )

    forecasts = list(forecasts)

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
    status_code=status.HTTP_201_CREATED,
)
async def update_forecast(
    request: Request,
    forecast_id: str,
    city_id: Annotated[str, Form()],
    forecast_datetime: Annotated[datetime, Form()],
    forecasted_temperature: Annotated[float, Form()],
    forecasted_humidity: Annotated[float, Form()],
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    if not db["forecasts"].find_one({"_id": ObjectId(forecast_id)}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    # Перевірка наявності міста за його ID
    if not db["cities"].find_one({"_id": ObjectId(city_id)}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )

    # Оновлення прогнозу
    update_result = db["forecasts"].update_one(
        {"_id": ObjectId(forecast_id)},
        {
            "$set": {
                "city_id": ObjectId(city_id),
                "datetime": forecast_datetime,
                "forecasted_temperature": forecasted_temperature,
                "forecasted_humidity": forecasted_humidity,
            }
        },
    )

    # Перевірка, чи відбулося оновлення
    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update forecast"
        )

    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast updated successfully"},
    )


@app.delete("/forecasts/{forecast_id}", tags=["Forecasts"])
def delete_forecast(
    request: Request,
    forecast_id: str,
    db: Annotated[Database, Depends(get_db)],
    user=Depends(get_superadmin),
):
    deleted_forecast = db["forecasts"].find_one_and_delete(
        {"_id": ObjectId(forecast_id)}
    )

    # Перевірка, чи був видалений документ
    if not deleted_forecast:
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
    db: Annotated[Database, Depends(get_db)],
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user["username"]})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="token", value=token.access_token)
    return response



@app.post("/register", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
    db: Annotated[Database, Depends(get_db)]
):
    existing_user = db["users"].find_one({"username": username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Such user already exists."
        )
    
    existing_email =  db["users"].find_one({"email": email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with such e-mail already exists."
        )
    
    if password != password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )
    hashed_password = get_password_hash(password)
    new_user = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": "user",
    }
    db["users"].insert_one(new_user)
    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={
            "user": None,
            "message": "User registered successfully"},
    )

@app.get("/register", response_class=HTMLResponse, name="register")
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "user": None})

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
