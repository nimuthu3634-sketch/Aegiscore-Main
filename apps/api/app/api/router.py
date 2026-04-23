from fastapi import APIRouter

from app.api.routes.assets import router as assets_router
from app.api.routes.auth import router as auth_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.policies import router as policies_router
from app.api.routes.reports import router as reports_router
from app.api.routes.responses import router as responses_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(ingestion_router)
api_router.include_router(assets_router)
api_router.include_router(alerts_router)
api_router.include_router(incidents_router)
api_router.include_router(responses_router)
api_router.include_router(policies_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
api_router.include_router(health_router)