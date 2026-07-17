#!/usr/bin/env python3
"""
enrich_media.py — auto-find + vet the four scenes for every place.

Uses yt-dlp's YouTube search (no API key) to hunt, per city:
  🚶 walk   — a real walking-tour video (seekable, embeddable, not live)
  🚗 drive  — a real driving-tour video (same vetting as a walk,
              windshield vantage)
  🔴 live   — a real 24/7 live cam, street/intersection vantage
  🪟 window — ALSO a real live stream, but the out-a-window vantage
              (skyline / rooftop / harbor / panorama)

OWNER RULES enforced here so the frontend never has to lie:
  • live/window must have live_status == is_live at vet time — a frozen
    or archived cam never ships.
  • everything must be playable_in_embed (no "watch on YouTube" traps).
  • can't find one? the place simply doesn't get that scene — honest gap.
  • hand-curated fields in the region JSON always outrank this sidecar
    (see js/lib/media.js), so a bad auto-pick can always be overridden.

Writes data/media.json:
  { "generated": iso, "places": { "<id>": {
      "walk":   { "yt", "title", "channel", "date", "duration" },
      "drive":  { "yt", "title", "channel", "date", "duration" },
      "live":   { "yt", "title", "verified" },
      "window": { "yt", "title", "verified" } } } }

The file is checkpointed after every city, so a long run can be
interrupted and resumed (already-done cities are skipped unless
--refresh). Runs are polite: ~1s sleep between searches.

Usage:
  python3 tools/enrich_media.py --max 12                 # next 12 unfinished
  python3 tools/enrich_media.py --only rome,paris        # specific ids
  python3 tools/enrich_media.py --tag famous --max 20    # famous cities first
  python3 tools/enrich_media.py --need walk --max 30     # only hunt walks
"""
import argparse
import glob
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "data" / "media.json"

SEARCH_N = 10
CUR_YEAR = datetime.now().year

WINDOW_WORDS = re.compile(
    r"skyline|rooftop|panoram|harbou?r|bay view|city view|aerial|"
    r"over the|from above|birds?.?eye|vista|seafront|waterfront|beach", re.I)
STREET_WORDS = re.compile(
    r"street|crossing|intersection|square|plaza|crosswalk|traffic|"
    r"downtown|walk|market|station|corner|avenue|boulevard|pedestrian", re.I)
