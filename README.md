# Soft Life Society 🌸

A wellness and lifestyle app centered on **Luna Reyes**, a Dominican-inspired AI lifestyle coach. Part of the Soft Life Blueprint™ ecosystem (softlifesocietyai.com).

## Tech Stack

- **Backend:** FastAPI + MongoDB (Motor)
- **Frontend:** Expo / React Native (TypeScript, expo-router)
- **Build/Deploy:** EAS Build (App Store submission is a later milestone)

## Features

- 🌸 **Luna** — chat-based AI coach persona
- 📊 **Calorie counter** — daily food logging with a calorie goal
- 💪 **Workout tracking** — log workouts, track your streak
- 🍽️ **Meal plans** — curated, structured meal plan content
- 🏆 **Challenges** — join and complete in-app challenges
- 💛 **Community** — connect with friends & family, send encouragement
- 🌙 **Light & dark mode** — full ivory/cream/blush/gold/rose/ink design system
- 🌷 **7-day free trial** → monthly/annual subscription paywall

## Project Structure

```
backend/    FastAPI + MongoDB API
frontend/   Expo / React Native app
```

## Running the backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit MONGODB_URI etc. as needed
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` (docs at `/docs`). Requires a running MongoDB instance (local or Atlas) — set `MONGODB_URI` in `.env`.

## Running the frontend

```bash
cd frontend
npm install
npx expo start
```

Update `extra.apiUrl` in `frontend/app.json` if your backend isn't at `http://localhost:8000` (e.g. use your machine's LAN IP when testing on a physical device).

## Design System

- **Palette:** ivory, cream, blush, gold, rose, ink (with a matching dark-mode palette)
- **Typography:** Cormorant Garamond (display/headings), DM Sans (body)
- **Tokens:** `frontend/theme/tokens.ts`

## Status

Core features are scaffolded and wired end-to-end (auth, trial/paywall, Luna chat, tracking, meal plans, challenges, community). Next steps: richer Luna coaching logic (optionally backed by an LLM), payment provider integration (Stripe/RevenueCat) for real subscriptions, push notifications, and App Store assets/submission.
