"""
FastAPI application factory for the Agaip framework.

This module creates and configures the FastAPI application with
middleware, exception handlers, and API routes.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from agaip.config.settings import Settings, get_settings
from agaip.core.application import get_application
from agaip.core.exceptions import AgaipException
from agaip.api.v1 import agents, tasks, health, admin
from agaip.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    application = get_application()
    await application.start()
    
    yield
    
    # Shutdown
    await application.stop()


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if settings is None:
        settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=settings.api.docs_url if not settings.is_production else None,
        redoc_url=settings.api.redoc_url if not settings.is_production else None,
        openapi_url=settings.api.openapi_url if not settings.is_production else None,
        lifespan=lifespan
    )
    
    # Add middleware
    _add_middleware(app, settings)
    
    # Add exception handlers
    _add_exception_handlers(app)
    
    # Add routes
    _add_routes(app, settings)
    
    return app


def _add_middleware(app: FastAPI, settings: Settings) -> None:
    """Add middleware to the application."""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=settings.api.cors_allow_credentials,
        allow_methods=settings.api.cors_allow_methods,
        allow_headers=settings.api.cors_allow_headers,
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    if settings.security.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)


def _add_exception_handlers(app: FastAPI) -> None:
    """Add custom exception handlers."""
    
    @app.exception_handler(AgaipException)
    async def agaip_exception_handler(request: Request, exc: AgaipException):
        return JSONResponse(
            status_code=400,
            content=exc.to_dict()
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "NotFound",
                "message": "The requested resource was not found",
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError", 
                "message": "An internal server error occurred",
                "request_id": getattr(request.state, "request_id", None)
            }
        )


def _add_routes(app: FastAPI, settings: Settings) -> None:
    """Add API routes to the application."""
    api_prefix = f"/api/{settings.api.version}"
    
    # Include routers
    app.include_router(health.router, prefix=api_prefix, tags=["health"])
    app.include_router(agents.router, prefix=api_prefix, tags=["agents"])
    app.include_router(tasks.router, prefix=api_prefix, tags=["tasks"])
    app.include_router(admin.router, prefix=api_prefix, tags=["admin"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "api_version": settings.api.version,
            "docs_url": settings.api.docs_url,
            "status": "running"
        }


# Global app instance
_app: FastAPI = None


def get_app() -> FastAPI:
    """Get the global FastAPI application instance."""
    global _app
    if _app is None:
        _app = create_app()
    return _app