WALK_WORDS = re.compile(r"walk|stroll|paseo|tour on foot", re.I)
BAD_WALK = re.compile(r"treadmill|virtual run|driving|drive |by car|cycling|bike", re.I)
DRIVE_WORDS = re.compile(r"driv(?:e|ing)|by car|road trip|scenic drive|dash ?cam", re.I)
BAD_DRIVE = re.compile(r"walk|stroll|treadmill|cycling|bike|train|flight|"
                       r"crash|accident|police|test drive|review", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def ytdlp_json(args, timeout=180):
    """Run yt-dlp, return list of parsed JSON lines (or [])."""
    cmd = ["yt-dlp", "--no-warnings", "-q", *args]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        lines = []
        for ln in out.stdout.splitlines():
            ln = ln.strip()
            if ln.startswith("{"):
                try:
                    lines.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
        return lines
    except (subprocess.TimeoutExpired, OSError):
        return []


# YouTube throttles sustained search bursts by returning nothing — a
# broad "X live cam" search never genuinely has zero fuzzy matches, so
# empty means throttled: back off and retry, and let the driver abort
# the run when a long streak shows we're fully blocked.
EMPTY_STREAK = {"n": 0}


def flat_search(query, n=SEARCH_N):
    for attempt in range(3):
        r = ytdlp_json(["--flat-playlist", "-j", f"ytsearch{n}:{query}"])
        if r:
            EMPTY_STREAK["n"] = 0
            return r
        EMPTY_STREAK["n"] += 1
        if attempt < 2:
            time.sleep(25 * (attempt + 1))
    return []


def full_info(video_id):
    r = ytdlp_json(["-j", f"https://www.youtube.com/watch?v={video_id}"], timeout=90)
    return r[0] if r else None


def embeddable(info):
    return bool(info) and info.get("playable_in_embed", False) \
        and info.get("age_limit", 0) == 0 \
        and info.get("availability") in (None, "public")


def scrub_namesakes(t):
    # "…Moscow time online" is a clock reference, "Little Havana" is a
    # Miami district — neither is a claim about where the feed IS.
    t = re.sub(r"\b[a-z]+\s+time\b", "", t)
    t = re.sub(r"\blittle\s+[a-z]+", "", t)
    return re.sub(r"\bporto\s+d[ei]\b", "", t)  # "Porto di Vernazza" = harbor-of, not Porto PT


def scrub_streets(t):
    # "Winston Churchill Blvd" (Mississauga) and "Churchill Square"
    # (St John's) are namesakes, not the town of Churchill. Applied to
    # name-TOKEN matching only — highlight phrases like "Times Square"
    # or "Tower Bridge" must keep matching the intact title.
    return re.sub(
        r"\b[a-z]+\s+(?:blvd|boulevard|ave|avenue|street|road|drive|"
        r"lane|court|crescent|meadows|heights|downs|square|plaza)\b", "", t)


# Native / local names — cam titles are often in the local language
# ("Roma Live Cam", "Москва", "서울"). Full-phrase inclusion only.
ALIASES = {
    "rome": ["roma"], "moscow": ["moskva", "москва"], "vienna": ["wien"],
    "prague": ["praha"], "munich": ["munchen"], "warsaw": ["warszawa"],
    "lisbon": ["lisboa"], "seville": ["sevilla"], "naples": ["napoli"],
    "florence": ["firenze"], "venice": ["venezia"], "cologne": ["koln"],
    "athens": ["athina"], "brussels": ["bruxelles", "brussel"],
    "copenhagen": ["kobenhavn"], "geneva": ["geneve"], "milan": ["milano"],
    "turin": ["torino"], "genoa": ["genova"], "seoul": ["서울"],
    "tokyo": ["東京"], "kyoto": ["京都"], "osaka": ["大阪"],
    "beijing": ["北京"], "shanghai": ["上海"], "saint-petersburg": ["санкт-петербург"],
    "kazan": ["казань"], "kyiv": ["київ", "kiev"], "bangkok": ["krung thep"],
    "havana": ["habana"], "mexico-city": ["ciudad de mexico", "cdmx"],
    "marrakesh": ["marrakech"], "fez": ["fes"],
}


def mentions_place(title, place):
    t0 = scrub_namesakes(norm(title))
    t = scrub_streets(t0)
    name_tokens = [w for w in re.split(r"[^a-z]+", norm(place["name"])) if len(w) > 3]
    if any(w in t for w in name_tokens) or norm(place["name"]) in t:
        return True
    for a in ALIASES.get(place.get("id") or "", []):
        if re.search(rf"\b{re.escape(norm(a))}\b", t0):
            return True
    # a place's own landmarks count: "Palma de Mallorca" IS the
    # Balearics, "Vernazza" IS Cinque Terre (full phrase only)
    for h in place.get("highlights") or []:
        name = norm(h.get("name") if isinstance(h, dict) else h)
        if len(name) > 3 and re.search(rf"\b{re.escape(name)}\b", t0):
            return True
    return False


# ---------------------------------------------------------- wrong-place guard
# Real picks this catches (found in the 2026-07 sweep): a Saint
# Petersburg PTZ cam sold as Moscow, LA's Venice Beach sold as Venice
# (Italy), Ghent WEST VIRGINIA sold as Ghent (Belgium), a war-news
# stream sold as Tehran's live cam. Heuristics, in order:
#   1. Titles naming another dataset place are fine if that place is
#      nearby (<300 km — Table Mountain honestly co-stars Cape Town),
#      or if OUR place is named first (the headline anchor: "Los
#      Angeles Live Cam · Venice Beach" is an LA feed).
#   2. Titles naming a different country (or, for non-US places, a US
#      state) are rejected outright.
#   3. News/war/protest streams are never "live cams".
GENERIC_TOKENS = {
    "city", "island", "islands", "beach", "coast", "coastal", "saint",
    "santa", "lake", "mount", "mountains", "national", "park", "valley",
    "falls", "river", "bay", "town", "old", "new", "great", "grand",
    "west", "east", "north", "south", "western", "eastern", "northern",
    "southern", "central", "upper", "lower", "long", "port", "little",
    "monument", "temple", "castle", "palace", "cathedral", "bridge",
}
US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
}
BAD_CAM = re.compile(
    r"\bwar\b|breaking news|news live|live news|missile|drone attack|"
    r"air ?strike|invasion|frontline|protest|\briots?\b|footage|"
    r"\bvs\.?\b|\bmatch\b|explosions?|\battacks?\b|bombing|shelling|"
    r"\.fm\b|radio station", re.I)
# news, sports and radio-station streams aren't place cams — but plain
# "radio"/"jazz radio" is just a music overlay on an otherwise real cam

OTHER_PLACES = {}     # id → (tokens, lat, lng)   — filled in main()
COUNTRY_NAMES = set() # normalized country names  — filled in main()


def name_tokens_of(place):
    toks = [w for w in re.split(r"[^a-z]+", norm(place["name"])) if len(w) > 3]
    return tuple(w for w in toks if w not in GENERIC_TOKENS)


