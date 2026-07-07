#!/usr/bin/env python3
"""
build_countries.py — generator for data/countries.json

The canonical country registry: the backbone of the country-first data model
(see OVERHAUL.md). Every country One World Tour covers OR plans to cover lives
here exactly once, with an ISO-3166-1 alpha-2 code, flag, continent, and a
`status`:

    live    — we already have locations for it (counted from data/*.json)
    backlog — on the world-coverage roadmap, not yet populated (COUNTRIES.md §4)

A flag emoji is derived from the ISO code (regional-indicator letters), so we
never hand-type a flag wrong. `priority` for backlog rows = the competitor's
videarth point count (a rough "how iconic / how much footage exists" signal).

Run:  python3 tools/build_countries.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

# code -> (common name, continent)
# ISO-3166-1 alpha-2. Continents are the browse axis (Continent → Country → Place).
COUNTRIES = {
    # ---- North America ----
    "US": ("United States", "North America"),
    "CA": ("Canada", "North America"),
    "MX": ("Mexico", "North America"),
    "CU": ("Cuba", "North America"),
    "CR": ("Costa Rica", "North America"),
    "BZ": ("Belize", "North America"),
    "BS": ("Bahamas", "North America"),
    # ---- South America ----
    "BR": ("Brazil", "South America"),
    "AR": ("Argentina", "South America"),
    "PE": ("Peru", "South America"),
    "CL": ("Chile", "South America"),
    "CO": ("Colombia", "South America"),
    "BO": ("Bolivia", "South America"),
    "UY": ("Uruguay", "South America"),
    "PY": ("Paraguay", "South America"),
    # ---- Europe ----
    "GB": ("United Kingdom", "Europe"),
    "FR": ("France", "Europe"),
    "DE": ("Germany", "Europe"),
    "IT": ("Italy", "Europe"),
    "ES": ("Spain", "Europe"),
    "PT": ("Portugal", "Europe"),
    "NL": ("Netherlands", "Europe"),
    "BE": ("Belgium", "Europe"),
    "AT": ("Austria", "Europe"),
    "CH": ("Switzerland", "Europe"),
    "GR": ("Greece", "Europe"),
    "IE": ("Ireland", "Europe"),
    "SE": ("Sweden", "Europe"),
    "NO": ("Norway", "Europe"),
    "FI": ("Finland", "Europe"),
    "DK": ("Denmark", "Europe"),
    "IS": ("Iceland", "Europe"),
    "PL": ("Poland", "Europe"),
    "HU": ("Hungary", "Europe"),
    "CZ": ("Czech Republic", "Europe"),
    "BG": ("Bulgaria", "Europe"),
    "CY": ("Cyprus", "Europe"),
    "EE": ("Estonia", "Europe"),
    "HR": ("Croatia", "Europe"),
    "RO": ("Romania", "Europe"),
    "ME": ("Montenegro", "Europe"),
    "BA": ("Bosnia and Herzegovina", "Europe"),
    "AL": ("Albania", "Europe"),
    "UA": ("Ukraine", "Europe"),
    "RS": ("Serbia", "Europe"),
    "LU": ("Luxembourg", "Europe"),
    "LT": ("Lithuania", "Europe"),
    "LV": ("Latvia", "Europe"),
    "MD": ("Moldova", "Europe"),
    "SK": ("Slovakia", "Europe"),
    "SI": ("Slovenia", "Europe"),
    "MT": ("Malta", "Europe"),
    "VA": ("Vatican City", "Europe"),
    "RU": ("Russia", "Europe"),  # transcontinental; filed under Europe for browse
    # ---- Asia ----
    "JP": ("Japan", "Asia"),
    "CN": ("China", "Asia"),
    "IN": ("India", "Asia"),
    "KR": ("South Korea", "Asia"),
    "TH": ("Thailand", "Asia"),
    "MY": ("Malaysia", "Asia"),
    "ID": ("Indonesia", "Asia"),
    "SG": ("Singapore", "Asia"),
    "PH": ("Philippines", "Asia"),
    "VN": ("Vietnam", "Asia"),
    "KH": ("Cambodia", "Asia"),
    "LA": ("Laos", "Asia"),
    "TW": ("Taiwan", "Asia"),
    "MN": ("Mongolia", "Asia"),
    "LK": ("Sri Lanka", "Asia"),
    "IL": ("Israel", "Asia"),
    "AE": ("United Arab Emirates", "Asia"),
    "SA": ("Saudi Arabia", "Asia"),
    "QA": ("Qatar", "Asia"),
    "JO": ("Jordan", "Asia"),
    "IR": ("Iran", "Asia"),
    "TR": ("Turkey", "Asia"),  # transcontinental; filed under Asia (matches our data)
    "AM": ("Armenia", "Asia"),
    "AZ": ("Azerbaijan", "Asia"),
    "GE": ("Georgia", "Asia"),
    # ---- Africa ----
    "MA": ("Morocco", "Africa"),
    "EG": ("Egypt", "Africa"),
    "KE": ("Kenya", "Africa"),
    "SN": ("Senegal", "Africa"),
    "ET": ("Ethiopia", "Africa"),
    "GM": ("Gambia", "Africa"),
    "ZA": ("South Africa", "Africa"),
    # ---- Oceania ----
    "AU": ("Australia", "Oceania"),
    "NZ": ("New Zealand", "Oceania"),
    "FM": ("Micronesia", "Oceania"),
}

# Competitor videarth point counts → backlog priority signal (COUNTRIES.md §2)
PRIORITY = {
    "JP": 42, "AU": 37, "RU": 33, "CN": 32, "IN": 29, "AR": 24, "TH": 18,
    "MY": 18, "KR": 11, "UA": 8, "PH": 7, "SG": 5, "IL": 5, "AE": 5, "KH": 5,
    "RS": 4, "VN": 4, "AM": 4, "VA": 3, "LT": 3, "LU": 3, "CU": 3, "CR": 3,
    "CO": 3, "MA": 3, "NZ": 3, "BO": 3, "SK": 2, "LV": 2, "MD": 2, "UY": 2,
    "IR": 2, "MN": 2, "GE": 2, "SA": 2, "KE": 2, "SN": 2, "ET": 2, "GM": 2,
    "PY": 2, "EG": 1, "BZ": 1, "AZ": 1, "JO": 1, "LA": 1, "TW": 1, "QA": 1,
    "LK": 1, "SI": 1, "ZA": 1,
}


def flag(code):
    """ISO alpha-2 -> flag emoji via regional indicator symbols."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def live_counts():
    """Count current locations per canonical country name across every region file
    registered in data/index.json (so newly-added continents count automatically)."""
    # any labels still drifting from canonical (covers pre-normalization data too)
    alias = {
        "England": "United Kingdom", "Scotland": "United Kingdom",
        "Wales": "United Kingdom", "Faroe Islands": "Denmark",
    }
    files = []
    idx = os.path.join(DATA, "index.json")
    if os.path.exists(idx):
        with open(idx, encoding="utf-8") as f:
            files = [os.path.basename(r["file"]) for r in json.load(f).get("regions", [])]
    for fn in ("canada.json", "usa.json", "europe.json", "ancient.json"):
        if fn not in files:
            files.append(fn)

    counts = {}
    for fn in files:
        path = os.path.join(DATA, fn)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        for loc in doc.get("locations", []):
            c = loc.get("country")
            if not c:
                continue
            name = alias.get(c, c)
            counts[name] = counts.get(name, 0) + 1
    return counts


