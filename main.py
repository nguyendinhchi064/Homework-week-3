import sys, asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.utils.db_utils import engine, Base
from src.api.books import router as books_router
from src.api.users import router as users_router
from src.api.rentals import router as rentals_router
from src.api.debug import router as debug_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Library Management API", version="1.0.0", lifespan=lifespan)

app.include_router(books_router)
app.include_router(users_router)
app.include_router(rentals_router)
app.include_router(debug_router)

@app.get("/", tags=["Health"])
async def health():
    return {"status": "ok"}
