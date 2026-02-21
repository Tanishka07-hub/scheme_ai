"""
pipeline/load_to_db.py

The full pipeline in one script:
  gov_schemes_data.json
      → clean_scheme()     (your cleaner.py)
      → validate_scheme()  (your validator.py)
      → SQLite DB          (scheme_ai.db via models.py)

Run from project root:
    python pipeline/load_to_db.py
"""

import sys
import os
import json

# Let Python find database_layer/ and other packages from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_layer.cleaner   import clean_scheme
from database_layer.validator import validate_scheme
from database_layer.db        import init_db, get_db_session
from database_layer.crud      import insert_many_schemes

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "gov_schemes_data.json")


def main():
    # ── 1. Load raw scraped JSON ──────────────────────────────
    if not os.path.exists(JSON_PATH):
        print(f"❌ {JSON_PATH} not found.")
        print("   Run scraper/scrape_final_schemes.py first.")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Handle both { "schemes": [...] } and plain [...]
    schemes = raw["schemes"] if isinstance(raw, dict) and "schemes" in raw else raw
    print(f"📦 Loaded {len(schemes)} raw schemes from JSON")

    # ── 2. Clean → Validate each scheme ──────────────────────
    ready    = []   # passed cleaning + validation
    rejected = []   # failed validation

    for s in schemes:
        if s.get("error") or not s.get("scheme_name"):
            rejected.append(s.get("source_url", "unknown"))
            continue

        cleaned = clean_scheme(s)           # your cleaner.py

        if validate_scheme(cleaned):        # your validator.py
            ready.append(cleaned)
        else:
            rejected.append(cleaned.get("source_url", "unknown"))

    print(f"✅ {len(ready)} schemes passed validation")
    print(f"⚠️  {len(rejected)} schemes rejected")
    if rejected:
        for url in rejected:
            print(f"   ✗ {url}")

    if not ready:
        print("\n❌ Nothing to insert. Check your scraped data.")
        sys.exit(1)

    # ── 3. Create DB tables if needed ────────────────────────
    init_db()

    # ── 4. Insert into SQLite ─────────────────────────────────
    print(f"\n⬆️  Inserting {len(ready)} schemes into database...")
    with get_db_session() as db:
        counts = insert_many_schemes(db, ready)

    # ── 5. Report ─────────────────────────────────────────────
    print(f"\n{'='*45}")
    print(f"✅ Done!")
    print(f"   Inserted : {counts['inserted']} new schemes")
    print(f"   Updated  : {counts['updated']} existing schemes")
    print(f"   Failed   : {counts['failed']}")
    print(f"\n   DB file  : scheme_ai.db")
    print(f"   API      : http://localhost:8000/api/schemes")
    print(f"{'='*45}")


if __name__ == "__main__":
    main()