def build():
    counts = live_counts()
    name_to_code = {n: c for c, (n, _) in COUNTRIES.items()}

    rows = []
    for code, (name, continent) in COUNTRIES.items():
        n = counts.get(name, 0)
        status = "live" if n > 0 else "backlog"
        row = {
            "code": code,
            "name": name,
            "flag": flag(code),
            "continent": continent,
            "status": status,
            "locations": n,
        }
        if status == "backlog":
            row["priority"] = PRIORITY.get(code, 0)
        rows.append(row)

    # live first (by count desc), then backlog (by priority desc), then name
    rows.sort(key=lambda r: (
        0 if r["status"] == "live" else 1,
        -r.get("locations", 0) if r["status"] == "live" else -r.get("priority", 0),
        r["name"],
    ))

    doc = {
        "_comment": "Canonical country registry — see OVERHAUL.md. Generated by tools/build_countries.py.",
        "continents": ["North America", "South America", "Europe", "Asia", "Africa", "Oceania"],
        "countries": rows,
    }
    dest = os.path.join(DATA, "countries.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    live = [r for r in rows if r["status"] == "live"]
    backlog = [r for r in rows if r["status"] == "backlog"]
    print(f"✓ wrote {len(rows)} countries "
          f"({len(live)} live / {len(backlog)} backlog) -> {os.path.normpath(dest)}")
    print(f"  live locations counted: {sum(r['locations'] for r in live)}")
    missing = [n for n in counts if n not in name_to_code]
    if missing:
        print(f"  ⚠ data countries not in registry: {missing}")


if __name__ == "__main__":
    build()
