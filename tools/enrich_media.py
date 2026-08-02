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
DENYLIST = ROOT / "data" / "media_denylist.json"


def load_denylist():
    """Ids a human watched and rejected. Heuristics can't see that a cam
    labelled "Monteverde" is a barangay in the Philippines rather than the
    cloud forest in Costa Rica — and without a memory of that judgement the
    next sweep finds it again. This file is that memory."""
    try:
        return json.loads(DENYLIST.read_text()).get("ids", {})
    except (OSError, ValueError):
        return {}


DENIED = load_denylist()

SEARCH_N = 10
CUR_YEAR = datetime.now().year

# The seats a place can fill. The two night seats are the day walk/drive
# seats with "and it is dark out" bolted on; live/window have no night
# twin ON PURPOSE — a live cam is already whatever time it is there, so a
# "night live cam" would be the same feed with a lie in the label.
SEATS = ("walk", "drive", "live", "window")
NIGHT_SEATS = ("night_walk", "night_drive")
# seat → the hand-curated field in the region JSON that outranks it
CURATED_FIELD = {"walk": "walk", "drive": "drive",
                 "live": "webcam", "window": "window",
                 "night_walk": "night_walk", "night_drive": "night_drive"}

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
                       r"crash|accident|police|test drive|review|"
                       # urbex is a subject, not a drive: "Road Trip: Exploring
                       # abandoned mountainside CCP Buildings (Nanchang)" was
                       # shipped as NANCHANG's drive in the 2026-08 China sweep.
                       r"abandoned|\burbex\b|derelict", re.I)

# 🌃 NIGHT. The night seats are the same seekable-video contract as their
# daytime twins — a night walk is a walk, a night drive is a drive — so
# they reuse every guard in this file and only add "…and it's dark out".
# The title has to SAY so: a walk shot at dusk that nobody labelled night
# is a daytime walk as far as we can prove, and guessing would be the
# same species of lie as a fake live cam.
NIGHT_WORDS = re.compile(
    r"\bnight\b|night ?life|nocturn|after dark|\bneon\b|\bevening\b|"
    r"midnight|\bdusk\b|illuminat|light ?up|noite|noche|notte|nacht|"
    r"nuit|natt|ночь|夜|야경|กลางคืน", re.I)
# "Night" that isn't a time of day: a hotel stay, a match, a film title.
BAD_NIGHT = re.compile(
    r"nights? (?:at|in) the (?:museum|opera)|good ?night|night ?core|"
    r"sleep|asmr|\d+ nights?\b|one night stand|saturday night live", re.I)
# …and the words that rescue a mixed title. "Jaipur Daytime and Evening
# Walk" really is a daytime walk that happens to run into dusk, so the
# day seat may keep it; "Las Vegas 4K - Midnight Drive" may not.
DAY_WORDS = re.compile(
    r"\bday(?:time|light)?\b|\bmorning\b|\bafternoon\b|\bsunrise\b|"
    r"\bmidday\b|\bnoon\b|\bsunny\b", re.I)


def night_title(t):
    """The title says it is dark out, and means the time of day."""
    t = t or ""
    return bool(NIGHT_WORDS.search(t)) and not BAD_NIGHT.search(t)


def daylight_title(t):
    """Safe for a DAY seat: it either never claims night, or claims day
    as well. Without this the day seat happily accepts a midnight drive
    and then labels it "Driving tour" — the same species of lie as a
    recorded loop in a live cam."""
    return not night_title(t) or bool(DAY_WORDS.search(t or ""))


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def nature_place(place):
    """True where an animal cam IS the point (Katmai's bears, Kruger)."""
    return (place.get("type") or "") in NATURE_TYPES


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


# A PERSON is not a place. The road scrub above only fires when the title
# spells the road type out, and plenty of titles don't: "Mississauga 4K
# Drive | Hwy 403 → Winston Churchill → Ridgeway Plaza" shipped as the
# driving tour of CHURCHILL, MANITOBA — a 900-person Arctic town — in the
# 2026-07 sweep, and "Driving Winston Churchill, Ontario" was queued up
# right behind it. Strip the honorific/given name together with the word
# it qualifies, so the dedication stops looking like a destination.
#
# Deliberately NOT here: "saint"/"st" (Saint Petersburg, St John's) and
# bare first names that are also real places on their own (Victoria,
# Nelson, Charlotte) — those must keep matching.
PERSON_NAMED = re.compile(
    r"\b(?:sir|lord|lady|dame|dr|prof|gen|col|capt|pres|president|"
    r"governor|mayor|bishop|father|winston|abraham|thomas jefferson|"
    r"john f\.?|jfk|martin luther(?: king)?|nelson mandela|"
    r"george washington|simon bolivar|jose marti|kwame nkrumah)\.?"
    r"\s+[a-z]+\b")


