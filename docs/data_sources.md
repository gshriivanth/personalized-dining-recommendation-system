# Data Sources

This document describes all data sources used in the Personalized Dining Recommendation System,
including their origin, access method, format, and how they are used in the baseline demo.

## Summary Table

| Source Name | What It Provides | Where It Comes From | Access Method | Format | Fields Used | Baseline Plan |
|------------|-----------------|---------------------|---------------|--------|-------------|----------------|
| USDA FoodData Central API | Official nutrition data for foods (raw, branded, prepared) | https://fdc.nal.usda.gov/api-guide.html | REST API | JSON | description, calories, protein, fat, carbs | Ingest ~100 food items |
| UCI Dining Menus (Anteatery) | Daily menu items and availability | https://uci.campusdish.com/ | HTML scrape / manual export | HTML → JSON | item name, meal, dietary tags | Ingest one day of menu items |
| UCI Dining Menus (Brandywine) | Daily menu items and availability | https://uci.campusdish.com/ | HTML scrape / manual export | HTML → JSON | item name, meal, dietary tags | Ingest one day of menu items |

UCI dining hall data is sourced from the official UCI Dining website, which provides
daily menus for Anteatery and Brandywine. Menu data is accessed via HTML pages and
normalized into structured FoodItem documents. For the baseline demo, a single day
of menu items from each dining hall is ingested. Nutrition data is supplemented using
Nutritionix when full nutritional information is not available directly from UCI Dining.


## Normalization Plan

All data sources are normalized into a single logical document format called **FoodItem**.
This ensures that data from different sources can be indexed and queried uniformly.

Each FoodItem includes:
- a unique item ID
- the source of the data
- searchable text fields (name, optional description)
- numeric nutrition metadata (calories and macros when available)
- optional contextual metadata (dining hall, meal type)

Missing fields are allowed and handled gracefully during indexing and querying.
