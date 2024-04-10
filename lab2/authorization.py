import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from psycopg import Cursor

from models import get_db


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


def authenticate_user(db: Cursor, username: str, password: str):
    db.execute(
        """
            SELECT * FROM users WHERE username = %s
        """,
        (username,),
    )
    user = db.fetchone()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def create_superadmin(db: Cursor):
    email = os.getenv("SUPERADMIN_EMAIL")
    password = os.getenv("SUPERADMIN_PASSWORD")
    hashed_password = get_password_hash(password)

    db.execute("SELECT * FROM users WHERE email = %s", (email,))
    superadmin = db.fetchone()

    if not superadmin:
        db.execute(
            """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES (%s, %s, %s, %s)
            """,
            ("superadmin", email, hashed_password, "admin"),
        )


def create_example_user(db: Cursor):
    email = "user@example.com"
    password = "userpasswordexample"
    hashed_password = get_password_hash(password)

    db.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = db.fetchone()

    if not user:
        db.execute(
            """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES (%s, %s, %s, %s)
            """,
            ("user", email, hashed_password, "user"),
        )


def get_current_user(
    db: Annotated[Cursor, Depends(get_db)],
    token: Annotated[str, Depends(api_key_scheme)],
):
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
        db.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = db.fetchone()
        if user is None:
            raise credentials_exception
        return user
    except ExpiredSignatureError:
        return None
    except JWTError:
        raise credentials_exception


def get_superadmin(user=Depends(get_current_user)):
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user
