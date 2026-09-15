# Soft Life Society 🌸

A wellness and lifestyle app centered on **Luna Reyes**, a Dominican-inspired AI lifestyle coach. Part of the Soft Life Blueprint™ ecosystem (softlifesocietyai.com). Tagline: *"Become the woman you've been working toward."*

## Tech Stack

- **Backend:** FastAPI + MongoDB (Motor)
- **Frontend:** Expo / React Native (TypeScript, expo-router)
- **Build/Deploy:** EAS Build (App Store submission is a later milestone)

## Features

- 🏠 **Home** — daily command center: greeting, Today's Focus, quick stats, a proactive AI meal suggestion, and a Challenges streak teaser
- ✨ **Your AI (Luna Reyes)** — one chat-based coach with four modes: Life 🌸, Money 💰, Wellness 🍓, Goals 🎯 — context-aware of your nutrition/goals data
- 🍽️ **Nourish AI** — calorie/macro ring dashboard, three ways to log food (📸 AI photo analysis, 🔎 search, ✍🏽 manual), and an AI meal builder
- 🎯 **Goals** — Money/Wellness/Career/Personal categories with targets, progress, milestones, an optional Quarterly/Long-Term timeframe, and a photo **Vision Board** per goal
- 📋 **Routines** — customizable Morning/Night checklists that reset daily, each paired with a daily affirmation, manifestation journal prompt, and custom affirmations
- 🏆 **Challenges** — 75/45/30-day templates with an intensity picker, fixed Water Intake & 10k Steps challenges, streaks, and a live Family & Friends leaderboard with shareable invite codes
- 👤 **Me** — subscription management, Light/Dark/System appearance, and profile menu
- 🌙 **Light, dark & system appearance** — blush/soft-pink/gold/black/cream palette with a matching dark palette, gold-gradient CTAs with a shimmer sweep
- A single custom line-icon system (`components/Icon.tsx`) across the tab bar and menus, in place of emoji-only icons
- ✨ **Animated app-open sequence** — logo scale/fade on a gold-glow gradient, tagline settle-in, staggered Home card reveal
- 🌷 **7-day free trial** → Free / $14.99 monthly / $99 annual paywall

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

**Luna & AI features:** set `ANTHROPIC_API_KEY` in `.env` to power Luna's chat (persona + mode + conversation history, model configurable via `LUNA_MODEL`, defaults to `claude-opus-5`), Nourish AI's meal-photo analysis, and the AI meal builder via the real Claude API. Leave it unset and these fall back to built-in templated/heuristic responses — no API calls, no cost, useful for local dev.

## Running the frontend

```bash
cd frontend
npm install
npx expo start
```

Update `extra.apiUrl` in `frontend/app.json` if your backend isn't at `http://localhost:8000` (e.g. use your machine's LAN IP when testing on a physical device).

## Design System

- **Palette:** Blush `#F6C8D8`, Soft Pink `#FCEEF3`, Gold `#D4AF37`, Black `#1A1A1A`, Cream `#FFF9F6` (dark: background `#111111`, cards `#1A1A1A` / `#242024`, text `#FFF9F6`, accents stay Blush + Gold)
- **Gold gradient:** `#F6E2A0 → #D4AF37 → #A87A1F` (light) / `#F6E2A0 → #D4AF37 → #9C7A2E` (dark) — used on CTAs, progress bars/rings
- **Typography:** Playfair Display (display/headings), Poppins (body/UI)
- **Tokens:** `frontend/theme/tokens.ts`

## Status

All seven core screens are built and wired end-to-end against the backend, with Luna and Nourish AI backed by the real Claude API when `ANTHROPIC_API_KEY` is set. Verified locally: a full backend API smoke test (auth, 4-mode Luna chat, nutrition/macros, goals, routines, challenges, leaderboard, invites, subscriptions) and a full browser walkthrough of the Expo web build (animated intro, all 7 tabs, light/dark mode). Next steps: payment provider integration (Stripe/RevenueCat) for real billing, push notifications, and App Store assets/submission.