def scrub_persons(t):
    return PERSON_NAMED.sub("", t)


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
    # Not translations — the names real uploaders use. Each of these was a
    # good pick that the distinctive-token rule refused: every word of "Ha
    # Long Bay" except the short one is a generic feature noun, "Smoky" is
    # misspelled "Smokey" more often than not, and a region is only ever
    # filmed as one of its lakes.
    "ha-long-bay": ["ha long", "halong"],
    "great-smoky-mountains": ["smokey mountain", "smoky mountain"],
    "italian-lakes": ["lake garda", "lake como", "lake maggiore",
                      "riva del garda", "bellagio", "varenna"],
    # ...and these are the renderings that INHERITS_HIGHLIGHTS would otherwise
    # cost us. Each of these four picks was anchored on a province-sized
    # highlight ("Tibet", "Beijing", "Guizhou") that proves nothing — but each
    # title does name the place, just not the way the corpus spells it.
    "namtso": ["nam co", "namco"],
    "cuandixia": ["爨底下", "chuandixia"],
    "fanjingshan": ["fanjing", "梵淨山", "梵净山"],
}

# Places whose HIGHLIGHTS may stand in for the place itself, because the
# highlight is somewhere INSIDE it: Cannes is on the French Riviera, Vernazza
# is Cinque Terre, Cades Cove is in the Smokies.
#
# Opt-in, and it has to be. `type` can't tell a container from a site —
# `catalonia` and `zhangye-danxia` are both "nature" — and `region` is the
# administrative one, so French Riviera's says "Provence-Alpes-Côte d'Azur".
# Nothing in the data separates a highlight that is a PART from one that is
# merely a NEIGHBOUR, and neighbours are how the 2026-08 sweep served Dunhuang's
# city drive as MOGAO CAVES', Jiaxing's as XITANG's, Luoyang's as LONGMEN
# GROTTOES', a Lake Powell marina cam as ANTELOPE CANYON's, a walk through
# Brantford as BRANT CONSERVATION AREA's, and — five thousand kilometres off —
# "Plaza de Armas de Querétaro en vivo" as CUSCO's live cam.
#
# Adding an id here is a claim that its highlights are all inside it. Leaving
# one out costs recall, which this project spends freely: a missing scene is an
# honest gap, a borrowed one is a lie.
INHERITS_HIGHLIGHTS = {
    "amalfi-coast", "balearic-islands", "bavarian-alps", "canary-islands",
    "catalonia", "cinque-terre", "death-valley", "faroe-islands",
    "french-riviera", "great-smoky-mountains", "italian-lakes",
    "jurassic-coast", "li-river", "lofoten", "monument-valley",
    "norwegian-fjords", "plitvice", "portugal-coast", "provence",
    "swiss-alps", "tuscany-florence",
}

# Cam operators title their streams in their own language, and YouTube ranks
# by title — so outside the anglosphere the English word "webcam" can miss a
# city's only real cam entirely. Country name (normalized) → extra cam words.
CAM_WORDS_BY_COUNTRY = {
    "poland": ["kamera na żywo"],
    "spain": ["cámara en vivo"], "mexico": ["cámara en vivo"],
    "argentina": ["cámara en vivo"], "colombia": ["cámara en vivo"],
    "peru": ["cámara en vivo"], "chile": ["cámara en vivo"],
    "france": ["webcam en direct"], "germany": ["webcam live"],
    "austria": ["livecam"], "switzerland": ["livecam"],
    "italy": ["webcam live"], "portugal": ["câmara ao vivo"],
    "brazil": ["câmera ao vivo"], "netherlands": ["live webcam"],
    "czechia": ["kamera živě"], "russia": ["веб камера онлайн"],
    "ukraine": ["веб камера онлайн"], "turkey": ["canlı kamera"],
    "japan": ["ライブカメラ"], "south korea": ["실시간 라이브"],
    "china": ["直播"], "taiwan": ["即時影像"], "thailand": ["กล้องสด"],
    "greece": ["live camera"], "norway": ["webkamera live"],
    "sweden": ["webbkamera live"], "finland": ["webkamera live"],
    "denmark": ["webkamera live"], "iceland": ["vefmyndavel live"],
    "croatia": ["kamera uzivo"], "slovenia": ["kamera v zivo"],
    "hungary": ["webkamera elo"], "romania": ["camera live"],
    "bulgaria": ["уеб камера на живо"], "serbia": ["kamera uzivo"],
    "israel": ["מצלמה חיה"], "egypt": ["كاميرا مباشرة"],
    "morocco": ["كاميرا مباشرة"], "indonesia": ["kamera live"],
    "vietnam": ["camera trực tiếp"], "philippines": ["live webcam"],
}


