# Baseline Implementation Summary (Week 3 Snapshot)

This document summarizes the baseline implementation as it existed during the Week 3 milestone. The current codebase has moved beyond this baseline (for example, database-backed ingestion), but this summary is kept for reference.

## Components Implemented at the Time

### Phase 1: Data Ingestion 

**Core files:**
- `src/logical_view/food.py` - Food dataclass (core schema)
- `src/logical_view/user_goals.py` - UserGoals dataclass
- `src/logical_view/consumed_today.py` - ConsumedToday dataclass
- `src/ingest/usda_fdc_client.py` - USDA FoodData Central API client
- `src/ingest/dininghall_sources.py` - UCI dining hall web scraper
- `src/ingest/ingest_pipeline.py` - Unified ingestion pipeline
- `src/config.py` - Project paths, cache locations, API config

**Features:**
- Fetches a diverse set of foods from USDA FDC (configurable, default max 1000)
- Scrapes UCI dining hall menus (Brandywine & Anteatery) via HTML parsing
- Parses nutrition data (calories, protein, carbs, fat, fiber)
- Infers meal categories (breakfast, lunch, dinner, snack, any)
- Infers dietary tags (vegan, vegetarian, gluten-free, organic)
- Normalizes to a unified `Food` schema
- Saves outputs to JSON and CSV
- Generates summary statistics (counts by source/meal category, averages)

### Phase 2: Indexing 

**Core files:**
- `src/index/inverted_index.py` - KeywordIndex + NutrientVectorIndex + tokenizer
- `src/index/build_index.py` - FoodIndexManager (unified search + persistence)

**Features:**
- **Keyword Inverted Index**: term → set of food IDs
- **Nutrient Vector Index**: food_id → Food object
- **Tokenization**: lowercase + split on non-alphanumeric characters
- **Filtering**: by meal category and calorie budget
- **Serialization**: save/load indexes to/from JSON
- **Unified Search**: query + filters via `FoodIndexManager.search()`

### Phase 3: Ranking 

**Nutrition-Aware Ranking**
- `src/query/food_ranking.py` - Personalized nutrition ranking + explanations

**Features:**
- Nutrient gap matching based on remaining targets
- Calorie budget constraint (heavy penalty for overshoot)
- Context bonuses (meal match, favorites)
- Explanation generation (nutrient contributions + context)
- Serving size scaling
- `FoodRanker.recommend()` returns structured recommendation dicts

**Traditional IR Ranking (Baseline IR track)**
- `src/ranking/tfidf.py` - TF-IDF ranker
- `src/ranking/bm25.py` - BM25 ranker

**Features:**
- Standard TF-IDF with multiple TF normalization modes
- BM25 with configurable `k1` and `b` parameters
- Rankings built from the same keyword index + food collection
- Used for classic text relevance comparisons against nutrition-aware ranking

### Phase 4: Demo 

**Core file:**
- `demo_baseline.py`

**Demonstrates:**
- Sample dataset creation
- Index building and keyword search
- Nutrition-aware ranking with context
- Multiple scenarios (breakfast, lunch, low-calorie)
- Explanation output and nutrient breakdowns

### Phase 5: Testing 

**Core files:**
- `tests/test_food_model.py` - Food, UserGoals, ConsumedToday
- `tests/test_ingestion_pipeline.py` - USDA parsing + inference
- `tests/test_usda_fdc_client.py` - USDA client behavior
- `tests/test_food_index.py` - Tokenization, indexes, manager search
- `tests/test_food_ranking.py` - Nutrition ranking + explanations
- `tests/test_ir_ranking.py` - TF-IDF and BM25 ranking

**Coverage highlights:**
- Data models serialization, defaults, and nutrient vectors
- USDA parsing, tag inference, meal classification
- Keyword search (OR/AND), filtering by meal and calories
- Ranking logic correctness and ordering
- IR ranking components (TF/IDF, TF-IDF, BM25)

## How to Run (Baseline)

### 1. Set up environment (baseline)
```bash
export USDA_FDC_API_KEY="your_key_here"
pip install requests beautifulsoup4 pytest
```

### 2. Run the demo (baseline)
```bash
python demo_baseline.py
```

### 3. Run tests (baseline)
```bash
pytest tests/ -v
```

### 4. Run the ingestion pipeline (baseline)
```bash
python -m src.ingest.ingest_pipeline
```

