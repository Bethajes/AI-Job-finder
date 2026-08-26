from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_audit,
    admin_companies,
    admin_jobs,
    admin_stats,
    admin_users,
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

# Week 8: admin dashboard & management
api_router.include_router(admin_users.router)
api_router.include_router(admin_companies.router)
api_router.include_router(admin_jobs.router)
api_router.include_router(admin_stats.router)
api_router.include_router(admin_audit.router)
