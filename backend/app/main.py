import logging
from contextlib import asynccontextmanager

from bson.errors import InvalidId
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.config import get_settings, validate_production_settings
from app.core.db import close_client, ensure_indexes, get_client
from app.routers import affirmations, auth, challenges, goals, luna, nutrition, routines, social, subscriptions

logger = logging.getLogger("soft_life_society")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_settings(settings)
    await ensure_indexes()
    yield
    await close_client()


app = FastAPI(title="Soft Life Society API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(luna.router)
app.include_router(nutrition.router)
app.include_router(goals.router)
app.include_router(routines.router)
app.include_router(affirmations.router)
app.include_router(challenges.router)
app.include_router(social.router)
app.include_router(subscriptions.router)


@app.exception_handler(InvalidId)
async def invalid_id_handler(request: Request, exc: InvalidId):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid resource id"})


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "Invalid data"})


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Something went a little sideways."})


@app.get("/")
async def root():
    return {"status": "ok", "app": "Soft Life Society 🌸"}


@app.get("/health")
async def health():
    try:
        await get_client().admin.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    return {"status": "healthy" if db_status == "connected" else "degraded", "database": db_status}
