# Index Plan — Week 3 Baseline

## Purpose
This document describes what data is indexed, how it is indexed, and at what granularity
for the Personalized Dining Recommendation System. The index plan is designed to support
the Week 3 baseline demo while remaining extensible for future iterations.

---

## Indexing Goals
The baseline index should:
- support keyword search over food items
- enable filtering using structured metadata
- allow ranking of results using TF-IDF
- avoid unnecessary indexing of numeric fields

---

## Index Granularity
**One document = one FoodItem**

Each indexed document represents a single food item.  
Documents are not entire menus, dining halls, or days.

This granularity:
- aligns with user expectations (students search for food items)
- enables item-level ranking and filtering
- matches the logical view defined in `logical_view.md`

---

## Fields Included in the Index

### Indexed (Tokenized) Fields
The following fields are tokenized and stored in the inverted index:

- `name`  
  Primary searchable field containing the food item name.

- `description` (optional)  
  Secondary searchable text when available.

- `dietary_tags` (optional)  
  Categorical tags such as `vegan`, `vegetarian`, or `gluten_free`.  
  These are indexed as tokens to support queries like “vegan dinner”.

Tokens from these fields are normalized using:
- lowercasing
- punctuation removal
- optional stopword filtering

---

### Non-Indexed Metadata Fields
The following fields are **not** indexed and are stored only as metadata:

- `dining_hall`
- `meal_period`
- `date`
- `station`
- `calories`
- `protein_g`
- `carbs_g`
- `fat_g`
- `source`
- `source_ref`

These fields are used for:
- filtering (e.g., calorie range, dining hall)
- ranking features (e.g., protein-based ranking later)
- result display

Numeric fields are intentionally excluded from the inverted index.

---

## Inverted Index Structure

The baseline inverted index maps:


Each posting contains:
- `item_id` (document identifier)
- `term_frequency` (number of times the token appears in the document)

Example structure:
```json
{
  "chicken": [
    ["anteatery_dinner_001", 1],
    ["nutritionix_042", 2]
  ],
  "vegan": [
    ["brandywine_lunch_010", 1]
  ]
}
