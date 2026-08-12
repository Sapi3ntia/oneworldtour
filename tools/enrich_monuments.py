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
    • an id in data/media_denylist.json         → skipped, globally or just
                                                 for the place it lied about
    A landmark we can't verify simply gets no tab. Never a filler video.

    The denylist is the memory this tool used to lack. A sweep in 2026-08 cut
    45 tabs that named the right landmark in the wrong hemisphere, then a
    re-run put seven of them straight back: deleting a tab also deletes it
    from `exclude`, so the search reran, found the same top hit, and told the
    same lie. Now the deletion sticks — see enrich_media.load_denylist(),
    which this shares rather than reimplements.

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
    r"drone crash|accident|fire\b|collapse|protest|closed\b|"
    # A feature film, identified by a release year in parens RIGHT AT THE FRONT
    # — "Ip Man (2008) - Foshan's masters challenge Jin". A bare "\(\d{4}\)"
    # anywhere is far too broad: uploaders stamp the upload year at the end
    # constantly, and that first draft threw out Macau's "SENADO Square Walking
    # Tour (2023)" and Pyongyang's "INSIDE Ryugyong Hotel ... (2021)", both
    # perfect tabs. Position is what separates a title from a timestamp.
    #
    # Rejecting the person instead was the other candidate and it is worse: of
    # the eight person-named tabs, six show a real site named after them — Lu
    # Xun's native place, Foshan's Yip-man museum, Tashilhunpo. A blanket rule
    # would delete six honest tabs to catch this one film.
    r"^.{0,20}\(\d{4}\)|\bfull film\b|\btrailer\b|\bost\b|"
    # a workout, not a place: "40 MIN FULL BODY TAI CHI WARM-UP AND QI GONG"
    r"workout|warm-?up|tutorial|lesson|"
    # a news package. "GLOBALink | From Russia to China, a thousands-mile
    # journey of Siberian cranes" is journalism about a migration route, and
    # the same wire gave Dalian a piece about seals instead of the Bohai Sea.
    r"globalink|\bcgtn\b|\bxinhua\b|\breuters\b|\bap archive\b|"
    # a compilation spans places by definition, so none of them is the tab
    r"compilation", re.I)

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
#
# The first four lines were written against the pre-China corpus and were far
# too narrow for it. `candidate_landmarks()` spends every `highlight` as a
# search term, and the China highlights are written for the blurbs, so they
# carry people, dishes, dynasties and species alongside actual buildings. The
# 2026-08-01 run turned each of those into a tab, and each category earned its
# line here by shipping a specific lie:
#
#   Ip Man (person)          → "Ip Man (2008) — Foshan's masters challenge Jin"
#   Manchukuo (era/state)    → "Manchukuo (1938)", archival propaganda footage
#   Tai chi (practice)       → "40 MIN FULL BODY TAI CHI WARM-UP AND QI GONG"
#   Uyghurs (a people)       → "The REAL Life of Uyghurs in China | S3, EP11"
#   Siberian crane (species) → a news package on a migration route
#   Hainanese chicken rice   → a food walk in SINGAPORE, filed under Haikou
#
# A monument tab is a look at a thing that stands somewhere. None of these
# stand anywhere, so no video of them can be the honest one.
NOT_A_MONUMENT = re.compile(
    r"^(mardi gras|carnival|oktoberfest|ramadan|diwali|hogmanay)$|"
    r"savanna|savannah$|ecosystem|habitat|biome|watershed|"
    r"^(first nations|six nations|indigenous|aboriginal)|"
    r"cuisine|gastronomy|festival|nightlife|shopping|culture$|"
    # a people, named either way round
    r"\bpeople$|^(uyghurs?|tuvans?|kazakhs?|tanka|hakka|miao|bai|tujia)$|"
    # a dish, a drink, a crop, a craft — filmable, but not in one place
    r"\b(noodles?|rice|tea|wine|beer|dumplings?|porcelain|silk|"
    r"rapeseed|dyeing|embroidery|calligraphy)$|"
    # a belief, a practice, a discipline, a text
    r"^(taoism|daoism|buddhism|confucianism|islam|shinto|tai ?chi|qi ?gong|"
    r"kung ?fu|kora|feng ?shui)$|\bsutra$|"
    # "Gandhara art" is a style; "Philadelphia Museum of Art" is a building on
    # a hill with steps, so only the bare two-word form counts as a style here.
    r"^\S+ art$|\barchitecture$|"
    # a deity is not a building, and every country that venerates one has a
    # temple to it: Leshan's "Maitreya" tab was Vihara Maitreya in Medan,
    # INDONESIA. (A person can stay — see the note in BAD_MONU.)
    r"^(maitreya|guanyin|avalokitesvara|amitabha|bodhisattva)$|"
    # an era, a dynasty, a vanished state
    r"\b(dynasty|empire|kingdom|era|period)$|^(manchukuo|manchuria|"
    r"northern wei|western xia)$|"
    # a species. "Crane" alone is a machine, so require the qualified form.
    r"\b(crane|goose|dolphin|turtle|panda|leopard|macaque|ibis|"
    r"antelope|gazelle|yak)$|"
    # a landform CLASS, not a landform: "Danxia landform" is a category that
    # Zhangye is an instance of, and the instance already has its own entry.
    r"\b(topography|landform|steppe|plateau|taiga|tundra|delta)$|"
    r"^(sea of clouds|rice terraces|stilt houses|covered corridors)$|"
    # an economic or administrative abstraction, and the trade routes, which
    # are thousands of km long and so are nowhere in particular
    r"^(special economic zone|.*\bexpo)$|"
    r"^(silk road|maritime silk road|tea horse road|karakoram highway)$",
    re.I)


