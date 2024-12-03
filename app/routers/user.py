# app/routers/user.py

from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from jose import JWTError, jwt

from app.models.user_model import User
from app.db.session import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.templates import templates  # Import templates

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Check if the user already exists
    stmt = select(User).filter(User.username == username)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # User already exists, render the register page with an error message
        return templates.TemplateResponse(
            "register.html", {"request": request, "message": "User already exists"}
        )

    # Hash the password and create a new user
    hashed_password = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    # Redirect to login page after successful registration
    return RedirectResponse(url="/users/login", status_code=status.HTTP_302_FOUND)


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Retrieve user by username
    stmt = select(User).filter(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify the password
    if not user or not verify_password(password, user.hashed_password):
        # Invalid credentials, render the login page with an error message
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Incorrect username or password"},
        )

    # Create an access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Set the access token in a cookie
    response = RedirectResponse(url="/memories", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        expires=int(access_token_expires.total_seconds()),
        samesite="lax",
        secure=False,  # Set to True if using HTTPS
    )
    return response


@router.get("/logout")
async def logout(response: Response):
    # Clear the access token cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response
