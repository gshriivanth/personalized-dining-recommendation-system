# Logical View — FoodItem Document

## What is a “document” in this system?
A single **FoodItem** is one document. A FoodItem represents an individual food item that
can appear in one of UC Irvine’s dining halls (Anteatery or Brandywine) or come from
Nutritionix as a nutrition-enrichment source.

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

## FoodItem Fields

### 1. Identity and Provenance
These fields uniquely identify a document and record its source.

- `item_id` (string)  
  Unique identifier for the food item document.

- `source` (string)  
  Indicates the data source (e.g., `uci_dining`, `nutritionix`).

- `source_ref` (string, optional)  
  Original identifier or reference from the source system (e.g., URL or Nutritionix ID).

---

### 2. Searchable Text Fields (Indexed)
These fields are tokenized and added to the inverted index.

- `name` (string)  
  Primary searchable field containing the food item name.

- `description` (string, optional)  
  Additional descriptive text if available.

- `dietary_tags` (list of strings, optional)  
  Tags such as `vegan`, `vegetarian`, or `gluten_free`.  
  These may also be indexed to support queries like “vegan dinner”.

---

### 3. Dining Context Metadata (Filterable)
These fields provide structured context and are used for filtering and display.

- `dining_hall` (string, optional)  
  Name of the dining hall (e.g., `Anteatery`, `Brandywine`).

- `meal_period` (string, optional)  
  Meal during which the item is served (`Breakfast`, `Lunch`, `Dinner`).

- `date` (string or date, optional)  
  Date the menu item is available.

- `station` (string, optional)  
  Station within the dining hall where the item is served.

---

### 4. Nutrition Metadata (Filterable / Ranking Features)
These numeric fields are not indexed but are used for filtering and ranking.

- `calories` (float, optional)
- `protein_g` (float, optional)
- `carbs_g` (float, optional)
- `fat_g` (float, optional)

These fields are optional because full nutrition information may not be available for
all dining hall menu items. Nutritionix may be used to supplement missing values.

---

## Field Usage Summary

### Indexed Fields
The inverted index is built using tokens from:
- `name`
- `description` (when present)
- optionally `dietary_tags`

### Metadata Fields
The following fields are used for filtering and display, but are not indexed:
- `dining_hall`
- `meal_period`
- nutrition metadata (`calories`, `protein_g`, etc.)

---

## Team Responsibilities (Logical View)

- **Bill (Data Ingestion)**  
  Confirms which fields are reliably available from UCI Dining (CampusDish) and Nutritionix.

- **Shriivanth (Indexing & Ranking)**  
  Defines tokenization rules and indexing decisions for searchable fields.

- **Patrick (Query & Demo)**  
  Ensures the logical view supports the planned queries, filters, and baseline demo.

---

## Baseline Scope Note
For the Week 3 baseline demo, a minimal subset of fields is sufficient:
- `item_id`, `source`
- `name`
- `dining_hall`, `meal_period`
- `calories` (optional)

Additional fields can be incorporated in later project iterations.
