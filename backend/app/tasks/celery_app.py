from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "bioweb",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

