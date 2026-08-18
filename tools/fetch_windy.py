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
import json, os, re, sys, time, math, urllib.request, urllib.parse, urllib.error

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYF  = os.path.join(ROOT, "tools", "windy.key")
OUT   = os.path.join(ROOT, "data", "windy.json")
OVRF  = os.path.join(ROOT, "tools", "windy_overrides.json")
CACHE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "owt_windy_cache")
BASE  = "https://api.windy.com/webcams/api/v3/webcams"

# The 2026-07-07 audit found "nearest active cam" happily picks airport,
# highway-milepost, traffic and sky cams. Never accept these as a window.
JUNK_TITLE = re.compile(
    r"\b(sky|MP \d|milepost|US \d|I-\d+|SR-\d|SH ?\d+|Hwy|traffic|junction|airport|"
    r"airfield|windsock|toll)\b",
    re.I)

# The word list above misses the way Australasian aviation cams name themselves:
# by ICAO code and compass bearing, never by the word "airport" — "Broken Hill -
# YBHI -> Facing East", "Ballarat - YBLT -> SW", "AYMH - Mt Hagen -> Facing
# North". The Oceania batch pulled nine of them in as windows before this
# existed. Australia is Y+3, New Zealand NZ+2, Papua New Guinea AY+2, and the
# case matters: under re.I, Y[A-Z]{3} also eats "your", "yard" and "Yarra".
# Every four-letter capital token in a 887-cam Australasian sample was one of
# these codes, so the pattern is tight rather than lucky.
JUNK_CODE = re.compile(r"\b(?:Y[A-Z]{3}|NZ[A-Z]{2}|AY[A-Z]{2})\b")

QUERY_RADIUS_KM = 50      # how wide the API search is
MAX_KM_IN_CITY  = 25      # "this cam is in the city" threshold
MAX_KM          = 50      # beyond this we record nothing (honest "no window")
REFRESH = "--refresh" in sys.argv

def _only_arg():
    """--only id,id,id — look up just these places, keep everything else."""
    if "--only" not in sys.argv:
        return None
    i = sys.argv.index("--only")
    if i + 1 >= len(sys.argv):
        sys.exit("--only needs a comma-separated list of place ids")
    return {x for x in sys.argv[i + 1].replace(" ", ",").split(",") if x}

ONLY = _only_arg()

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
        title = c.get("title") or ""
        if JUNK_TITLE.search(title) or JUNK_CODE.search(title):
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
    # Start from what we already shipped, don't start from nothing. This
    # script used to build `out` empty and write it wholesale, so ANY place
    # whose lookup raised — one rate-limited afternoon, one network blip —
    # silently vanished from data/windy.json along with its verified cam.
    # A run can now only ADD a cam, REPLACE one, or drop one it actually
    # re-checked and found gone.
    try:
        out = json.load(open(OUT))
    except (FileNotFoundError, json.JSONDecodeError):
        out = {}
    prev = dict(out)
    if ONLY:
        ghosts = ONLY - {l[0] for l in locs}
        if ghosts:
            print(f"  warning: {len(ghosts)} id(s) in --only are on no map: "
                  f"{', '.join(sorted(ghosts))}")
        locs = [l for l in locs if l[0] in ONLY]
    print(f"locations: {len(locs)}  (refresh={REFRESH}"
          f"{', --only' if ONLY else ''}, {len(prev)} already on file)")
    n_win = n_live = n_empty = n_err = n_lost = 0
    for i, (lid, name, lat, lng) in enumerate(locs):
        try:
            cams = nearby(lat, lng)
        except Exception as e:
            n_err += 1
            print(f"  ERR {name}: {str(e)[:80]}"
                  f"{'  (keeping the cam already on file)' if lid in prev else ''}")
            continue
        win  = best(cams, lat, lng, require_live=False)
        live = best(cams, lat, lng, require_live=True)
        if not win and not live:
            n_empty += 1
            # Re-checked and genuinely empty: this one really does go.
            if out.pop(lid, None):
                n_lost += 1
                print(f"  drop {name}: nothing acceptable within {MAX_KM} km "
                      f"any more — the cam we had is gone or now filtered")
            continue
        entry = {}
        if win:  entry["window"] = win["id"]; entry["title"] = win["title"]; entry["km"] = win["km"]
        if live: entry["live"]   = live["id"]
        if win:  n_win += 1
        if live: n_live += 1
        out[lid] = entry
        if (i + 1) % 50 == 0:
            print(f"  ...{i+1}/{len(locs)}  windows={n_win} live={n_live} empty={n_empty}")
    # Hand-audited verdicts (wrong-place / junk cams) always win over the
    # automatic match — see tools/windy_overrides.json and prune_windy.py.
    try:
        from prune_windy import apply_overrides
        ovr = json.load(open(OVRF))
        out, stats = apply_overrides(out, ovr)
        print(f"  overrides: dropped {stats['entry']} entries, "
              f"{stats['live']} live tiers, {stats['window']} window tiers")
    except FileNotFoundError:
        pass
    out = dict(sorted(out.items()))
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=0, separators=(",", ":"))
    print(f"\nWROTE {OUT}")
    print(f"  entries on file: {len(out)}  (was {len(prev)}, "
          f"{len(set(out) - set(prev))} new, {n_lost} dropped as gone)")
    print(f"  cities with a window: {n_win}/{len(locs)}")
    print(f"  cities with a LIVE stream: {n_live}")
    print(f"  no cam within {MAX_KM}km: {n_empty}   errors: {n_err}")

if __name__ == "__main__":
    main()
