#!/usr/bin/env python3
"""
build_monuments.py — attach up to 5 named monument/landmark tours to cities.

Monuments are a SEPARATE category from the walking tour and the (live) window.
Each is a real, recorded YouTube video of a specific landmark, seeked to a good
moment. Source: harvested from virtualvacation.us/monument (a flat anonymous list
of `ytid?start=ss`), then identified by its real YouTube oEmbed title and given a
clean monument name here — we expand their base into NAMED, per-city sets.

Every id below was confirmed public via keyless YouTube oEmbed (200 + title).
oEmbed proves the upload exists and is public, NOT that it allows embedding —
that is enforced at runtime by js/ytembed.js, which detects an onError (embed
disabled / removed / private) and shows an honest "no longer available" state.
Re-vet over time with the same oEmbed check; a 401/404 means the upload was
pulled. LatAm/Africa capital monuments added 2026-07-04 (WebSearch -> oEmbed).
2026-07-17 batch (NYC, Kremlin, SF ×3, Trevi, Sydney, Rio ×3, Santorini,
Gateway Arch) vetted the stronger way: yt-dlp full-info with
playable_in_embed + public + not-live, same bar as enrich_media.py.

Idempotent: rewrites each location's `monuments` array to exactly MAP[id].
Run from the project root:  /usr/bin/python3 tools/build_monuments.py
"""
import json, glob, os, sys

