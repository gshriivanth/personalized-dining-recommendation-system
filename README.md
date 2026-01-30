# Personalized Dining Recommendation System

## Course
CS 125 – Next Generation Search Systems (UC Irvine)

## Project Overview
This project implements a baseline search and recommendation system for dining and nutrition data. The system ingests real-world food data, constructs an index over searchable fields, and supports keyword-based queries with filtering and ranking.

The goal of the baseline milestone is to demonstrate an end-to-end search pipeline:
raw data → logical view → index → query → ranked results.

## Data Sources
- Nutritionix API (structured nutrition data in JSON format)
- Dining hall menu data (HTML pages normalized into structured records)

## System Components
- Data ingestion and normalization
- Logical document representation (food items)
- Inverted index construction
- Query processing with filtering and ranking

## Repository Structure
- notebooks/   # Optional demos or experiments (not required for final system)
- src/         # Core Python source code (indexing, ranking, ingestion, queries)
- data/        # Raw and processed datasets
- docs/        # Design notes, plans, and checklist documentation

## Team Roles
- Bill: Data ingestion and normalization
- Shriivanth: Indexing and ranking
- Patrick: Query handling, testing, and demo
