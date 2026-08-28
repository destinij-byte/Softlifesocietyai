from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, challenges, luna, meal_plans, nutrition, social, subscriptions, workouts

app = FastAPI(title="Soft Life Society API", version="0.1.0")

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
app.include_router(workouts.router)
app.include_router(meal_plans.router)
app.include_router(challenges.router)
app.include_router(social.router)
app.include_router(subscriptions.router)


@app.get("/")
async def root():
    return {"status": "ok", "app": "Soft Life Society 🌸"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
