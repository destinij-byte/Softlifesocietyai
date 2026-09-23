import logging
from contextlib import asynccontextmanager

from bson.errors import InvalidId
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.config import get_settings, validate_production_settings
from app.core.db import close_client, ensure_indexes, get_client
from app.routers import affirmations, auth, blueprint, challenges, goals, home, luna, night_reset, nutrition, progress, routines, social, subscriptions, weekly_reset, webhooks

logger = logging.getLogger("soft_life_society")
# Root logging has no handler by default (Python only prints WARNING+ to
# stderr as a last resort), so every logger.info() in this app — including
# the password-reset dev-mode fallback that's the *only* way to recover the
# reset token until RESEND_API_KEY is set — would otherwise be silently
# dropped. Configure this app's own logger explicitly rather than touching
# the root logger, so other libraries' log levels are left alone.
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

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
app.include_router(blueprint.router)
app.include_router(home.router)
app.include_router(night_reset.router)
app.include_router(progress.router)
app.include_router(weekly_reset.router)
app.include_router(webhooks.router)


@app.exception_handler(InvalidId)
async def invalid_id_handler(request: Request, exc: InvalidId):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid resource id"})


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "Invalid data"})


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


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
