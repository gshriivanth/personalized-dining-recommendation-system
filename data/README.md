# Data Directory

This folder stores raw and processed data artifacts.

## Structure

- `raw/`
  - Raw JSON responses from the USDA FoodData Central (FDC) API
  - Raw HTML menu pages scraped from UCI Dining

- `processed/`
  - Normalized `Food` records saved as JSON/CSV
  - Index artifacts for the baseline demo

## Notes

- Raw data is **not required** for the baseline demo but is useful for debugging.
- Processed data is the primary input for indexing and ranking.
