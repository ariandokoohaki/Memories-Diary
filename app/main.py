# app/main.py

import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth import get_current_user
from app.db.base import Base
from app.db.session import get_db, sync_engine
from app.routers import memory, user
from app.templates import templates  # Import templates from app.templates


if not os.path.exists("./data"):
    os.makedirs("./data")


app = FastAPI()


# Initialize the database with all models (using synchronous engine)
Base.metadata.create_all(bind=sync_engine)


# Allow CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(user.router)
app.include_router(memory.router)


# Get the directory of the current file (app/main.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the absolute path to the 'frontend/static' directory
static_dir = os.path.join(current_dir, "..", "frontend", "static")

# Verify the static directory exists
if not os.path.isdir(static_dir):
    raise RuntimeError(f"Static directory '{static_dir}' does not exist")


# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Serve index.html
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Serve register.html
@app.get("/users/register", response_class=HTMLResponse)
async def serve_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Serve login.html
@app.get("/users/login", response_class=HTMLResponse)
async def serve_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Serve memories.html
@app.get("/memories", response_class=HTMLResponse)
async def serve_memories(
    request: Request,
    current_user: Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(memory_model.Memory).filter(
            memory_model.Memory.user_id == current_user.id
        )
    )
    memories = result.scalars().all()
    return templates.TemplateResponse(
        "memories.html",
        {"request": request, "memories": memories, "user": current_user},
    )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "detail": exc.detail},
        status_code=exc.status_code,
    )
