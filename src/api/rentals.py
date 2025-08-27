from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID
from src.api.deps import get_db
from src.models.Books import Books
from src.models.Users import Users
from src.models.RentalReq import Rental  
from src.schemas.rental_schema import RentCreate, ReturnCreate, Rental as RentalOut

router = APIRouter(tags=["Rentals"])

@router.get("/rentals", response_model=List[RentalOut])
async def list_rentals(
    db: AsyncSession = Depends(get_db),
    active: Optional[bool] = Query(None, description="Filter by active (not returned)"),
    user_id: Optional[UUID] = None,
    book_id: Optional[str] = None,
):
    stmt = select(Rental)
    if active is True:
        stmt = stmt.where(Rental.returned_at.is_(None))
    if active is False:
        stmt = stmt.where(Rental.returned_at.is_not(None))
    if user_id:
        stmt = stmt.where(Rental.user_id == user_id)
    if book_id:
        stmt = stmt.where(Rental.book_id == book_id)
    stmt = stmt.order_by(Rental.rented_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/rent", response_model=RentalOut, status_code=status.HTTP_201_CREATED)
async def rent_book(payload: RentCreate, db: AsyncSession = Depends(get_db)):
    book = await db.get(Books, payload.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be >= 1")
    if (book.available_copies or 0) < payload.quantity:
        raise HTTPException(status_code=409, detail="Not enough available copies")

    user = await db.get(Users, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    due = date.today() + timedelta(days=payload.days)
    rental = Rental(user_id=payload.user_id, book_id=payload.book_id, quantity=payload.quantity, due_date=due)
    book.available_copies = (book.available_copies or 0) - payload.quantity

    db.add(rental)
    db.add(book)
    await db.commit()
    await db.refresh(rental)
    return rental

@router.post("/return", response_model=RentalOut)
async def return_book(payload: ReturnCreate, db: AsyncSession = Depends(get_db)):
    rental = None
    if payload.rental_id is not None:
        rental = await db.get(Rental, payload.rental_id)
    else:
        if not payload.user_id or not payload.book_id:
            raise HTTPException(status_code=400, detail="Provide rental_id or both user_id and book_id")
        stmt = (select(Rental)
                .where(Rental.user_id == payload.user_id,
                       Rental.book_id == payload.book_id,
                       Rental.returned_at.is_(None))
                .order_by(Rental.rented_at.desc())
                .limit(1))
        result = await db.execute(stmt)
        rental = result.scalars().first()

    if not rental:
        raise HTTPException(status_code=404, detail="Active rental not found")
    if rental.returned_at is not None:
        return rental  # idempotent

    book = await db.get(Books, rental.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found for rental")

    rental.returned_at = func.now()
    book.available_copies = (book.available_copies or 0) + (rental.quantity or 0)

    db.add(rental)
    db.add(book)
    await db.commit()
    await db.refresh(rental)
    return rental
