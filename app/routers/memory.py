# app/routers/memory.py

from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.memory_model import Memory
from app.models.user_model import User
from app.schemas.memory_schema import MemoryCreate
from app.db.session import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_class=RedirectResponse)
async def create_memory(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_memory = Memory(title=title, description=description, user_id=current_user.id)
    db.add(new_memory)
    try:
        await db.commit()
        await db.refresh(new_memory)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    # Redirect back to the memories page
    return RedirectResponse(url="/memories", status_code=status.HTTP_302_FOUND)
