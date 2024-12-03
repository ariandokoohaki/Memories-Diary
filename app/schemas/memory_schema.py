# app/schemas/memory_schema.py

from datetime import datetime

from pydantic import BaseModel


class MemoryBase(BaseModel):
    title: str
    description: str


class MemoryCreate(MemoryBase):
    pass


class MemoryResponse(MemoryBase):
    id: int
    created_at: datetime
    user_id: int

    model_config = {"from_attributes": True}
