from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.api.routes import auth, users, issuers, credentials, verification
from app.models.base import init_db
from app.services.blockchain import blockchain_service
from app.services.ipfs import ipfs_service
from app.services.auth import redis_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Quantum-Secure Blockchain-based Digital Credential Locker",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")

    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")

    # Initialize blockchain connection
    try:
        logger.info("Connecting to blockchain...")
        if blockchain_service.connect():
            logger.info("Blockchain connected successfully")
        else:
            logger.warning("Failed to connect to blockchain")
    except Exception as e:
        logger.error(f"Blockchain connection error: {str(e)}")

    # Initialize IPFS connection
    try:
        logger.info("Connecting to IPFS...")
        if ipfs_service.connect():
            logger.info("IPFS connected successfully")
        else:
            logger.warning("Failed to connect to IPFS")
    except Exception as e:
        logger.error(f"IPFS connection error: {str(e)}")

    # Initialize Redis connection
    try:
        logger.info("Connecting to Redis...")
        if redis_service.connect():
            logger.info("Redis connected successfully")
        else:
            logger.warning("Failed to connect to Redis")
    except Exception as e:
        logger.error(f"Redis connection error: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down application")

    # Close IPFS connection
    try:
        ipfs_service.disconnect()
        logger.info("IPFS disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting IPFS: {str(e)}")

    # Close Redis connection
    try:
        redis_service.disconnect()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting Redis: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint - Health check"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    # Check service connections
    blockchain_status = "connected" if blockchain_service.is_connected() else "disconnected"
    ipfs_status = "connected" if ipfs_service.is_connected() else "disconnected"
    redis_status = "connected" if redis_service.is_connected() else "disconnected"

    # Overall health
    all_connected = all([
        blockchain_status == "connected",
        ipfs_status == "connected",
        redis_status == "connected"
    ])

    return {
        "status": "healthy" if all_connected else "degraded",
        "services": {
            "api": "running",
            "database": "connected",
            "blockchain": blockchain_status,
            "ipfs": ipfs_status,
            "redis": redis_status,
        },
    }


# Include API routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"],
)

app.include_router(
    issuers.router,
    prefix=f"{settings.API_V1_PREFIX}/issuers",
    tags=["Issuers"],
)

app.include_router(
    credentials.router,
    prefix=f"{settings.API_V1_PREFIX}/credentials",
    tags=["Credentials"],
)

app.include_router(
    verification.router,
    prefix=f"{settings.API_V1_PREFIX}/verify",
    tags=["Verification"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
