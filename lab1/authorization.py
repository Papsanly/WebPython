import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from lab1.schemas import AccessTokenSchema
from models import User, get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return AccessTokenSchema(access_token=encoded_jwt, token_type="bearer")


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def create_superadmin(db: Session):
    email = os.getenv("SUPERADMIN_EMAIL")
    password = os.getenv("SUPERADMIN_PASSWORD")
    superadmin = db.scalar(select(User).where(User.email == email))
    if not superadmin:
        db.execute(
            insert(User).values(
                username="superadmin",
                email=email,
                hashed_password=get_password_hash(password),
                role="admin",
            )
        )


def create_example_user(db: Session):
    email = "user@example.com"
    password = "userpasswordexample"
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        db.execute(
            insert(User).values(
                username="user",
                email=email,
                hashed_password=get_password_hash(password),
                role="user",
            )
        )


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


def get_superadmin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user
