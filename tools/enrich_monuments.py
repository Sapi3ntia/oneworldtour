#!/usr/bin/env python3
"""
enrich_monuments.py — auto-find + vet 🏛️ monument tours, the way
enrich_media.py auto-finds walks.

WHY THIS EXISTS
    `tools/build_monuments.py` is hand-curated: a human picks the video AND
    the exact second it gets good. That produces the best tabs we have, but
    it does not scale — 30 of 362 places had monuments while 196 places
    already carried curated `highlights` naming their real landmarks
    (Château Frontenac, Lincoln Memorial, Liberty Bell, …). Those names are
    the search terms; this tool spends them.

WHAT IT LOOKS FOR
    Per landmark, ONE recorded video that is actually a clear look at that
    landmark: embeddable, public, not live, long enough to be a tour and
    short enough not to be a compilation, recent enough to look like the
    place does now, and — because the ask was "cool CLEAR footage" — ranked
    by resolution, so a 4K walk-through beats a 720p slideshow every time.

WHAT IT REFUSES (the honesty rule, same as every other scene)
    • not embeddable / not public / age-gated  → skipped
    • live                                     → that's the 🔴 seat, not this one
    • title doesn't name the landmark          → skipped
    • title anchors a different dataset city   → skipped (Paris casino
                                                 "Eiffel Tower" is Las Vegas)
    • top-10s, reactions, vlogs, documentaries, game/AI recreations → skipped
    A landmark we can't verify simply gets no tab. Never a filler video.

CURATION STILL WINS
    Auto picks are written with "source": "auto". build_monuments.py keeps
    curated entries first and preserves auto ones after them (cap 5), so the
    two tools compose instead of clobbering each other. Promote a good auto
    pick by moving it into build_monuments.py's MAP with a real `start`.

    `start` is 0 for auto picks: we can verify WHAT a video shows, but not
    WHERE it gets good — claiming a hand-picked moment we never watched
    would be the same species of lie as a fake live cam.

Checkpointed after every place, so a long run resumes cleanly.

Usage:
  python3 tools/enrich_monuments.py --max 20            # next 20 places
  python3 tools/enrich_monuments.py --only paris,cairo  # specific ids
  python3 tools/enrich_monuments.py --tag famous --max 40
  python3 tools/enrich_monuments.py --per-city 3        # cap new tabs/city
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich_media as em          # shared search + vetting (single source of truth)

ROOT = Path(__file__).resolve().parent.parent
CAP = 5                            # monument tabs per city, matches build_monuments.py
CUR_YEAR = datetime.now().year

# The whole point of a monument tab is that it looks good — a 352p clip of a
# landmark is worse than an honest empty slot, and one slipped through on
# 2026-07-18 (Irkutsk / 130 Kvartal) before this floor existed.
MIN_HEIGHT = 720

# A monument tour is a look at a THING. These titles are about something else.
BAD_MONU = re.compile(
    r"top\s*\d+|best\s*\d+|\d+\s*(?:things|places|facts)|"
    r"reaction|vlog\b|explained|documentary|full movie|podcast|"
    r"minecraft|roblox|\bgta\b|assassin'?s creed|unreal engine|"
    r"ai[\s-]generated|midjourney|animation|3d model|blender|"
    r"how to|tips|guide to|cheap|budget|scam|worst|avoid|"
    r"drone crash|accident|fire\b|collapse|protest|closed\b", re.I)

# Words that carry no identity — "the Tower of London" is identified by
# "london"+"tower", but "national"/"park" alone identify nothing.
LM_STOP = {
    "the", "of", "de", "del", "la", "le", "les", "des", "du", "el", "al",
    "and", "at", "in", "on", "national", "state", "city", "old", "new",
    "great", "grand", "royal", "central", "north", "south", "east", "west",
    "upper", "lower", "saint", "san", "santa", "mount", "monte",
}

# Landmark names that are not filmable objects — an event, a people, a
# habitat, an era. Searching these returns mood footage, not a monument.
NOT_A_MONUMENT = re.compile(
    r"^(mardi gras|carnival|oktoberfest|ramadan|diwali|hogmanay)$|"
    r"savanna|savannah$|ecosystem|habitat|biome|watershed|"
    r"^(first nations|six nations|indigenous|aboriginal)|"
    r"cuisine|gastronomy|festival|nightlife|shopping|culture$", re.I)


def lm_tokens(name):
    """Distinctive lowercase tokens of a landmark name."""
    return [w for w in re.split(r"[^a-z0-9]+", em.norm(name))
            if len(w) > 2 and w not in LM_STOP]


def mentions_landmark(title, name):
    """Strict: every distinctive token of the landmark must appear.

    "Château Frontenac" must not match a generic "Quebec City 4K" video —
    a monument tab that doesn't show the monument is exactly the kind of
    near-miss this project treats as a lie.
    """
    toks = lm_tokens(name)
    if not toks:
        return False
    t = em.norm(title)
    return all(re.search(rf"\b{re.escape(w)}", t) for w in toks)


def quality(info):
    """Rank key: clearer and newer is better. 'Cool clear footage' is the
    whole point of the monument tab, so resolution leads."""
    h = info.get("height") or 0
    if not h:
        m = re.search(r"(\d{3,4})p", info.get("resolution") or "")
        h = int(m.group(1)) if m else 0
    date = info.get("upload_date") or ""
    year = int(date[:4]) if date[:4].isdigit() else 0
    return (h, year, info.get("view_count") or 0)


def find_monument(place, name, exclude):
    """One vetted, embeddable, clear tour of `name`, or None."""
    city = place.get("name") or ""
    queries = [f"{name} {city} 4K tour", f"{name} 4K walking tour"]
    cands, seen = [], set()
    for qi, q in enumerate(queries):
        if qi:
            time.sleep(2)
        for e in em.flat_search(q, 10):
            vid, title = e.get("id"), (e.get("title") or "")
            dur = e.get("duration") or 0
            if not vid or vid in seen or vid in exclude:
                continue
            if e.get("live_status") == "is_live":
                continue
            if not (120 <= dur <= 5400):          # not a Short, not a marathon
                continue
            if BAD_MONU.search(title) or not mentions_landmark(title, name):
                continue
            if em.wrong_place_title(title, place):
                continue
            seen.add(vid)
            cands.append(e)
        if len(cands) >= 5:
            break
    if not cands:
        return None

    # full-info vet the most promising few, then keep the CLEAREST that passed
    passed = []
    for e in cands[:5]:
        info = em.full_info(e["id"])
        if not info or not em.embeddable(info) or info.get("is_live"):
            continue
        ft = info.get("title", "")
        if BAD_MONU.search(ft) or not mentions_landmark(ft, name):
            continue
        if em.wrong_place_title(ft, place):
            continue
        date = info.get("upload_date") or ""
        year = int(date[:4]) if date[:4].isdigit() else 0
        if year and year < CUR_YEAR - 8:          # monuments age slower than streets
            continue
        passed.append(info)
        if quality(info)[0] >= 2160:              # already 4K, stop paying for search
            break
    if not passed:
        return None
    best = max(passed, key=quality)
    if quality(best)[0] < MIN_HEIGHT:
        return None                                # blurry is worse than absent
    return {"name": name, "yt": best["id"], "start": 0, "source": "auto",
            "title": best.get("title", ""), "height": quality(best)[0]}


# For a CITY the city is not its own monument — "Paris 4K tour" is the walk,
# not a landmark tab. For a ruin or a named formation the site IS the thing:
# Nan Madol, Göbekli Tepe and Chichén Itzá have no sub-landmarks to list, and
# `ancient.json` averaged 0.72 scenes per place largely because of it. There,
# searching the place's own name is the correct and only move.
SELF_MONUMENT_TYPES = {"ruin", "history", "natural"}


def candidate_landmarks(loc):
    """Landmark names worth searching, best first."""
    out, seen = [], set()
    have = {em.norm(m.get("name")) for m in (loc.get("monuments") or [])}
    for h in loc.get("highlights") or []:
        name = (h.get("name") if isinstance(h, dict) else h) or ""
        name = name.strip()
        key = em.norm(name)
        if not name or key in seen or key in have:
            continue
        if key == em.norm(loc.get("name") or ""):
            continue                               # the city isn't its own monument
        if NOT_A_MONUMENT.search(name) or not lm_tokens(name):
            continue
        seen.add(key)
        out.append(name)
    if not out and (loc.get("type") or "") in SELF_MONUMENT_TYPES:
        name = (loc.get("name") or "").strip()
        if name and em.norm(name) not in have and lm_tokens(name):
            out.append(name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=10, help="places this run")
    ap.add_argument("--only", help="comma-separated place ids")
    ap.add_argument("--tag", help="only this tag (famous/hidden)")
    ap.add_argument("--per-city", type=int, default=3, help="new tabs per city")
    ap.add_argument("--refresh", action="store_true",
                    help="re-search places that already hit the cap")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else None
    media = {}
    mpath = ROOT / "data" / "media.json"
    if mpath.exists():
        media = json.load(open(mpath)).get("places", {})

    # region file → parsed json, so we write each file once per place batch
    files, places = {}, []
    for f in sorted((ROOT / "data").glob("*.json")):
        if f.name in ("index.json", "countries.json", "windy.json", "media.json"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        if not isinstance(d, dict) or "locations" not in d:
            continue
        files[f] = d
        for loc in d["locations"]:
            places.append((f, loc))

    # the wrong-place guard needs the whole gazetteer loaded
    for _, loc in places:
        c = loc.get("coordinates") or {}
        em.OTHER_PLACES[loc["id"]] = (em.name_tokens_of(loc), c.get("lat", 0), c.get("lng", 0))
        em.COUNTRY_NAMES.add(em.norm(loc.get("country") or ""))

    todo = []
    for f, loc in places:
        if only and loc["id"] not in only:
            continue
        if args.tag and loc.get("tag") != args.tag:
            continue
        if len(loc.get("monuments") or []) >= CAP and not args.refresh:
            continue
        if not candidate_landmarks(loc):
            continue
        todo.append((f, loc))
    todo = todo[: args.max]
    print(f"hunting monuments for {len(todo)} place(s)")

    added_total = 0
    for i, (f, loc) in enumerate(todo, 1):
        t0 = time.time()
        mons = list(loc.get("monuments") or [])
        room = min(CAP - len(mons), args.per_city)
        # never reuse a video this place already spends on another tab
        used = {m.get("yt") for m in mons}
        for seat in ("walk", "drive", "live", "window"):
            v = (media.get(loc["id"]) or {}).get(seat) or {}
            if v.get("yt"):
                used.add(v["yt"])

        found = []
        for name in candidate_landmarks(loc):
            if room <= 0:
                break
            hit = find_monument(loc, name, used)
            time.sleep(3)                          # polite
            if not hit:
                continue
            used.add(hit["yt"])
            # keep the height so a future sweep can audit picks by quality —
            # without it there is no way to find blurry tabs except re-querying
            mons.append({"name": hit["name"], "yt": hit["yt"],
                         "start": 0, "source": "auto", "height": hit["height"]})
            found.append(f"{hit['name']}({hit['height']}p)")
            room -= 1
            added_total += 1

        if found:
            loc["monuments"] = mons[:CAP]
            json.dump(files[f], open(f, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
        status = ", ".join(found) if found else "nothing verifiable — honest gap"
        print(f"[{i}/{len(todo)}] {loc['name']:<26} {status}  ({time.time()-t0:.0f}s)")

        if em.EMPTY_STREAK["n"] >= 8:
            print("YouTube search is refusing us — stopping so the gaps stay "
                  "honest. Re-run later; finished places are skipped.")
            break

    print(f"\ndone — {added_total} monument tab(s) added.")


if __name__ == "__main__":
    main()
