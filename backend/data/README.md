# Data Directory

This folder stores raw and processed data artifacts from earlier milestones.

## Structure

- `raw/`
  - Raw JSON responses from the USDA FoodData Central (FDC) API
  - Raw HTML menu pages scraped from UCI Dining

- `processed/`
  - Normalized `Food` records saved as JSON/CSV (baseline-era artifacts)
  - Index artifacts from the baseline demo

## Notes

- Raw data was **not required** for the baseline demo but was useful for debugging.
- In the baseline phase, processed data was the primary input for indexing and ranking.
- The current pipeline uses database storage instead of local JSON/CSV outputs.
