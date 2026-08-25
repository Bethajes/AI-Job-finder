from fastapi import APIRouter

from app.api.v1.endpoints import (
    applications,
    auth,
    health,
    jobs,
    notifications,
    profiles,
    saved_jobs,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(saved_jobs.router)
api_router.include_router(notifications.router)
api_router.include_router(health.router)