# Every country / province / region any place declares — filled in main(),
# read by is_a_region(). A name in here describes an area, not a monument.
ADMIN_AREAS = set()


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
            if em.denied(place, vid):             # a human already rejected it
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


def is_a_region(loc, key):
    """True if this landmark name is an administrative area, not a thing in one.

    Filled from the corpus itself in main(), so it needs no country-specific
    list: every `country`, `province` and `region` any place declares lands in
    ADMIN_AREAS. Searching one of these gets you footage of somewhere the size
    of a country, filed under one city inside it — Langzhong's "Sichuan" tab
    was a market town near Chengdu, 250 km away, and Cuandixia's "Beijing" tab
    was a survey of hidden villages across the whole municipality.

    A place's OWN names count too: Macau's "Macau" tab is a Macau montage, not
    a monument. That costs the occasional lucky hit — Detian Falls' "Vietnam"
    tab really was the Ban Gioc/Detian border waterfall — but the falls are
    the place itself, so nothing true is lost.
    """
    if key in ADMIN_AREAS:
        return True
    own = (loc.get("country"), loc.get("province"),
           loc.get("region"), loc.get("_region"))
    return key in {em.norm(v) for v in own if v}


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
        if is_a_region(loc, key):
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
        em.register_place(loc)
        for v in (loc.get("country"), loc.get("province"),
                  loc.get("region"), loc.get("_region")):
            if v:
                ADMIN_AREAS.add(em.norm(v))

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
            # Keep the height so a future sweep can audit picks by quality, and
            # the title so it can audit them for HONESTY. find_monument() has
            # returned a title all along and this line dropped it, so the whole
            # monument set was unauditable offline: prune_media.py can re-vet a
            # media seat from disk, but the 2026-08-01 China run had to be
            # re-fetched from YouTube, 706 calls, to find out what it had shipped.
            mons.append({"name": hit["name"], "yt": hit["yt"], "start": 0,
                         "source": "auto", "title": hit.get("title", ""),
                         "height": hit["height"]})
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
