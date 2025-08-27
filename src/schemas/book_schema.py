from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class BookCreate(BaseModel):
    title: str
    author: str
    published_year: int = Field(ge=0, le=2100)
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    image_url_s: Optional[str] = None
    image_url_m: Optional[str] = None
    image_url_l: Optional[str] = None
    total_copies: int = Field(default=1, ge=0)

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    published_year: Optional[int] = Field(None, ge=0, le=2100)
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    image_url_s: Optional[str] = None
    image_url_m: Optional[str] = None
    image_url_l: Optional[str] = None
    total_copies: Optional[int] = Field(None, ge=0)

class Book(BaseModel):
    id: UUID
    title: str
    author: str
    published_year: int
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    image_url_s: Optional[str] = None
    image_url_m: Optional[str] = None
    image_url_l: Optional[str] = None
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
