from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.utils.db_utils import engine
from src.api.deps import get_db
from src.models.Books import Books

router = APIRouter(prefix="/_debug", tags=["_debug"])

@router.get("/db")
async def db_info(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Books))
    rows = res.scalars().all()
    # also check via raw SQL count
    cnt = (await db.execute(text("SELECT COUNT(*) FROM books"))).scalar_one()
    return {"engine_url": str(engine.url), "books_len": len(rows), "books_count": cnt}
