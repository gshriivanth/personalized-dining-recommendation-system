#!/usr/bin/env python3
"""
Initialize Postgres schema using docs/schema.sql.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

# Ensure backend/ is on sys.path so `src` imports resolve when running this
# script directly (e.g. `python scripts/init_db.py` from backend/).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg

from src.config import DATABASE_URL


def _iter_statements(sql: str) -> Iterator[str]:
    """Yield individual SQL statements, correctly handling:
    - $$ dollar-quote blocks (PL/pgSQL function bodies)
    - -- line comments (which may contain semicolons)
    """
    buf: list[str] = []
    in_dollar_quote = False
    i = 0
    while i < len(sql):
        # Skip -- line comments when not inside a dollar-quote block
        if not in_dollar_quote and sql[i : i + 2] == "--":
            end = sql.find("\n", i)
            if end == -1:
                break
            buf.append(sql[i : end + 1])
            i = end + 1
            continue

        if sql[i : i + 2] == "$$":
            in_dollar_quote = not in_dollar_quote
            buf.append("$$")
            i += 2
        elif sql[i] == ";" and not in_dollar_quote:
            stmt = "".join(buf).strip()
            if stmt:
                yield stmt
            buf = []
            i += 1
        else:
            buf.append(sql[i])
            i += 1
    last = "".join(buf).strip()
    if last:
        yield last


def main() -> None:
    if not DATABASE_URL:
        raise RuntimeError("Missing DATABASE_URL env var.")

    schema_path = Path(__file__).resolve().parents[1] / "docs" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            for stmt in _iter_statements(schema_sql):
                cur.execute(stmt)

    print("Schema applied successfully.")


if __name__ == "__main__":
    main()