# location id -> [ {name, yt, start} ]  (cap 5; ordered most-iconic first)
MAP = {
    # ---- Europe ----
    "paris": [
        {"name": "Eiffel Tower",     "yt": "wqpOqalkRVE", "start": 438},
        {"name": "The Louvre",       "yt": "9hDEJK-zzUk", "start": 22},
        {"name": "Arc de Triomphe",  "yt": "buOobuqZ5RU", "start": 15},
    ],
    "rome": [
        {"name": "Colosseum",          "yt": "VtzDzVGSMLU", "start": 204},
        {"name": "Pantheon",           "yt": "tsnk3ruKUsY", "start": 1},
        {"name": "St Peter's Basilica","yt": "2M7Avt39oF4", "start": 1},
        {"name": "Trevi Fountain",     "yt": "Ky4pQ0kJxUE", "start": 0},
    ],
    "berlin": [
        {"name": "Brandenburg Gate", "yt": "CP5Q5JG2jU8", "start": 15},
        {"name": "Reichstag",        "yt": "GSCbzHvrmjE", "start": 32},
    ],
    "london": [
        {"name": "Big Ben & London Eye", "yt": "aBOsIVU9mms", "start": 824},
    ],
    "barcelona": [
        {"name": "Sagrada Família", "yt": "bJlUA-lnvYg", "start": 379},
    ],
    "moscow": [
        {"name": "Red Square",  "yt": "CxXjIv7rDig", "start": 565},
        {"name": "The Kremlin", "yt": "hSuy58oamGA", "start": 0},
    ],
    "cinque-terre": [
        {"name": "Manarola", "yt": "yB5HFvXchfM", "start": 545},
    ],
    "cyclades": [
        {"name": "Santorini (Oia)", "yt": "g8pID6lhThY", "start": 0},
    ],
    # ---- North America ----
    "new-york-city": [
        {"name": "Times Square",      "yt": "csMnb-8BoE8", "start": 0},
        {"name": "Statue of Liberty", "yt": "wJDes04sYMA", "start": 0},
    ],
    "san-francisco": [
        {"name": "Golden Gate Bridge",   "yt": "zd6BYcjNMYw", "start": 303},
        {"name": "Transamerica Pyramid", "yt": "ymuN7-3MklE", "start": 0},
        {"name": "Castro Street",        "yt": "d3JBGCLZ7eQ", "start": 0},
        {"name": "Salesforce Tower & Park", "yt": "d3JEg0iSxYg", "start": 0},
        {"name": "Golden Gate Park",     "yt": "dwL_uUrI8V4", "start": 0},
    ],
    "st-louis": [
        {"name": "Gateway Arch", "yt": "kCJYaMMBUOk", "start": 0},
    ],
    "chicago": [
        {"name": "Cloud Gate (The Bean)",   "yt": "gXY64MidsdE", "start": 8},
        {"name": "Willis Tower Skydeck",    "yt": "mh6ax4oV1oI", "start": 696},
    ],
    "los-angeles": [
        {"name": "Santa Monica Pier", "yt": "9JDPariSR0w", "start": 1},
    ],
    "cn-tower": [
        {"name": "CN Tower", "yt": "fgbFdV7yL_o", "start": 7},
    ],
    # ---- Asia ----
    "tokyo": [
        {"name": "Tokyo Tower",      "yt": "4WnO4IzHQrE", "start": 1290},
        {"name": "Shibuya Crossing", "yt": "_dWyKj7I9JM", "start": 0},
    ],
    "beijing": [
        {"name": "Great Wall (Mutianyu)", "yt": "WXIfF7TN1QQ", "start": 120},
    ],
    "seoul": [
        {"name": "Lotte World Tower", "yt": "XWPUsUw-iec", "start": 7},
    ],
    "hiroshima": [
        {"name": "Atomic Bomb Dome", "yt": "qwNoxabhgdw", "start": 1},
    ],
    # ---- Africa ----
    "cairo": [
        {"name": "Pyramids of Giza", "yt": "EaQr917lRgI", "start": 344},
    ],
    "dakar": [
        {"name": "African Renaissance Monument", "yt": "RQwS6JK7WrY", "start": 0},
    ],
    "addis-ababa": [
        {"name": "National Museum (home of Lucy)", "yt": "CL1XiT9bQdw", "start": 0},
    ],
    "johannesburg": [
        {"name": "Apartheid Museum", "yt": "DRO2JLH7tRs", "start": 0},
    ],
    # ---- Oceania ----
    "sydney": [
        {"name": "Sydney Opera House", "yt": "50LJQz5bRFQ", "start": 0},
    ],
    # ---- Latin America ----
    "rio-de-janeiro": [
        {"name": "Christ the Redeemer", "yt": "cgO1CjDhNRI", "start": 0},
        {"name": "Copacabana Beach",    "yt": "sRRODmeZjPc", "start": 0},
        {"name": "Sugarloaf Mountain",  "yt": "0ejre42k5vk", "start": 0},
    ],
    "bogota": [
        {"name": "Monserrate", "yt": "aEDbd-bDYXY", "start": 0},
    ],
    "havana": [
        {"name": "El Capitolio", "yt": "o0-Fe_2SJ6Y", "start": 0},
        {"name": "El Malecón",   "yt": "3s57K70l8-k", "start": 0},
    ],
    "montevideo": [
        {"name": "Palacio Salvo", "yt": "vkpI8lL1Iqw", "start": 0},
    ],
    "la-paz": [
        {"name": "Mi Teleférico", "yt": "_rrwe6TgJyw", "start": 0},
    ],
    "asuncion": [
        {"name": "Palacio de los López",            "yt": "YXT5_TLEdqs", "start": 0},
        {"name": "Panteón Nacional de los Héroes",   "yt": "yGNm-asB8U8", "start": 0},
    ],
    "san-jose": [
        {"name": "National Theatre of Costa Rica", "yt": "xofqHTD_ZVg", "start": 0},
    ],
}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, "data", "*.json")))
    remaining = set(MAP)
    changed = 0
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        locs = d.get("locations") if isinstance(d, dict) else None
        if not locs:
            continue
        touched = False
        for l in locs:
            lid = l.get("id")
            if lid in MAP:
                mons = [{"name": m["name"], "yt": m["yt"], "start": m.get("start", 0)}
                        for m in MAP[lid][:5]]
                # Keep auto picks (tools/enrich_monuments.py, "source":"auto")
                # AFTER the curated ones instead of wiping them: curation wins
                # the good seats, automation fills whatever room is left. A
                # curated entry for the same landmark or video always displaces
                # its auto twin.
                taken_yt = {m["yt"] for m in mons}
                taken_nm = {m["name"].lower() for m in mons}
                for m in l.get("monuments") or []:
                    if len(mons) >= 5:
                        break
                    if m.get("source") != "auto" or not m.get("yt"):
                        continue
                    if m["yt"] in taken_yt or (m.get("name") or "").lower() in taken_nm:
                        continue
                    mons.append(m)
                    taken_yt.add(m["yt"])
                    taken_nm.add((m.get("name") or "").lower())
                if l.get("monuments") != mons:
                    l["monuments"] = mons
                    touched = True
                    changed += 1
                remaining.discard(lid)
                print(f"  {lid:18} <- {len(mons)} monument(s): {', '.join(m['name'] for m in mons)}")
        if touched:
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"WROTE {os.path.basename(f)}")
    if remaining:
        print("\n!! ids in MAP not found in any data file:", ", ".join(sorted(remaining)), file=sys.stderr)
    print(f"\n=== {changed} location(s) updated; {len(MAP)-len(remaining)}/{len(MAP)} ids matched ===")


if __name__ == "__main__":
    main()