APOS = re.compile(r"[ʻʼ‘’'`´]")
POSSESSIVE = re.compile(r"[ʻʼ‘’'`´]s\b")


def squash(s):
    """Normalized, with the marks that split a name into unsearchable pieces
    removed: Kauaʻi is one word, Xi'an is one word. Applied to BOTH sides of
    every comparison, so the title agrees.

    The possessive goes entirely, or the apostrophe just welds the s on and the
    word stops matching itself: "Mallorca's Crazy Snake Road" gave "mallorcas",
    which is not "mallorca", so BALEARIC ISLANDS lost a drive that is plainly
    Mallorca's — and "Portugal's Coast" searched for "portugals"."""
    return APOS.sub("", POSSESSIVE.sub("", norm(s)))


def distinctive(name):
    """The tokens of `name` that could only mean this place."""
    toks = [w for w in re.split(r"[^a-z]+", squash(name)) if len(w) > 3]
    return tuple(w for w in toks if w not in GENERIC_TOKENS)


def token_hit(w, t):
    """Is token `w` in title `t`?

    Long tokens match loosely, because cam operators run their names together
    and there is no boundary to find: "BerlinWebcam1", "WebcamSydney 1",
    "SedonaLiveCam.com". Short ones must stand as whole words — otherwise
    "brant" matches "Brantford" and BRANT CONSERVATION AREA is served a walk
    through the city next door.
    """
    if len(w) >= 6:
        return w in t
    return re.search(rf"\b{re.escape(w)}\b", t) is not None


