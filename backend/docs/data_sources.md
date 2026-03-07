# Data Sources

This document describes the data sources used during the baseline phase of the Personalized Dining Recommendation System,
including their origin, access method, format, update frequency, and how they were used in that demo.

## Summary Table

| Source Name | What It Provides | Where It Comes From | Access Method | Format | Update Frequency | Fields Used | Baseline Plan |
|------------|------------------|---------------------|---------------|--------|------------------|-------------|---------------|
| USDA FoodData Central (FDC) API | Nutrition data for branded and foundation foods | https://fdc.nal.usda.gov/api-guide.html | REST API | JSON | Periodic (USDA-managed; frequency not guaranteed) | description, calories, protein, fat, carbs, fiber | Ingested a limited subset for baseline (e.g., 50–200 items) |
| UCI Dining Menus (Brandywine) | Daily menu items and availability | https://uci.mydininghub.com/en | HTML scrape | HTML → JSON | Daily | item name, meal period, dietary tags | Ingested one day of menu items |
| UCI Dining Menus (Anteatery) | Daily menu items and availability | https://uci.mydininghub.com/en | HTML scrape | HTML → JSON | Daily | item name, meal period, dietary tags | Ingested one day of menu items |

UCI dining hall data was sourced from the official UCI Dining website, which provides
daily menus for Anteatery and Brandywine. Menu data was accessed via HTML pages and
normalized into structured **Food** documents. For the baseline demo, a single day
of menu items from each dining hall was ingested.

## Normalization Plan

All data sources are normalized into a single logical document format called **Food**.
This ensures that data from different sources can be indexed and queried uniformly.

Each Food includes:
- a unique food ID
- the source of the data
- searchable text fields (name; brand if available)
- numeric nutrition metadata (calories and macros when available)
- optional contextual metadata (meal category, dietary tags)

Missing fields are allowed and handled gracefully during indexing and querying.
