# Project Status — Personalized Dining Recommendation System
_Last updated: 2026-03-08_

---

## Overview

CS 125 (UC Irvine) project. Full-stack personalized nutrition recommendation app with:
- **Backend**: FastAPI + Supabase Postgres, in-memory keyword + nutrient vector index, USDA FDC API integration, UCI dining hall scraper
- **Mobile**: React Native (Expo SDK 54, Expo Router v3), Zustand state management, React Query for server state, Supabase Auth

---

## Architecture

```
USDA FDC API ──┐
               ├─→ ingest_pipeline.py ─→ Food dataclass ─→ Postgres (foods table)
UCI Dining ────┘                                         └─→ in-memory FoodIndexManager

Mobile App ──→ FastAPI ──→ FoodIndexManager ──→ FoodRanker ──→ RecommendationItem[]
               │         └─→ USDA FDC fallback (on cache miss)
               └─→ Supabase Auth (JWT / ES256 / JWKS)
```

---

## Backend (`backend/`)

### Core Data Model (`src/logical_view/food.py`)
`Food` dataclass with all fields required for a full US Nutrition Facts label:

**Core macros** (per 100g):
- `food_id`, `name`, `source`, `brand`, `meal_category`, `tags`
- `calories`, `protein`, `carbs`, `fat`, `fiber`

**Extended nutrition label fields** (per 100g, `Optional[float]`, `None` if unavailable):
- `saturated_fat`, `trans_fat` (g)
- `cholesterol`, `sodium` (mg)
- `sugars`, `added_sugars` (g)
- `vitamin_d` (mcg), `calcium`, `iron`, `potassium` (mg)

### Database Schema (`docs/schema.sql`)
Tables in Supabase Postgres:
- `profiles` — user display name; auto-created by trigger on `auth.users` insert
- `foods` — USDA + UCI dining items; PK is `(source, food_id)`; includes all 10 extended nutrition columns
- `food_tags` — dietary tags (vegetarian, vegan, gluten-free, etc.)
- `user_goals` — per-user daily macro targets (calories/protein/carbs/fat/fiber)
- `user_favorites` — user-favorited foods with a `food_name` snapshot; no FK to foods (UCI dining items are in-memory only)
- `user_consumption_log` — meal log entries with `meal_type` and `food_name` snapshot; no FK to foods
- `user_recipes` — unused placeholder for future recipe feature

All tables have RLS policies (`auth.uid() = user_id`).

A `delete_stale_usda_foods(days_old)` function + `pg_cron` job runs nightly at 03:00 UTC to purge USDA foods not refreshed in 30+ days.

**⚠️ Migration required**: Run `python scripts/init_db.py` from `backend/` to apply the 10 new nutrition columns to an existing database.

### Ingestion (`src/ingest/`)
- **`usda_fdc_client.py`** — wraps USDA FDC `/foods/search` and `/food/{fdcId}`; responses cached to `data/cache/`
- **`dininghall_sources.py`** — `UCIDiningScraper` scrapes Brandywine and Anteatery via BeautifulSoup; UCI foods use negative `food_id` and `source = uci_dining_brandywine` / `uci_dining_anteatery`
- **`ingest_pipeline.py`** — `DataIngestionPipeline` orchestrates both sources
  - `NUTRIENT_IDS` maps 15 USDA nutrient IDs (energy, protein, carbs, fat, fiber + 10 extended)
  - `parse_usda_food()` extracts all fields; uses `_opt(key)` helper that returns `None` when value is 0 (nutrient not present in FDC record)

### Database Layer (`src/db/postgres.py`)
- `upsert_foods(foods)` — upserts all 20 food columns + replaces `food_tags` rows
- `fetch_foods(limit, sources, source_prefixes)` — full SELECT + GROUP BY with tag aggregation; returns `List[Food]`

### API Layer (`api/`)

