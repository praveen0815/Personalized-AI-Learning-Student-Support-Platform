"""FastAPI application for the knowledge base, tutor, and adaptive assessments."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.assessments import router as assessments_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.students import router as students_router
from app.api.routes.tutor import router as tutor_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.database import database_status, init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting knowledge base (embedding=%s/%s dim=%s, llm=%s/%s)",
        settings.embedding_provider,
        settings.embedding_model,
        settings.embedding_dimension,
        settings.llm_provider or "unset",
        settings.llm_model or "unset",
    )
    try:
        init_db()
    except Exception as exc:
        logger.exception("Database initialization failed (%s)", type(exc).__name__)
        raise RuntimeError(
            "Database initialization failed. Check DATABASE_URL and that PostgreSQL "
            "is running with permission to enable the pgvector extension."
        ) from None
    yield


app = FastAPI(
    title="Personalized AI Learning Platform",
    description=(
        "Educational knowledge base, source-grounded tutor, and adaptive assessments. "
        "Questions are written from uploaded material. Topic mastery and learning gaps "
        "use an explainable weighted average, not a knowledge-tracing model."
    ),
    version="0.3.0",
    lifespan=lifespan,
)
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)
app.include_router(knowledge_router)
app.include_router(tutor_router)
app.include_router(assessments_router)
app.include_router(students_router)


@app.exception_handler(AppError)
async def handle_app_error(_request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health", tags=["health"], summary="Backend and database status")
def health() -> dict[str, str]:
    database = database_status()
    status = "ok" if database == "connected" else "degraded"
    return {"status": status, "database": database}
