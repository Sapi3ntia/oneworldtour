#!/usr/bin/env python3
"""
check_trips.py — verify every curated trip stop resolves to a real place.

WHY THIS EXISTS
    data/trips.json is hand-written, and a stop is just an id string. A
    typo ("st-louis" vs "saint-louis") produces a route that silently
    skips a city — the trip still renders, still looks fine, and quietly
    lies about where it goes. That is the same failure mode as a fake
    live cam, so it gets the same treatment: caught at build time, never
    shipped.

It also reports what each trip actually has to show, because a trip whose
stops are all empty seats is technically valid and practically useless.

Usage:
  python3 tools/check_trips.py           # exits 1 if any stop is unknown
  python3 tools/check_trips.py --scenes  # + per-trip scene inventory
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"index.json", "countries.json", "windy.json", "media.json",
        "trips.json", "tv.json"}


def load_places():
    out = {}
    for f in sorted((ROOT / "data").glob("*.json")):
        if f.name in SKIP:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or "locations" not in d:
            continue
        for loc in d["locations"]:
            out[loc["id"]] = loc
    return out


def km(a, b):
    """Great-circle distance, same haversine as js/lib/geo.js."""
    if not a or not b:
        return 0
    r = 6371
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lng"] - a["lng"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(h)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", action="store_true",
                    help="also report what each trip can actually show")
    args = ap.parse_args()

    places = load_places()
    media = json.loads((ROOT / "data" / "media.json").read_text())["places"]
    trips = json.loads((ROOT / "data" / "trips.json").read_text(encoding="utf-8"))["trips"]

    bad, seen_ids = [], set()
    for t in trips:
        if t["id"] in seen_ids:
            bad.append(f"{t['id']}: duplicate trip id")
        seen_ids.add(t["id"])
        stop_ids = [s["id"] for s in t["stops"]]
        for sid in stop_ids:
            if sid not in places:
                bad.append(f"{t['id']}: unknown place id '{sid}'")
        if len(set(stop_ids)) != len(stop_ids):
            dupes = {s for s in stop_ids if stop_ids.count(s) > 1}
            bad.append(f"{t['id']}: repeated stop(s) {sorted(dupes)}")
        if len(stop_ids) < 3:
            bad.append(f"{t['id']}: only {len(stop_ids)} stop(s) — not a route")

    for t in trips:
        stops = [places[s["id"]] for s in t["stops"] if s["id"] in places]
        dist = sum(km(stops[i].get("coordinates"), stops[i + 1].get("coordinates"))
                   for i in range(len(stops) - 1))
        line = f"{t['emoji']} {t['name']:<26} {len(stops):>2} stops  {dist:>6,} km"
        if args.scenes:
            n = {k: 0 for k in ("walk", "drive", "live", "window", "monuments")}
            for p in stops:
                m = media.get(p["id"], {})
                n["walk"] += bool(p.get("walk") or m.get("walk"))
                n["drive"] += bool(p.get("drive") or m.get("drive"))
                n["live"] += bool(p.get("webcam") or m.get("live"))
                n["window"] += bool(p.get("window") or m.get("window"))
                n["monuments"] += bool(p.get("monuments"))
            line += ("   🚶{walk} 🚗{drive} 🔴{live} 🪟{window} 🏛️{monuments}"
                     .format(**n))
        print(line)

    if bad:
        print("\nBROKEN:", file=sys.stderr)
        for b in bad:
            print("  " + b, file=sys.stderr)
        sys.exit(1)
    print(f"\n{len(trips)} trip(s), every stop resolves.")


if __name__ == "__main__":
    main()
