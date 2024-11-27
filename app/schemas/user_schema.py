# app/schemas/user_schema.py

from pydantic import BaseModel, constr

class UserBase(BaseModel):
    username: constr(min_length=3, max_length=30)

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = {
        "from_attributes": True
    }
