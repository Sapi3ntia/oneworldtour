#!/usr/bin/env python3
"""
build_world.py — generator for the world-coverage backlog (the 50 countries in
COUNTRIES.md §4). Brings One World Tour from 39 → 89 countries.

Same philosophy as build_europe.py: WE curate which destinations to feature (the
editorial pick is ours), but every coordinate + Wikipedia slug is VERIFIED LIVE
against the Wikipedia REST summary API — never recalled from memory. A row whose
page is missing or has no coordinates is NOT emitted; it's reported for manual
fixing. Blurbs fall back to the live Wikipedia summary in the front-end, exactly
like the existing data, so we don't hand-author 180 blurbs.

Output: per-continent region files (asia/africa/oceania/latinamerica.json) plus
new European countries appended into europe.json. Country code / flag / continent
come from data/countries.json (the registry), so they're always consistent.

Verification results are cached in tools/.wiki_cache.json (re-runs are fast and
offline-friendly). Pass --refresh to re-fetch.

Run:  python3 tools/build_world.py [--refresh]
"""

import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(HERE, ".wiki_cache.json")
UA = "OneWorldTour/1.0 (educational virtual-travel project; contact: local)"

SOUND = {
    "city": "city-hum.mp3", "history": "european-plaza.mp3",
    "coastal": "ocean-waves.mp3", "island": "ocean-waves.mp3",
    "mountain": "mountain-wind.mp3", "nature": "mountain-wind.mp3",
    "village": "european-plaza.mp3", "desert": "mountain-wind.mp3",
}

# Which region-file each continent's NEW content lands in, and the region's
# display name + id for data/index.json.
CONTINENT_FILE = {
    "Asia": ("asia.json", "asia", "Asia"),
    "Africa": ("africa.json", "africa", "Africa"),
    "Oceania": ("oceania.json", "oceania", "Oceania"),
    # South + Central America/Caribbean new content shares one "Latin America" region
    "South America": ("latinamerica.json", "latinamerica", "Latin America"),
    "NorthAmericaNew": ("latinamerica.json", "latinamerica", "Latin America"),
    # New European countries append into the existing europe.json / "Europe" region
    "Europe": ("europe.json", "europe", "Europe"),
}
# countries whose continent is North America but belong in the Latin America bucket
LATAM_NA = {"Cuba", "Costa Rica", "Belize"}

