#!/usr/bin/env python3
"""
normalize_countries.py — in-place country normalization for data/*.json

Fixes the data-hygiene issues logged in OVERHAUL.md §4 and brings every existing
location in line with the country-first model (data/countries.json):

  I-1  England / Scotland / Wales / Northern Ireland  ->  country "United Kingdom",
       the constituent country preserved as `region` (so London/Edinburgh/Liverpool
       all roll up to one UK).
  I-4  Faroe Islands  ->  country "Denmark", region "Faroe Islands" (it's a Danish
       territory; we keep the pin, count it honestly).
  I-2  Every location gains `country_code` (ISO-3166-1 alpha-2) and `continent`,
       and its `country_flag` is set from the canonical registry (never mistyped).

Operates on the LIVE JSON in place (the build_*.py generators are one-off and now
stale — ambient entries etc. were hand-added since). Idempotent: safe to re-run.

Run:  python3 tools/normalize_countries.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
FILES = ("canada.json", "usa.json", "europe.json", "ancient.json")

# constituent country / territory  ->  (sovereign country, sub-region label)
FOLD = {
    "England": ("United Kingdom", "England"),
    "Scotland": ("United Kingdom", "Scotland"),
    "Wales": ("United Kingdom", "Wales"),
    "Northern Ireland": ("United Kingdom", "Northern Ireland"),
    "Faroe Islands": ("Denmark", "Faroe Islands"),
}


def load_registry():
    with open(os.path.join(DATA, "countries.json"), encoding="utf-8") as f:
        reg = json.load(f)
    by_name = {c["name"]: c for c in reg["countries"]}
    return by_name


def normalize():
    reg = load_registry()
    total, folded, coded, warnings = 0, 0, 0, []

    for fn in FILES:
        path = os.path.join(DATA, fn)
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)

        for loc in doc.get("locations", []):
            total += 1
            country = loc.get("country")
            if not country:
                warnings.append(f"{fn}:{loc.get('id')} has no country")
                continue

            # I-1 / I-4 — fold constituents & territories into the sovereign state
            if country in FOLD:
                sov, sub = FOLD[country]
                if not loc.get("region"):
                    loc["region"] = sub
                loc["country"] = sov
                country = sov
                folded += 1

            # I-2 — stamp code + continent + canonical flag
            meta = reg.get(country)
            if not meta:
                warnings.append(f"{fn}:{loc.get('id')} country '{country}' not in registry")
                continue
            loc["country_code"] = meta["code"]
            loc["continent"] = meta["continent"]
            loc["country_flag"] = meta["flag"]
            coded += 1

        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"  ✓ {fn}: {len(doc.get('locations', []))} locations")

    print(f"\n✓ normalized {total} locations: {folded} folded to sovereign country, "
          f"{coded} stamped with code+continent+flag")
    if warnings:
        print("⚠ warnings:")
        for w in warnings:
            print("   -", w)
    else:
        print("  no warnings — every location maps to the registry.")


if __name__ == "__main__":
    normalize()
