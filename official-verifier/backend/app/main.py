"""FastAPI application entry point."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.db.base import db
from app.api.v1 import endpoints, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.disconnect()


app = FastAPI(
    title="Official Website Verification Platform",
    description="API for verifying official websites and preventing scams",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to headers."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "ok": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.ENV == "dev" else None
        }
    )


# Include routers
app.include_router(endpoints.router, prefix="/v1", tags=["public"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Official Website Verification Platform",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        await db.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/metrics")
async def metrics():
    """
    Prometheus-style metrics endpoint.
    
    TODO: Implement actual metrics collection using prometheus_client
    """
    # Stub implementation
    return {
        "lookup_requests_total": 0,
        "avg_latency_ms": 0,
        "harvester_success": 0,
        "harvester_failures": 0
    }


# Dev-only endpoint for hashing API keys
if settings.ENV == "dev":
    from app.core.security import hash_api_key
    
    @app.post("/dev/hash-key")
    async def hash_key(key: str):
        """Hash an API key (dev only)."""
        return {"key_hash": hash_api_key(key)}
