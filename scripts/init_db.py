#!/usr/bin/env python3
"""
Initialize Postgres schema using docs/schema.sql.
"""
from __future__ import annotations

from pathlib import Path

import psycopg

from src.config import DATABASE_URL


def main() -> None:
    if not DATABASE_URL:
        raise RuntimeError("Missing DATABASE_URL env var.")

    schema_path = Path(__file__).resolve().parents[1] / "docs" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)

    print("Schema applied successfully.")


if __name__ == "__main__":
    main()
