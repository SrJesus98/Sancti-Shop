"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.db.seed import seed_database
from app.db.session import create_db_and_tables
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.views.router import router as views_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events."""
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created")
    seed_database()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API routes
app.include_router(api_router)

# View routes (HTML pages)
app.include_router(views_router)


@app.get("/")
async def root():
    """Redirect to views."""
    return RedirectResponse(url="/views/")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