def haversine_km(lat1, lng1, lat2, lng2):
    from math import asin, cos, radians, sin, sqrt
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def _first_pos(tokens, t):
    best = None
    for w in tokens:
        m = re.search(rf"\b{re.escape(w)}\b", t)
        if m and (best is None or m.start() < best):
            best = m.start()
    return best


def wrong_place_title(title, place):
    """True if the title anchors somewhere that isn't `place`."""
    t = scrub_namesakes(norm(title))
    own = name_tokens_of(place)
    own_pos = _first_pos(own, t)
    own_country = norm(place.get("country") or "")
    me = place.get("coordinates") or {}

    # another dataset place, fully named, far away, named before us
    for pid, (toks, lat, lng) in OTHER_PLACES.items():
        if pid == place.get("id") or not toks or set(toks) & set(own):
            continue
        pos = _first_pos(toks, t)
        if pos is None or any(not re.search(rf"\b{re.escape(w)}\b", t) for w in toks):
            continue
        if haversine_km(me.get("lat", 0), me.get("lng", 0), lat, lng) < 300:
            continue                      # neighbors co-star honestly
        if own_pos is not None and own_pos < pos:
            continue                      # our place is the headline
        return True

    # a different country by name ("new mexico" is a US state, not
    # Mexico). Exemption: if the title ALSO names our own country it's
    # a border/co-listing ("Iguazu Falls Argentina and Brazil"), not a
    # relocation.
    own_country_named = bool(own_country) and \
        re.search(rf"\b{re.escape(own_country)}\b", t)
    if not own_country_named:
        t2 = re.sub(r"\bnew mexico\b", "", t)
        for cname in COUNTRY_NAMES:
            if not cname or cname == own_country or cname in norm(place["name"]):
                continue
            if cname == "georgia" and own_country == "united states":
                continue                  # the US state, not the country
            if re.search(rf"\b{re.escape(cname)}\b", t2):
                return True

        # a US state in the title of a non-US place → a namesake town
        if own_country != "united states":
            for st in US_STATES:
                if st == own_country or st in norm(place["name"]):
                    continue
                if re.search(rf"\b{re.escape(st)}\b", t):
                    return True
    return False


# ------------------------------------------------------- walks & drives
def find_seekable(place, query, want, avoid):
    """A real, seekable tour video (walk or drive): embeddable, not
    live, recent enough that the streets still look like this."""
    cands = []
    for e in flat_search(query):
        title = e.get("title") or ""
        dur = e.get("duration") or 0
        if e.get("live_status") == "is_live":
            continue
        if not (600 <= dur <= 6 * 3600):
            continue
        if not want.search(title) or avoid.search(title):
            continue
        if not mentions_place(title, place) or wrong_place_title(title, place):
            continue
        cands.append(e)
    # try the most promising few until one passes the full vet
    for e in cands[:4]:
        info = full_info(e["id"])
        if not info or not embeddable(info) or info.get("is_live"):
            continue
        date = info.get("upload_date") or ""
        year = int(date[:4]) if date[:4].isdigit() else 0
        if year and year < CUR_YEAR - 6:
            continue          # too stale — the streets have changed
        return {
            "yt": info["id"],
            "title": info.get("title", ""),
            "channel": info.get("channel", ""),
            "date": date,
            "duration": info.get("duration", 0),
        }
    return None


def find_walk(place):
    return find_seekable(place, f"{place['name']} {place['country']} walking tour 4k",
                         WALK_WORDS, BAD_WALK)


def find_drive(place):
    return find_seekable(place, f"{place['name']} {place['country']} driving tour 4k",
                         DRIVE_WORDS, BAD_DRIVE)


# ---------------------------------------------------------------- live cams
def find_cams(place, exclude=()):
    """One search, then classify live hits into street vs window vantage.
    `exclude`: yt ids already used by this place's other seats — never
    offer the same feed twice."""
    q = f"{place['name']} live cam"
    live = []
    for e in flat_search(q, 12):
        if e.get("live_status") != "is_live" or e.get("id") in exclude:
            continue
        title = e.get("title") or ""
        if BAD_CAM.search(title):
            continue
        if not mentions_place(title, place) or wrong_place_title(title, place):
            continue
        live.append(e)

    def classify(e):
        t = e.get("title") or ""
        if WINDOW_WORDS.search(t) and not STREET_WORDS.search(t):
            return "window"
        if STREET_WORDS.search(t):
            return "street"
        return "either"

    # rank candidates per seat: clearly-classified first, 'either' after
    ranked = {"live": [], "window": []}
    for e in live:
        c = classify(e)
        if c == "street":
            ranked["live"].append(e)
        elif c == "window":
            ranked["window"].append(e)
    for e in live:
        if classify(e) == "either":
            ranked["live"].append(e)
            ranked["window"].append(e)

    # vet down each seat's list until one passes — a single un-embeddable
    # first pick must not cost the city its whole seat
    out, used, vetted = {}, set(), {}
    now = datetime.now(timezone.utc).date().isoformat()
    for seat in ("live", "window"):
        for e in ranked[seat][:5]:
            if e["id"] in used:
                continue
            if e["id"] not in vetted:
                info = full_info(e["id"])
                # the FULL title is what we store — re-run the title
                # rules on it (search snippets are often shortened)
                ft = (info or {}).get("title", "")
                ok = bool(info) and embeddable(info) and info.get("is_live") \
                    and not BAD_CAM.search(ft) \
                    and mentions_place(ft, place) and not wrong_place_title(ft, place)
                vetted[e["id"]] = info if ok else None   # live RIGHT NOW at vet time
            info = vetted[e["id"]]
            if not info:
                continue
            out[seat] = {"yt": info["id"], "title": info.get("title", ""), "verified": now}
            used.add(e["id"])
            break
    return out


