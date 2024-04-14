import os
from datetime import datetime, timedelta
from typing import Annotated
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy import select, insert
from sqlalchemy.orm import Session
from pymongo.database import Database
import pymongo

from models import User, Forecast, City, Country

@dataclass
class AccessToken:
    access_token: str
    token_type: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

api_key_scheme = APIKeyCookie(name="token", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=ALGORITHM)
    return AccessToken(access_token=encoded_jwt, token_type="bearer")

def authenticate_user(db: Database, username: str, password: str) -> User | None:
    user = db["users"].find_one({"username": username})
    if user and verify_password(password, user['hashed_password']):
        return user
    return None

def create_superadmin(db: Database):
    email = os.getenv("SUPERADMIN_EMAIL")
    password = os.getenv("SUPERADMIN_PASSWORD")
    superadmin = db["users"].find_one({"email": email})
    if not superadmin:
        user_data = {
            "username": "superadmin",
            "email": email,
            "hashed_password": get_password_hash(password),
            "role": "admin"
        }
        db["users"].insert_one(user_data)

def create_example_user(db: Database):
    email = "user@example.com"
    password = "userpasswordexample"
    user = db["users"].find_one({"email": email})
    if not user:
        user_data = {
            "username": "user",
            "email": email,
            "hashed_password": get_password_hash(password),
            "role": "user"
        }
        db["users"].insert_one(user_data)

def get_current_user(
    db: Database,
    token: Annotated[str, Depends(api_key_scheme)],
) -> User | None:
    if token is None:
        return None
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db["users"].find_one({"username": username})
        if user is None:
            raise credentials_exception
        return user
    except ExpiredSignatureError:
        return None
    except JWTError:
        raise credentials_exception


def get_superadmin(user: Annotated[User, Depends(get_current_user)]):
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user
