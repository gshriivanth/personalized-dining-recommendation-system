# src/types.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Document:
    """
    A single indexable item in our corpus.

    For this project, a Document typically represents one food item (e.g., a USDA FDC food),
    and later may represent a dining hall menu item enriched with nutrition metadata.

    Fields:
      - doc_id: globally unique identifier for the document (e.g., "usda:123456")
      - source: where this document came from (e.g., "usda_fdc", "uci_menus")
      - name: human-readable name (e.g., "Chicken breast, roasted")
      - text: the text to index (should include name and any searchable descriptors)
      - metadata: structured extra info (nutrients, dataType, tags, etc.)
      - hall: optional, for UCI menus ("Anteatery", "Brandywine"), not used for USDA-only docs
    """
    doc_id: str
    source: str
    name: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    hall: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return asdict(self)