# ---------------------------------------------------------------- driver
def load_places():
    places = []
    for f in sorted(glob.glob(str(ROOT / "data" / "*.json"))):
        base = Path(f).name
        if base in ("index.json", "countries.json", "windy.json", "media.json"):
            continue
        d = json.load(open(f))
        for loc in d.get("locations", []):
            loc["_region"] = base
            places.append(loc)
    return places


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=10, help="cities this run")
    ap.add_argument("--only", help="comma-separated place ids")
    ap.add_argument("--tag", help="only this tag (famous/hidden)")
    ap.add_argument("--need", choices=["walk", "drive", "live", "window", "any"], default="any")
    ap.add_argument("--refresh", action="store_true", help="redo places already in media.json")
    args = ap.parse_args()

    media = {"generated": None, "places": {}}
    if MEDIA.exists():
        media = json.load(open(MEDIA))
        media.setdefault("places", {})

    places = load_places()
    for p in places:
        c = p.get("coordinates") or {}
        OTHER_PLACES[p["id"]] = (name_tokens_of(p), c.get("lat", 0), c.get("lng", 0))
        COUNTRY_NAMES.add(norm(p.get("country") or ""))
    only = set(args.only.split(",")) if args.only else None

    def curated_has(loc, scene):
        return bool(loc.get({"walk": "walk", "drive": "drive",
                             "live": "webcam", "window": "window"}[scene]))

    def wants(loc):
        if only and loc["id"] not in only:
            return False
        if args.tag and loc.get("tag") != args.tag:
            return False
        done = media["places"].get(loc["id"], {})
        needs = []
        for scene in ("walk", "drive", "live", "window"):
            if curated_has(loc, scene) or scene in done:
                continue
            needs.append(scene)
        if args.need != "any":
            needs = [s for s in needs if s == args.need]
        loc["_needs"] = needs
        if not args.refresh and not needs:
            return False
        return True

    todo = [p for p in places if wants(p)][: args.max]
    print(f"enriching {len(todo)} places → {MEDIA}")

    for i, loc in enumerate(todo, 1):
        t0 = time.time()
        entry = media["places"].setdefault(loc["id"], {})
        found = []
        needs = loc.get("_needs") or ["walk", "drive", "live", "window"]

        if "walk" in needs:
            w = find_walk(loc)
            if w:
                entry["walk"] = w
                found.append(f"walk:{w['yt']}({w['date'][:4]})")
            time.sleep(4)
        if "drive" in needs:
            d = find_drive(loc)
            if d:
                entry["drive"] = d
                found.append(f"drive:{d['yt']}({d['date'][:4]})")
            time.sleep(4)
        if "live" in needs or "window" in needs:
            taken = {v.get("yt") for v in entry.values()
                     if isinstance(v, dict) and v.get("yt")}
            cams = find_cams(loc, exclude=taken)
            for seat in ("live", "window"):
                if seat in needs and seat in cams:
                    other = entry.get("window" if seat == "live" else "live")
                    if other and other.get("yt") == cams[seat]["yt"]:
                        continue          # never the same feed in both seats
                    entry[seat] = cams[seat]
                    found.append(f"{seat}:{cams[seat]['yt']}")
            time.sleep(4)

        if not entry:
            media["places"].pop(loc["id"], None)
        media["generated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        MEDIA.write_text(json.dumps(media, indent=1, ensure_ascii=False))
        status = ", ".join(found) if found else "nothing verifiable — honest gap"
        print(f"[{i}/{len(todo)}] {loc['name']:<24} {status}  ({time.time()-t0:.0f}s)")

        if EMPTY_STREAK["n"] >= 8:
            print("YouTube search is refusing us (8+ empty responses in a "
                  "row) — stopping so the 'gaps' stay honest. Re-run later; "
                  "the checkpoint resumes where this left off.")
            break

    print("done.")


if __name__ == "__main__":
    main()
