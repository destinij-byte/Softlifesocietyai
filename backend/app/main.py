from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, challenges, goals, luna, nutrition, routines, social, subscriptions

app = FastAPI(title="Soft Life Society API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(luna.router)
app.include_router(nutrition.router)
app.include_router(goals.router)
app.include_router(routines.router)
app.include_router(challenges.router)
app.include_router(social.router)
app.include_router(subscriptions.router)


@app.get("/")
async def root():
    return {"status": "ok", "app": "Soft Life Society 🌸"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
