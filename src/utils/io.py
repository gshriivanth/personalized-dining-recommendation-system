# src/utils/io.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union


PathLike = Union[str, Path]


def read_json(path: PathLike) -> Any:
    """
    Read JSON from disk and return the parsed Python object.

    Returns:
      - dict for JSON objects
      - list for JSON arrays
      - etc.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: PathLike, obj: Any, indent: int = 2) -> None:
    """
    Write a Python object as JSON to disk.

    Creates parent directories automatically.
    Writes UTF-8.
    Uses indent=2 for readable cached artifacts.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