# -------------------------------------------------------------------------
# THE CURATED BACKLOG.  country -> [ (display_name, wiki_slug, type, tag, emoji) ]
# tag: famous | hidden.  Coordinates are fetched & verified from wiki_slug.
# -------------------------------------------------------------------------
DEST = {
 # ============================== ASIA ==============================
 "Japan": [
    ("Tokyo","Tokyo","city","famous","🗼"),
    ("Kyoto","Kyoto","history","famous","⛩️"),
    ("Osaka","Osaka","city","famous","🏯"),
    ("Mount Fuji","Mount_Fuji","mountain","famous","🗻"),
    ("Hiroshima","Hiroshima","history","famous","🕊️"),
    ("Nara","Nara,_Nara","history","hidden","🦌")],
 "China": [
    ("Beijing","Beijing","city","famous","🏯"),
    ("Shanghai","Shanghai","city","famous","🌃"),
    ("Great Wall at Badaling","Badaling","history","famous","🧱"),
    ("Xi'an","Xi'an","history","famous","🏺"),
    ("Guilin","Guilin","nature","famous","⛰️"),
    ("Hong Kong","Hong_Kong","city","famous","🌆")],
 "India": [
    ("New Delhi","Delhi","city","famous","🛕"),
    ("Taj Mahal, Agra","Taj_Mahal","history","famous","🕌"),
    ("Jaipur","Jaipur","history","famous","🏰"),
    ("Mumbai","Mumbai","city","famous","🌃"),
    ("Varanasi","Varanasi","history","famous","🪔"),
    ("Kerala Backwaters","Kerala_backwaters","nature","hidden","🛶")],
 "South Korea": [
    ("Seoul","Seoul","city","famous","🏙️"),
    ("Busan","Busan","coastal","famous","🌊"),
    ("Gyeongju","Gyeongju","history","hidden","🏯"),
    ("Jeju Island","Jeju_Island","island","famous","🌋")],
 "Thailand": [
    ("Bangkok","Bangkok","city","famous","🛕"),
    ("Chiang Mai","Chiang_Mai","history","famous","🏮"),
    ("Phuket","Phuket_Province","coastal","famous","🏝️"),
    ("Ayutthaya","Ayutthaya_(city)","history","hidden","🏛️")],
 "Malaysia": [
    ("Kuala Lumpur","Kuala_Lumpur","city","famous","🌃"),
    ("George Town, Penang","George_Town,_Penang","history","famous","🏮"),
    ("Malacca City","Malacca_City","history","hidden","⛵"),
    ("Kota Kinabalu","Kota_Kinabalu","nature","hidden","🏔️")],
 "Singapore": [
    ("Singapore","Singapore","city","famous","🌆"),
    ("Gardens by the Bay","Gardens_by_the_Bay","nature","famous","🌳"),
    ("Sentosa","Sentosa","island","hidden","🎡")],
 "Philippines": [
    ("Manila","Manila","city","famous","🏙️"),
    ("Cebu City","Cebu_City","coastal","famous","🌊"),
    ("El Nido, Palawan","El_Nido,_Palawan","island","famous","🏝️"),
    ("Banaue Rice Terraces","Banaue_Rice_Terraces","nature","hidden","🌾")],
 "Vietnam": [
    ("Hanoi","Hanoi","city","famous","🏮"),
    ("Ho Chi Minh City","Ho_Chi_Minh_City","city","famous","🌃"),
    ("Ha Long Bay","Hạ_Long_Bay","coastal","famous","⛰️"),
    ("Hoi An","Hội_An_Ancient_Town","history","famous","🏮")],
 "Cambodia": [
    ("Angkor Wat","Angkor_Wat","history","famous","🛕"),
    ("Phnom Penh","Phnom_Penh","city","famous","🏯"),
    ("Siem Reap","Siem_Reap","history","hidden","🏛️")],
 "Laos": [
    ("Luang Prabang","Luang_Prabang","history","famous","🛕"),
    ("Vientiane","Vientiane","city","hidden","🏯")],
 "Taiwan": [
    ("Taipei","Taipei","city","famous","🌃"),
    ("Taroko Gorge","Taroko_National_Park","nature","famous","⛰️"),
    ("Tainan","Tainan","history","hidden","🏮")],
 "Mongolia": [
    ("Ulaanbaatar","Ulaanbaatar","city","famous","🏙️"),
    ("Gobi Desert","Gobi_Desert","desert","famous","🐫")],
 "Sri Lanka": [
    ("Colombo","Colombo","city","famous","🏙️"),
    ("Kandy","Kandy","history","famous","🛕"),
    ("Sigiriya","Sigiriya","history","hidden","🪨")],
 "Israel": [
    ("Jerusalem","Jerusalem","history","famous","🕍"),
    ("Tel Aviv","Tel_Aviv","city","famous","🏖️"),
    ("Masada","Masada","history","hidden","🏜️")],
 "United Arab Emirates": [
    ("Dubai","Dubai","city","famous","🌃"),
    ("Abu Dhabi","Abu_Dhabi","city","famous","🕌")],
 "Saudi Arabia": [
    ("Riyadh","Riyadh","city","famous","🏙️"),
    ("Jeddah","Jeddah","coastal","famous","🌊"),
    ("Hegra (AlUla)","Mada'in_Salih","history","hidden","🏜️")],
 "Qatar": [
    ("Doha","Doha","city","famous","🌃")],
 "Jordan": [
    ("Petra","Petra","history","famous","🏛️"),
    ("Amman","Amman","city","famous","🏙️"),
    ("Wadi Rum","Wadi_Rum","desert","famous","🏜️")],
 "Iran": [
    ("Tehran","Tehran","city","famous","🏙️"),
    ("Isfahan","Isfahan","history","famous","🕌"),
    ("Persepolis","Persepolis","history","famous","🏛️"),
    ("Shiraz","Shiraz","history","hidden","🌹")],
 "Armenia": [
    ("Yerevan","Yerevan","city","famous","🏙️"),
    ("Lake Sevan","Lake_Sevan","nature","hidden","🏞️"),
    ("Tatev Monastery","Tatev_Monastery","history","hidden","⛪")],
 "Azerbaijan": [
    ("Baku","Baku","city","famous","🔥")],
 "Georgia": [
    ("Tbilisi","Tbilisi","city","famous","🏙️"),
    ("Gergeti / Kazbegi","Gergeti_Trinity_Church","mountain","hidden","⛰️")],

 # ============================== AFRICA ==============================
 "Morocco": [
    ("Marrakesh","Marrakesh","history","famous","🕌"),
    ("Fez","Fez,_Morocco","history","famous","🏺"),
    ("Chefchaouen","Chefchaouen","village","hidden","🔵"),
    ("Sahara at Merzouga","Merzouga","desert","famous","🐫"),
    ("Casablanca","Casablanca","city","famous","🏙️")],
 "Egypt": [
    ("Giza Pyramids","Giza_pyramid_complex","history","famous","🐫"),
    ("Cairo","Cairo","city","famous","🏙️"),
    ("Luxor","Luxor","history","famous","🏛️"),
    ("Aswan","Aswan","history","hidden","⛵")],
 "Kenya": [
    ("Nairobi","Nairobi","city","famous","🏙️"),
    ("Maasai Mara","Maasai_Mara","nature","famous","🦁"),
    ("Mombasa","Mombasa","coastal","hidden","🏖️")],
 "Senegal": [
    ("Dakar","Dakar","city","famous","🏙️"),
    ("Gorée Island","Gorée","history","hidden","⚓")],
 "Ethiopia": [
    ("Addis Ababa","Addis_Ababa","city","famous","🏙️"),
    ("Lalibela","Lalibela","history","famous","⛪"),
    ("Gondar","Gondar","history","hidden","🏰")],
 "Gambia": [
    ("Banjul","Banjul","city","famous","🏙️")],
 "South Africa": [
    ("Cape Town","Cape_Town","coastal","famous","🏔️"),
    ("Table Mountain","Table_Mountain","mountain","famous","⛰️"),
    ("Johannesburg","Johannesburg","city","famous","🏙️"),
    ("Kruger National Park","Kruger_National_Park","nature","famous","🦁")],

 # ============================== OCEANIA ==============================
 "Australia": [
    ("Sydney","Sydney","city","famous","🌉"),
    ("Melbourne","Melbourne","city","famous","🎨"),
    ("Uluru","Uluru","desert","famous","🪨"),
    ("Great Barrier Reef","Great_Barrier_Reef","coastal","famous","🐠"),
    ("Cairns","Cairns","coastal","hidden","🌴"),
    ("Perth","Perth","coastal","hidden","🏖️")],
 "New Zealand": [
    ("Auckland","Auckland","city","famous","⛵"),
    ("Queenstown","Queenstown,_New_Zealand","mountain","famous","🏔️"),
    ("Wellington","Wellington","city","famous","🎬"),
    ("Rotorua","Rotorua","nature","hidden","♨️"),
    ("Milford Sound","Milford_Sound","nature","famous","🏞️")],

 # ====================== LATIN AMERICA (S + C) ======================
 "Argentina": [
    ("Buenos Aires","Buenos_Aires","city","famous","💃"),
    ("Iguazú Falls","Iguazu_Falls","nature","famous","💦"),
    ("Bariloche","San_Carlos_de_Bariloche","mountain","famous","🏔️"),
    ("Mendoza","Mendoza,_Argentina","nature","hidden","🍷"),
    ("Ushuaia","Ushuaia","coastal","hidden","🐧")],
 "Bolivia": [
    ("La Paz","La_Paz","city","famous","🏔️"),
    ("Salar de Uyuni","Salar_de_Uyuni","nature","famous","🧂"),
    ("Sucre","Sucre","history","hidden","⛪")],
 "Colombia": [
    ("Bogotá","Bogotá","city","famous","🏙️"),
    ("Cartagena","Cartagena,_Colombia","coastal","famous","🏰"),
    ("Medellín","Medellín","city","famous","🌸")],
 "Uruguay": [
    ("Montevideo","Montevideo","city","famous","🏙️"),
    ("Punta del Este","Punta_del_Este","coastal","famous","🏖️"),
    ("Colonia del Sacramento","Colonia_del_Sacramento","history","hidden","🚸")],
 "Paraguay": [
    ("Asunción","Asunción","city","famous","🏙️")],
 "Cuba": [
    ("Havana","Havana","history","famous","🚗"),
    ("Trinidad","Trinidad,_Cuba","history","hidden","🎶"),
    ("Varadero","Varadero","coastal","famous","🏖️")],
 "Costa Rica": [
    ("San José","San_José,_Costa_Rica","city","famous","🏙️"),
    ("Arenal Volcano","Arenal_Volcano","nature","famous","🌋"),
    ("Monteverde","Monteverde","nature","hidden","🌿"),
    ("Manuel Antonio","Manuel_Antonio_National_Park","coastal","famous","🐒")],
 "Belize": [
    ("Belize City","Belize_City","coastal","famous","🌊"),
    ("Caracol","Caracol","history","hidden","🛕"),
    ("Ambergris Caye","Ambergris_Caye","island","famous","🤿")],

 # ====================== NEW EUROPE (append) ======================
 "Ukraine": [
    ("Kyiv","Kyiv","city","famous","⛪"),
    ("Lviv","Lviv","history","famous","☕"),
    ("Odesa","Odesa","coastal","hidden","⚓")],
 "Serbia": [
    ("Belgrade","Belgrade","city","famous","🏰"),
    ("Novi Sad","Novi_Sad","history","hidden","🎸")],
 "Luxembourg": [
    ("Luxembourg City","Luxembourg_City","history","famous","🏰")],
 "Lithuania": [
    ("Vilnius","Vilnius","history","famous","⛪"),
    ("Trakai Castle","Trakai_Island_Castle","history","hidden","🏰")],
 "Latvia": [
    ("Riga","Riga","history","famous","🏛️")],
 "Moldova": [
    ("Chișinău","Chișinău","city","hidden","🍇")],
 "Slovakia": [
    ("Bratislava","Bratislava","history","famous","🏰"),
    ("High Tatras","Tatra_Mountains","mountain","hidden","🏔️")],
 "Slovenia": [
    ("Ljubljana","Ljubljana","history","famous","🐉"),
    ("Lake Bled","Lake_Bled","nature","famous","🏞️"),
    ("Piran","Piran","coastal","hidden","⛪")],
 "Vatican City": [
    ("Vatican City","Vatican_City","history","famous","⛪")],
 "Russia": [
    ("Moscow","Moscow","city","famous","🏯"),
    ("Saint Petersburg","Saint_Petersburg","history","famous","🎭"),
    ("Kazan","Kazan","history","hidden","🕌"),
    ("Lake Baikal","Lake_Baikal","nature","famous","🏞️")],
}


