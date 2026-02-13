# Personalized Dining Recommendation System

## Course
CS 125 – Next Generation Search Systems (UC Irvine)

## Project Overview
This project started as a baseline search and recommendation system for dining and nutrition data. It ingests real-world food data, constructs an index over searchable fields, and supports keyword-based queries with filtering and ranking.

The baseline milestone demonstrated an end-to-end search pipeline:
raw data → logical view → index → query → ranked results.

## Data Sources
- USDA FoodData Central (FDC) API (structured nutrition data in JSON format)
- UCI dining hall menu data (HTML pages normalized into structured records)

## System Components
- Data ingestion and normalization
- Logical document representation (Food)
- Inverted index construction
- Query processing with filtering and ranking

## Repository Structure
- src/         # Core Python source code (indexing, ranking, ingestion, queries)
- data/        # Raw artifacts and legacy processed datasets
- docs/        # Design notes, plans, and checklist documentation

## Team Roles
- Bill: Data ingestion and normalization
- Shriivanth: Indexing and ranking
- Patrick: Query handling, testing, and demo
