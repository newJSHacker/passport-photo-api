from fastapi import APIRouter

from app.api.routes import checkout, documents, photos

api_router = APIRouter()
api_router.include_router(documents.router)
api_router.include_router(photos.router)
api_router.include_router(checkout.router)
