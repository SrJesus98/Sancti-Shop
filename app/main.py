"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.router import api_router
from app.core.config import settings
from app.db.session import create_db_and_tables

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
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint."""
    return """
    <html>
        <head>
            <title>E-commerce</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-4xl font-bold text-blue-600">E-commerce</h1>
                <p class="mt-4 text-gray-700">Proyecto inicializado correctamente</p>
                <div class="mt-8">
                    <a href="/docs" class="text-blue-500 hover:underline">API Docs</a>
                </div>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
