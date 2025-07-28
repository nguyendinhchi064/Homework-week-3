from fastapi import APIRouter
from src.api.hello_world.main import router as hello_world_router

router = APIRouter()

router.include_router(hello_world_router)