#### Auth
- JWT verification via ES256/JWKS (Supabase's public JWKS endpoint)
- Every protected route calls `get_current_user()` which validates the Bearer token

#### Explore Endpoints (`api/routers/explore.py`)
- `GET /v1/explore/search` — keyword search; falls back to USDA FDC API if in-memory index returns no results
- `POST /v1/explore/recommend` — personalized ranked recommendations
  - With `query`: searches index → USDA FDC fallback if no results → ranks via `FoodRanker`
  - Without `query`: surfaces only user's non-dining favorites → ranks via `FoodRanker`
  - **Key fix**: USDA fallback now sets `candidates` *before* attempting DB upsert, so a DB failure (e.g., pending migration) no longer silently swallows search results

#### Dining Endpoints (`api/routers/dining.py`)
- `GET /v1/dining/halls` — hall open/closed status
- `GET /v1/dining/{hall}/menu` — raw menu for a hall
- `POST /v1/dining/{hall}/recommend` — personalized ranked recommendations from scraped menu

#### Profile / Meal Log Endpoints (`api/routers/profile.py`)
- `GET/PUT /v1/profile/{id}/goals` — nutrition goals
- `GET/POST /v1/profile/{id}/favorites` — favorites list
- `DELETE /v1/profile/{id}/favorites/{source}/{food_id}` — remove favorite
- `POST /v1/profile/{id}/meals` — log a meal
- `GET /v1/profile/{id}/meals/today` — consumed-today summary

#### Food API Model (`api/models/food.py`)
`FoodResponse` Pydantic model includes all 10 extended nutrition fields as `Optional[float] = None` so they serialize to `null` in JSON when absent.

### Ranking
- **`FoodRanker`** (`src/implicit_ranking/food_ranking.py`) — nutrition-aware scoring
  - Weights: protein=2.5, fiber=1.2, carbs=1.0, fat=1.0
  - Remaining daily targets divided by `meals_remaining` (morning=3, afternoon=2, evening=1) for per-meal scoring
  - Heavy penalty (`-20 * (1 + overshoot_ratio)`) for exceeding per-meal calorie budget
  - Favorites boosted; output includes `explanation` text
- **BM25 / TF-IDF rankers** (`src/query_based_ranking/`) — query-based ranking alternatives (used internally)

---

## Mobile (`mobile/`)

### Color Scheme (`constants/theme.ts`)
- **`Colors.dining`** changed from dark forest green to match `Colors.explore` (navy blue):
  - `primary: "#023E8A"`, `accent: "#74C69D"`, `light: "#E0F0FF"`, `surface: "#0353A4"`
- This cascades to the dining tab header, log FAB, profile save button, tab bar active color, and onboarding screens

### State Management (`lib/store/profile.ts` — Zustand)
Persisted store contains:
- `userId`, `name`, `goals` (NutritionGoals), `consumedToday` (ConsumedToday)
- `favorites: Set<string>` — compound IDs in format `"source:food_id"` (e.g. `"usda_fdc:12345"`)
- Actions: `setGoals`, `addFavorite`, `removeFavorite`, `reset`

### API Client (`lib/api/`)
- `client.ts` — axios instance with base URL from `EXPO_PUBLIC_API_URL`; attaches Supabase session JWT as Bearer token
- `profile.ts` — `updateGoals`, `addFavorite`, `removeFavorite`, `logMeal` (with `LogMealPayload`)
- `explore.ts` — `searchFoods`, `fetchExploreRecommendations`
- `dining.ts` — `fetchHalls`, `fetchDiningRecommendations`

### Types (`lib/types/`)
- `food.ts` — `Food` interface includes all 10 extended nutrition fields as `number | null`
- `api.ts` — request/response types for all API calls
- `user.ts` — `NutritionGoals`, `ConsumedToday`

### Screens

#### Explore Tab (`app/(tabs)/explore/index.tsx`)
- Navy header with search bar and meal type filter pills (Any / Breakfast / Lunch / Dinner / Snack)
- Calls `POST /v1/explore/recommend` via `useExploreRecommendations` hook
- Only fetches if there is an active search query OR the user has non-dining favorites
- Tapping a `RecommendationCard` opens `FoodDetailModal`
- Empty state: "Favorite a non-dining hall food to see it here, or search above"

#### Dining Hall Tab (`app/(tabs)/dining/index.tsx`)
- Navy header (matches explore theme) with hall selector (Brandywine / Anteatery) and meal period tabs
- Tapping a `RecommendationCard` opens `FoodDetailModal`

#### Log Tab (`app/(tabs)/log.tsx`)
- Displays consumed-today summary (total calories, protein, carbs, fat, fiber)
- Lists recent meal log entries with meal type labels

#### Profile Tab (`app/(tabs)/profile.tsx`)
- **Account Information section** (new):
  - Email — fetched via `supabase.auth.getUser()` on mount
  - Member Since — formatted as "Month YYYY" from `created_at`
  - "Send Password Reset Email" button — calls `supabase.auth.resetPasswordForEmail(email)`
- **Daily Nutrition Goals section** — editable fields for calories/protein/carbs/fat/fiber; saved to backend

### Components

#### `RecommendationCard` (`components/ui/RecommendationCard.tsx`)
- `variant="dining"` or `variant="explore"` (navy theme for both)
- Shows food name, brand, up to 4 `MacroBadge` nutrient highlights, explanation text
- **Border**: `borderWidth: 1.5`, `borderColor: "rgba(2, 62, 138, 0.35)"` — visible outline to distinguish cards

#### `FoodDetailModal` (`components/ui/FoodDetailModal.tsx`)
Full US Nutrition Facts label bottom-sheet modal:

**Nutrition label rows** (per serving, `N/A` if null):
- Calories (large display)
- Total Fat → Saturated Fat (indented) → Trans Fat (indented, italic)
- Cholesterol, Sodium
- Total Carbohydrate → Dietary Fiber (indented) → Total Sugars (indented) → Added Sugars (double-indented, conditional)
- Protein (bold)
- Vitamin D, Calcium, Iron, Potassium

**Scaling**: all `food.*` values are stored per-100g; scaled by `serving_size_g / 100` for display.

**Actions**:
- Meal type selector pills: Breakfast / Lunch / Dinner / Snack
- "Add to Log" — `POST /v1/profile/{id}/meals`, invalidates `consumed-today` React Query cache, closes modal
- "Favorite" / "Favorited" toggle — `addFavorite` / `removeFavorite` API calls, updates Zustand store

#### `MacroBadge` (`components/ui/MacroBadge.tsx`)
Small colored pill showing a nutrient name and value (e.g. "32g Protein").

#### `HallStatusBadge` (`components/ui/HallStatusBadge.tsx`)
Open/closed status indicator for a dining hall.

### Hooks
- `useExploreRecommendations(query?, mealType?)` — calls `/v1/explore/recommend`; only enabled when there is a query or non-dining favorites
- `useDiningRecommendations(hall, period?)` — calls `/v1/dining/{hall}/recommend`

---

## Auth Flow

1. **Sign up** → Supabase sends confirmation email → deep-link callback to `/(auth)/callback`
2. **Login** → Supabase returns JWT (ES256) → stored in SecureStore via Supabase client
3. **API calls** → Supabase session attached as Bearer token → FastAPI validates via JWKS
4. **Sign out** → `supabase.auth.signOut()` → Zustand store reset → redirect to `/(auth)/login`
5. **Password reset** → `supabase.auth.resetPasswordForEmail(email)` → user clicks link in email

---

## Known Issues / Pending Work

### ⚠️ DB Migration Required
The extended nutrition columns (`saturated_fat`, `trans_fat`, `cholesterol`, `sodium`, `sugars`, `added_sugars`, `vitamin_d`, `calcium`, `iron`, `potassium`) must be added to the live Supabase database:
```bash
cd backend
python scripts/init_db.py
```
Until this is run, `upsert_foods` will fail for new USDA foods. The USDA fallback in the explore endpoints now handles this gracefully (results are still returned even if the DB upsert fails), but foods will not be persisted to the index for future requests.

### Extended Nutrition Fields Populate Only for Newly Fetched Foods
Foods already in the DB have `null` for all extended fields until they are re-fetched from USDA FDC. The `FoodDetailModal` shows `N/A` for these. Running a fresh ingestion (`python -m src.ingest.ingest_pipeline`) will repopulate the DB with extended fields for all foods.

### Dining Hall Foods Never Have Extended Nutrition Fields
The UCI dining scraper (`dininghall_sources.py`) scrapes menus from `uci.mydininghub.com` which does not provide detailed nutrition data beyond the 5 core macros. All extended fields will show `N/A` for dining hall foods.

---

## File Map (Key Files)

```
backend/
├── api/
│   ├── main.py                    — FastAPI app, lifespan startup (loads index from DB)
│   ├── dependencies.py            — FastAPI Depends: get_current_user, index_manager_dep
│   ├── models/
│   │   ├── food.py                — FoodResponse (20 fields including 10 extended)
│   │   └── recommendations.py    — RecommendationItem, request/response models
│   ├── routers/
│   │   ├── explore.py             — /v1/explore/* (search + recommend with USDA fallback)
│   │   ├── dining.py              — /v1/dining/* (hall status + personalized recs)
│   │   └── profile.py             — /v1/profile/* (goals, favorites, meal log)
│   └── services/
│       ├── ranking_service.py     — adapter: Pydantic → dataclass → FoodRanker → Pydantic
│       ├── dining_service.py      — UCIDiningScraper wrapper + hall open/closed status
│       └── index_service.py       — singleton FoodIndexManager
├── src/
│   ├── logical_view/
│   │   ├── food.py                — Food dataclass (25 fields)
│   │   ├── user_goals.py          — UserGoals dataclass
│   │   └── consumed_today.py      — ConsumedToday dataclass
│   ├── ingest/
│   │   ├── usda_fdc_client.py     — USDA FDC API client with disk cache
│   │   ├── dininghall_sources.py  — UCIDiningScraper (BeautifulSoup)
│   │   └── ingest_pipeline.py     — DataIngestionPipeline orchestrator
│   ├── index/
│   │   ├── inverted_index.py      — KeywordIndex + NutrientVectorIndex
│   │   └── build_index.py         — FoodIndexManager (wraps both indexes)
│   ├── implicit_ranking/
│   │   └── food_ranking.py        — FoodRanker (nutrition-aware scoring)
│   ├── query_based_ranking/
│   │   ├── bm25.py                — BM25Ranker
│   │   └── tfidf.py               — TFIDFRanker
│   ├── db/
│   │   ├── postgres.py            — upsert_foods, fetch_foods (psycopg v3)
│   │   └── user_db.py             — get_favorites, log_meal, etc.
│   └── config.py                  — PROJECT_ROOT, DATABASE_URL, USDA_FDC_API_KEY
├── docs/
│   └── schema.sql                 — Full Postgres schema + migrations
└── scripts/
    └── init_db.py                 — Applies schema.sql to live DB

mobile/
├── app/
│   ├── (auth)/
│   │   ├── login.tsx              — Email/password login
│   │   ├── signup.tsx             — Registration
│   │   └── callback.tsx           — Deep-link handler for email confirmation
│   ├── (tabs)/
│   │   ├── _layout.tsx            — Tab navigator (Home, Dining, Explore, Log, Profile)
│   │   ├── index.tsx              — Home screen
│   │   ├── dining/index.tsx       — Dining Hall tab (+ FoodDetailModal)
│   │   ├── explore/index.tsx      — Explore tab (+ FoodDetailModal)
│   │   ├── log.tsx                — Meal log / consumed-today
│   │   └── profile.tsx            — Profile + account info + nutrition goals
│   └── _layout.tsx                — Root layout (QueryClientProvider, auth guard)
├── components/ui/
│   ├── RecommendationCard.tsx     — Food card with border + onPress
│   ├── FoodDetailModal.tsx        — Full nutrition label bottom-sheet modal
│   ├── MacroBadge.tsx             — Nutrient highlight pill
│   └── HallStatusBadge.tsx        — Hall open/closed badge
├── constants/
│   └── theme.ts                   — Colors (dining = navy, explore = navy), Spacing, Typography
├── hooks/
│   ├── useExploreRecommendations.ts
│   └── useDiningRecommendations.ts
└── lib/
    ├── api/
    │   ├── client.ts              — axios instance + auth interceptor
    │   ├── explore.ts
    │   ├── dining.ts
    │   └── profile.ts             — updateGoals, addFavorite, removeFavorite, logMeal
    ├── store/
    │   └── profile.ts             — Zustand store (userId, goals, consumed, favorites)
    ├── supabase.ts                 — Supabase client (AsyncStorage session persistence)
    └── types/
        ├── food.ts                — Food interface (15 fields including 10 extended)
        ├── api.ts                 — API request/response types
        └── user.ts                — NutritionGoals, ConsumedToday
```
