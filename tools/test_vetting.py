#!/usr/bin/env python3
"""
test_vetting.py — the bad picks, frozen so they can't come back.

Every `want=False` case below is a scene that ACTUALLY SHIPPED, or was one
`--apply` away from shipping. Every `want=True` case is a good pick that some
rule refused until it was loosened correctly. That is the whole point: the
vetting rules in enrich_media.py only get stricter, and each tightening is one
regex away from silently killing honest footage or resurrecting a lie.

No network, no yt-dlp — pure title-vetting logic against the real corpus.

Usage:
  python3 tools/test_vetting.py        # exits 1 on any failure
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich_media as em

# populate the corpus-derived globals the rules consult
for p in em.load_places():
    em.register_place(p)
    em.OTHER_PLACE_NAMES.add(em.norm(p["name"]))

PLACES = {p["id"]: p for p in em.load_places()}


def place(pid):
    p = PLACES.get(pid)
    if not p:
        raise SystemExit(f"no such place id: {pid}")
    return p


fails = []


def case(fn, want, title, pid, note=""):
    got = bool(fn(title, place(pid)))
    if got != want:
        fails.append(f"FAIL {fn.__name__} want={want} got={got}: {title[:70]}"
                     + (f"\n     ({note})" if note else ""))


M = em.mentions_place
W = em.wrong_place_title
C = em.city_tour_of_the_wild

# --- mentions_place: a generic token must not be enough --------------------
case(M, False, "Mount Athos LIVE webcam", "mount-tai",
     "'mount' is generic; Athos is in Greece")
case(M, False, "Yellow River Scenic Drive 4K", "li-river",
     "'river' is generic")
case(M, False, "Hong Kong Island Driving Tour", "lamma-island",
     "'island' is generic; Lamma is car-free")
case(M, False, "Day Trip To Grand River Conservation Park - Elora Gorge",
     "brant-conservation-area", "'conservation'/'area' are generic")
case(M, False, "BRANTFORD Walking Tour Ontario Canada", "brant-conservation-area",
     "short token 'brant' must not substring-match 'brantford'")
case(M, False, "Venice Grand Canal Hotel Live Cam", "wuzhen",
     "landmark inheritance needs a distinctive token of its own")

# --- mentions_place: a SITE may not borrow a NEIGHBOUR's name -------------
case(M, False, "Dunhuang 4K City Drive | Silent Morning in China's Silk Road",
     "mogao-caves", "Dunhuang is the city next door, not the caves")
case(M, False, "Jiaxing Driving Tour - The Most Livable City in Zhejiang",
     "xitang", "Jiaxing is the prefecture city, not the water town")
case(M, False, "UNSEEN CHINA | Driving in Luoyang - The Birthplace of ...",
     "longmen-grottoes", "Luoyang is the city, not the grottoes")
case(M, False, "LIVE 24/7 | Lake Powell Marina Cam | Boats, Sunsets",
     "antelope-canyon", "a marina on a lake 15 km away")
case(M, False, "Plaza de Armas de Queretaro en vivo", "cusco",
     "'Plaza de Armas' is shared by half of Latin America — this is Mexico")
case(M, False, "Northern Lights powered by EXPLORE.org", "churchill",
     "the title never says Churchill; an aurora cam could be anywhere Arctic")

# --- ...but a CONTAINER still may ----------------------------------------
case(M, True, "China's Ultimate Valley Scenic Drive - Yangshuo Guilin 4K HDR",
     "li-river", "Yangshuo and Guilin are both ON the Li River")
case(M, True, "Mallorca Webcam Sant Elm Beach LIVE 4K", "balearic-islands")
case(M, True, "LIVE WEBCAM CANNES - Boulevard du Midi", "french-riviera")
case(M, True, "Driving to Durdle Door | Scenic UK Coastal Journey (4K)",
     "jurassic-coast")
case(M, True, "Geirangerfjord cruise port, Geiranger", "norwegian-fjords")
case(M, True, "Montalcino to Siena, Toscana | Italy Scenic Drive 4K",
     "tuscany-florence")

# --- the aliases that keep the good picks the container rule would cost ---
case(M, True, "Tibet Scenic Walking 4K - ... the Highest Salt Lake Nam co",
     "namtso", "'Nam co' is the romanization the uploader used")
case(M, True, "China Walk 4K | 500-Year-Old Stone Village in Beijing 爨底下",
     "cuandixia", "the Chinese name is right there in the title")
case(M, True, "Driving on the Mount Fanjing Mountain Ring Road - Guizhou",
     "fanjingshan", "'Fanjing' is how it is rendered in English")

# --- mentions_place: the good picks it must still accept -------------------
case(M, True, "XI'AN, CHINA | City Wall (Yongning Gate) Walking Tour | 4k",
     "xi-an", "the apostrophe form real uploaders use")
case(M, True, "Kauaʻi Hawaii 4K Driving Tour", "kauai",
     "the okina must not split the name into unsearchable pieces")
case(M, True, "SedonaLiveCam.com - Live View", "sedona",
     "cam operators run names together; long tokens match loosely")
case(M, True, "WebcamSydney 1 - Live", "sydney")
case(M, True, "Driving Through Ha Long, Vietnam", "ha-long-bay",
     "alias: every non-generic word of the name is a feature noun")
case(M, True, "Driving in the Great Smokey Mountains", "great-smoky-mountains",
     "alias plural: 'Smokey' is the common misspelling")
case(M, True, "Great Smokey Mountain National Park 4K - Driving Into The Clouds",
     "great-smoky-mountains", "the singular form, as actually stored")
case(M, True, "Riva del Garda Lake Garda Italy Walking Tour", "italian-lakes",
     "alias: a region is only ever filmed as one of its lakes")
case(M, True, "Barcelona Walking Tour, Catalonia Spain", "catalonia",
     "region inherits its city's footage — the clause NOT reverted")

# --- wrong_place_title: Canadian provinces --------------------------------
case(W, True, "Ross Bay, Victoria BC - Sunset Walk", "victoria-peak",
     "', BC' anchors Canada; Victoria Peak is in Hong Kong")
case(W, True, "Walking in Victoria, British Columbia", "victoria-peak")
case(W, False, "Walking Tour, on a Rainy Morning in Kowloon", "victoria-peak",
     "', on' is ordinary English — ON is deliberately not an abbreviation")

# --- city_tour_of_the_wild ------------------------------------------------
case(C, True, "Zhangye City Walk 4K - Downtown Streets", "zhangye-danxia",
     "the city's streets standing in for the geopark")
case(C, False, "Downtown SEDONA Arizona Walking Tour", "sedona",
     "Sedona IS a town typed nature — it names itself")
case(C, False, "Driving from Downtown Yan'An to China's Famous Hukou Waterfall",
     "hukou-waterfall", "an honest drive that merely starts downtown")

# --- music_loop_not_a_cam -------------------------------------------------
for want, title in [
    (True, "24/7 Chill Italian Vibes & Mediterranean Music \U0001f3b6 "
           "Scenic Amalfi Coast & Lake Como Relaxation 4K"),
    (True, "Lofi Beats to Study To - Tokyo Rain Ambience"),
    (False, "Amalfi Coast Live Webcam with Relaxing Music"),
    (False, "Times Square Live Camera"),
]:
    got = em.music_loop_not_a_cam(title)
    if got != want:
        fails.append(f"FAIL music_loop_not_a_cam want={want} got={got}: {title[:70]}")

# --- BAD_CAM: lottery studios, BAD_DRIVE: urbex ---------------------------
for rx, want, title in [
    (em.BAD_CAM, True, "LIVE DRAW TOTO MACAU 5D HARI INI"),
    (em.BAD_CAM, False, "Macau Senado Square Live Webcam"),
    (em.BAD_DRIVE, True,
     "Road Trip: Exploring abandoned mountainside CCP Buildings (Nanchang)"),
    (em.BAD_DRIVE, False, "Nanchang 4K Night Driving Tour"),
]:
    got = bool(rx.search(title))
    if got != want:
        fails.append(f"FAIL {rx is em.BAD_CAM and 'BAD_CAM' or 'BAD_DRIVE'} "
                     f"want={want} got={got}: {title[:70]}")

# --- "New X" is not X, but "New York" IS New York -------------------------
# mexico-city's distinctive tokens reduce to just ("mexico",) because "city"
# is generic, so every title containing "New Mexico" read as a video of Mexico
# City — that is what cost Albuquerque its Sandia Peak Tramway tab. The guard
# has to stay asymmetric: new-york-city reduces to ("york",) and genuinely
# needs "New York" to match it.
for pid, want, title in [
    ("albuquerque", False,
     "Sandia Peak Tramway, New Mexico \U0001f332 - America's Longest Aerial Tramway [4K]"),
    ("albuquerque", True, "Mexico City Centro Historico Walking Tour 4K"),
    ("mexico-city", False, "Mexico City Centro Historico Walking Tour 4K"),
    ("boston", True, "New York City Times Square Walking Tour"),
    ("new-york-city", False, "New York City Times Square Walking Tour"),
    ("new-orleans", False, "New Orleans French Quarter Walk 4K"),
]:
    got = em.wrong_place_title(title, place(pid))
    if got != want:
        fails.append(f"FAIL wrong_place_title[{pid}] want={want} got={got}: "
                     f"{title[:60]}")

if fails:
    print("\n".join(fails))
    print(f"\nvetting: FAILED ({len(fails)})")
    sys.exit(1)
print("vetting: all cases pass")
