from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from src.api.deps import get_db
from src.models.Users import Users
from src.schemas.user_schema import UserCreate, UserUpdate, User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[User])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Users).order_by(Users.created_at.desc()))
    return result.scalars().all()

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(Users).where(Users.email == payload.email))
    if exists.scalars().first():
        raise HTTPException(status_code=409, detail="Email already exists")

    user = Users(name=payload.name, email=payload.email, phone=payload.phone)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=User)
async def update_user(user_id: UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None and payload.email != user.email:
        exists = await db.execute(select(Users).where(Users.email == payload.email, Users.id != user_id))
        if exists.scalars().first():
            raise HTTPException(status_code=409, detail="Email already exists")

    if payload.name is not None: user.name = payload.name
    if payload.email is not None: user.email = payload.email
    if payload.phone is not None: user.phone = payload.phone

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute("""
        SELECT COUNT(1) FROM rentals r
        WHERE r.user_id = :uid AND r.returned_at IS NULL
    """, {"uid": user_id})
    active_rentals = result.scalar_one() or 0
    if active_rentals > 0:
        raise HTTPException(status_code=409, detail="Cannot delete a user with active rentals")

    await db.delete(user)
    await db.commit()
    return None
