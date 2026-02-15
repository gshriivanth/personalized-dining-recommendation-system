# tests/conftest.py
"""
Pytest session-level fixtures and import guards.

psycopg ships a compiled C extension.  In some environments (e.g. an x86_64
binary installed into an arm64 venv) the extension fails to load, which
prevents pytest from even collecting test modules that import anything in the
src.db or src.ingest packages.

Inserting a MagicMock for psycopg *before* any test module is imported lets
the collection phase succeed.  Tests that actually exercise database code
already mock at a higher level (patch the pipeline / client classes), so the
stub never surfaces during normal test execution.
"""
import sys
from unittest.mock import MagicMock

if "psycopg" not in sys.modules:
    sys.modules["psycopg"] = MagicMock()
