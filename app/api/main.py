from fastapi import APIRouter

from app.api.routes import admin, catalog, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(catalog.router)
api_router.include_router(admin.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