def slugify(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def load_registry():
    with open(os.path.join(DATA, "countries.json"), encoding="utf-8") as f:
        reg = json.load(f)
    return {c["name"]: c for c in reg["countries"]}


def load_cache(refresh):
    if refresh or not os.path.exists(CACHE):
        return {}
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache):
    # only persist resolved results (success or *permanent* error) — never a 429/timeout
    keep = {k: v for k, v in cache.items()
            if "error" not in v or v["error"] in ("missing", "no-coordinates")}
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=1)


def _get_json(url, max_attempts=7):
    """GET with polite handling of 429s: honour Retry-After, escalating backoff."""
    backoff = [5, 12, 25, 40, 60, 90]
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_attempts - 1:
                ra = e.headers.get("Retry-After")
                wait = int(ra) if (ra and ra.isdigit()) else backoff[min(attempt, len(backoff) - 1)]
                print(f"    …429, waiting {wait}s (attempt {attempt + 1})")
                time.sleep(wait + 1)
                continue
            raise
        except Exception:  # noqa - transient network: short backoff
            if attempt < max_attempts - 1:
                time.sleep(backoff[min(attempt, len(backoff) - 1)])
                continue
            raise
    raise RuntimeError("exhausted retries")


def _api_batch(titles):
    """Query the MediaWiki action API for coordinates of up to ~45 titles at once,
    following normalizations + redirects AND the `continue` token (the coordinates
    prop paginates — without this, pages past the first chunk look coord-less).
    Returns {requested_title: {lat,lng}|{error}}."""
    step = {}                 # from-title -> to-title (normalize + redirect chain)
    coords = {}               # final title -> {lat,lng}
    seen = set()              # final titles the API returned a page for
    cont = {}
    for _ in range(20):       # safety cap on continuation hops
        params = {
            "action": "query", "prop": "coordinates", "coprop": "type|name",
            "coprimary": "all",   # some cities store coords as secondary (primary:false)
            "titles": "|".join(titles), "redirects": "1", "format": "json",
            "formatversion": "2",
        }
        params.update(cont)
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
        data = _get_json(url)
        q = data.get("query", {})
        for n in q.get("normalized", []):
            step[n["from"]] = n["to"]
        for rd in q.get("redirects", []):
            step[rd["from"]] = rd["to"]
        for p in q.get("pages", []):
            seen.add(p["title"])
            if p.get("missing"):
                continue
            if p.get("coordinates"):
                cs = p["coordinates"]
                c = next((x for x in cs if x.get("primary")), cs[0])  # prefer primary
                coords[p["title"]] = {"lat": round(c["lat"], 5), "lng": round(c["lon"], 5)}
        if "continue" in data:
            cont = data["continue"]
            time.sleep(0.2)
        else:
            break

    out = {}
    for t in titles:
        cur, hops = t, 0
        while cur in step and hops < 6:
            cur, hops = step[cur], hops + 1
        if cur in coords:
            out[t] = {"lat": coords[cur]["lat"], "lng": coords[cur]["lng"], "title": cur}
        elif cur in seen:
            out[t] = {"error": "no-coordinates", "title": cur}
        else:
            out[t] = {"error": "missing"}
    return out


