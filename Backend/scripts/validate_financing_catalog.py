"""Validate a proposed financing snapshot without fetching, publishing or writing.

Run from Backend: python scripts/validate_financing_catalog.py [proposal.json]
Only a human-reviewed file should replace app/data/financing_catalog_v2.json.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError

from app.services.financing_workspace import load_catalogue, source_review_due
from app.db import pkt_today


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        catalogue = load_catalogue(args.path)
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Catalogue rejected: {type(exc).__name__}. Review the local file against /api/financing/catalog/schema.")
        return 1
    due = source_review_due(catalogue, pkt_today())
    print(f"Valid schema v{catalogue.schema_version}: {catalogue.version}, {len(catalogue.programs)} programs.")
    print("Source review: " + ("DUE — do not claim these terms are current." if due else "within the configured review window; not a live lender feed."))
    print("No file was changed and nothing was published. Human source verification is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
