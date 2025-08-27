from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from uuid import UUID

from src.api.deps import get_db
from src.models.Books import Books as BookModel
from src.schemas.book_schema import BookCreate, BookUpdate, Book as BookOut

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("", response_model=List[BookOut])
async def list_books(
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Search by title/author")
):
    stmt = select(BookModel)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(BookModel.title.ilike(like), BookModel.author.ilike(like))
        )
    stmt = stmt.order_by(BookModel.title.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Use UUID in the path so FastAPI validates the param.
    If someone passes '1', they'll get 422 instead of a 500 from the DB.
    """
    book = await db.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(payload: BookCreate, db: AsyncSession = Depends(get_db)):
    # unique ISBN if provided
    if payload.isbn:
        res = await db.execute(select(BookModel).where(BookModel.isbn == payload.isbn))
        if res.scalars().first():
            raise HTTPException(status_code=409, detail="ISBN already exists")

    book = BookModel(
        title=payload.title,
        author=payload.author,
        published_year=payload.published_year,
        publisher=payload.publisher,
        isbn=payload.isbn,
        image_url_s=payload.image_url_s,
        image_url_m=payload.image_url_m,
        image_url_l=payload.image_url_l,
        total_copies=payload.total_copies,
        available_copies=payload.total_copies,
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book

@router.patch("/{book_id}", response_model=BookOut)
async def update_book(book_id: UUID, payload: BookUpdate, db: AsyncSession = Depends(get_db)):
    book = await db.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if payload.isbn is not None and payload.isbn != book.isbn:
        res = await db.execute(select(BookModel).where(BookModel.isbn == payload.isbn))
        if res.scalars().first():
            raise HTTPException(status_code=409, detail="ISBN already exists")

    if payload.title is not None: book.title = payload.title
    if payload.author is not None: book.author = payload.author
    if payload.published_year is not None: book.published_year = payload.published_year
    if payload.publisher is not None: book.publisher = payload.publisher
    if payload.isbn is not None: book.isbn = payload.isbn
    if payload.image_url_s is not None: book.image_url_s = payload.image_url_s
    if payload.image_url_m is not None: book.image_url_m = payload.image_url_m
    if payload.image_url_l is not None: book.image_url_l = payload.image_url_l
    if payload.total_copies is not None:
        diff = payload.total_copies - (book.total_copies or 0)
        book.total_copies = payload.total_copies
        book.available_copies = max(0, (book.available_copies or 0) + diff)

    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: UUID, db: AsyncSession = Depends(get_db)):
    book = await db.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # block deletion if there are active rentals
    # (using text SQL is fine, but staying consistent with UUID typing)
    result = await db.execute(
        "SELECT COUNT(1) FROM rentals WHERE book_id = :bid AND returned_at IS NULL",
        {"bid": str(book_id)}
    )
    if (result.scalar_one() or 0) > 0:
        raise HTTPException(status_code=409, detail="Cannot delete a book with active rentals")

    await db.delete(book)
    await db.commit()
    return None

# Optional helper to avoid UUID typing for users: get by ISBN
@router.get("/by-isbn/{isbn}", response_model=BookOut)
async def get_book_by_isbn(isbn: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BookModel).where(BookModel.isbn == isbn))
    book = res.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