def resolve_slugs(slugs, cache):
    """Resolve every slug to coords via batched action-API calls (with retry)."""
    todo = [s for s in slugs if s not in cache]
    title_of = {s: s.replace("_", " ") for s in todo}
    titles = list({title_of[s] for s in todo})
    result_by_title = {}
    batches = [titles[i:i + 45] for i in range(0, len(titles), 45)]
    for n, batch in enumerate(batches):
        print(f"  batch {n + 1}/{len(batches)} ({len(batch)} titles)…")
        try:
            result_by_title.update(_api_batch(batch))   # _get_json handles 429 retries
        except Exception as e:  # noqa
            for t in batch:
                result_by_title[t] = {"error": str(e)[:60]}
        time.sleep(1.5)
    for s in todo:
        cache[s] = result_by_title.get(title_of[s], {"error": "unresolved"})
    return cache


def build(refresh=False):
    reg = load_registry()
    cache = load_cache(refresh)
    buckets = {}          # filename -> {region meta, locations[]}
    ok, failures = 0, []
    seen_ids = set()

    # ---- pre-resolve every slug's coordinates in batched API calls ----
    all_slugs = [row[1] for rows in DEST.values() for row in rows]
    resolve_slugs(all_slugs, cache)
    save_cache(cache)

    for country, rows in DEST.items():
        meta = reg.get(country)
        if not meta:
            failures.append(f"{country}: not in registry"); continue
        cont = meta["continent"]
        key = "NorthAmericaNew" if country in LATAM_NA else cont
        fn, region_id, region_name = CONTINENT_FILE[key]
        bucket = buckets.setdefault(fn, {"id": region_id, "name": region_name, "locations": []})

        for (name, slug, type_, tag, emoji) in rows:
            info = cache.get(slug, {"error": "unresolved"})
            if "error" in info:
                failures.append(f"{country} / {name} [{slug}] -> {info['error']}")
                continue
            lid = slugify(name)
            while lid in seen_ids:
                lid += "-2"
            seen_ids.add(lid)
            rec = {
                "id": lid,
                "name": name,
                "country": country,
                "country_code": meta["code"],
                "country_flag": meta["flag"],
                "continent": cont,
                "region": "",
                "type": type_,
                "tag": tag,
                "emoji": emoji,
                "coordinates": {"lat": info["lat"], "lng": info["lng"]},
                "street_view": {"lat": info["lat"], "lng": info["lng"], "heading": 0, "pitch": 0, "fov": 90},
                "wikipedia_slug": slug,
                "sounds": [SOUND.get(type_, "city-hum.mp3")],
                "highlights": [],
                "blurb": "",
                "fun_fact": "",
                "hidden_gem_tip": None,
            }
            bucket["locations"].append(rec)
            ok += 1

    save_cache(cache)

    # ---- write per-continent files; append into existing europe.json ----
    written = []
    for fn, bucket in buckets.items():
        path = os.path.join(DATA, fn)
        if fn == "europe.json":
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            existing = {l["id"] for l in doc["locations"]}
            added = [r for r in bucket["locations"] if r["id"] not in existing]
            doc["locations"].extend(added)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
                f.write("\n")
            written.append(f"{fn}: +{len(added)} appended ({len(doc['locations'])} total)")
        else:
            doc = {"region": bucket["name"], "continent": None,
                   "code": bucket["id"].upper(), "locations": bucket["locations"]}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
                f.write("\n")
            written.append(f"{fn}: {len(bucket['locations'])} locations (region '{bucket['name']}')")

    print(f"✓ verified + built {ok} locations across {len(DEST)} countries\n")
    for w in written:
        print("  •", w)
    if failures:
        print(f"\n⚠ {len(failures)} rows need a slug fix (not emitted):")
        for fl in failures:
            print("   -", fl)
    else:
        print("\n  all rows verified — no slug fixes needed.")


if __name__ == "__main__":
    build(refresh="--refresh" in sys.argv)
