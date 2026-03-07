# Logical View — Food Document

## What is a “document” in this system?
A single **Food** is one document. A Food represents an individual food item that
can come from USDA FoodData Central or UCI Dining menus.

This logical view defines:
- what fields exist in each document
- which fields are searchable (indexed)
- which fields are metadata (used for filtering and display)

---

## Granularity
**One document = one food item.**

Documents represent individual food items rather than entire menus or dining hall pages.
This granularity aligns with user expectations, since users search for and compare specific
foods rather than collections of foods.

---

## Food Fields

### 1. Identity and Provenance
These fields uniquely identify a document and record its source.

- `food_id` (int)  
  Unique identifier for the food item.

- `source` (string)  
  Indicates the data source (e.g., `usda_fdc`, `uci_dining_brandywine`).

- `brand` (string, optional)  
  Brand name for branded foods (USDA FDC), or dining hall name for UCI items.

---

### 2. Searchable Text Fields (Indexed)
These fields are tokenized and added to the inverted index.

- `name` (string)  
  Primary searchable field containing the food item name.

- `brand` (string, optional)  
  Included in tokenization when present.

---

### 3. Context Metadata (Filterable)
These fields provide structured context and are used for filtering and display.

- `meal_category` (string)  
  Meal category inferred from the item (`breakfast`, `lunch`, `dinner`, `snack`, `any`).

- `tags` (list of strings, optional)  
  Dietary tags such as `vegan`, `vegetarian`, or `gluten-free`.

---

### 4. Nutrition Metadata (Filterable / Ranking Features)
These numeric fields are not indexed but are used for filtering and ranking.

- `calories` (float)
- `protein` (float)
- `carbs` (float)
- `fat` (float)
- `fiber` (float)

---

## Field Usage Summary

### Indexed Fields
The inverted index is built using tokens from:
- `name`
- `brand` (when present)

### Metadata Fields
The following fields are used for filtering, ranking, and display, but are not indexed:
- `meal_category`
- `tags`
- nutrition metadata (`calories`, `protein`, `carbs`, `fat`, `fiber`)

---

## Baseline Scope Note
For the Week 3 baseline demo, a minimal subset of fields was sufficient:
- `food_id`, `source`
- `name`
- `meal_category`
- `calories` (optional)

Additional fields were planned for later iterations.
