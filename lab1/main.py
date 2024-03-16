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
    create_example_user,
    create_superadmin,
)
from models import (
    SessionLocal,
    engine,
    get_db,
    User,
    Forecast,
    Base,
)
from schemas import (
    ForecastSchema,
    MessageSchema,
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

templates = Jinja2Templates(directory="templates")


@app.get("/", tags=["Forecasts"])
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post(
    "/forecasts/",
    tags=["Forecasts"],
    response_model=ForecastSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_forecast(
    forecast: ForecastSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    return db.scalar(insert(Forecast).values(**forecast).returning(Forecast))


@app.get("/forecasts/{forecast_id}", tags=["Forecasts"], response_model=ForecastSchema)
def get_forecast(forecast_id: int, db: Session = Depends(get_db)):
    forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))
    if forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )
    return forecast


@app.put(
    "/forecasts/{forecast_id}",
    tags=["Forecasts"],
    response_model=MessageSchema,
    status_code=status.HTTP_201_CREATED,
)
async def update_forecast(
    forecast_id: int,
    forecast: ForecastUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )

    db_forecast = db.scalar(select(Forecast).where(Forecast.id == forecast_id))

    if db_forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    db.execute(update(Forecast).where(Forecast.id == forecast_id).values(**forecast))

    return {"message": "Forecast updated successfully"}


@app.delete(
    "/forecasts/{forecast_id}", tags=["Forecasts"], response_model=MessageSchema
)
def delete_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )

    forecast = db.scalar(
        delete(Forecast).where(Forecast.id == forecast_id).returning(Forecast)
    )
    if forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    return {"message": "Forecast deleted successfully"}


@app.post("/token", tags=["Authorization"], response_model=AccessTokenSchema)
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

    uvicorn.run(app, host="127.0.0.1", port=8000)
