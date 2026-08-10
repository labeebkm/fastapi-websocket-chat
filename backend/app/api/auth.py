from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Temporary in-memory users
# We will replace this with PostgreSQL later.

users = {
    "alice": {
        "username": "alice",
        "password": hash_password("alice123"),
    },
    "bob": {
        "username": "bob",
        "password": hash_password("bob123"),
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(request: LoginRequest):

    user = users.get(request.username)

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(
        request.password,
        user["password"],
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        username=user["username"]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }