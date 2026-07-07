#!/usr/bin/env python3
"""
fetch_windy.py — build-time Windy Webcams lookup for every location.

WHY build-time: the Windy API key must never ship in client JS. We do the
`nearby` lookups here, pick the best cam per city, and bake only the public
webcam IDs into data/windy.json. At runtime the app embeds Windy's KEYLESS
public player (https://webcams.windy.com/webcams/public/embed/player/<id>/<type>),
so the key stays server-side and there's no token-expiry to manage.

For each location we record up to two cams:
  • window — the best ACTIVE cam near the city (its /day timelapse = a real,
             current "look out the window"). Fills the 🪟 Window tier.
  • live   — the best ACTIVE cam that also exposes a real /live stream, if any.
             Fills the 🔴 Live tier.
Both are chosen by: prefer in-city (<=25 km), then by viewCount (popularity ~
"this is the good, iconic view"). A cam farther than MAX_KM is treated as "no
window here" — we stay honest rather than snap to another town.

Attribution: the public embed player carries Windy's own branding; the Window
UI also shows a "cams via Windy" credit. (Windy ToS requires attribution.)

Usage:
  python3 tools/fetch_windy.py            # uses cache where present
  python3 tools/fetch_windy.py --refresh  # ignore cache, re-fetch all
Cache lives in scratchpad so re-runs during dev don't burn API quota.
"""
import json, os, sys, time, math, urllib.request, urllib.parse, urllib.error

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYF  = os.path.join(ROOT, "tools", "windy.key")
OUT   = os.path.join(ROOT, "data", "windy.json")
CACHE = "/tmp/claude-1000/-home-kali-projects-oneworldtour/1b13f396-26ed-40ae-beca-1a1ab4f221a5/scratchpad/windy_cache"
BASE  = "https://api.windy.com/webcams/api/v3/webcams"

QUERY_RADIUS_KM = 50      # how wide the API search is
MAX_KM_IN_CITY  = 25      # "this cam is in the city" threshold
MAX_KM          = 50      # beyond this we record nothing (honest "no window")
REFRESH = "--refresh" in sys.argv

with open(KEYF) as f:
    KEY = f.read().strip()
os.makedirs(CACHE, exist_ok=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def nearby(lat, lng):
    """Cached Windy nearby lookup → list of webcam dicts."""
    cf = os.path.join(CACHE, f"{lat:.4f}_{lng:.4f}.json")
    if not REFRESH and os.path.exists(cf):
        with open(cf) as f:
            return json.load(f).get("webcams", [])
    qs = urllib.parse.urlencode({
        "nearby": f"{lat},{lng},{QUERY_RADIUS_KM}", "limit": 25,
        "include": "player,location,categories",
    })
    for attempt in range(3):
        try:
            req = urllib.request.Request(BASE + "?" + qs, headers={"x-windy-api-key": KEY})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
            with open(cf, "w") as f:
                json.dump(data, f)
            time.sleep(0.12)                       # be polite to the API
            return data.get("webcams", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:                      # rate-limited → back off
                time.sleep(2 + attempt * 2); continue
            raise
    return []

def best(cams, city_lat, city_lng, require_live=False):
    """Pick the best cam: in-city first (<=25km), then by viewCount."""
    cand = []
    for c in cams:
        if c.get("status") != "active":
            continue
        loc = c.get("location") or {}
        clat, clng = loc.get("latitude"), loc.get("longitude")
        if clat is None or clng is None:
            continue
        if require_live and "live" not in (c.get("player") or {}):
            continue
        km = haversine(city_lat, city_lng, clat, clng)
        if km > MAX_KM:
            continue
        cand.append((km, c))
    if not cand:
        return None
    in_city = [x for x in cand if x[0] <= MAX_KM_IN_CITY]
    pool = in_city or cand
    km, c = max(pool, key=lambda x: x[1].get("viewCount", 0))
    return {"id": str(c["webcamId"]), "title": c.get("title") or "", "km": round(km),
            "views": c.get("viewCount", 0)}

def load_locations():
    idx = json.load(open(os.path.join(ROOT, "data", "index.json")))
    locs = []
    for region in idx["regions"]:
        if not region.get("enabled"):
            continue
        path = os.path.join(ROOT, "data", os.path.basename(region["file"])) \
               if not region["file"].startswith("data/") else os.path.join(ROOT, region["file"])
        try:
            rj = json.load(open(path))
        except FileNotFoundError:
            print("  ! missing region file:", region["file"]); continue
        for l in rj.get("locations", []):
            co = l.get("coordinates") or {}
            if co.get("lat") is None or co.get("lng") is None:
                continue
            locs.append((l["id"], l.get("name", l["id"]), co["lat"], co["lng"]))
    return locs

def main():
    locs = load_locations()
    print(f"locations: {len(locs)}  (refresh={REFRESH})")
    out = {}
    n_win = n_live = n_empty = n_err = 0
    for i, (lid, name, lat, lng) in enumerate(locs):
        try:
            cams = nearby(lat, lng)
        except Exception as e:
            n_err += 1; print(f"  ERR {name}: {str(e)[:80]}"); continue
        win  = best(cams, lat, lng, require_live=False)
        live = best(cams, lat, lng, require_live=True)
        if not win and not live:
            n_empty += 1; continue
        entry = {}
        if win:  entry["window"] = win["id"]; entry["title"] = win["title"]; entry["km"] = win["km"]
        if live: entry["live"]   = live["id"]
        if win:  n_win += 1
        if live: n_live += 1
        out[lid] = entry
        if (i + 1) % 50 == 0:
            print(f"  ...{i+1}/{len(locs)}  windows={n_win} live={n_live} empty={n_empty}")
    out = dict(sorted(out.items()))
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=0, separators=(",", ":"))
    print(f"\nWROTE {OUT}")
    print(f"  cities with a window: {n_win}/{len(locs)}")
    print(f"  cities with a LIVE stream: {n_live}")
    print(f"  no cam within {MAX_KM}km: {n_empty}   errors: {n_err}")

if __name__ == "__main__":
    main()
