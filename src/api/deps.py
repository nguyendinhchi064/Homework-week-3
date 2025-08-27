# src/api/deps.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.db_utils import create_database_session  

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in create_database_session():
        yield session
