from fastapi import FastAPI

from apps.api.app.config import get_settings
from apps.api.app.routers import audit, health, memories, policies, retrieval, review

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(health.router)
app.include_router(memories.router, prefix=settings.api_v1_prefix)
app.include_router(retrieval.router, prefix=settings.api_v1_prefix)
app.include_router(review.router, prefix=settings.api_v1_prefix)
app.include_router(policies.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router, prefix=settings.api_v1_prefix)

