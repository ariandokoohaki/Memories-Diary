from fastapi import FastAPI

from .routers import memory, user

app = FastAPI()

app.include_router(user.router)
app.include_router(memory.router)
