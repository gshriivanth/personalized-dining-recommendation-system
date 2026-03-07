# Index Plan — Week 3 Baseline (Historical)

## Purpose
This document describes what data was indexed, how it was indexed, and at what granularity
for the Week 3 baseline. The plan was written to support that demo while staying extensible.

---

## Indexing Goals
The baseline index was intended to:
- support keyword search over food items
- enable filtering using structured metadata
- allow ranking of results using TF-IDF/BM25
- avoid unnecessary indexing of numeric fields

---

## Index Granularity
**One document = one Food**

Each indexed document represents a single food item.  
Documents are not entire menus, dining halls, or days.

This granularity:
- aligns with user expectations (students search for food items)
- enables item-level ranking and filtering
- matches the logical view defined in `docs/logical_view.md`

---

## Fields Included in the Index

### Indexed (Tokenized) Fields
The following fields are tokenized and stored in the inverted index:

- `name`  
  Primary searchable field containing the food item name.

- `brand` (optional)  
  Included in tokenization when present (USDA branded foods or dining hall name).

Tokens from these fields are normalized using:
- lowercasing
- punctuation removal
- optional stopword filtering

---

### Non-Indexed Metadata Fields
The following fields are **not** indexed and are stored only as metadata:

- `meal_category`
- `tags`
- `calories`
- `protein`
- `carbs`
- `fat`
- `fiber`
- `source`

These fields are used for:
- filtering (e.g., meal category, calorie budget)
- ranking features (e.g., nutrition-aware scoring)
- result display

Numeric fields are intentionally excluded from the inverted index.

---

## Inverted Index Structure

The baseline inverted index mapped:
- **token → set of food IDs**

Example structure:
```json
{
  "chicken": [1, 42, 105],
  "vegan": [10, 18]
}
```