### 5. Run the nutrition ranking demo (baseline)
```bash
python -m src.query.food_ranking
```

## Key Design Decisions

### 1. Dual-Index Architecture
- **Keyword Index** for fast text search
- **Nutrient Index** for filtering + nutrition ranking
- **Rationale**: supports both IR-style retrieval and nutrition-aware scoring

### 2. Two Ranking Tracks
- **Nutrition-aware ranking** for personalized recommendations
- **Classic IR ranking** (TF-IDF, BM25) for baseline comparison at the time
- **Rationale**: separates relevance-by-text from relevance-by-nutrition

### 3. Logical View Data Models
- `Food`, `UserGoals`, `ConsumedToday` in `src/logical_view/`
- **Rationale**: clean schema boundary between data ingestion and ranking

### 4. Context-Aware Recommendations
- `RankingContext` models meal type + favorites
- **Rationale**: aligns with PRD requirements for explicit + preference context

### 5. Explainable Output
- Each recommendation includes a human-readable explanation
- **Rationale**: transparency + trust in recommendations

## Alignment with Implementation Guide (Baseline Status)

| Phase | Requirement | Status | Implementation |
|-------|-------------|--------|----------------|
| 2 | Select nutrition API | done | USDA FDC API |
| 2 | Fetch 500-1000 foods | done | `DataIngestionPipeline.fetch_usda_foods()` |
| 2 | Parse to structured format | done | `parse_usda_food()` |
| 2 | Save as CSV and JSON | done | `save_to_csv()`, `save_to_json()` |
| 3 | Define food schema | done | `Food` dataclass |
| 3 | Map nutrients | done | calories, protein, carbs, fat, fiber |
| 4 | Build keyword index | done | `KeywordIndex` |
| 4 | Build nutrient index | done | `NutrientVectorIndex` |
| 5 | Implement ranking | done | `FoodRanker` + `score_food()` |
| 5 | Nutrient gap matching | done | `calculate_remaining_targets()` |
| 5 | Context bonuses | done | meal category + favorites |
| 5 | Calorie constraints | done | overshoot penalty |
| 6 | Traditional IR baseline (Week 3) | done | `TFIDFRanker`, `BM25Ranker` |
| 7 | Define test scenarios | done | 100+ unit tests |
| 7 | Prepare demo | done | `demo_baseline.py` |

## Code Organization

```
src/
├── logical_view/
│   ├── food.py              # Food schema
│   ├── user_goals.py        # User goals schema
│   └── consumed_today.py    # Consumed nutrients schema
├── ingest/
│   ├── usda_fdc_client.py   # USDA API client
│   ├── dininghall_sources.py # UCI dining hall scraper
│   └── ingest_pipeline.py   # Unified ingestion pipeline
├── index/
│   ├── inverted_index.py    # Keyword + nutrient indexes
│   └── build_index.py       # FoodIndexManager
├── ranking/
│   ├── tfidf.py             # TF-IDF ranking
│   └── bm25.py              # BM25 ranking
├── query/
│   └── food_ranking.py      # Nutrition-aware ranking
├── utils/
│   └── io.py                # JSON read/write helpers
└── config.py                # Paths, cache, API config

tests/
├── test_food_model.py
├── test_ingestion_pipeline.py
├── test_usda_fdc_client.py
├── test_food_index.py
├── test_food_ranking.py
└── test_ir_ranking.py

demo_baseline.py             # End-to-end demo
```

## Metrics (Baseline Snapshot)

- **Python LOC (src + demo)**: 2,583
- **Python LOC (including tests)**: 4,183
- **Test Files**: 6
- **Total Tests**: 111
- **Data Sources**: 2 (USDA + UCI Dining)

## What's Not Included (Baseline Scope)

- Database persistence (beyond JSON/CSV artifacts)
- iOS app or UI layer
- ML-based personalization models
- User authentication
- Barcode scanning
- Recipe generation

## Summary

This baseline snapshot demonstrates:

1.  **Data Ingestion**: multi-source (USDA + UCI) with normalization
2.  **Indexing**: keyword + nutrient vector indexes with filtering
3.  **Ranking**: nutrition-aware scoring + IR baselines from that phase (TF-IDF/BM25)
4.  **Personalization**: goals, consumed tracking, favorites, meal context
5.  **Explainability**: human-readable reasoning per recommendation