def mentions_place(title, place):
    t0 = scrub_namesakes(norm(title))
    t = scrub_persons(scrub_streets(t0))
    # DISTINCTIVE tokens only, on word boundaries. Matching a place on a
    # generic word is how the 2026-08 China sweep shipped "Driving Tour Along
    # the Yellow River Highway" as LI RIVER's drive, "Mount Athos Healing
    # Prayer" as MOUNT TAI's live cam, and a Hong Kong ISLAND drive as
    # car-free LAMMA ISLAND's: strip the short word and "river", "mount" and
    # "island" are all that is left of those names. A place with no
    # distinctive token of its own has to be named in full.
    t, t0 = squash(t), squash(t0)
    if any(token_hit(w, t) for w in distinctive(place["name"])):
        return True
    base = squash(place["name"])
    if base in t:
        return True
    # ...or the name minus its trailing feature noun, so "Driving Through Ha
    # Long" still counts for HA LONG BAY. Two words minimum: the one-word
    # remainders ("Mount Tai" → "tai") are exactly the namesake magnets.
    core = " ".join(w for w in base.split() if w not in GENERIC_TOKENS)
    if len(core.split()) >= 2 and core in t:
        return True
    # `s?` because uploaders pluralize freely and an alias is curated anyway:
    # "smokey mountain" has to reach "Great Smokey Mountains" too.
    for a in ALIASES.get(place.get("id") or "", []):
        if re.search(rf"\b{re.escape(squash(a))}s?\b", t0):
            return True
    # a container's landmarks count: "Palma de Mallorca" IS the Balearics,
    # "Vernazza" IS Cinque Terre (full phrase only). A region entry has no
    # other way in — Catalonia's scenes can only be Barcelona's. Containers
    # only, though; see INHERITS_HIGHLIGHTS for why a site borrowing its
    # neighbour's name is the whole problem.
    # The landmark needs a distinctive token of its own, too, or it anchors
    # any namesake anywhere: WUZHEN's top highlight is "Grand Canal", so
    # `Grand Canal live webcam` returned VENICE and the phrase matched.
    if (place.get("id") or "") not in INHERITS_HIGHLIGHTS:
        return False
    for h in place.get("highlights") or []:
        name = squash(h.get("name") if isinstance(h, dict) else h)
        if len(name) <= 3 or not distinctive(name):
            continue
        if re.search(rf"\b{re.escape(name)}s?\b", t0):
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
    # pure feature nouns: hundreds of places have one, so on its own the word
    # identifies nothing. "Grand Canal" is Wuzhen's AND Venice's.
    "canal", "harbour", "harbor", "square",
    # every Ontario conservation area shares these two, so on their own they
    # single out nothing: "Day Trip To Grand River Conservation Park" was
    # shipped as BRANT CONSERVATION AREA's drive on the strength of the word
    # "conservation" alone — the video is Elora, an hour upstream.
    "conservation", "area",
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
US_ABBR = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY",
)
# Canada gets the same treatment as the US states, because it produces the
# same trap in the other direction: "Ross Bay, Victoria BC" was shipped as
# VICTORIA PEAK's window in the 2026-08 sweep. "ON" is deliberately absent
# from the abbreviations — ", on" is ordinary English ("Walking Tour, on a
# Rainy Morning") in a way ", BC" never is. Ontario's full name still counts.
CA_PROVINCES = {
    "alberta", "british columbia", "manitoba", "new brunswick",
    "newfoundland", "labrador", "nova scotia", "ontario",
    "prince edward island", "quebec", "saskatchewan", "yukon",
    "northwest territories", "nunavut",
}
CA_ABBR = ("AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "PE", "QC", "SK", "YT")
# abbreviation → state, in the same (alphabetical-by-state) order, so a US
# place can be checked against a US state named in a title instead of being
# skipped entirely. See the us-vs-us block in wrong_place_title().
US_ABBR_STATE = dict(zip(US_ABBR, [
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
]))
# Multi-city ROTATORS are the single biggest false positive in cam search
# ("1200 TOP LIVE WEBCAMS around the World", "European Webcam Journey — a
# panoramic tour of 280 cities", earthTV's "The World Live", WebCamera.pl's
# all-of-Poland mosaic). They ARE live, and they DO eventually show our city
# — but a feed that cycles through 280 places is not this place's window, and
# a viewer who opens it sees somewhere else. Never a seat.
# A nest box is not a city. Real 2026-07 picks this catches: a kestrel nest
# at the UN standing in as VIENNA's live cam, peregrine nest boxes as San
# José's BOTH seats, an aquarium otter tank as Seattle's window. These are
# fine cams — they're just not a look at the place, and `wild.json` exists
# precisely so animal cams can be their own destination. Applied only to
# places whose type isn't already nature (see nature_place()).
WILDLIFE_CAM = re.compile(
    r"nest ?(?:box|cam|site)?\b|\bnesting\b|kestrel|peregrine|falcon|osprey|"
    r"\beagles?\b|\bowls?\b|heron|stork|puffin|penguin|\bhive\b|bee ?cam|"
    r"aquarium|\bzoo\b|feeder|birdcam|bird ?cam|\bden\b|burrow|"
    r"panda|koala|otter|\bcubs?\b|hatch", re.I)
NATURE_TYPES = {"nature", "wilderness", "natural"}
# A wild place's scene cannot be a city-centre tour. "ZHANGYE, CHINA | City
# Walking Tour" shipped as the walk for ZHANGYE DANXIA — the rainbow-striped
# landform park outside the city — in the 2026-08 China sweep, because Zhangye
# is the park's own first highlight and the phrase matched. Cities still
# co-star honestly ("Drive from Zhangye to the Danxia park"); this only fires
# when the title frames the video AS a tour of a city.
WILD_TYPES = NATURE_TYPES | {"mountain", "desert"}
CITY_TOUR = re.compile(
    r"city (?:walk|walking|driving|drive|tour|centre|center|street)|"
    r"\bdowntown\b|city ?cent(?:re|er)|urban (?:walk|drive|life)", re.I)


def names_place_directly(title, place):
    """The title contains the place's OWN name — not merely one of its tokens,
    one of its landmarks, or an alias."""
    t = norm(title)
    base = norm(place["name"])
    if base in t:
        return True
    core = " ".join(w for w in base.split() if w not in GENERIC_TOKENS)
    return len(core.split()) >= 2 and core in t


def city_tour_of_the_wild(title, place):
    """True if a city-tour video is being offered as a wild place's scene.

    Only when the title never names the place itself. Plenty of wild entries
    ARE towns ("Downtown SEDONA", "Flagstaff — 4K Downtown Drive", a street
    cam in Mendoza) and plenty of honest drives simply start in one ("from
    Downtown Yan'An to China's Famous Hukou Waterfall"). What's left is a city
    tour standing in for somewhere it isn't: Zhangye's streets for the Danxia
    park, downtown Brantford for Brant Conservation Area.
    """
    return ((place.get("type") or "") in WILD_TYPES
            and bool(CITY_TOUR.search(title))
            and not names_place_directly(title, place))

AGGREGATOR_CAM = re.compile(
    r"\d{2,}\s*(?:\+\s*)?(?:top\s+)?(?:live\s+)?(?:web)?cams?\b|"
    r"(?:web)?cams?\s+(?:from\s+)?around\s+the\s+world|world\s+live\b|"
    r"(?:web)?cam(?:era)?s?\s+(?:tour|journey|trip|marathon|mosaic|mix)\b|"
    r"rolling\s+cam|multi[\s-]?cam|cam\s+switcher|"
    r"tour\s+of\s+\d+|\d+\s+(?:cities|countries|beaches|locations)|"
    # "…Camera Feeds from Donetsk, Sumy, Kyiv, Kharkiv and more" — a list of
    # places with an open end is a rotator, however few it names outright.
    r"feeds?\s+from\s+.+\band\s+more\b|"
    r"earthtv|webcamera\.pl|skyline\s?webcams", re.I)
BAD_CAM = re.compile(
    r"\bwar\b|breaking news|news live|live news|missile|drone attack|"
    r"air ?strike|invasion|frontline|protest|\briots?\b|footage|"
    r"\bvs\.?\b|\bmatch\b|explosions?|\battacks?\b|bombing|shelling|"
    r"\.fm\b|radio station|"
    # a disaster feed is a newsroom pointing at a place, not the place's cam
    r"wild ?fires?\b|\bblaze\b|evacuat|state of emergency|declares emergency|"
    r"earthquake|hurricane|typhoon|tornado|\bflooding\b|"
    # things that stream on a live channel without being a view of a place
    r"\bre-?live\b|\breplay\b|compilation|\bdigest\b|"      # not happening now
    r"\bdocumentary\b|\bfilm\b|\bepisodes?\b|"              # a programme on loop
    r"\btv\s?\d+\b|television channel|"                     # a broadcaster
    r"model rail|model train|"                              # someone's layout
    r"\bfr24\b|flightradar|"                                # a map, not a camera
    # a lottery draw streams 24/7 and names its city, but it is a studio
    # ticking numbers: "LIVE DRAW TOTO MACAU" shipped as MACAU's window.
    r"\blive draw\b|\btoto\b|\blotter(?:y|ie)\b|\bjackpot\b|\bbingo\b|"
    r"\bslots?\b|\bcasino games?\b", re.I)

# Scenery b-roll under a music bed, looping 24/7. Genuinely live, and
# genuinely not a camera: "24/7 Chill Italian Vibes & Mediterranean Music 🎶
# Scenic Amalfi Coast & Lake Como Relaxation 4K" — two coastlines 700 km
# apart — was shipped as the AMALFI COAST's live seat. Kept apart from
# BAD_CAM because it is a pair of rules, not a word list: a music framing
# AND no claim of a camera anywhere in the title. That second half is what
# lets "Hong Kong's ONLY 24/7 LIVE camera from The Peak with Relaxing Music
# BGM" — a real PTZ feed that happens to play music — still pass.
MUSIC_LOOP = re.compile(
    r"relaxation|\bvibes\b|lo-?fi|"
    # "chill" only where a music noun follows it. On its own it describes the
    # scene as often as the soundtrack: "LIVE 24/7: Malta Ship Spotting by day,
    # chilling by night | 4K Grand Harbour" is an actual harbour camera.
    r"chill(?:ed|ing)?\s+(?:\w+\s+){0,2}?(?:music|beats|mix)|"
    r"(?:ambient|study|sleep|meditation) music|music (?:to|for) ", re.I)
CAM_CLAIM = re.compile(
    r"web ?cam|\bcams?\b|camera|live view|live from|live stream of|"
    r"直播|ライブカメラ|실시간", re.I)


def music_loop_not_a_cam(title):
    return bool(MUSIC_LOOP.search(title)) and not CAM_CLAIM.search(title)
# news, sports and radio-station streams aren't place cams — but plain
# "radio"/"jazz radio" is just a music overlay on an otherwise real cam.
# "RE-LIVE Planespotting at Frankfurt Airport" is the sharpest of these:
# it is genuinely streaming right now, and it is genuinely a replay.

OTHER_PLACES = {}     # id → (tokens, lat, lng)   — filled in main()
OTHER_PLACE_NAMES = set()  # every dataset place name, normalized — filled in main()
COUNTRY_NAMES = set() # normalized country names  — filled in main()


def name_tokens_of(place):
    return distinctive(place["name"])


# ids whose name literally starts with "New" — see the guard in
# wrong_place_title(). Filled by register_place() alongside OTHER_PLACES.
NEW_NAMED = set()


def register_place(loc):
    """Put one place into the gazetteer the wrong-place guards read.

    Every caller needs all of OTHER_PLACES, COUNTRY_NAMES and NEW_NAMED loaded
    or the guards quietly under-report, and there are five callers, so the
    three-line dance lived in five places and NEW_NAMED would have been added
    to four of them.
    """
    c = loc.get("coordinates") or {}
    OTHER_PLACES[loc["id"]] = (name_tokens_of(loc), c.get("lat", 0), c.get("lng", 0))
    COUNTRY_NAMES.add(norm(loc.get("country") or ""))
    if norm(loc.get("name") or "").startswith("new "):
        NEW_NAMED.add(loc["id"])


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
        # "New Mexico" is not Mexico City, but "New York" IS New York City.
        # So a place whose own name does not start with "New" may not be found
        # inside a "New <token>" phrase. mexico-city reduces to the single
        # token "mexico" ("city" is generic), which made "Sandia Peak Tramway,
        # New Mexico" read as a video shot 1,600 km from Albuquerque. The
        # country loop below already guards this, but only for the one literal
        # string "new mexico" — this is the same bug one loop earlier.
        g = "" if pid in NEW_NAMED else r"(?<!new )"
        if any(not re.search(rf"{g}\b{re.escape(w)}\b", t) for w in toks):
            continue
        pos = _first_pos(toks, t)
        if pos is None:
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
            # ...and the POSTAL ABBREVIATION, which the full-name loop above
            # misses: "Peregrine Falcon Feed (Manchester, NH, USA)" shipped as
            # MANCHESTER, ENGLAND's window in the 2026-07 sweep. Only after a
            # comma, so the many abbreviations that are also ordinary words
            # ("IN", "OR", "ME", "OK", "HI") can't fire on prose.
            if re.search(r",\s*(?:" + "|".join(US_ABBR) + r")\b",
                         title, re.I):
                return True

        # ...and the same for a CANADIAN province, for non-Canadian places
        if own_country != "canada":
            for prov in CA_PROVINCES:
                if prov == own_country or prov in norm(place["name"]):
                    continue
                if re.search(rf"\b{re.escape(prov)}\b", t):
                    return True
            # No comma required, unlike the US list above: Canadians write
            # "Victoria BC" bare, and "Ross Bay, Victoria BC" was VICTORIA
            # PEAK's window until this line. Safe because these stay
            # case-sensitive and none of them is an English word — the one
            # trap is a date, so a digit can't precede ("Ancient Rome 500 BC").
            if re.search(r"(?<![0-9])[,\s]\s*(?:" + "|".join(CA_ABBR) + r")\b",
                         title):
                return True

    # US place vs a DIFFERENT US state. Everything above skips US places on
    # purpose — every US cam title names a US state, so refusing them all
    # would be useless. Compare against the place's OWN state instead. This
    # is how Flagstaff, ARIZONA ended up showing a webcam on Flagstaff Lake
    # in Eustis, MAINE, and Monument Valley showed a covered bridge in
    # Vermont. Our own name winning the headline still exempts the title,
    # so "Flagstaff, Arizona, USA | LIVE Train Camera" stays.
    if own_country == "united states":
        own_state = norm(place.get("region") or "")
        # "Monument Valley" has no distinctive tokens at all (both words are
        # generic), so own_pos is None and the headline test below would be
        # dead. Fall back to the literal name — it sits at the front of
        # "Exploring Monument Valley Utah", which is a Utah-side view of the
        # same park, not a relocation.
        head = own_pos
        if head is None:
            base = norm(place["name"]).split(",")[0].strip()
            head = t.find(base) if base and base in t else None
        # state → where it sits in the title, because the headline test below
        # needs a position. An abbreviation has no literal position for its
        # expanded name, so carry the position of the ABBREVIATION instead:
        # "Tulsa, OK Downtown ... Greenwood District Tour" expands OK to
        # oklahoma, which appears nowhere in the string, so _first_pos returned
        # None, the exemption could not fire, and Tulsa was ruled to be
        # somewhere other than Oklahoma. Same for Albuquerque's "NM".
        named = {st: _first_pos([st], t)
                 for st in US_STATES if re.search(rf"\b{re.escape(st)}\b", t)}
        m = re.search(r",\s*([A-Z]{2})\b", title)
        if m and m.group(1).upper() in US_ABBR_STATE:
            named.setdefault(US_ABBR_STATE[m.group(1).upper()], m.start())
        for st, pos in named.items():
            if st == own_state or st in norm(place["name"]):
                continue
            if head is not None and pos is not None and head < pos:
                continue                  # our place is still the headline
            return True
    return False


# ------------------------------------------------------- walks & drives
def find_seekable(place, query, want, avoid, min_dur=600, night=False):
    """A real, seekable tour video (walk or drive): embeddable, not
    live, recent enough that the streets still look like this.

    `night` is the entire difference between a day seat and its night
    twin, and it cuts BOTH ways: True demands the title say it's dark,
    False demands it not claim night at all. One-way would let a night
    video quietly fill the daytime seat, which is how Las Vegas ended
    up offering "Midnight Drive" as its Driving tour."""
    cands = []
    for e in flat_search(query):
        title = e.get("title") or ""
        dur = e.get("duration") or 0
        if e.get("id") in DENIED:
            continue
        if e.get("live_status") == "is_live":
            continue
        if not (min_dur <= dur <= 6 * 3600):
            continue
        if not want.search(title) or avoid.search(title):
            continue
        if night and not night_title(title):
            continue
        if not night and not daylight_title(title):
            continue
        if not mentions_place(title, place) or wrong_place_title(title, place):
            continue
        if city_tour_of_the_wild(title, place):
            continue
        cands.append(e)
    # try the most promising few until one passes the full vet
    for e in cands[:4]:
        info = full_info(e["id"])
        if not info or not embeddable(info) or info.get("is_live"):
            continue
        # the FULL title is what we store, and search snippets are often
        # shortened — re-run the title rules on it, same as find_cams does
        ft = info.get("title", "")
        if not want.search(ft) or avoid.search(ft):
            continue
        if night and not night_title(ft):
            continue
        if not night and not daylight_title(ft):
            continue
        if not mentions_place(ft, place) or wrong_place_title(ft, place):
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


# The night seats are the SAME seats with one extra condition: it has to
# actually be dark out. They deliberately reuse find_seekable rather than
# forking a "nightlife finder", so every guard earned by walk/drive —
# scrub_persons, wrong_place_title, the staleness cutoff, embeddability —
# applies here for free. `night=True` is the whole difference.
def find_night_walk(place):
    return find_seekable(place, f"{place['name']} {place['country']} night walk 4k",
                         WALK_WORDS, BAD_WALK, night=True)


def find_night_drive(place):
    return find_seekable(place, f"{place['name']} {place['country']} night drive 4k",
                         DRIVE_WORDS, BAD_DRIVE, night=True)


# ---------------------------------------------------------------- live cams
def cam_queries(place):
    """Query variants, cheapest-yield-first.

    Measured 2026-07: a single "{name} live cam" is far too narrow — it
    returned ZERO live results for Copenhagen, Kraków and Marrakesh while
    "webcam live" and "live webcam 24/7" surfaced real streams for the same
    cities. YouTube's ranking treats "live cam" / "webcam" as near-unrelated
    phrasings, so we ask both ways, plus the local-language word where we
    know it, plus the place's own top landmark (cam titles name the landmark
    far more often than the city: "Nyhavn", not "Copenhagen").
    """
    name = place["name"]
    qs = [f"{name} live cam", f"{name} webcam live", f"{name} live webcam 24/7"]
    # local-language cam words materially outperform English outside the
    # anglosphere ("kamera na żywo", "cámara en vivo", "webcam en direct")
    for alias in (ALIASES.get(place.get("id") or "") or [])[:1]:
        qs.append(f"{alias} live webcam")
    for word in CAM_WORDS_BY_COUNTRY.get(norm(place.get("country") or ""), []):
        qs.append(f"{name} {word}")
    # the top landmark, which is what the cam operator actually names it
    for h in (place.get("highlights") or [])[:1]:
        hn = h.get("name") if isinstance(h, dict) else h
        if hn and norm(hn) != norm(name):
            qs.append(f"{hn} live webcam")
    return qs


def find_cams(place, exclude=(), seats=("live", "window")):
    """Search several phrasings, pool the live hits, then classify them
    into street vs window vantage.  `exclude`: yt ids already used by this
    place's other seats — never offer the same feed twice.

    `seats` must list ONLY the seats the caller still needs. A cam whose
    title reads neither clearly street nor clearly window is a candidate
    for both seats, and the first seat to be filled consumes it — so
    filling a seat nobody asked for silently steals the city's only cam
    from the seat it actually needed. (Edinburgh, 2026-07: its real
    Arthur's Seat feed was being eaten by the already-filled `live` seat
    and the `window` gap stayed empty.)
    """
    live, seen = [], set()
    for qi, q in enumerate(cam_queries(place)):
        if qi:
            time.sleep(2)             # polite between variants
        for e in flat_search(q, 12):
            if e.get("live_status") != "is_live" or e.get("id") in exclude:
                continue
            if e.get("id") in seen or e.get("id") in DENIED:
                continue
            title = e.get("title") or ""
            if BAD_CAM.search(title) or AGGREGATOR_CAM.search(title):
                continue
            if music_loop_not_a_cam(title):
                continue
            if not nature_place(place) and WILDLIFE_CAM.search(title):
                continue
            if not mentions_place(title, place) or wrong_place_title(title, place):
                continue
            seen.add(e["id"])
            live.append(e)
        # enough real candidates to fill both seats — stop paying for search
        if len(live) >= 6:
            break

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
    for seat in seats:
        for e in ranked[seat][:5]:
            if e["id"] in used:
                continue
            if e["id"] not in vetted:
                info = full_info(e["id"])
                # the FULL title is what we store — re-run the title
                # rules on it (search snippets are often shortened)
                ft = (info or {}).get("title", "")
                ok = bool(info) and embeddable(info) and info.get("is_live") \
                    and not BAD_CAM.search(ft) and not AGGREGATOR_CAM.search(ft) \
                    and not (not nature_place(place) and WILDLIFE_CAM.search(ft)) \
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
    ap.add_argument("--need", choices=[*SEATS, *NIGHT_SEATS, "night", "any"],
                    default="any",
                    help="'any' sweeps the four day seats; the night seats are "
                         "opt-in ('night' = both) so a routine refresh doesn't "
                         "mark every city as incomplete forever")
    ap.add_argument("--refresh", action="store_true", help="redo places already in media.json")
    args = ap.parse_args()

    media = {"generated": None, "places": {}}
    if MEDIA.exists():
        media = json.load(open(MEDIA))
        media.setdefault("places", {})

    places = load_places()
    for p in places:
        register_place(p)
        OTHER_PLACE_NAMES.add(norm(p["name"]))
    only = set(args.only.split(",")) if args.only else None

    def curated_has(loc, scene):
        return bool(loc.get(CURATED_FIELD[scene]))

    def wants(loc):
        if only and loc["id"] not in only:
            return False
        if args.tag and loc.get("tag") != args.tag:
            return False
        done = media["places"].get(loc["id"], {})
        scan = NIGHT_SEATS if args.need in ("night", *NIGHT_SEATS) else SEATS
        if args.need not in ("any", "night"):
            scan = (args.need,)
        needs = [s for s in scan
                 if not curated_has(loc, s) and s not in done]
        if args.refresh and not needs:
            needs = list(scan)          # redo the seats this run is about
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
        needs = loc.get("_needs") or list(SEATS)

        # A seat and its twin must never hold the SAME video — showing one
        # tape twice under two labels is a lie in one of the two seats.
        def free(seat, pick):
            twin = {"walk": "night_walk", "night_walk": "walk",
                    "drive": "night_drive", "night_drive": "drive"}[seat]
            return pick and pick["yt"] != (entry.get(twin) or {}).get("yt")

        if "walk" in needs:
            w = find_walk(loc)
            if free("walk", w):
                entry["walk"] = w
                found.append(f"walk:{w['yt']}({w['date'][:4]})")
            time.sleep(4)
        if "drive" in needs:
            d = find_drive(loc)
            if free("drive", d):
                entry["drive"] = d
                found.append(f"drive:{d['yt']}({d['date'][:4]})")
            time.sleep(4)
        if "night_walk" in needs:
            nw = find_night_walk(loc)
            if free("night_walk", nw):
                entry["night_walk"] = nw
                found.append(f"night_walk:{nw['yt']}({nw['date'][:4]})")
            time.sleep(4)
        if "night_drive" in needs:
            nd = find_night_drive(loc)
            if free("night_drive", nd):
                entry["night_drive"] = nd
                found.append(f"night_drive:{nd['yt']}({nd['date'][:4]})")
            time.sleep(4)
        if "live" in needs or "window" in needs:
            taken = {v.get("yt") for v in entry.values()
                     if isinstance(v, dict) and v.get("yt")}
            want_seats = [s for s in ("live", "window") if s in needs]
            cams = find_cams(loc, exclude=taken, seats=want_seats)
            for seat in want_seats:
                if seat in cams:
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
