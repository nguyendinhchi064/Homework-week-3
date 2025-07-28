from fastapi import FastAPI
from src.api.main_router import router as main_router

app = FastAPI()
app.include_router(main_router)
