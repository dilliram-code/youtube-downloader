import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.endpoints import router as api_router
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import init_db
from backend.app.jobs.manager import job_manager

async def periodic_cleanup_task():
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            await job_manager.cleanup_expired_jobs()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup task: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Vidora backend...")
    settings.setup_directories()
    await init_db()
    cleanup_task = asyncio.create_task(periodic_cleanup_task())
    yield
    cleanup_task.cancel()
    logger.info("Vidora backend shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Vidora Modern Media Extraction and Processing Backend API",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An internal server error occurred.",
            "detail": str(exc) if settings.DEBUG else None
        }
    )

# Register Endpoints
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
