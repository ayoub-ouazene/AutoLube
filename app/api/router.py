from fastapi import APIRouter

from app.api.v1 import chat


api_router = APIRouter()
api_router.include_router(chat.router)


# When you add more v1 routers later, register them here:
# from app.api.v1 import products
# api_router.include_router(products.router)