from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime, date

class RentCreate(BaseModel):
    user_id: UUID
    book_id: UUID
    quantity: int = Field(1, ge=1)
    days: int = Field(14, ge=1, le=60)

class ReturnCreate(BaseModel):
    rental_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    book_id: Optional[UUID] = None

class Rental(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    quantity: int
    rented_at: datetime
    due_date: date
    returned_at: Optional[datetime] = None

    class Config:
        from_attributes = True
