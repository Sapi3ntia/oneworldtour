#!/usr/bin/env python3
"""One-off audit: fetch real title/km for LIVE cam ids in data/windy.json.

data/windy.json stores title/km for the WINDOW cam only; the live cam id is
bare. To judge live-tier relevance (the 2026-07-07 slideshow/wrong-cam review)
we re-query the nearby list per place and look the live id up. Read-only:
prints a table, writes nothing. Key comes from tools/windy.key (gitignored) —
never printed.
"""
import json, math, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = open(os.path.join(ROOT, "tools", "windy.key")).read().strip()
BASE = "https://api.windy.com/webcams/api/v3/webcams"
RADIUS_KM = 50

def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def nearby(lat, lng):
    qs = urllib.parse.urlencode({
        "nearby": f"{lat},{lng},{RADIUS_KM}", "limit": 50,
        "include": "player,location,categories",
    })
    for attempt in range(3):
        try:
            req = urllib.request.Request(BASE + "?" + qs, headers={"x-windy-api-key": KEY})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
            time.sleep(0.15)
            return data.get("webcams", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + attempt * 2); continue
            raise
    return []

def main():
    windy = json.load(open(os.path.join(ROOT, "data", "windy.json")))
    locs = {}
    idx = json.load(open(os.path.join(ROOT, "data", "index.json")))
    for region in idx["regions"]:
        if not region.get("enabled"):
            continue
        path = os.path.join(ROOT, region["file"]) if region["file"].startswith("data/") \
               else os.path.join(ROOT, "data", os.path.basename(region["file"]))
        for l in json.load(open(path)).get("locations", []):
            locs[l["id"]] = l

    targets = [(lid, w) for lid, w in sorted(windy.items())
               if w.get("live") and w["live"] != w.get("window")]
    print(f"auditing {len(targets)} entries with a distinct live cam...", file=sys.stderr)
    rows = []
    for i, (lid, w) in enumerate(targets):
        l = locs.get(lid)
        if not l:
            continue
        lat, lng = l["coordinates"]["lat"], l["coordinates"]["lng"]
        try:
            cams = nearby(lat, lng)
        except Exception as e:
            rows.append((lid, l["name"], -1, f"ERR {str(e)[:60]}")); continue
        hit = next((c for c in cams if str(c.get("webcamId")) == w["live"]), None)
        if not hit:
            rows.append((lid, l["name"], -1, "live cam id no longer in nearby list"))
        else:
            loc = hit.get("location") or {}
            km = round(haversine(lat, lng, loc.get("latitude"), loc.get("longitude")))
            rows.append((lid, l["name"], km, hit.get("title") or ""))
        if (i + 1) % 20 == 0:
            print(f"  ...{i+1}/{len(targets)}", file=sys.stderr)
    print(json.dumps(rows, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
