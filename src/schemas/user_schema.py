from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class User(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
