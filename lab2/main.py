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
from psycopg import Cursor

from authorization import (
    authenticate_user,
    create_access_token,
    create_example_user,
    create_superadmin,
    get_superadmin,
    get_current_user,
)
from models import get_db, get_cursor


async def startup_event():
    db = get_cursor()
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
def index(
    request: Request,
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_current_user),
):
    cities = db.execute("select * from cities").fetchall()
    return templates.TemplateResponse(
        name="index.html", request=request, context={"user": user, "cities": cities}
    )


@app.get("/create-forecast", tags=["Forecasts"], response_class=HTMLResponse)
def create_forecast(
    request: Request,
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_superadmin),
):
    cities = db.execute("select * from cities").fetchall()
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
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_superadmin),
):
    db.execute("select * from forecasts where id = %s", (forecast_id,))
    forecast = db.fetchone()
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
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_superadmin),
):
    db.execute("select * from cities where id = %s", (city_id,))
    city = db.fetchone()
    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    db.execute(
        """
            insert into forecasts (city_id, datetime, forecasted_temperature, forecasted_humidity) 
            VALUES (%s, %s, %s, %s)
        """,
        (city_id, forecast_datetime, forecasted_temperature, forecasted_humidity),
    )
    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast created successfully"},
    )


@app.get("/forecasts", tags=["Forecasts"], response_class=HTMLResponse)
def get_forecast(
    request: Request,
    city_name: str,
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_current_user),
    forecast_datetime_from: datetime | None = None,
    forecast_datetime_to: datetime | None = None,
):
    forecast_datetime_to_str = forecast_datetime_to
    forecast_datetime_from_str = forecast_datetime_from
    if not forecast_datetime_to:
        forecast_datetime_to_str = "infinity"
    if not forecast_datetime_from:
        forecast_datetime_from_str = "-infinity"

    db.execute(
        """
            SELECT forecasts.*
            FROM forecasts
            JOIN cities ON cities.id = forecasts.city_id
            WHERE LOWER(cities.name) = LOWER(%s)
              AND forecasts.datetime <= %s
              AND forecasts.datetime >= %s
            ORDER BY forecasts.datetime;
        """,
        (city_name, forecast_datetime_to_str, forecast_datetime_from_str),
    )
    forecasts = db.fetchall()
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
    forecast_id: int,
    city_id: Annotated[int, Form()],
    forecast_datetime: Annotated[datetime, Form()],
    forecasted_temperature: Annotated[int, Form()],
    forecasted_humidity: Annotated[int, Form()],
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_superadmin),
):
    db.execute("SELECT 1 FROM forecasts WHERE id = %s", (forecast_id,))
    if not db.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    db.execute("SELECT 1 FROM cities WHERE id = %s", (city_id,))
    if not db.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )

    db.execute(
        """
            UPDATE forecasts
            SET city_id = %s,
                datetime = %s,
                forecasted_temperature = %s,
                forecasted_humidity = %s
            WHERE id = %s
        """,
        (
            city_id,
            forecast_datetime,
            forecasted_temperature,
            forecasted_humidity,
            forecast_id,
        ),
    )
    return templates.TemplateResponse(
        name="message.html",
        request=request,
        context={"user": user, "message": "Forecast updated successfully"},
    )


@app.delete("/forecasts/{forecast_id}", tags=["Forecasts"])
def delete_forecast(
    request: Request,
    forecast_id: int,
    db: Annotated[Cursor, Depends(get_db)],
    user=Depends(get_superadmin),
):
    db.execute(
        """
                DELETE FROM forecasts WHERE id = %s RETURNING id
            """,
        (forecast_id,),
    )
    deleted_forecast_id = db.fetchone()

    if not deleted_forecast_id:
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
    db: Annotated[Cursor, Depends(get_db)],
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
