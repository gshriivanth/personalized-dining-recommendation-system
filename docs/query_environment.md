# Query Environment — Week 3 Baseline (Historical)

## Overview
The query environment described how users issued queries, what context was available at query time,
and whether the system supported standing/subscription queries during the Week 3 baseline. The primary
users were **UC Irvine students** searching for food items served at **Anteatery** and **Brandywine**.

---

## Query Types Supported

### 1) Typed Queries (Primary)
Users enter a text query (keywords) representing what they want to find.

Examples:
- `chicken bowl`
- `vegan`
- `high protein`
- `salad`

Behavior:
- The query string is tokenized using the same normalization rules as indexing
- Matching Food documents are retrieved via the inverted index
- Results are ranked (baseline: TF-IDF/BM25 or nutrition-aware ranking)

---

### 2) Context Queries (Filters + Constraints)
In addition to typed keywords, users often have contextual constraints that narrow results.

Baseline context filters (supported in Week 3) included:
- `meal_category`: `breakfast`, `lunch`, `dinner`, `snack`, `any`
- nutrition constraints (metadata filters), such as:
  - calorie range (e.g., 200–600 calories)
  - minimum protein (optional extension)

Examples:
- Query: `burrito` + filter `meal_category=lunch`
- Query: `vegan` + filter `meal_category=dinner`
- Query: `chicken` + filter `calories <= 600`

Behavior:
- Retrieve candidates using the inverted index (keyword match)
- Apply metadata filters (context) to the candidate set
- Rank the remaining results and return top K

---

### 3) Subscription / Standing Queries (Future Scope)
A subscription (standing) query is a saved query that the system runs repeatedly over time
(e.g., daily menu updates) and notifies the user when new matches appear.

Example standing queries (future iteration):
- “Notify me when **vegan dinner** appears at **Brandywine**”
- “Alert me when a meal under **500 calories** is available at **Anteatery**”

Baseline scope note:
- Subscription queries were **not implemented** in the Week 3 baseline demo
- The system was designed so they could be added later once menu ingestion updated daily

---

## Output Format (Baseline Demo)
For each query, the system returned a ranked list of Food results with:
- food name
- key nutrition facts (when available)
- relevance score (TF-IDF/BM25) or nutrition score

---

## Example Query Scenarios for the Baseline Demo
1. Typed only: `chicken bowl`
2. Typed + context: `vegan` with `meal_category=lunch`
3. Typed + nutrition filter: `burrito` with `200 <= calories <= 600`
