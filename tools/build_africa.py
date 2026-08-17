#!/usr/bin/env python3
"""
build_africa.py — the Africa batch (2026-08).

WHAT WAS WRONG
    Africa was the thinnest continent in the atlas by a wide margin: 23 places
    across **7 of 54 countries**, in a 45 KB file, and 8 of those 23 were
    skeletons — no blurb, no fun fact, no highlights, no region. Empty
    highlights is not merely thin prose: `enrich_monuments.py` spends
    highlights as its search terms, so Luxor — a place with more standing
    monuments per square kilometre than almost anywhere on earth — could never
    earn a monument tab, because there was nothing to search with.

    The whole of West Africa was one city. Central Africa, the Sahel, the Horn
    and the Indian Ocean islands had nothing at all. A continent of 30 million
    km² was Morocco, Egypt, Kenya, Senegal, Ethiopia, the Gambia and South
    Africa.

WHAT THIS DOES
    Adds the new places and fills the skeletons in one pass, the same shape as
    `build_latinamerica.py`. Editorial choice is ours — which town, which
    landmark, what is worth saying — but every **coordinate comes from Wikidata
    P625** and every **slug is resolved live** and stored as the article's
    canonical title, per README "Filling a region out". Nothing here is
    recalled from memory except the prose.

    Re-runnable and additive: a place that already exists keeps every field it
    already has (and always keeps `walk`/`webcam`/`window`/`monuments` — those
    belong to the scene pipeline, not to us). Only empty fields get filled.

THE NAMESAKE GUARD, AND WHY A BOX IS NOT ENOUGH HERE
    Every other batch could lean on a bounding box: a slug that resolves
    outside the continent resolved to the wrong article. Africa breaks that.
    Any box wide enough to hold Bizerte (37.28°N) also holds Lagos, *Portugal*
    (37.10°N, -8.67°E) — the exact namesake this batch is most likely to hit,
    since Lagos, Nigeria is one of the places being added. The box cannot see
    the difference.

    So this batch checks **Wikidata P17 (country)** as well, resolved live for
    the country articles themselves so no QID is typed from memory. A mismatch
    is a **warning, not a refusal**: P17 legitimately points at historical or
    unrecognised states — `Tripoli,_Libya` answers Q3433694 (Tripolitania),
    not Q1016, and Laas Geel answers Somaliland. Those are correct articles
    with surprising P17s, and refusing them would lose real places. The box
    stays the hard refusal; COUNTRY is the line a human reads.

Run:  python3 tools/build_africa.py            # report only
      python3 tools/build_africa.py --apply
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wiki import Resolver, haversine

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "data" / "africa.json"

# How far a record may sit from its own article's P625 before we want a human
# to look. An `area` type legitimately sits far from its centroid point.
FAR_KM = 60.0
AREA_TYPES = {"nature", "desert", "island", "mountain"}

# These strings are not free-form. `build_countries.py` counts a country's
# places by matching `loc["country"]` against the registry's *canonical name*,
# so "Ivory Coast" here would leave Côte d'Ivoire showing zero places while
# quietly holding four. Every name below is copied from COUNTRIES in
# build_countries.py, spelling and all.
COUNTRY_CODE = {
    "Algeria": "DZ", "Angola": "AO", "Benin": "BJ", "Botswana": "BW",
    "Burkina Faso": "BF", "Burundi": "BI", "Cameroon": "CM",
    "Cape Verde": "CV", "Central African Republic": "CF", "Chad": "TD",
    "Comoros": "KM", "Côte d'Ivoire": "CI", "DR Congo": "CD",
    "Djibouti": "DJ", "Egypt": "EG", "Equatorial Guinea": "GQ",
    "Eritrea": "ER", "Eswatini": "SZ", "Ethiopia": "ET", "Gabon": "GA",
    "Gambia": "GM", "Ghana": "GH", "Guinea": "GN", "Guinea-Bissau": "GW",
    "Kenya": "KE", "Lesotho": "LS", "Liberia": "LR", "Libya": "LY",
    "Madagascar": "MG", "Malawi": "MW", "Mali": "ML", "Mauritania": "MR",
    "Mauritius": "MU", "Morocco": "MA", "Mozambique": "MZ", "Namibia": "NA",
    "Niger": "NE", "Nigeria": "NG", "Republic of the Congo": "CG",
    "Rwanda": "RW", "São Tomé and Príncipe": "ST", "Senegal": "SN",
    "Seychelles": "SC", "Sierra Leone": "SL", "Somalia": "SO",
    "South Africa": "ZA", "South Sudan": "SS", "Sudan": "SD",
    "Tanzania": "TZ", "Togo": "TG", "Tunisia": "TN", "Uganda": "UG",
    "Zambia": "ZM", "Zimbabwe": "ZW",
}

# The article title to resolve for each country, where it is not the canonical
# name with underscores. Resolving these gives us the expected P17 QID without
# a single QID typed from memory.
COUNTRY_SLUG = {
    "Gambia": "The_Gambia",
    "Côte d'Ivoire": "Ivory_Coast",
    "DR Congo": "Democratic_Republic_of_the_Congo",
}

# Wide enough for Cape Verde (-25.4°), Rodrigues (63.4°), Bizerte (37.3°) and
# Cape Agulhas (-34.8°), and nothing further. See the module docstring: this is
# a coarse net, not the namesake guard — COUNTRY is.
AFRICA_BOX = (-35.5, 37.6, -26.0, 63.6)      # lat_min, lat_max, lng_min, lng_max


# ---------------------------------------------------------------------------
# THE CURATED CONTENT.
#
# highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, a
# dish, a dance, an era or a festival. Africa makes that rule easy to break:
# "Dogon", "Ashanti", "Maasai", "Berber", "Zulu" all read like places and are
# all peoples. Each highlight below is a thing that stands somewhere, so a
# video of it can exist. (See enrich_monuments.NOT_A_MONUMENT.)
#
# A `None` slug is deliberate: the UI renders highlights as text chips, so a
# name with no link costs nothing and a dead link is rot.
#
# `search_name` is set wherever the bare name has a namesake somewhere else —
# Lagos (Portugal), Tripoli (Lebanon), Victoria (British Columbia, Hong Kong,
# Australia). No downstream title guard can catch a namesake, so it is said
# here, at the only point where we know.
# ---------------------------------------------------------------------------
NEW = {
# ============================== TUNISIA ==============================
"tunis": dict(
    name="Tunis", slug="Tunis", country="Tunisia", region="Tunis Governorate",
    type="city", tag="famous", emoji="🕌", sounds=["city-hum.mp3"],
    highlights=[("Medina of Tunis", "Medina_of_Tunis"),
                ("Al-Zaytuna Mosque", "Al-Zaytuna_Mosque"),
                ("Bardo National Museum", "Bardo_National_Museum_(Tunis)"),
                ("Avenue Habib Bourguiba", "Avenue_Habib_Bourguiba"),
                ("Bab el Bhar", "Bab_el_Bhar")],
    blurb="A capital in two halves that meet at a gate: behind it a medina of "
          "700 monuments and covered souks laid out in the 8th century, in "
          "front of it a French colonial grid of cafés and jacaranda down the "
          "middle of the avenue. The whole city sits between a salt lake and "
          "the sea.",
    fact="The Bardo Museum holds the largest collection of Roman mosaics in "
         "the world, most of them lifted from villa floors within a day's "
         "drive of the building.",
    tip="Climb to the roof terrace of one of the souk's carpet shops off Rue "
        "Jamaa Ez Zitouna — they let you up for nothing and the minaret of the "
        "Zitouna is suddenly at eye level."),
"carthage": dict(
    name="Carthage", slug="Carthage", country="Tunisia",
    region="Tunis Governorate", type="ruin", tag="famous", emoji="🏛️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Byrsa Hill", "Byrsa"),
                ("Baths of Antoninus", "Baths_of_Antoninus"),
                ("Tophet of Carthage", None),
                ("Punic Ports", None)],
    blurb="The city that fought Rome three times and lost the third time "
          "completely is now a leafy seaside suburb of Tunis, with its ruins "
          "scattered between villas. What stands is mostly the Roman city "
          "built on top of the Punic one — including the largest bath complex "
          "outside Rome itself, right at the waterline.",
    fact="The two Punic harbours are still legible from the air: a rectangular "
         "commercial basin and, behind it, a perfect circle that berthed some "
         "220 warships around a central island.",
    tip="Go to the Antonine Baths late in the afternoon — the columns are lit "
        "from the west and the sea comes right up to the terrace wall."),
"sidi-bou-said": dict(
    name="Sidi Bou Said", slug="Sidi_Bou_Said", country="Tunisia",
    region="Tunis Governorate", type="village", tag="famous", emoji="🔵",
    sounds=["ocean-waves.mp3"],
    highlights=[("Ennejma Ezzahra", "Ennejma_Ezzahra"),
                ("Dar el-Annabi", None),
                ("Café des Nattes", None),
                ("Sidi Bou Said Lighthouse", None)],
    blurb="A clifftop village above the Gulf of Tunis where every wall is "
          "whitewashed and every door, shutter and window grille is the same "
          "cobalt blue — a rule imposed by a French baron in 1915 and never "
          "repealed. One steep cobbled street runs up from the bottom to the "
          "lighthouse.",
    fact="The blue-and-white scheme was the doing of Rodolphe d'Erlanger, who "
         "built his own palace here and made the colour a condition of "
         "building permits.",
    tip="Keep walking past the cafés to the small cemetery at the cliff edge — "
        "almost nobody does, and it has the best view back along the coast to "
        "Carthage."),
"el-jem": dict(
    name="El Jem", slug="El_Djem", country="Tunisia",
    region="Mahdia Governorate", type="ruin", tag="hidden", emoji="🏟️",
    sounds=["wind.mp3"],
    highlights=[("Amphitheatre of El Jem", "Amphitheatre_of_El_Jem"),
                ("El Djem Archaeological Museum", None),
                ("House of Africa", None)],
    blurb="A small inland town that happens to contain the third-largest Roman "
          "amphitheatre ever built, standing three tiers high in the middle of "
          "the olive plain with houses pressed up against its arches. It seated "
          "35,000 in a town that has never had that many people.",
    fact="Because it was never quarried down to the foundations, you can still "
         "walk the underground corridors where animals and fighters waited "
         "under the sand of the arena floor.",
    tip="The museum a kilometre south is usually empty and has the mosaics "
        "that came out of the villas — including floors still in situ under "
        "open sky."),
"kairouan": dict(
    name="Kairouan", slug="Kairouan", country="Tunisia",
    region="Kairouan Governorate", type="history", tag="famous", emoji="🕌",
    sounds=["desert-wind.mp3"],
    highlights=[("Great Mosque of Kairouan", "Great_Mosque_of_Kairouan"),
                ("Mosque of the Three Doors", "Mosque_of_the_Three_Doors"),
                ("Aghlabid Basins", "Aghlabid_Basins"),
                ("Zaouia of Sidi Sahab", "Mosque_of_the_Barber")],
    blurb="The oldest Muslim city in North Africa, founded in 670 on a dry "
          "plain with no river and no harbour, and for three centuries the "
          "intellectual capital of the western Islamic world. Its Great Mosque "
          "is a fortress from outside and a forest of reused Roman columns "
          "inside.",
    fact="Two 9th-century open reservoirs on the edge of town, one 128 m "
         "across, settled and stored the water that made a city possible where "
         "there was none.",
    tip="The mosque's courtyard is open to visitors even when the prayer hall "
        "is not; go at midday when the white marble paving throws light up into "
        "the arcades."),
"tozeur": dict(
    name="Tozeur", slug="Tozeur", country="Tunisia",
    region="Tozeur Governorate", type="desert", tag="hidden", emoji="🌴",
    sounds=["desert-wind.mp3"],
    highlights=[("Chott el Djerid", "Chott_el_Djerid"),
                ("Chebika", "Chebika"),
                ("Tamerza", "Tamerza"),
                ("Ouled el-Hadef", None)],
    blurb="An oasis town on the edge of a salt flat, where a quarter of a "
          "million palms are irrigated by a 13th-century division of springs "
          "still measured in the same units. The old quarter is built of "
          "yellow brick laid in relief patterns you can read like textile.",
    fact="The palm groves run on a water-sharing scheme drawn up by the "
         "mathematician Ibn Chabbat in the 1200s, allocating flow by time "
         "rather than volume.",
    tip="Drive out onto the causeway across Chott el Djerid at sunrise — the "
        "salt crust turns pink and the far shore lifts off the ground in a "
        "mirage."),
"djerba": dict(
    name="Djerba", slug="Djerba", country="Tunisia",
    region="Medenine Governorate", type="island", tag="hidden", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("El Ghriba Synagogue", "El_Ghriba_Synagogue"),
                ("Houmt Souk", "Houmt_Souk"),
                ("Borj El Kebir", None),
                ("Roman Road of Djerba", None)],
    blurb="A flat, low island off the Gulf of Gabès, joined to the mainland by "
          "a Roman causeway that is still the road in. Whitewashed courtyard "
          "houses sit apart from each other across the whole island rather "
          "than clustering, so it reads as one enormous village.",
    fact="El Ghriba is the oldest synagogue in Africa still in use, and its "
         "community has kept a continuous presence on the island for well over "
         "a thousand years.",
    tip="Houmt Souk's fish market runs an auction most mornings — the "
        "octopus come up in the terracotta pots they were caught in."),
"dougga": dict(
    name="Dougga", slug="Dougga", country="Tunisia",
    region="Beja Governorate", type="ruin", tag="hidden", emoji="🏛️",
    sounds=["wilderness.mp3"],
    highlights=[("Capitol of Dougga", None),
                ("Libyco-Punic Mausoleum", "Libyco-Punic_Mausoleum_of_Dougga"),
                ("Theatre of Dougga", None)],
    blurb="The best-preserved Roman town in North Africa, spread over a "
          "hillside of olive groves with no modern village on top of it. The "
          "streets, the forum, the theatre and a Capitol with its portico "
          "still standing are all where they were left.",
    fact="Its 2nd-century BC Libyco-Punic mausoleum carries a bilingual "
         "inscription that gave scholars their key to the Numidian language.",
    tip="Follow the paved street downhill past the baths to the house with the "
        "twelve-seat public latrine — it is intact, and nobody is ever "
        "standing there."),

# ============================== ALGERIA ==============================
"algiers": dict(
    name="Algiers", slug="Algiers", country="Algeria",
    region="Algiers Province", type="city", tag="famous", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Casbah of Algiers", "Casbah_of_Algiers"),
                ("Notre-Dame d'Afrique", "Notre-Dame_d'Afrique"),
                ("Ketchaoua Mosque", "Ketchaoua_Mosque"),
                ("Maqam Echahid", "Maqam_Echahid"),
                ("Jardin d'Essai du Hamma", "Jardin_d'Essai_du_Hamma")],
    blurb="A white city stacked up a steep amphitheatre above its bay — French "
          "boulevards with arcades along the waterfront, and above them the "
          "Casbah, a nearly vertical Ottoman quarter of stepped lanes where "
          "the houses lean on each other across the gap.",
    fact="Algiers was called *la Blanche* for the lime wash on its houses, "
          "which colonial ordinance and habit have kept up: seen from the sea "
          "the whole slope is still one colour.",
    tip="The Jardin d'Essai below the Casbah has a 400 m alley of Ficus and "
        "Washingtonia palms planted in 1832 — it is free, shaded, and mostly "
        "used by people reading."),
"constantine": dict(
    name="Constantine", slug="Constantine,_Algeria", country="Algeria",
    region="Constantine Province", type="city", tag="hidden", emoji="🌉",
    sounds=["city-hum.mp3"],
    highlights=[("Sidi M'Cid Bridge", "Sidi_M'Cid_Bridge"),
                ("Emir Abdelkader Mosque", "Emir_Abdelkader_Mosque"),
                ("Palace of Ahmed Bey", "Palace_of_Ahmed_Bey"),
                ("Rhumel Gorge", None)],
    blurb="A city on a rock, split from its surroundings by a limestone gorge "
          "200 m deep and joined back to them by a series of bridges — one of "
          "them a footbridge slung across the void on cables in 1912. Streets "
          "end at railings above nothing.",
    fact="Constantine has been continuously inhabited for some 2,500 years, "
         "which its defensive position explains entirely: the gorge does the "
         "work of a wall on three sides.",
    tip="Walk the Sidi M'Cid bridge at dusk and then take the stairs cut into "
        "the gorge wall below it — the city noise drops away within twenty "
        "steps."),
"timgad": dict(
    name="Timgad", slug="Timgad", country="Algeria",
    region="Batna Province", type="ruin", tag="hidden", emoji="🏛️",
    sounds=["wind.mp3"],
    highlights=[("Arch of Trajan", None),
                ("Library of Timgad", "Library_of_Timgad"),
                ("Timgad Theatre", None)],
    blurb="A Roman colony founded around AD 100 on an empty plain and laid out "
          "as a perfect grid for retired soldiers — then abandoned, buried in "
          "sand, and dug out almost complete. You can read the town plan by "
          "standing at the crossroads and looking four ways.",
    fact="Its public library, paid for by a private citizen, had niches for "
         "some 3,000 scrolls — one of very few Roman libraries whose ground "
         "plan survives at all.",
    tip="Climb the tiers of the theatre for the only view that shows the grid "
        "whole, with the Aurès mountains closing the horizon behind it."),
"ghardaia": dict(
    name="Ghardaïa", slug="Ghardaïa", country="Algeria",
    region="Ghardaïa Province", type="desert", tag="hidden", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("M'Zab Valley", "M'zab"),
                ("Beni Isguen", "Beni_Isguen"),
                ("Ghardaïa Mosque", None)],
    blurb="The largest of five fortified towns built in a dry valley in the "
          "11th century, each one a cone of cubic houses spiralling up to a "
          "mosque-fortress at the summit. Nothing is ornamental; the plan is "
          "the architecture.",
    fact="Le Corbusier studied the M'Zab towns in the 1930s and took their "
         "stacked terraces and shaded arcades straight into his own thinking "
         "about mass housing.",
    tip="The pyramid-roofed market square of Ghardaïa runs a daily auction "
        "where sellers walk laps of the arcade calling their own price."),
"tassili-n-ajjer": dict(
    name="Tassili n'Ajjer", slug="Tassili_n'Ajjer", country="Algeria",
    region="Illizi Province", type="desert", tag="famous", emoji="🖼️",
    sounds=["desert-wind.mp3"],
    highlights=[("Djanet", "Djanet"),
                ("Tadrart Rouge", None),
                ("Sefar rock shelters", None)],
    blurb="A sandstone plateau in the deep Sahara eroded into some 300 natural "
          "arches and thousands of rock towers, and carrying one of the "
          "largest concentrations of prehistoric art anywhere — cattle, "
          "giraffe and swimmers painted on rock that is now bare desert.",
    fact="The paintings record a green Sahara: the animals in them need "
         "grassland and standing water, and the newest layers show the moment "
         "the herds gave way to camels.",
    tip="The plateau is walked, not driven — the classic route out of Djanet "
        "takes days on foot with pack animals, camping under the arches."),
"oran": dict(
    name="Oran", slug="Oran", country="Algeria", region="Oran Province",
    type="coastal", tag="hidden", emoji="⚓", sounds=["ocean-waves.mp3"],
    highlights=[("Fort Santa Cruz", "Fort_Santa_Cruz"),
                ("Great Mosque of Oran", "Great_Mosque_of_Oran"),
                ("Place du 1er Novembre", None),
                ("Oran Cathedral", "Oran_Cathedral")],
    blurb="Algeria's second city and its most Mediterranean-facing one — a "
          "port under a mountain crowned by a Spanish fort, with an opera "
          "house, a long corniche and the loudest music scene in the country.",
    fact="Raï grew up in Oran's bars and wedding halls in the 1970s and 80s "
         "before it left the country entirely; the city is still where the "
         "form is argued about.",
    tip="Take the road up to Santa Cruz on foot from Sidi El Houari — it is a "
        "steep hour through the old Spanish quarter and the bay opens up "
        "behind you the whole way."),

# ============================== LIBYA ==============================
"tripoli-libya": dict(
    name="Tripoli", slug="Tripoli,_Libya", country="Libya",
    region="Tripoli District", type="city", tag="famous", emoji="🕌",
    sounds=["ocean-waves.mp3"], search_name="Tripoli Libya",
    highlights=[("Red Castle", "Red_Castle_Museum"),
                ("Arch of Marcus Aurelius", "Arch_of_Marcus_Aurelius_(Tripoli)"),
                ("Gurgi Mosque", "Gurgi_Mosque"),
                ("Martyrs' Square", "Martyrs'_Square,_Tripoli")],
    blurb="Libya's capital sits on a rocky headland with its old walled city "
          "pushed right up against the harbour — a dense grid of Ottoman "
          "houses, a Roman arch standing in the middle of it, and a castle at "
          "the corner that has been rebuilt by everyone who ever held the "
          "port.",
    fact="The four-way arch of Marcus Aurelius, finished in AD 165, is the "
         "oldest structure still standing in the city and now sits several "
         "metres below the modern street.",
    tip="The covered souk behind the Gurgi Mosque still works in trades by "
        "lane — coppersmiths in one, gold in the next, and the noise tells you "
        "which one you are in."),
"leptis-magna": dict(
    name="Leptis Magna", slug="Leptis_Magna", country="Libya",
    region="Murqub District", type="ruin", tag="famous", emoji="🏛️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Arch of Septimius Severus", None),
                ("Leptis Magna Theatre", None),
                ("Hadrianic Baths", None),
                ("Severan Basilica", None)],
    blurb="One of the most complete Roman cities anywhere, on an empty stretch "
          "of Libyan coast — a marble forum, a basilica standing to two "
          "storeys, a theatre facing the sea, and streets that were buried in "
          "sand for a thousand years and so were never robbed for stone.",
    fact="Its scale is political: Septimius Severus, who became emperor in "
         "AD 193, was born here and rebuilt his home town on an imperial "
         "budget.",
    tip="The far end of the site, past the amphitheatre, has a circus right on "
        "the shore — 450 m long, with the sea breaking behind the finishing "
        "straight."),
"ghadames": dict(
    name="Ghadames", slug="Ghadames", country="Libya",
    region="Nalut District", type="desert", tag="hidden", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Old Town of Ghadames", None),
                ("Ghadames Palm Gardens", None)],
    blurb="An oasis on the Algerian and Tunisian border where the old town is "
          "built as one continuous structure: covered alleys at ground level "
          "for the men, an open roof terrace network above them used by the "
          "women, and palm gardens fed by a single spring.",
    fact="Ghadames is called the pearl of the desert for its whitewash and its "
         "shade — the covered streets keep the interior tens of degrees cooler "
         "than the sand outside.",
    tip="The roof level is a second town: you can walk a large part of the old "
        "city without ever coming down to the lanes."),

# ============================== MOROCCO (additions) ==============================
"rabat": dict(
    name="Rabat", slug="Rabat", country="Morocco",
    region="Rabat-Sale-Kenitra", type="city", tag="famous", emoji="🏛️",
    sounds=["city-hum.mp3"],
    highlights=[("Hassan Tower", "Hassan_Tower"),
                ("Kasbah of the Udayas", "Kasbah_of_the_Udayas"),
                ("Chellah", "Chellah"),
                ("Mausoleum of Mohammed V", "Mausoleum_of_Mohammed_V"),
                ("Rabat Medina", None)],
    blurb="A capital that stays quiet: a walled medina, a blue-and-white "
          "kasbah on the cliff above the river mouth, and an enormous unfinished "
          "12th-century mosque whose minaret stops halfway up and whose columns "
          "stand in rows with nothing on them.",
    fact="Chellah, on the edge of the modern city, is a Roman town with a "
         "Merinid necropolis built inside its walls — and a large colony of "
         "storks nesting on top of both.",
    tip="Sit in the Andalusian garden inside the Kasbah of the Udayas in the "
        "late afternoon; entry is free and the terrace beyond it looks straight "
        "across the Bou Regreg to Salé."),
"tangier": dict(
    name="Tangier", slug="Tangier", country="Morocco",
    region="Tangier-Tetouan-Al Hoceima", type="coastal", tag="famous",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    highlights=[("Cap Spartel", "Cap_Spartel"),
                ("Caves of Hercules", "Caves_of_Hercules"),
                ("Grand Socco", "Grand_Socco"),
                ("Kasbah of Tangier", None)],
    blurb="The city where the Mediterranean meets the Atlantic, 14 km from "
          "Spain and visibly aware of it. An international zone until 1956, it "
          "kept the habits: cafés full of arguments, a medina tipping down to "
          "the port, and a shoreline that faces two seas at once.",
    fact="At Cap Spartel you can stand at the corner where the Atlantic and "
         "the Mediterranean meet; on a clear day the Spanish coast is a solid "
         "line across the strait.",
    tip="The Café Hafa has been cut into terraces on the cliff since 1921 — "
        "mint tea, plastic chairs, and nothing between you and the water."),
"essaouira": dict(
    name="Essaouira", slug="Essaouira", country="Morocco",
    region="Marrakesh-Safi", type="coastal", tag="hidden", emoji="🌬️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Skala de la Ville", None),
                ("Medina of Essaouira", None),
                ("Mogador Island", "Mogador_Island"),
                ("Essaouira Harbour", None)],
    blurb="A walled Atlantic port laid out on a grid by a French engineer in "
          "the 1760s, which is why the medina has straight streets and "
          "sightlines nowhere else in Morocco has. Blue boats, gulls, ramparts "
          "with cannon still pointing out to sea, and wind more or less always.",
    fact="The reliable northeast wind that makes the beach a kitesurfing "
         "fixture is the same one that made this the safest harbour on the "
         "coast for square-rigged ships.",
    tip="Walk the Skala ramparts at the north end just before sunset — the "
        "cannon line is free to enter and the light comes straight down the "
        "length of it."),
"ait-benhaddou": dict(
    name="Aït Benhaddou", slug="Aït_Benhaddou", country="Morocco",
    region="Draa-Tafilalet", type="village", tag="famous", emoji="🏰",
    sounds=["desert-wind.mp3"],
    highlights=[("Ksar of Aït Benhaddou", None),
                ("Telouet Kasbah", "Telouet_Kasbah"),
                ("Ounila Valley", None)],
    blurb="A fortified earthen village stacked up one side of a hill above a "
          "riverbed, on the old caravan road from the Sahara to Marrakesh. "
          "Rammed earth and straw, towers with geometric relief, and a "
          "granary at the top that everything else defends.",
    fact="Because mud brick has to be renewed constantly, most of what stands "
         "is under a century old on foundations far older — the village is a "
         "building maintained rather than a ruin preserved.",
    tip="Cross the river on the stepping stones rather than the new bridge and "
        "climb to the agadir at the summit; the whole Ounila valley opens out "
        "behind the hill."),
"meknes": dict(
    name="Meknes", slug="Meknes", country="Morocco", region="Fes-Meknes",
    type="history", tag="hidden", emoji="🏰", sounds=["plaza.mp3"],
    highlights=[("Bab Mansour", "Bab_Mansour"),
                ("Volubilis", "Volubilis"),
                ("Heri es-Souani", None),
                ("Place el-Hedim", None)],
    blurb="The quietest of Morocco's four imperial cities, and the most "
          "monumental — a 17th-century sultan spent fifty years walling it, "
          "building granaries the size of cathedrals and a gate so large the "
          "square in front of it feels undersized.",
    fact="The Heri es-Souani granary and stables were built with metre-thick "
         "walls and underfloor water channels to keep grain cool enough to "
         "store for years, for a garrison of tens of thousands of horses.",
    tip="Volubilis is half an hour north and the mosaics are still on the "
        "floors of the houses, outdoors, with nobody standing over them."),
"toubkal": dict(
    name="Toubkal", slug="Toubkal", country="Morocco", region="Marrakesh-Safi",
    type="mountain", tag="hidden", emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Imlil", "Imlil"),
                ("Toubkal National Park", "Toubkal_National_Park"),
                ("Sidi Chamharouch", None)],
    blurb="North Africa's highest summit, 4,167 m of bare red rock two hours "
          "from Marrakesh, reached on foot from a walnut-shaded village at the "
          "end of the road. Snow on it from November to May, and the Sahara "
          "visible from the top on a clear morning.",
    fact="The trail passes Sidi Chamharouch, a whitewashed boulder shrine at "
         "2,300 m that pilgrims still walk to — a working destination on what "
         "looks like a purely alpine route.",
    tip="Stay a night in Imlil and start before dawn: by ten the cloud usually "
        "builds off the valley and the summit view closes."),

# ============================== EGYPT (additions) ==============================
"alexandria": dict(
    name="Alexandria", slug="Alexandria", country="Egypt",
    region="Alexandria Governorate", type="coastal", tag="famous", emoji="🏛️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Bibliotheca Alexandrina", "Bibliotheca_Alexandrina"),
                ("Citadel of Qaitbay", "Citadel_of_Qaitbay"),
                ("Pompey's Pillar", "Pompey's_Pillar_(column)"),
                ("Catacombs of Kom El Shoqafa", "Catacombs_of_Kom_El_Shoqafa"),
                ("Montaza Palace", "Montaza_Palace")],
    blurb="Egypt's Mediterranean city, strung along a 15 km corniche and "
          "facing away from the rest of the country. Founded by Alexander, run "
          "by Greeks for three centuries, and rebuilt so often that most of the "
          "ancient city is now under the modern one or under the harbour.",
    fact="The Citadel of Qaitbay stands on the exact footprint of the "
         "Pharos lighthouse and was partly built from its fallen stone after "
         "an earthquake brought the tower down.",
    tip="Ride a tram — Africa's oldest, running since 1863 — east along the "
        "shore to Montaza for the price of a few pence and a slow look at the "
        "whole waterfront."),
"abu-simbel": dict(
    name="Abu Simbel", slug="Abu_Simbel", country="Egypt",
    region="Aswan Governorate", type="history", tag="famous", emoji="🗿",
    sounds=["desert-wind.mp3"],
    highlights=[("Great Temple of Ramesses II", None),
                ("Temple of Hathor and Nefertari", None),
                ("Lake Nasser", "Lake_Nasser")],
    blurb="Two temples cut into a sandstone cliff above the Nile in the 13th "
          "century BC, fronted by four seated colossi of Ramesses II each over "
          "20 m high. They face the sunrise across what is now a lake the size "
          "of a small sea.",
    fact="The whole complex was sawn into 1,036 blocks in the 1960s and "
         "rebuilt 65 m higher and 200 m back, on an artificial hill, to keep it "
         "above the rising Aswan reservoir.",
    tip="Twice a year, in February and October, the rising sun reaches all the "
        "way down the 60 m axis and lights the statues in the innermost "
        "sanctuary."),
"siwa-oasis": dict(
    name="Siwa Oasis", slug="Siwa_Oasis", country="Egypt",
    region="Matrouh Governorate", type="desert", tag="hidden", emoji="🌴",
    sounds=["desert-wind.mp3"],
    highlights=[("Shali Fortress", None),
                ("Temple of the Oracle", "Temple_of_the_Oracle"),
                ("Great Sand Sea", "Great_Sand_Sea"),
                ("Cleopatra's Bath", None)],
    blurb="A depression of springs and 300,000 date palms 50 km from the "
          "Libyan border and 550 km from the Nile, with its own language and a "
          "ruined salt-brick citadel melting slowly in the middle of town. The "
          "Great Sand Sea starts at the edge of the gardens.",
    fact="Alexander the Great crossed the desert to the oracle here in 331 BC "
         "and left satisfied; what the priests told him he never repeated.",
    tip="Float in the cold spring at Cleopatra's Bath early, then take a bike "
        "out to Fatnas Island in the salt lake for the sunset — it is flat the "
        "whole way."),
"sharm-el-sheikh": dict(
    name="Sharm El Sheikh", slug="Sharm_El_Sheikh", country="Egypt",
    region="South Sinai Governorate", type="coastal", tag="famous", emoji="🐠",
    sounds=["ocean-waves.mp3"],
    highlights=[("Ras Muhammad National Park", "Ras_Muhammad_National_Park"),
                ("Naama Bay", "Naama_Bay"),
                ("Tiran Island", "Tiran_Island"),
                ("Shark's Bay", None)],
    blurb="The southern tip of Sinai, where desert mountains come down to a "
          "reef wall that drops hundreds of metres a few strokes from the "
          "shore. Warm, clear and calm most of the year, which is why the whole "
          "coast became dive resorts.",
    fact="Ras Muhammad, at the very point, is where the Gulfs of Suez and "
         "Aqaba meet — the currents concentrate fish there in numbers that make "
         "it one of the most-dived places on earth.",
    tip="You do not need a boat: walk in off the beach at Ras Umm Sid and the "
        "reef edge is thirty metres out."),
"saint-catherine-sinai": dict(
    name="Saint Catherine's Monastery", slug="Saint_Catherine's_Monastery",
    country="Egypt", region="South Sinai Governorate", type="history",
    tag="hidden", emoji="⛪", sounds=["mountain-wind.mp3"],
    highlights=[("Mount Sinai", "Mount_Sinai"),
                ("Mount Catherine", "Mount_Catherine"),
                ("Sinai Icon Collection", None)],
    blurb="A walled 6th-century monastery in a granite valley at 1,570 m, "
          "occupied without a break since it was built and holding a library "
          "second only to the Vatican's for early manuscripts. Bedouin villages "
          "and bare red mountains in every direction.",
    fact="Its walls have never been breached in fifteen centuries, and it "
         "holds a letter of protection attributed to the Prophet Muhammad "
         "alongside its Byzantine icons.",
    tip="Climb the 3,750 Steps of Repentance rather than the camel path — they "
        "were cut by a single monk as penance and they come out at the summit "
        "chapel."),
"dahab": dict(
    name="Dahab", slug="Dahab", country="Egypt",
    region="South Sinai Governorate", type="coastal", tag="hidden", emoji="🤿",
    sounds=["ocean-waves.mp3"],
    highlights=[("Blue Hole", "Blue_Hole_(Red_Sea)"),
                ("Ras Abu Galum", None),
                ("Dahab Lagoon", None)],
    blurb="A former Bedouin fishing village on the Gulf of Aqaba that turned "
          "into a low-rise strip of cushions and dive shops without ever "
          "growing towers. Mountains behind, Saudi Arabia across the water, and "
          "a reef you can wade to.",
    fact="The Blue Hole just north of town is a 100 m submarine sinkhole in "
         "the reef — famous, beautiful, and one of the most dangerous dive "
         "sites in the world for anyone who tries its deep arch.",
    tip="Walk or camel north from the Blue Hole to Ras Abu Galum, where there "
        "is no road at all — Bedouin huts on the beach and nothing else."),

# ============================== SUDAN ==============================
"khartoum": dict(
    name="Khartoum", slug="Khartoum", country="Sudan",
    region="Khartoum State", type="city", tag="famous", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Tuti Island", "Tuti_Island"),
                ("National Museum of Sudan", "National_Museum_of_Sudan"),
                ("Omdurman", "Omdurman"),
                ("Al-Mogran", None)],
    blurb="The city at the confluence, where the Blue Nile coming off the "
          "Ethiopian highlands meets the White Nile from the Great Lakes and "
          "the two run side by side for a stretch before mixing. Three towns "
          "face each other across the water and are counted as one capital.",
    fact="The Arabic name is usually read as *khartum*, an elephant's trunk — "
         "the shape of the sandbank curling out where the two rivers join.",
    tip="Tuti Island sits in the middle of the confluence and is still farmed; "
        "the footbridge across is the cheapest way to stand between two "
        "different-coloured rivers."),
"meroe": dict(
    name="Meroë", slug="Meroë", country="Sudan", region="River Nile State",
    type="ruin", tag="famous", emoji="🔺", sounds=["desert-wind.mp3"],
    highlights=[("Nubian pyramids", "Nubian_pyramids"),
                ("Naqa", "Naqa"),
                ("Musawwarat es-Sufra", "Musawwarat_es-Sufra")],
    blurb="The capital of the Kingdom of Kush, whose rulers built some 200 "
          "steep-sided pyramids in the sand east of the Nile — smaller than "
          "Egypt's, far more numerous, and standing in a group on open dunes "
          "with nobody there.",
    fact="Sudan has roughly twice as many ancient pyramids as Egypt does, and "
         "the Meroitic ones are the steepest anywhere, rising at around 70 "
         "degrees.",
    tip="Come at first light: the dunes run right up against the pyramid bases "
        "and the low sun separates every one of them from its own shadow."),

# ============================== MAURITANIA ==============================
"chinguetti": dict(
    name="Chinguetti", slug="Chinguetti", country="Mauritania",
    region="Adrar Region", type="desert", tag="hidden", emoji="📚",
    sounds=["desert-wind.mp3"],
    highlights=[("Friday Mosque of Chinguetti", None),
                ("Adrar Plateau", "Adrar_Plateau"),
                ("Chinguetti Old Quarter", None)],
    blurb="A caravan town on the edge of the Sahara, founded in the 13th "
          "century as a gathering point for pilgrims heading east, and now "
          "half-buried — dunes stand against the walls of the old quarter and "
          "the streets are sand.",
    fact="A handful of family libraries here still hold medieval manuscripts "
         "on law, astronomy and mathematics, kept in the same houses for "
         "generations with almost no institutional support.",
    tip="Ask at one of the libraries in the old town rather than the new — the "
        "keepers will unwrap the books on a table for you and explain what each "
        "one is."),
"nouakchott": dict(
    name="Nouakchott", slug="Nouakchott", country="Mauritania",
    region="Nouakchott", type="city", tag="hidden", emoji="🐟",
    sounds=["ocean-waves.mp3"],
    highlights=[("Port de Pêche", None),
                ("Saudi Mosque", None),
                ("Nouakchott Grand Market", None)],
    blurb="A capital built from almost nothing in 1958 — a village of a few "
          "hundred people chosen because it was neutral ground — now a low, "
          "flat, sand-coloured city of over a million on the Atlantic edge of "
          "the Sahara.",
    fact="Its fishing beach is one of the great sights of the coast: hundreds "
         "of hand-painted pirogues are launched through the surf and hauled "
         "back up the sand by hand every afternoon.",
    tip="Be at the Port de Pêche around four when the boats come in — the "
        "sorting, the gutting and the auction all happen on the sand within a "
        "few metres of the water."),
# ============================== SENEGAL (additions) ==============================
"saint-louis-senegal": dict(
    name="Saint-Louis", slug="Saint-Louis,_Senegal", country="Senegal",
    region="Saint-Louis Region", type="city", tag="hidden", emoji="🏘️",
    sounds=["ocean-waves.mp3"], search_name="Saint-Louis Senegal",
    highlights=[("Faidherbe Bridge", "Faidherbe_Bridge"),
                ("Langue de Barbarie", "Langue_de_Barbarie"),
                ("Guet Ndar", None),
                ("Djoudj National Bird Sanctuary",
                 "Djoudj_National_Bird_Sanctuary")],
    blurb="A colonial-era town built on an island in the mouth of the Senegal "
          "River, with a long iron bridge at one end and a sandbar fishing "
          "quarter at the other. Balconied houses in faded ochre, and pirogues "
          "pulled up on both banks.",
    fact="Saint-Louis was the capital of French West Africa until 1902, and "
         "the first French settlement anywhere in Africa — the grid of the "
         "island has not changed since the 18th century.",
    tip="Cross to Guet Ndar in the early morning; the fishing village on the "
        "sandbar is one of the densest places in the country and the boats "
        "launch straight into Atlantic surf."),
"lake-retba": dict(
    name="Lake Retba", slug="Lake_Retba", country="Senegal",
    region="Dakar Region", type="nature", tag="hidden", emoji="🌸",
    sounds=["wind.mp3"],
    highlights=[("Salt harvesting flats", None),
                ("Dunes of Retba", None)],
    blurb="A shallow lagoon an hour from Dakar, separated from the Atlantic by "
          "a strip of dune, whose water turns rose to deep pink in the dry "
          "season. Men stand chest-deep for hours breaking salt off the bottom "
          "and loading it into pirogues by basket.",
    fact="The colour comes from a salt-loving alga that produces red pigment to "
         "cope with light; the lake is saltier than the Dead Sea at the height "
         "of the dry season.",
    tip="Walk over the dune to the ocean side — a few hundred metres of sand "
        "separates pink water from grey Atlantic, and almost nobody makes the "
        "crossing."),

# ============================== MALI ==============================
"djenne": dict(
    name="Djenné", slug="Djenné", country="Mali", region="Mopti Region",
    type="history", tag="famous", emoji="🕌", sounds=["desert-wind.mp3"],
    highlights=[("Great Mosque of Djenné", "Great_Mosque_of_Djenné"),
                ("Djenné-Djenno", "Djenné-Djenno"),
                ("Monday Market", None)],
    blurb="A town on an island in the Bani river whose Great Mosque is the "
          "largest mud-brick building in the world — three towers, a forest of "
          "palm-wood beams sticking out of the walls, and a surface that has to "
          "be re-plastered by hand every year.",
    fact="The re-plastering is a festival: the whole town carries mud to the "
         "walls in a single day, and the projecting timbers are the permanent "
         "scaffolding that makes it possible.",
    tip="Come on a Monday, when the market fills the square in front of the "
        "mosque and the building has crowds at its feet for scale."),
"timbuktu": dict(
    name="Timbuktu", slug="Timbuktu", country="Mali",
    region="Tombouctou Region", type="desert", tag="famous", emoji="📜",
    sounds=["desert-wind.mp3"],
    highlights=[("Djinguereber Mosque", "Djinguereber_Mosque"),
                ("Sankore Madrasah", "Sankore_Madrasah"),
                ("Sidi Yahya Mosque", "Sidi_Yahya_Mosque")],
    blurb="The byword for the ends of the earth is a real town of low mud "
          "houses where the Niger's northern bend comes closest to the Sahara — "
          "the point where river trade met camel trade, and for two centuries "
          "one of the richest scholarly cities in the world.",
    fact="Private libraries here hold hundreds of thousands of manuscripts; "
         "families smuggled much of the collection out in trunks and rice sacks "
         "when the town was occupied in 2012.",
    tip="The three great mosques are within a twenty-minute walk of each other, "
        "and Sankore's pyramid of protruding beams is best seen from the sand "
        "lane on its north side."),
"bamako": dict(
    name="Bamako", slug="Bamako", country="Mali",
    region="Bamako Capital District", type="city", tag="famous", emoji="🎶",
    sounds=["city-hum.mp3"],
    highlights=[("National Museum of Mali", "National_Museum_of_Mali"),
                ("Bamako Grand Mosque", None),
                ("Point G", None),
                ("Marché Rose", None)],
    blurb="Mali's capital spreads along both banks of the Niger under a low "
          "escarpment, dusty and loud and, by common consent, one of the great "
          "music cities of the world — the place where kora, ngoni and electric "
          "guitar were argued into the same band.",
    fact="The National Museum is widely rated the best in West Africa, with "
         "textiles, masks and terracottas from the Niger's inland delta going "
         "back well over a thousand years.",
    tip="Cross the Pont des Martyrs on foot at sunset for the view up the "
        "river, then follow the noise: the clubs on the left bank start late "
        "and the bands are usually the real ones."),
"bandiagara-escarpment": dict(
    name="Bandiagara Escarpment", slug="Bandiagara_Escarpment", country="Mali",
    region="Mopti Region", type="mountain", tag="hidden", emoji="🧗",
    sounds=["wind.mp3"],
    highlights=[("Cliff villages of Bandiagara", None),
                ("Sangha", None),
                ("Granaries of the escarpment", None)],
    blurb="A 150 km sandstone cliff rising 500 m off the plain, with villages "
          "built into the scree at its foot and older dwellings still visible "
          "in the rock face high above them — square granaries with thatched "
          "caps wedged into ledges that look unreachable.",
    fact="The niches high in the cliff predate the villages below and were "
         "built by earlier inhabitants; how the stone was carried up to them is "
         "still argued about.",
    tip="Walk the base of the escarpment between villages rather than driving "
        "the plateau road — the whole cliff stays overhead for hours."),

# ============================== GHANA ==============================
"accra": dict(
    name="Accra", slug="Accra", country="Ghana", region="Greater Accra Region",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Kwame Nkrumah Memorial Park", "Kwame_Nkrumah_Memorial_Park"),
                ("Jamestown", "Jamestown,_Accra"),
                ("Independence Square", "Independence_Square_(Ghana)"),
                ("Makola Market", "Makola_Market"),
                ("Labadi Beach", None)],
    blurb="A wide, hot, fast-growing capital on the Gulf of Guinea, with a "
          "colonial fishing quarter and a lighthouse at one end and glass "
          "towers at the other. The city that first came out of European rule "
          "in sub-Saharan Africa, and comfortable about saying so.",
    fact="Independence Square holds 30,000 people and was built for the 1957 "
         "handover; its Black Star Gate has stood for the country's flag ever "
         "since.",
    tip="Jamestown at dawn: the boats come in below the old lighthouse, and "
        "the whole beach turns into a market before the heat arrives."),
"cape-coast-castle": dict(
    name="Cape Coast Castle", slug="Cape_Coast_Castle", country="Ghana",
    region="Central Region", type="history", tag="famous", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Elmina Castle", "Elmina_Castle"),
                ("Kakum National Park", "Kakum_National_Park"),
                ("Fort William", None)],
    blurb="A whitewashed fort on the surf line, with cannon on the terrace and "
          "windowless dungeons cut into the rock beneath it. Along this stretch "
          "of coast there are around forty such forts within a few hours of "
          "each other — the densest concentration of them anywhere.",
    fact="The 'Door of No Return' opens directly onto the beach; since 1998 it "
         "has been used in the other direction too, for the return of remains "
         "from the Americas.",
    tip="Elmina, twelve kilometres west, is older — built by the Portuguese in "
        "1482 — and its harbour full of painted canoes is a working port, not "
        "a monument."),
"kumasi": dict(
    name="Kumasi", slug="Kumasi", country="Ghana", region="Ashanti Region",
    type="city", tag="hidden", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Manhyia Palace", "Manhyia_Palace"),
                ("Kejetia Market", "Kejetia_Market"),
                ("Lake Bosomtwe", "Lake_Bosumtwi"),
                ("Prempeh II Jubilee Museum", None)],
    blurb="The old inland capital of a kingdom that was never quite conquered, "
          "set among green hills 250 km from the coast. Its market is the "
          "largest in West Africa — a bowl of tin roofs holding tens of "
          "thousands of stalls that reads as a single silver lake from above.",
    fact="Kumasi's craft villages each do one thing: kente weaving in "
         "Bonwire, brass casting in Krofofrom, adinkra stamping in Ntonso — "
         "all within half an hour of the centre.",
    tip="Lake Bosomtwe, half an hour south, fills a meteorite crater 8 km "
        "across; fishing there is still done sitting astride a plank."),

# ============================== NIGERIA ==============================
"lagos": dict(
    name="Lagos", slug="Lagos", country="Nigeria", region="Lagos State",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    search_name="Lagos Nigeria",
    highlights=[("Lekki Conservation Centre", "Lekki_Conservation_Centre"),
                ("Freedom Park", "Freedom_Park,_Lagos"),
                ("Third Mainland Bridge", "Third_Mainland_Bridge"),
                ("Tarkwa Bay", "Tarkwa_Bay_Beach"),
                ("National Museum Lagos", None)],
    blurb="Africa's largest city, built across a lagoon, a series of islands "
          "and the mainland behind them, and still growing faster than almost "
          "anywhere on earth. Traffic, generators, Afrobeats out of every "
          "doorway, and a creative output the whole continent follows.",
    fact="The Third Mainland Bridge runs 11.8 km across open lagoon and was "
         "the longest bridge in Africa for three decades.",
    tip="Take the boat to Tarkwa Bay — a beach with no road access at all, "
        "twenty minutes from the financial district, where the city noise "
        "simply stops."),
"abuja": dict(
    name="Abuja", slug="Abuja", country="Nigeria",
    region="Federal Capital Territory", type="city", tag="famous", emoji="🕌",
    sounds=["city-hum.mp3"],
    highlights=[("Aso Rock", "Aso_Rock"),
                ("Abuja National Mosque", "Abuja_National_Mosque"),
                ("Nigerian National Christian Centre",
                 "Nigerian_National_Christian_Centre"),
                ("Millennium Park", "Millennium_Park_(Abuja)"),
                ("Zuma Rock", "Zuma_Rock")],
    blurb="A capital designed from nothing in the 1980s on neutral ground in "
          "the middle of the country — wide avenues, a green master plan, and "
          "a 400 m granite monolith standing directly behind the government "
          "district.",
    fact="The mosque and the national church face each other across the same "
         "avenue, a piece of city planning that was entirely deliberate.",
    tip="Zuma Rock, on the road in from the north, is a 300 m block of stone "
        "rising straight off the plain — most people photograph it from the "
        "car and never stop, but there is a lay-by."),
"olumo-rock": dict(
    name="Olumo Rock", slug="Olumo_Rock", country="Nigeria",
    region="Ogun State", type="mountain", tag="hidden", emoji="🪨",
    sounds=["wilderness.mp3"],
    highlights=[("Abeokuta", "Abeokuta"),
                ("Olumo Rock caves", None)],
    blurb="A granite outcrop in the middle of Abeokuta — the name means "
          "'under the rock' — riddled with caves and clefts that sheltered the "
          "town's founders during the wars of the 1820s. A stair and a lift now "
          "run up it, and the view is the whole red-roofed city.",
    fact="Families still live in the compounds at the base of the rock and "
         "keep shrines in the caves that were used as hiding places two "
         "centuries ago.",
    tip="Go up the old carved steps rather than the lift; they thread through "
        "gaps in the boulders barely wide enough to pass."),
"yankari": dict(
    name="Yankari National Park", slug="Yankari_National_Park",
    country="Nigeria", region="Bauchi State", type="nature", tag="hidden",
    emoji="🐘", sounds=["wilderness.mp3"],
    highlights=[("Wikki Warm Spring", None),
                ("Marshall Caves", None),
                ("Gaji River", None)],
    blurb="Savannah and gallery forest in the northeast, holding the largest "
          "surviving elephant population in Nigeria and a spring that pushes "
          "out clear water at a constant 31°C, deep enough to swim in and "
          "bright blue against the sand.",
    fact="Wikki Spring discharges around 21 million litres a day, which is why "
         "the pool it feeds never cools, never clouds and never stops.",
    tip="Swim at first light — the spring is floodlit at night but the animals "
        "come down to the Gaji river in the hour after dawn."),

# ============================== BURKINA FASO ==============================
"ouagadougou": dict(
    name="Ouagadougou", slug="Ouagadougou", country="Burkina Faso",
    region="Centre Region", type="city", tag="famous", emoji="🎬",
    sounds=["city-hum.mp3"],
    highlights=[("Cathedral of Ouagadougou", "Ouagadougou_Cathedral"),
                ("Moro-Naba Palace", None),
                ("Bangr-Weoogo Park", None),
                ("Grand Marché", None)],
    blurb="A flat, red-earth capital of low buildings and very wide streets, "
          "and the improbable film capital of the continent: every two years "
          "the whole city gives itself over to a festival that has run since "
          "1969.",
    fact="FESPACO is the largest African film festival in the world, and its "
         "top prize — the Étalon de Yennenga — is named after a legendary "
         "horsewoman whose statue stands at a city roundabout.",
    tip="The Moro-Naba palace holds a short ceremony most Friday mornings, "
        "open to anyone standing in the courtyard, and it is over in fifteen "
        "minutes."),
"loropeni": dict(
    name="Ruins of Loropéni", slug="Ruins_of_Loropéni",
    country="Burkina Faso", region="Poni Province", type="ruin", tag="hidden",
    emoji="🧱", sounds=["wilderness.mp3"],
    highlights=[("Loropéni walls", None),
                ("Gaoua", "Gaoua")],
    blurb="Laterite walls up to six metres high enclosing a hectare of "
          "forest in the far southwest — the best preserved of some hundred "
          "fortified settlements built along an old gold route, and standing "
          "with no roof, no floor and no record of who left.",
    fact="Loropéni was Burkina Faso's first World Heritage site, inscribed in "
         "2009, and most of the enclosure has still never been excavated.",
    tip="The walls are a twenty-minute walk from the road through farmland; "
        "there is rarely anyone else on site."),

# ============================== BENIN ==============================
"ganvie": dict(
    name="Ganvié", slug="Ganvie", country="Benin",
    region="Atlantique Department", type="village", tag="hidden", emoji="🛶",
    sounds=["wilderness.mp3"],
    highlights=[("Lake Nokoué", "Lake_Nokoué"),
                ("Ganvié stilt village", None),
                ("Floating market", None)],
    blurb="A town of some 20,000 people built entirely on stilts in a shallow "
          "lagoon, reached only by pirogue. Houses, a school, a church and a "
          "market all stand on poles in a metre of water, and every journey "
          "between them is made by paddle.",
    fact="The village exists because slave raiders were forbidden by custom "
         "from entering water — a settlement in the middle of the lagoon was "
         "simply out of reach.",
    tip="Take the boat out at dawn from Abomey-Calavi; the floating market "
        "forms and dissolves within about an hour."),
"ouidah": dict(
    name="Ouidah", slug="Ouidah", country="Benin",
    region="Atlantique Department", type="history", tag="hidden", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Door of No Return", None),
                ("Temple of Pythons", None),
                ("Portuguese Fort of Ouidah", None),
                ("Sacred Forest of Kpasse", None)],
    blurb="A low coastal town at the head of a four-kilometre sand road that "
          "runs from the old auction square to the beach, lined with memorials "
          "and ending at an arch facing the Atlantic. Also the historic centre "
          "of Vodun, whose temples are ordinary buildings on ordinary streets.",
    fact="The Route des Esclaves is walked in the direction the captives were "
         "walked, and the trees along it — the Tree of Forgetting, the Tree of "
         "Return — are marked where they stood.",
    tip="The Portuguese fort at the top of the road is now the history museum "
        "and is usually empty; the guides there know the town street by "
        "street."),
"abomey": dict(
    name="Abomey", slug="Abomey", country="Benin", region="Zou Department",
    type="history", tag="hidden", emoji="🏛️", sounds=["wilderness.mp3"],
    highlights=[("Royal Palaces of Abomey", "Royal_Palaces_of_Abomey"),
                ("Abomey Historical Museum", None)],
    blurb="The capital of the kingdom of Dahomey, where twelve successive "
          "kings each built a new earthen palace beside the last inside one "
          "enormous mud-walled enclosure — 44 hectares of courtyards, bas-relief "
          "panels and audience halls.",
    fact="The bas-reliefs on the palace walls are a written record: each panel "
         "encodes a reign, a battle or a proverb, and they are how the "
         "kingdom's history was kept.",
    tip="The museum occupies two of the palaces; ask to be shown the "
        "reliefs in the Salle des Bas-reliefs, where the originals are kept "
        "out of the rain."),

# ============================== TOGO ==============================
"lome": dict(
    name="Lomé", slug="Lomé", country="Togo", region="Maritime Region",
    type="city", tag="hidden", emoji="🌴", sounds=["ocean-waves.mp3"],
    highlights=[("Grand Marché", None),
                ("Lomé Cathedral", None),
                ("Independence Monument", None),
                ("Akodessewa Fetish Market", None)],
    blurb="A capital right on the beach and right on the border — you can walk "
          "from the city centre into Ghana in a few minutes. Palm-lined "
          "boulevard along the sand, a German colonial cathedral, and a market "
          "run for generations by the traders known as the Nana Benz.",
    fact="Those traders controlled the wax-print cloth business across West "
         "Africa so completely that they were nicknamed for the cars they "
         "bought with the profits.",
    tip="The beach road east of the port has fishermen hauling nets in by hand "
        "every morning, thirty or forty to a line, singing to keep time."),
"koutammakou": dict(
    name="Koutammakou", slug="Koutammakou", country="Togo",
    region="Kara Region", type="village", tag="hidden", emoji="🏚️",
    sounds=["wilderness.mp3"],
    highlights=[("Takienta tower houses", None),
                ("Kara", "Kara,_Togo")],
    blurb="A landscape in the northeast filled with takienta — fortified "
          "two-storey mud tower-houses with round turrets and flat roofs used "
          "as living space, granaries and defence all at once. They are still "
          "built, still lived in, and still rebuilt each year.",
    fact="The house is a model of the household: animals below, people and "
         "grain above, and the roof terrace where the cooking and the sleeping "
         "happen in the dry season.",
    tip="Come at the end of the rains, when the millet is high and the towers "
        "stand out of green rather than dust."),

# ============================== CÔTE D'IVOIRE ==============================
"abidjan": dict(
    name="Abidjan", slug="Abidjan", country="Côte d'Ivoire",
    region="Abidjan Autonomous District", type="city", tag="famous",
    emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("St. Paul's Cathedral", "St._Paul's_Cathedral,_Abidjan"),
                ("Le Plateau", "Le_Plateau,_Abidjan"),
                ("Banco National Park", "Banco_National_Park"),
                ("Treichville", "Treichville")],
    blurb="A lagoon city of towers, bridges and ferries, and the economic "
          "engine of French-speaking West Africa. Le Plateau's skyline is the "
          "reason it was once called the Manhattan of the tropics; the "
          "neighbourhoods across the water are where the music comes from.",
    fact="Banco National Park is a stretch of primary rainforest inside the "
         "city limits — 30 km² of it, with 50 m trees, surrounded on all sides "
         "by suburbs.",
    tip="Take a wooden pinasse ferry rather than a taxi between Plateau and "
        "Treichville; it costs almost nothing and gives the only decent view "
        "of the skyline."),
"yamoussoukro": dict(
    name="Yamoussoukro", slug="Yamoussoukro", country="Côte d'Ivoire",
    region="Yamoussoukro Autonomous District", type="city", tag="hidden",
    emoji="⛪", sounds=["plaza.mp3"],
    highlights=[("Basilica of Our Lady of Peace",
                 "Basilica_of_Our_Lady_of_Peace"),
                ("Kossou Lake", None),
                ("Presidential Palace", None)],
    blurb="A village that became the official capital because its most famous "
          "son said so, and now holds the largest church in the world by floor "
          "area, standing on an empty plain at the end of an eight-lane road "
          "that carries almost no traffic.",
    fact="The basilica's dome is modelled on St Peter's and its stained glass "
         "covers 7,400 m²; the whole thing was consecrated in 1990 for a "
         "congregation that has never filled it.",
    tip="The lake beside the presidential palace has been stocked with "
        "crocodiles since the 1970s and they are fed in the late afternoon, "
        "from the bank, in front of anyone standing there."),
"grand-bassam": dict(
    name="Grand-Bassam", slug="Grand-Bassam", country="Côte d'Ivoire",
    region="Comoé District", type="coastal", tag="hidden", emoji="🏖️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Old Quarter of Grand-Bassam", None),
                ("Costume Museum", None),
                ("Ébrié Lagoon", None)],
    blurb="The first colonial capital, abandoned after a yellow fever epidemic "
          "and left to weather on a sandbar between the lagoon and the ocean — "
          "arcaded trading houses, a governor's palace and a customs shed, all "
          "peeling in the salt air an hour from Abidjan.",
    fact="The town was left almost intact precisely because it was abandoned "
         "early: nothing was built over it, so the 1890s street plan is the "
         "one you walk.",
    tip="Weekdays the old quarter is close to deserted; the beach behind it "
        "has a strong undertow, so the swimming is in the lagoon."),

# ============================== CAPE VERDE ==============================
"mindelo": dict(
    name="Mindelo", slug="Mindelo", country="Cape Verde",
    region="São Vicente", type="coastal", tag="hidden", emoji="🎼",
    sounds=["ocean-waves.mp3"],
    highlights=[("Monte Cara", None),
                ("Porto Grande Bay", None),
                ("Praça Nova", None),
                ("Mercado Municipal", None)],
    blurb="A port in a drowned volcanic crater on a bare brown island, with "
          "pastel colonial buildings around the bay and a headland across the "
          "water shaped exactly like a face looking at the sky. The musical "
          "capital of the archipelago.",
    fact="Mindelo grew as a coaling station for Atlantic steamers, which is "
         "why a small island town has a British-built customs house, a replica "
         "of Lisbon's Belém tower and its own brass-band tradition.",
    tip="Bars along Rua de Lisboa put on live morna and coladeira most nights "
        "from about eleven — the later it gets, the better the players."),
"pico-do-fogo": dict(
    name="Pico do Fogo", slug="Pico_do_Fogo", country="Cape Verde",
    region="Fogo", type="mountain", tag="hidden", emoji="🌋",
    sounds=["mountain-wind.mp3"],
    highlights=[("Chã das Caldeiras", "Chã_das_Caldeiras"),
                ("Fogo Natural Park", None),
                ("Bordeira cliff", None)],
    blurb="A 2,829 m cone standing inside a collapsed caldera whose rear wall "
          "rises a kilometre in a single curve. People live on the crater "
          "floor, farm the ash, and make wine from vines grown in black "
          "gravel.",
    fact="The village inside the caldera has been buried by lava twice in "
         "living memory, most recently in 2014 — and rebuilt on top of the new "
         "rock both times.",
    tip="The climb is about three hours up loose scree and forty minutes back "
        "down, because you descend the ash slope in long sliding strides."),

# ============================== NIGER ==============================
"agadez": dict(
    name="Agadez", slug="Agadez", country="Niger", region="Agadez Region",
    type="desert", tag="hidden", emoji="🕌", sounds=["desert-wind.mp3"],
    highlights=[("Great Mosque of Agadez", "Agadez_Grand_Mosque"),
                ("Sultan's Palace", None),
                ("Aïr Mountains", "Aïr_Mountains")],
    blurb="The gateway to the Sahara: a mud-brick town at the southern edge of "
          "the desert whose 27 m minaret, bristling with palm beams, is the "
          "tallest mud structure anywhere and has been the landmark for caravans "
          "arriving from the north since the 16th century.",
    fact="Agadez still receives salt caravans from Bilma, several hundred "
         "kilometres east across open desert — one of the last long-distance "
         "camel trades still running.",
    tip="They will let you climb the minaret's internal stair; it is dark, "
        "tight and worth it for the roofscape of the old town."),

# ============================== SIERRA LEONE ==============================
"freetown": dict(
    name="Freetown", slug="Freetown", country="Sierra Leone",
    region="Western Area", type="coastal", tag="famous", emoji="🌳",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cotton Tree", "Cotton_Tree_(Sierra_Leone)"),
                ("Tacugama Chimpanzee Sanctuary",
                 "Tacugama_Chimpanzee_Sanctuary"),
                ("Bunce Island", "Bunce_Island"),
                ("Lumley Beach", None)],
    blurb="A city wrapped around one of the largest natural harbours in the "
          "world, with forested mountains rising straight off the back of it "
          "and white beaches running down the peninsula south of town.",
    fact="Freetown was founded in 1792 by formerly enslaved people from Nova "
         "Scotia, who landed at the harbour and walked up to a cotton tree in "
         "the middle of what is now the city.",
    tip="Take the ferry across to Tagrin at sunset for the view back at the "
        "mountains, or the boat upriver to Bunce Island, which is left exactly "
        "as it fell."),

# ============================== LIBERIA ==============================
"monrovia": dict(
    name="Monrovia", slug="Monrovia", country="Liberia",
    region="Montserrado County", type="city", tag="hidden", emoji="🏙️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Providence Island", "Providence_Island,_Liberia"),
                ("Ducor Palace Hotel", "Ducor_Hotel"),
                ("Waterside Market", None),
                ("Centennial Pavilion", None)],
    blurb="A capital on a peninsula between the Atlantic and the Mesurado "
          "river, laid out with American street names by settlers who arrived "
          "in 1822. Zinc roofs, heavy surf, and the wettest capital city in the "
          "world by annual rainfall.",
    fact="The abandoned Ducor hotel on the hill above town was one of Africa's "
         "first five-star hotels; its roof is now the best free viewpoint over "
         "the whole peninsula.",
    tip="Providence Island, where the first settlers landed, sits under the "
        "bridge at the edge of downtown and can be walked in twenty minutes."),

# ============================== GUINEA ==============================
"conakry": dict(
    name="Conakry", slug="Conakry", country="Guinea", region="Conakry Region",
    type="city", tag="hidden", emoji="🏙️", sounds=["ocean-waves.mp3"],
    highlights=[("Grand Mosque of Conakry", "Grand_Mosque_of_Conakry"),
                ("Îles de Los", "Îles_de_Los"),
                ("Botanical Garden of Camayenne", None),
                ("Palais du Peuple", None)],
    blurb="A capital squeezed onto a long narrow peninsula, so the whole city "
          "is one axis with water on both sides. Its Grand Mosque is among the "
          "largest in sub-Saharan Africa, and the market streets behind it are "
          "as dense as the peninsula is thin.",
    fact="The Îles de Los, a short boat ride off the tip, were held by Britain "
         "and traded to France in 1904 — which is why the beaches nearest the "
         "capital have English names.",
    tip="Take the pirogue to Île de Roume on a weekday; it is twenty minutes "
        "out and the beach is usually yours."),
"fouta-djallon": dict(
    name="Fouta Djallon", slug="Fouta_Djallon", country="Guinea",
    region="Labé Region", type="mountain", tag="hidden", emoji="💧",
    sounds=["waterfall.mp3"],
    highlights=[("Ditinn Falls", None),
                ("Kambadaga Falls", None),
                ("Dalaba", "Dalaba")],
    blurb="A cool sandstone highland of terraced plateaux and deep gorges that "
          "catches the monsoon and sends it out in every direction — the "
          "Niger, the Senegal and the Gambia all rise within a hundred "
          "kilometres of each other here.",
    fact="It is called the water tower of West Africa for good reason: three "
         "of the region's major rivers begin on this one massif.",
    tip="Ditinn drops 115 m off a flat plateau lip into a green bowl, and you "
        "can walk to the top edge and look straight down it."),

# ============================== GUINEA-BISSAU ==============================
"bijagos": dict(
    name="Bijagós Archipelago", slug="Bijagós_Archipelago",
    country="Guinea-Bissau", region="Bolama Region", type="island",
    tag="hidden", emoji="🐢", sounds=["ocean-waves.mp3"],
    highlights=[("Bubaque", "Bubaque"),
                ("Orango National Park", None),
                ("Bolama", "Bolama")],
    blurb="Eighty-eight low islands of mangrove, palm and white sand off the "
          "coast, only about twenty of them permanently inhabited, with huge "
          "tides that redraw the channels twice a day and no roads worth the "
          "name.",
    fact="Orango's saltwater-tolerant hippos live in and out of the sea "
         "between islands, and the archipelago's beaches are one of the most "
         "important green turtle nesting sites in the Atlantic.",
    tip="Bolama, the old colonial capital, was abandoned in 1941 and is being "
        "taken back by the forest — arcaded avenues with trees growing "
        "through them."),
# ============================== CAMEROON ==============================
"yaounde": dict(
    name="Yaoundé", slug="Yaoundé", country="Cameroon", region="Centre Region",
    type="city", tag="hidden", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Reunification Monument", "Reunification_Monument"),
                ("Mont Fébé", None),
                ("Mfoundi Market", None),
                ("Cathedral of Our Lady of Victories", None)],
    blurb="A capital built across seven hills at 750 m, green and much cooler "
          "than the coast, with roads that climb and drop constantly and views "
          "over red roofs and forest from almost anywhere in it.",
    fact="The spiral Reunification Monument marks the 1961 joining of the "
         "French and British Cameroons — two administrations, two school "
         "systems and two official languages fused into one country.",
    tip="Walk up Mont Fébé in the early morning for the whole city under mist, "
        "then come down through the craft village on its lower slope."),
"douala": dict(
    name="Douala", slug="Douala", country="Cameroon", region="Littoral Region",
    type="city", tag="hidden", emoji="⚓", sounds=["city-hum.mp3"],
    highlights=[("La Nouvelle Liberté", "La_Nouvelle_Liberté"),
                ("Bonanjo", None),
                ("Wouri Bridge", None),
                ("Marché des Fleurs", None)],
    blurb="Cameroon's port and its largest city, hot and humid on the Wouri "
          "estuary, where most of Central Africa's cargo actually lands. "
          "Colonial-era Bonanjo on one side, a vast informal market economy on "
          "the other.",
    fact="La Nouvelle Liberté, a 12 m figure at a main roundabout, is welded "
         "from scrap metal collected across the city — a monument made "
         "literally out of Douala.",
    tip="Cross the Wouri bridge on foot at dusk if the traffic allows; the "
        "pirogues come back up the estuary against the light."),
"mount-cameroon": dict(
    name="Mount Cameroon", slug="Mount_Cameroon", country="Cameroon",
    region="Southwest Region", type="mountain", tag="famous", emoji="🌋",
    sounds=["mountain-wind.mp3"],
    highlights=[("Buea", "Buea"),
                ("Limbe", "Limbe,_Cameroon"),
                ("Mann's Spring", None)],
    blurb="West Africa's highest peak, an active volcano rising 4,040 m "
          "straight out of the Atlantic in one unbroken slope — rainforest at "
          "the bottom, lava fields and grass at the top, and the whole climb "
          "done from sea level.",
    fact="The southwest flank is one of the wettest places on earth, taking "
         "close to ten metres of rain a year, while the summit sits in dry "
         "wind above the cloud.",
    tip="The Guinness Mountain Race runs the whole ascent and descent in under "
        "five hours each February; the rest of the year the same route takes "
        "walkers two days."),

# ============================== GABON ==============================
"libreville": dict(
    name="Libreville", slug="Libreville", country="Gabon",
    region="Estuaire Province", type="city", tag="hidden", emoji="🏙️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Mont-Bouët Market", None),
                ("St. Michael's Church", None),
                ("Pointe Denis", None),
                ("National Museum of Arts and Traditions", None)],
    blurb="A small, expensive oil capital strung along the Atlantic where the "
          "Komo estuary opens out, backed immediately by rainforest. Wide "
          "beach boulevard, a few towers, and the sense of a city that stops "
          "abruptly at the treeline.",
    fact="St. Michael's has 31 wooden columns, each carved by a blind "
         "Gabonese sculptor with a different biblical scene — the interior is "
         "effectively a single work.",
    tip="Take the boat across the estuary to Pointe Denis: forty minutes, and "
        "the beach on the far side runs empty for kilometres."),
"loango": dict(
    name="Loango National Park", slug="Loango_National_Park", country="Gabon",
    region="Ogooué-Maritime Province", type="nature", tag="hidden", emoji="🐘",
    sounds=["ocean-waves.mp3"],
    highlights=[("Iguéla Lagoon", None),
                ("Petit Loango", None),
                ("Louri Beach", None)],
    blurb="The place where forest elephants, buffalo and occasionally gorillas "
          "walk out of the rainforest onto an empty Atlantic beach — 1,550 km² "
          "of lagoon, savannah, mangrove and surf on Gabon's central coast.",
    fact="Gabon set aside 13 national parks in a single act in 2002, turning "
         "about 11% of the country into protected land overnight; Loango is the "
         "one people mean by 'Africa's last Eden'.",
    tip="Humpbacks calve offshore from July to September and are visible from "
        "the beach — no boat required, just patience at the surf line."),

# ============================== REPUBLIC OF THE CONGO ==============================
"brazzaville": dict(
    name="Brazzaville", slug="Brazzaville",
    country="Republic of the Congo", region="Brazzaville", type="city",
    tag="hidden", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Basilica of Sainte-Anne",
                 "Basilica_of_Sainte-Anne,_Brazzaville"),
                ("Poto-Poto", "Poto-Poto"),
                ("Case de Gaulle", None),
                ("Les Rapides", None)],
    blurb="One half of the only pair of capital cities that face each other "
          "across a river — Kinshasa is a kilometre away on the far bank, and "
          "the two skylines watch each other all day. Low-rise, green and much "
          "quieter than its neighbour.",
    fact="The green-tiled parabolic vaults of Sainte-Anne were built in the "
         "1940s in reinforced concrete with no interior columns at all, which "
         "is why the nave reads as one continuous curve.",
    tip="Go down to Les Rapides in the late afternoon: the Congo breaks over "
        "rock ledges just below the city and the far bank is a different "
        "country."),

# ============================== DR CONGO ==============================
"kinshasa": dict(
    name="Kinshasa", slug="Kinshasa", country="DR Congo", region="Kinshasa",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Lola ya Bonobo", "Lola_ya_Bonobo"),
                ("Boulevard du 30 Juin", None),
                ("Académie des Beaux-Arts", None),
                ("Marché Central", None)],
    blurb="The largest French-speaking city in the world and one of the "
          "largest cities anywhere, sprawling along the south bank of the "
          "Congo river where it widens into a pool. Loud, enormous, and the "
          "source of the guitar music that reshaped the whole continent.",
    fact="Congolese rumba, invented in Kinshasa's bars, was inscribed on "
         "UNESCO's intangible heritage list in 2021 — the city exported it to "
         "every capital between Dakar and Nairobi.",
    tip="Lola ya Bonobo, on the city's southern edge, is the only bonobo "
        "sanctuary in the world, and the animals live in forest enclosures you "
        "walk the perimeter of."),
"virunga": dict(
    name="Virunga National Park", slug="Virunga_National_Park",
    country="DR Congo", region="North Kivu", type="nature", tag="famous",
    emoji="🦍", sounds=["wilderness.mp3"],
    highlights=[("Mount Nyiragongo", "Mount_Nyiragongo"),
                ("Rwenzori Mountains", "Rwenzori_Mountains"),
                ("Lake Edward", "Lake_Edward")],
    blurb="Africa's oldest national park and its most biologically varied: "
          "7,800 km² running from swamp and savannah through mountain gorilla "
          "forest up to glaciers and an active lava lake, all inside one "
          "boundary.",
    fact="Nyiragongo holds the largest lava lake on earth — a churning red "
         "surface a couple of hundred metres across, which climbers look down "
         "into from the crater rim overnight.",
    tip="The volcano climb is done in a day with a hut at the top; the point "
        "is to be there after dark, when the lake lights the whole cloud "
        "above it."),

# ============================== CHAD ==============================
"ennedi": dict(
    name="Ennedi Massif", slug="Ennedi_Massif", country="Chad",
    region="Ennedi-Ouest Region", type="desert", tag="hidden", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Guelta d'Archei", "Guelta_d'Archei"),
                ("Aloba Arch", None),
                ("Ennedi rock art", None)],
    blurb="A sandstone plateau in the northeast Sahara eroded into arches, "
          "towers and slot canyons, with permanent water holes hidden in the "
          "deepest gorges and rock paintings on the walls above them.",
    fact="The Guelta d'Archei holds a relict population of West African "
         "crocodiles — survivors from when the Sahara was wet, living in a "
         "pool a few hundred metres long with no river for hundreds of "
         "kilometres.",
    tip="Camel caravans still bring herds down into the Archei gorge to drink; "
        "the noise inside the canyon walls is extraordinary."),
"ndjamena": dict(
    name="N'Djamena", slug="N'Djamena", country="Chad", region="N'Djamena",
    type="city", tag="hidden", emoji="🏙️", sounds=["desert-wind.mp3"],
    highlights=[("Grand Mosque of N'Djamena", None),
                ("Chad National Museum", None),
                ("Chari River", None),
                ("Marché de Dembé", None)],
    blurb="A low Sahel capital on the Chari river, directly across the water "
          "from Cameroon, where the desert north and the farming south of the "
          "country meet and trade. Dust, wide avenues, and a river that swells "
          "and shrinks by kilometres with the seasons.",
    fact="The national museum holds the cast of Toumaï, a seven-million-year-old "
         "hominin skull found in the Djurab desert north of the city — one of "
         "the oldest ever recovered.",
    tip="The Chari bank on the southern edge of town is where fishermen land "
        "captain fish nearly as long as their pirogues, most mornings."),

# ============================== CENTRAL AFRICAN REPUBLIC ==============================
"dzanga-sangha": dict(
    name="Dzanga-Sangha", slug="Dzanga-Sangha_Special_Reserve",
    country="Central African Republic", region="Sangha-Mbaéré", type="nature",
    tag="hidden", emoji="🐘", sounds=["wilderness.mp3"],
    highlights=[("Dzanga Bai", None),
                ("Sangha River", None),
                ("Bayanga", None)],
    blurb="Lowland rainforest in the far southwest corner where three "
          "countries meet, holding one of the last great gatherings of forest "
          "elephants — up to a hundred at a time in a single mineral clearing "
          "cut out of unbroken canopy.",
    fact="Dzanga Bai is called the village of elephants: they come for the "
         "salts in the mud, dig with their trunks, and can be watched from a "
         "platform at the treeline for hours.",
    tip="The forest here is one of the few places where you can track lowland "
        "gorillas on foot, with guides who have habituated the same family for "
        "years."),

# ============================== EQUATORIAL GUINEA ==============================
"malabo": dict(
    name="Malabo", slug="Malabo", country="Equatorial Guinea",
    region="Bioko Norte", type="city", tag="hidden", emoji="🌋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Malabo Cathedral", "Malabo_Cathedral"),
                ("Pico Basilé", "Pico_Basilé"),
                ("Plaza de la Independencia", None),
                ("Malabo Old Town", None)],
    blurb="A capital that is not on the mainland at all: it sits in the "
          "drowned crater of a volcano on the island of Bioko, 300 km "
          "offshore, under a 3,000 m peak that is usually in cloud. Spanish "
          "colonial arcades, twin cathedral spires, and rainforest starting "
          "where the streets end.",
    fact="Equatorial Guinea is the only sovereign African state with Spanish "
         "as an official language, and Malabo's old town is laid out and built "
         "accordingly.",
    tip="The road up Pico Basilé climbs through five distinct forest belts in "
        "an hour and ends above the cloud with the whole island below."),

# ============================== SÃO TOMÉ AND PRÍNCIPE ==============================
"sao-tome": dict(
    name="São Tomé", slug="São_Tomé", country="São Tomé and Príncipe",
    region="Água Grande District", type="city", tag="hidden", emoji="🍫",
    sounds=["ocean-waves.mp3"],
    highlights=[("Fort São Sebastião", None),
                ("Cathedral of São Tomé", None),
                ("Roça Agostinho Neto", None),
                ("Pico Cão Grande", "Pico_Cão_Grande")],
    blurb="A tiny equatorial capital of pastel Portuguese buildings and mango "
          "trees on a volcanic island covered in abandoned cocoa plantations. "
          "Nothing is more than a few minutes from either the sea or the "
          "forest.",
    fact="The islands were uninhabited when the Portuguese arrived in the "
         "1470s and became the first plantation economy in the tropics — the "
         "model later exported across the Atlantic.",
    tip="Drive south to see Pico Cão Grande, a 300 m volcanic needle standing "
        "clear out of the jungle; the roadside view of it is free and "
        "startling."),

# ============================== ANGOLA ==============================
"luanda": dict(
    name="Luanda", slug="Luanda", country="Angola", region="Luanda Province",
    type="city", tag="hidden", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Fortress of São Miguel", "Fortress_of_São_Miguel"),
                ("Marginal de Luanda", None),
                ("Ilha do Cabo", None),
                ("Miradouro da Lua", None)],
    blurb="A bay city of towers and cranes wrapped around a long sandspit, "
          "rebuilt at speed since the war ended in 2002 and, for several years "
          "running, the most expensive city in the world for foreign residents.",
    fact="The 1576 fortress above the port has stood through Portuguese, Dutch "
         "and Angolan rule and now holds the armed forces museum, with the bay "
         "laid out below its walls.",
    tip="Drive 40 km south to the Miradouro da Lua, where the coastal road "
        "runs along eroded cliffs that look like a lunar surface dropped into "
        "the Atlantic."),
"kalandula-falls": dict(
    name="Kalandula Falls", slug="Kalandula_Falls", country="Angola",
    region="Malanje Province", type="nature", tag="hidden", emoji="💦",
    sounds=["waterfall.mp3"],
    highlights=[("Lucala River", None),
                ("Pungo Andongo", "Pungo_Andongo"),
                ("Malanje", None)],
    blurb="One of the largest waterfalls in Africa by volume and almost "
          "nobody's first guess: a 105 m horseshoe on the Lucala river, over "
          "400 m wide in the rains, dropping into forest with no fence, no "
          "walkway and usually no other visitors.",
    fact="In the wet season the spray reaches the top of the escarpment, and "
          "the viewpoint is simply a grass edge at the lip of the gorge.",
    tip="A footpath drops from the northern rim to the plunge pool in about "
        "forty minutes — steep, slippery, and the only way to feel the size of "
        "it."),

# ============================== RWANDA ==============================
"kigali": dict(
    name="Kigali", slug="Kigali", country="Rwanda", region="Kigali Province",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Kigali Genocide Memorial", "Kigali_Genocide_Memorial"),
                ("Kimironko Market", None),
                ("Nyamirambo", None),
                ("Inema Arts Center", None)],
    blurb="A capital spread over a series of steep ridges and valleys, "
          "conspicuously clean and orderly, where the roads follow the "
          "contours and every neighbourhood looks across at another one.",
    fact="Plastic bags have been banned countrywide since 2008, and the last "
         "Saturday morning of every month is Umuganda — a national community "
         "work session when traffic stops and the streets are swept.",
    tip="Nyamirambo, the oldest quarter, has a women's centre running walking "
        "tours through the back lanes that end with lunch in someone's "
        "courtyard."),
"volcanoes-national-park": dict(
    name="Volcanoes National Park", slug="Volcanoes_National_Park",
    country="Rwanda", region="Northern Province", type="nature", tag="famous",
    emoji="🦍", sounds=["wilderness.mp3"],
    highlights=[("Mount Bisoke", "Mount_Bisoke"),
                ("Mount Karisimbi", "Mount_Karisimbi"),
                ("Musanze", "Musanze"),
                ("Dian Fossey Tomb", None)],
    blurb="Bamboo and hagenia forest on the slopes of five extinct volcanoes "
          "along the Congo and Uganda borders — the mountains where mountain "
          "gorillas live, and where the terraced farmland stops at a dry-stone "
          "wall and the forest starts.",
    fact="Mountain gorillas exist nowhere in captivity; every one of the "
         "roughly 1,000 alive lives in this massif or in Bwindi, and the "
         "population is now slowly growing.",
    tip="Bisoke's crater lake is a four-hour round trip through knee-deep mud "
        "and is climbed far less than the gorilla treks that start from the "
        "same gate."),
"lake-kivu": dict(
    name="Lake Kivu", slug="Lake_Kivu", country="Rwanda",
    region="Western Province", type="nature", tag="hidden", emoji="🌊",
    sounds=["wind.mp3"],
    highlights=[("Gisenyi", "Gisenyi"),
                ("Karongi", "Karongi"),
                ("Napoleon Island", None)],
    blurb="A deep lake in the Rift Valley between Rwanda and Congo, ringed by "
          "green hills and small beaches, with no crocodiles, no hippos and no "
          "bilharzia — which makes it one of the very few large African lakes "
          "you can simply swim in.",
    fact="Kivu holds an estimated 55 billion m³ of dissolved methane in its "
         "deep water, which is now being tapped and burned for electricity "
         "from a platform offshore.",
    tip="The Congo Nile Trail runs 227 km along the eastern shore and can be "
        "picked up for a single afternoon's stretch between two lakeside "
        "villages."),

# ============================== BURUNDI ==============================
"bujumbura": dict(
    name="Bujumbura", slug="Bujumbura", country="Burundi",
    region="Bujumbura Mairie", type="city", tag="hidden", emoji="🏖️",
    sounds=["wind.mp3"],
    highlights=[("Lake Tanganyika", None),
                ("Rusizi National Park", None),
                ("Livingstone-Stanley Monument", None),
                ("Saga Beach", None)],
    blurb="Burundi's largest city sits at the very top of Lake Tanganyika with "
          "mountains rising behind it, so the streets run downhill to a "
          "freshwater beach with white sand and the Congolese shore visible "
          "across the water.",
    fact="Tanganyika is the second-deepest lake in the world at 1,470 m and "
         "holds about 16% of the planet's available fresh water.",
    tip="The stone south of town marks where Livingstone and Stanley are said "
        "to have camped in 1871 — a small monument on a quiet road with a "
        "clear view down the lake."),
# ============================== UGANDA ==============================
"kampala": dict(
    name="Kampala", slug="Kampala", country="Uganda", region="Central Region",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Kasubi Tombs", "Kasubi_Tombs"),
                ("Uganda National Mosque", "Uganda_National_Mosque"),
                ("Uganda Martyrs Shrine", "Namugongo"),
                ("Owino Market", None)],
    blurb="A capital built over a set of low hills north of Lake Victoria, "
          "green and steeply folded, where each ridge historically carried one "
          "institution — a palace, a cathedral, a mosque — and the valleys "
          "between them carry the traffic.",
    fact="The Kasubi Tombs are the largest thatched building in the world: a "
         "single domed structure of reed and grass over the burial place of "
         "four kings of Buganda.",
    tip="Climb the minaret of the National Mosque on Old Kampala hill — the "
        "guides take you up for a small fee and it is the only 360° view of "
        "the city."),
"bwindi": dict(
    name="Bwindi Impenetrable Forest",
    slug="Bwindi_Impenetrable_National_Park", country="Uganda",
    region="Western Region", type="nature", tag="famous", emoji="🦍",
    sounds=["wilderness.mp3"],
    highlights=[("Buhoma", None),
                ("Munyaga River Trail", None),
                ("Rushaga sector", None)],
    blurb="A 331 km² block of montane rainforest on the edge of the Rift, so "
          "dense that its name is a plain description — vines, undergrowth and "
          "steep ravines with no line of sight, holding roughly half the "
          "world's mountain gorillas.",
    fact="Bwindi has survived as forest for over 25,000 years, which is why "
         "its species list is longer than any other in East Africa — including "
         "trees that exist nowhere else.",
    tip="The Batwa community trails on the forest edge are led by people whose "
        "families lived inside it, and they explain a forest that otherwise "
        "reads as a green wall."),
"murchison-falls": dict(
    name="Murchison Falls", slug="Murchison_Falls_National_Park",
    country="Uganda", region="Northern Region", type="nature", tag="famous",
    emoji="💦", sounds=["waterfall.mp3"],
    highlights=[("Murchison Falls", "Murchison_Falls"),
                ("Lake Albert", "Lake_Albert_(Africa)"),
                ("Victoria Nile", None),
                ("Paraa", None)],
    blurb="Uganda's largest park, split by the Victoria Nile, which funnels "
          "its entire flow through a rock gap seven metres wide and drops it "
          "43 m in one blast of white water before flattening out into a "
          "hippo-filled delta.",
    fact="The river squeezing through that gap moves roughly 300 cubic metres "
         "a second — the whole Nile, at that point, passes through a slot you "
         "could throw a stone across.",
    tip="Take the boat upriver to the base of the falls and then walk the "
        "final path to the top; you arrive at the lip from below, which is the "
        "right order."),
"jinja": dict(
    name="Jinja", slug="Jinja,_Uganda", country="Uganda",
    region="Eastern Region", type="city", tag="hidden", emoji="🚣",
    sounds=["wilderness.mp3"],
    highlights=[("Source of the Nile", None),
                ("Bujagali Falls", "Bujagali_Falls"),
                ("Lake Victoria", None),
                ("Jinja Main Street", None)],
    blurb="The town at the point where the Nile leaves Lake Victoria and "
          "starts north — a wide, calm outflow with a monument on the bank, and "
          "downstream of it enough whitewater to have made this East Africa's "
          "rafting capital.",
    fact="The source was identified by Speke in 1862 and argued about for "
         "decades afterwards; the river runs some 6,600 km from this bank to "
         "the Mediterranean.",
    tip="Jinja's main street is a nearly intact strip of 1950s Indian-built "
        "shopfronts with deep verandas — walk it before heading to the water."),

# ============================== TANZANIA ==============================
"stone-town": dict(
    name="Stone Town", slug="Stone_Town", country="Tanzania",
    region="Zanzibar Urban West", type="history", tag="famous", emoji="🚪",
    sounds=["ocean-waves.mp3"],
    highlights=[("House of Wonders", "House_of_Wonders"),
                ("Old Fort", "Old_Fort_of_Zanzibar"),
                ("Forodhani Gardens", None),
                ("Darajani Market", None)],
    blurb="The old quarter of Zanzibar City: coral-stone houses three and four "
          "storeys high leaning over lanes too narrow for cars, carved wooden "
          "doors on every other building, and a seafront where dhows still "
          "come in under sail.",
    fact="The House of Wonders was the first building in East Africa to have "
         "electricity and the first in Zanzibar with a lift, which is exactly "
         "how it got the name.",
    tip="Forodhani Gardens turns into a grill market at sunset — the whole "
        "waterfront fills with charcoal smoke and the boys jump off the sea "
        "wall between the stalls."),
"kilimanjaro": dict(
    name="Mount Kilimanjaro", slug="Mount_Kilimanjaro", country="Tanzania",
    region="Kilimanjaro Region", type="mountain", tag="famous", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Uhuru Peak", None),
                ("Shira Plateau", None),
                ("Moshi", "Moshi,_Tanzania"),
                ("Barranco Wall", None)],
    blurb="The highest mountain in Africa and the tallest free-standing "
          "mountain on earth — 5,895 m rising alone out of flat plains, so the "
          "whole thing is visible from base to summit when the cloud lifts.",
    fact="A climb passes through five climate zones in a few days, from "
         "farmland and rainforest through moorland and alpine desert to an "
         "arctic summit with glaciers on the equator.",
    tip="The Machame route takes longer than the Marangu 'Coca-Cola' route and "
        "has a far higher success rate, because the extra days are what "
        "acclimatise you."),
"serengeti": dict(
    name="Serengeti", slug="Serengeti_National_Park", country="Tanzania",
    region="Mara Region", type="nature", tag="famous", emoji="🦓",
    sounds=["wilderness.mp3"],
    highlights=[("Grumeti River", None),
                ("Moru Kopjes", None),
                ("Seronera Valley", None)],
    blurb="Fifteen thousand square kilometres of grassland, acacia and granite "
          "outcrops carrying the largest land-mammal migration on earth: close "
          "to two million wildebeest and zebra moving in a slow annual circle "
          "with the rain.",
    fact="The kopjes — island hills of ancient granite standing out of the "
         "plain — hold their own water and shade, and are where the lions and "
         "hyraxes spend the middle of the day.",
    tip="Balloon flights leave before dawn from Seronera and land in the "
        "grass; from a hundred metres up the herd structure is suddenly "
        "legible."),
"ngorongoro": dict(
    name="Ngorongoro Crater", slug="Ngorongoro_Conservation_Area",
    country="Tanzania", region="Arusha Region", type="nature", tag="famous",
    emoji="🌋", sounds=["wilderness.mp3"],
    highlights=[("Ngorongoro Crater", "Ngorongoro_Crater"),
                ("Olduvai Gorge", "Olduvai_Gorge"),
                ("Empakaai Crater", None)],
    blurb="An intact volcanic caldera 20 km across and 600 m deep, with a "
          "permanent population of some 25,000 large animals living on its "
          "floor — grassland, a soda lake and a fever-tree forest all inside "
          "one rim you drive down into.",
    fact="Olduvai Gorge, on the edge of the same conservation area, produced "
         "the fossils and stone tools that pushed human origins back nearly two "
         "million years.",
    tip="Be at the descent road when the gate opens; the crater floor holds "
        "mist until about nine and the rim viewpoints are clear only early."),
"dar-es-salaam": dict(
    name="Dar es Salaam", slug="Dar_es_Salaam", country="Tanzania",
    region="Dar es Salaam Region", type="city", tag="famous", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Kariakoo", "Kariakoo"),
                ("National Museum of Tanzania", "National_Museum_of_Tanzania"),
                ("Kivukoni Fish Market", None),
                ("Coco Beach", None)],
    blurb="Tanzania's biggest city and one of the fastest-growing anywhere, "
          "wrapped around a near-enclosed natural harbour whose entrance is a "
          "narrow gap — which is what the name, 'haven of peace', is about.",
    fact="Kariakoo market takes its name from the Carrier Corps quartered "
         "there in the First World War, and now floods a whole district of "
         "streets around its 1970s concrete hall.",
    tip="The ferry to Kigamboni costs a few hundred shillings and gives the "
        "best view of the harbour mouth, dhows included, in about five "
        "minutes."),
"lake-natron": dict(
    name="Lake Natron", slug="Lake_Natron", country="Tanzania",
    region="Arusha Region", type="nature", tag="hidden", emoji="🦩",
    sounds=["wind.mp3"],
    highlights=[("Ol Doinyo Lengai", "Ol_Doinyo_Lengai"),
                ("Engare Sero", None),
                ("Ngare Sero Waterfall", None)],
    blurb="A shallow soda lake in the Rift so alkaline and so hot that almost "
          "nothing can live in it — and for exactly that reason it is the only "
          "regular breeding site for East Africa's lesser flamingos, which nest "
          "on salt islands nothing else can reach.",
    fact="Beside it stands Ol Doinyo Lengai, the only active volcano on earth "
         "erupting natrocarbonatite lava — which flows black, cool enough to "
         "stand near, and turns white within hours.",
    tip="The footprint site at Engare Sero preserves more than 400 human "
        "tracks in volcanic ash, laid down between 5,000 and 19,000 years "
        "ago."),

# ============================== KENYA (additions) ==============================
"lamu": dict(
    name="Lamu", slug="Lamu", country="Kenya", region="Lamu County",
    type="island", tag="hidden", emoji="🐈", sounds=["ocean-waves.mp3"],
    highlights=[("Lamu Old Town", "Lamu_Old_Town"),
                ("Lamu Fort", None),
                ("Shela Beach", None),
                ("Riyadha Mosque", None)],
    blurb="The oldest continuously inhabited Swahili settlement, on an island "
          "off the northern coast, where there are essentially no cars — "
          "donkeys and dhows do the work, and the lanes between the coral "
          "houses are too narrow for anything else.",
    fact="Lamu has been lived in without a break since the 12th century, and "
         "the town's building tradition — coral rag, mangrove poles, carved "
         "doors, inner courtyards — has changed very little since.",
    tip="Walk the twelve kilometres of empty sand south from Shela, or take a "
        "sunset dhow: the crews sail rather than motor if you ask."),
"amboseli": dict(
    name="Amboseli National Park", slug="Amboseli_National_Park",
    country="Kenya", region="Kajiado County", type="nature", tag="famous",
    emoji="🐘", sounds=["wilderness.mp3"],
    highlights=[("Observation Hill", None),
                ("Lake Amboseli", None),
                ("Enkongo Narok Swamp", None)],
    blurb="Dry, dusty short-grass plains directly under Kilimanjaro, fed by "
          "swamps of meltwater that come from the mountain underground — which "
          "is why big elephant herds stand in green marsh in the middle of what "
          "looks like desert.",
    fact="Amboseli's elephants are among the best-studied in the world: "
         "individuals here have been followed continuously since 1972, across "
         "several generations.",
    tip="The mountain is usually only clear for an hour after sunrise and "
        "again just before sunset — the rest of the day it hides entirely in "
        "its own cloud."),
"lake-nakuru": dict(
    name="Lake Nakuru", slug="Lake_Nakuru", country="Kenya",
    region="Nakuru County", type="nature", tag="hidden", emoji="🦩",
    sounds=["wind.mp3"],
    highlights=[("Lake Nakuru National Park", "Lake_Nakuru_National_Park"),
                ("Menengai Crater", "Menengai"),
                ("Baboon Cliff", None)],
    blurb="A shallow soda lake in the floor of the Rift Valley, ringed by "
          "acacia and fever trees and fenced as a sanctuary — one of the few "
          "places where both black and white rhino are reliably seen, with the "
          "escarpment standing over the whole thing.",
    fact="Its algae once drew well over a million flamingos at a time; the "
         "flock now moves between Rift lakes as water levels shift, which is "
         "why the numbers swing so hard year to year.",
    tip="Drive up to Baboon Cliff in the late afternoon — the lake, the "
        "flamingo line and the far wall of the Rift are all in one frame."),
"mount-kenya": dict(
    name="Mount Kenya", slug="Mount_Kenya", country="Kenya",
    region="Central Kenya", type="mountain", tag="famous", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Mount Kenya National Park", "Mount_Kenya_National_Park"),
                ("Point Lenana", None),
                ("Batian", None),
                ("Lake Michaelson", None)],
    blurb="An eroded volcano straddling the equator whose two highest peaks "
          "are technical rock climbs, with glaciers, tarns and giant lobelias "
          "on the way up and a third summit that walkers can reach.",
    fact="It gave the country its name, and it carries permanent ice within a "
         "few kilometres of the equator — though the glaciers have lost most "
         "of their area in a century.",
    tip="The Chogoria route on the eastern side passes Lake Michaelson in a "
        "cirque under vertical walls, and is far quieter than the Naro Moru "
        "approach."),

# ============================== ETHIOPIA (additions) ==============================
"axum": dict(
    name="Axum", slug="Axum", country="Ethiopia", region="Tigray Region",
    type="history", tag="famous", emoji="🗿", sounds=["desert-wind.mp3"],
    highlights=[("Obelisk of Axum", "Obelisk_of_Axum"),
                ("Church of Our Lady Mary of Zion",
                 "Church_of_Our_Lady_Mary_of_Zion"),
                ("Dungur", "Dungur"),
                ("Tombs of Kaleb and Gebre Meskel", None)],
    blurb="The capital of a trading empire that minted its own coinage and "
          "ran the Red Sea, marked by a field of carved granite stelae — the "
          "largest of them a single 33 m block, quarried, carved and raised, "
          "which fell and still lies where it broke.",
    fact="Ethiopian tradition holds that the Ark of the Covenant is kept in a "
         "chapel beside the Church of Our Lady Mary of Zion, guarded by one "
         "monk who may never leave the enclosure.",
    tip="Walk out to the tombs of Kaleb and Gebre Meskel on the hill north of "
        "town — cut stone chambers, no crowds, and the whole plateau below."),
"danakil": dict(
    name="Danakil Depression", slug="Danakil_Depression", country="Ethiopia",
    region="Afar Region", type="desert", tag="famous", emoji="🌋",
    sounds=["desert-wind.mp3"],
    highlights=[("Dallol", "Dallol,_Ethiopia"),
                ("Erta Ale", "Erta_Ale"),
                ("Lake Karum", None)],
    blurb="One of the lowest and hottest places on the planet, more than 100 m "
          "below sea level, where three tectonic plates pull apart — sulphur "
          "terraces in acid yellows and greens, salt flats to the horizon, and "
          "a permanent lava lake to the south.",
    fact="Dallol holds the highest recorded average annual temperature of any "
         "inhabited place on earth, around 34°C measured year-round.",
    tip="Salt is still cut by hand from the flats and carried out by camel "
        "caravan; the trains form in the afternoon and walk through the night."),
"simien-mountains": dict(
    name="Simien Mountains", slug="Simien_Mountains", country="Ethiopia",
    region="Amhara Region", type="mountain", tag="famous", emoji="⛰️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Ras Dashen", "Ras_Dashen"),
                ("Simien Mountains National Park",
                 "Simien_Mountains_National_Park"),
                ("Geech Abyss", None)],
    blurb="An eroded basalt plateau cut into pinnacles and 1,000 m escarpments "
          "— the result of a shield volcano being worn back for 40 million "
          "years. The walking is along the rim, with the drop always on one "
          "side.",
    fact="Ras Dashen at 4,550 m is Ethiopia's highest point, and the range "
         "holds animals found nowhere else on earth, including the walia ibex "
         "on the cliff faces themselves.",
    tip="Camp at Geech and walk out to Imet Gogo at dawn: the promontory has "
        "sheer drops on three sides and the cloud sits below it."),
"bahir-dar": dict(
    name="Bahir Dar", slug="Bahir_Dar", country="Ethiopia",
    region="Amhara Region", type="city", tag="hidden", emoji="⛵",
    sounds=["wind.mp3"],
    highlights=[("Blue Nile Falls", "Blue_Nile_Falls"),
                ("Lake Tana", "Lake_Tana"),
                ("Ura Kidane Mehret", None),
                ("Bezawit Hill", None)],
    blurb="A palm-lined town on the southern shore of Ethiopia's largest lake, "
          "where the Blue Nile begins. Monasteries stand on the lake's islands, "
          "some of them founded in the 14th century and painted floor to "
          "ceiling inside.",
    fact="Papyrus tankwa boats, the same design shown in ancient Egyptian "
         "reliefs, are still built and paddled on Lake Tana for fishing and "
         "for crossing to the islands.",
    tip="Take the boat to the Zege peninsula in the morning and walk the "
        "coffee-forest path between three round churches; the paintings inside "
        "are the point."),
"harar": dict(
    name="Harar", slug="Harar", country="Ethiopia", region="Harari Region",
    type="history", tag="famous", emoji="🐺", sounds=["desert-wind.mp3"],
    highlights=[("Jugol", None),
                ("Harar Jugol wall", None),
                ("Rimbaud House", None),
                ("Harar Market", None)],
    blurb="A walled city in the eastern highlands with 82 mosques inside about "
          "a square kilometre and lanes painted in flat blocks of colour. It "
          "was closed to outsiders for centuries and still feels like a city "
          "with its own rules.",
    fact="Hyenas come into the streets at night through gaps in the wall left "
         "for them, and men have hand-fed them at the edge of town for "
         "generations.",
    tip="Get lost deliberately inside Jugol — the whole walled town is small "
        "enough that any lane eventually returns you to a gate."),

# ============================== ERITREA ==============================
"asmara": dict(
    name="Asmara", slug="Asmara", country="Eritrea", region="Maekel Region",
    type="city", tag="famous", emoji="🏛️", sounds=["european-plaza.mp3"],
    highlights=[("Fiat Tagliero Building", "Fiat_Tagliero_Building"),
                ("Cinema Impero", "Cinema_Impero"),
                ("Asmara Opera House", None),
                ("Nda Mariam Cathedral", None)],
    blurb="A highland capital at 2,325 m that was rebuilt in the 1930s as a "
          "showcase of Italian modernism and then left almost untouched: "
          "streamlined cinemas, futurist petrol stations, palm-lined avenues "
          "and a pace set by pavement cafés.",
    fact="The Fiat Tagliero service station of 1938 has two 15 m concrete "
         "wings with no supports under them at all — the engineer reportedly "
         "had to be persuaded at gunpoint to remove the props.",
    tip="Do the evening passeggiata on Harnet Avenue; the whole city walks it "
        "between six and eight, and the cinemas open their foyers."),
"massawa": dict(
    name="Massawa", slug="Massawa", country="Eritrea",
    region="Northern Red Sea Region", type="coastal", tag="hidden", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Massawa Old Town", None),
                ("Imperial Palace", None),
                ("Massawa causeway", None)],
    blurb="A Red Sea port built across two coral islands linked by causeways, "
          "with Ottoman and Egyptian arcades, carved balconies and heavy war "
          "damage left visible. Fiercely hot at sea level, an hour and 2,300 m "
          "below Asmara.",
    fact="The road down from the highlands drops from alpine air to Red Sea "
         "humidity in about 110 km, one of the steepest sustained descents of "
         "any highway in Africa.",
    tip="The old town on Massawa Island is best in the last hour of light, "
        "when the coral stone goes orange and the arcades are in shade."),

# ============================== DJIBOUTI ==============================
"lake-assal": dict(
    name="Lake Assal", slug="Lake_Assal_(Djibouti)", country="Djibouti",
    region="Tadjourah Region", type="nature", tag="hidden", emoji="🧂",
    sounds=["desert-wind.mp3"],
    highlights=[("Ardoukôba", None),
                ("Ghoubbet-el-Kharab", None),
                ("Salt flats of Assal", None)],
    blurb="A crater lake 155 m below sea level — the lowest point in Africa — "
          "ringed by a blinding white salt shelf and black lava fields, with "
          "water so dense you float in it without trying.",
    fact="At around ten times the salinity of the ocean, Assal is the saltiest "
         "body of water on earth outside Antarctica's subglacial pools.",
    tip="The far shore has a fissure field from the 1978 Ardoukôba eruption — "
        "you can walk into cracks that opened when the continent pulled apart."),
"djibouti-city": dict(
    name="Djibouti City", slug="Djibouti_(city)", country="Djibouti",
    region="Djibouti Region", type="city", tag="hidden", emoji="🏙️",
    sounds=["ocean-waves.mp3"], search_name="Djibouti City",
    highlights=[("Hamoudi Mosque", None),
                ("Marché Central", None),
                ("Place Menelik", None),
                ("Doraleh", None)],
    blurb="A small, very hot port city at the mouth of the Red Sea, with "
          "whitewashed arcaded blocks around Place Menelik and a harbour that "
          "handles most of landlocked Ethiopia's trade.",
    fact="Djibouti sits on the Bab-el-Mandeb approach, through which a "
         "substantial share of world shipping passes — which is why a country "
         "of a million people hosts foreign bases from four continents.",
    tip="Take a boat out to Moucha Island for the afternoon; it is half an "
        "hour offshore and the reef starts at the beach."),

# ============================== SOMALIA ==============================
"mogadishu": dict(
    name="Mogadishu", slug="Mogadishu", country="Somalia", region="Banaadir",
    type="coastal", tag="hidden", emoji="🕌", sounds=["ocean-waves.mp3"],
    highlights=[("Arba'a Rukun Mosque", "Arba'a_Rukun_Mosque"),
                ("Mogadishu Cathedral", "Mogadishu_Cathedral"),
                ("Bakaara Market", "Bakaara_Market"),
                ("Lido Beach", None)],
    blurb="An ancient Indian Ocean trading port with a long white beach, "
          "rebuilding after three decades of war — Italian colonial arcades, "
          "Arab-influenced old quarters and one of the oldest mosques in the "
          "region still standing among it.",
    fact="Mogadishu was a major stop on the medieval Indian Ocean trade "
         "circuit; Ibn Battuta visited in 1331 and described a city already "
         "wealthy on cloth exports.",
    tip="Lido Beach on a Friday afternoon is the city at its most itself: "
        "football, swimmers and fish grills the whole length of the sand."),
"laas-geel": dict(
    name="Laas Geel", slug="Laas_Geel", country="Somalia",
    region="Maroodi Jeex", type="ruin", tag="hidden", emoji="🎨",
    sounds=["desert-wind.mp3"],
    highlights=[("Laas Geel rock shelters", None),
                ("Hargeisa", "Hargeisa")],
    blurb="Granite overhangs on a dry plateau holding some of the best-"
          "preserved rock art in Africa — cows in ceremonial robes, human "
          "figures with arms raised, painted in ochre, white and red and never "
          "exposed to direct rain.",
    fact="The paintings were only described by outsiders in 2002 and are "
         "thought to be 5,000 years old or more; the colours are still "
         "startlingly strong because the shelters face away from the weather.",
    tip="It is an hour from Hargeisa on the Berbera road, and the site is "
        "climbed rather than walked — the best panels are in the upper "
        "shelters."),

# ============================== SOUTH SUDAN ==============================
"juba": dict(
    name="Juba", slug="Juba", country="South Sudan",
    region="Central Equatoria", type="city", tag="hidden", emoji="🏙️",
    sounds=["wilderness.mp3"],
    highlights=[("Jebel Kujur", None),
                ("Juba Bridge", None),
                ("All Saints Cathedral", None),
                ("Konyo Konyo Market", None)],
    blurb="The capital of the world's youngest country, on the west bank of "
          "the White Nile where the river stops being navigable from the "
          "north. Low, hot, red-earthed, and expanding faster than any plan "
          "for it.",
    fact="South Sudan became independent in 2011, making Juba a national "
         "capital younger than the smartphone.",
    tip="Jebel Kujur, the rocky hill on the western edge, is a short climb and "
        "gives the only view over the river bend and the whole town."),
"sudd": dict(
    name="The Sudd", slug="Sudd", country="South Sudan", region="Jonglei",
    type="nature", tag="hidden", emoji="🐦", sounds=["wilderness.mp3"],
    highlights=[("White Nile", None),
                ("Papyrus channels", None),
                ("Bor", None)],
    blurb="One of the largest wetlands on earth: the White Nile spreads out "
          "across a nearly flat basin into a shifting maze of papyrus, reed "
          "and open lagoon that can swell to the size of England in flood.",
    fact="The swamp is so obstructive that it defeated every attempt to sail "
         "up the Nile from the north for two thousand years — its Arabic name "
         "simply means 'the barrier'.",
    tip="The white-eared kob migration through the eastern floodplain is one "
        "of the largest antelope movements left anywhere, and almost nobody "
        "outside the country has seen it."),
# ============================== MADAGASCAR ==============================
"antananarivo": dict(
    name="Antananarivo", slug="Antananarivo", country="Madagascar",
    region="Analamanga", type="city", tag="famous", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Rova of Antananarivo", "Rova_of_Antananarivo"),
                ("Analakely Market", None),
                ("Lake Anosy", None),
                ("Andafiavaratra Palace", None)],
    blurb="A capital built up and over a dozen steep hills at 1,280 m, with "
          "stairways instead of streets in much of the old town, tall narrow "
          "brick houses, and a royal palace on the highest ridge visible from "
          "everywhere below.",
    fact="The city's name means 'of the thousand', for the garrison a 17th-"
         "century king is said to have stationed on the hill — it has never "
         "been called anything else since.",
    tip="Climb the stairways of the Haute-Ville in the late afternoon rather "
        "than taking a taxi round; the whole plateau of rice paddies opens up "
        "from the terraces by the palace."),
"avenue-of-the-baobabs": dict(
    name="Avenue of the Baobabs", slug="Avenue_of_the_Baobabs",
    country="Madagascar", region="Menabe", type="nature", tag="famous",
    emoji="🌳", sounds=["wind.mp3"],
    highlights=[("Kirindy Forest", "Kirindy_Forest"),
                ("Morondava", "Morondava"),
                ("Baobab Amoureux", None)],
    blurb="A dirt road on the west coast lined with around twenty *Adansonia "
          "grandidieri* — smooth grey columns up to 30 m high with a small "
          "crown of branches at the very top, left standing when the forest "
          "around them was cleared for rice.",
    fact="These trees are up to 800 years old and are the remnant of a dense "
         "dry forest; the avenue exists because the baobabs were too useful to "
         "cut and everything else was not.",
    tip="Sunset is the famous hour and it is crowded; sunrise gives the same "
        "light from the other side with almost nobody there."),
"tsingy-de-bemaraha": dict(
    name="Tsingy de Bemaraha", slug="Tsingy_de_Bemaraha_Strict_Nature_Reserve",
    country="Madagascar", region="Melaky", type="nature", tag="famous",
    emoji="🗡️", sounds=["wilderness.mp3"],
    highlights=[("Manambolo Gorge", None),
                ("Grand Tsingy", None),
                ("Bekopaka", None)],
    blurb="A limestone plateau dissolved by rain into a field of vertical "
          "blades — hundreds of square kilometres of grey stone needles, "
          "canyons and caves, crossed on via ferrata cables and rope bridges "
          "because there is no walkable ground.",
    fact="*Tsingy* is usually translated as 'where one cannot walk barefoot', "
         "which is a plain statement of fact: the rock edges are sharp enough "
         "to cut through a boot sole.",
    tip="The Manambolo gorge is done by pirogue at the base of the formation, "
        "which is the only way to see how deep the whole thing is cut."),
"nosy-be": dict(
    name="Nosy Be", slug="Nosy_Be", country="Madagascar", region="Diana",
    type="island", tag="hidden", emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Mount Passot", None),
                ("Lokobe Reserve", None),
                ("Hell-Ville", None),
                ("Nosy Komba", None)],
    blurb="A volcanic island off the northwest coast, planted with ylang-ylang "
          "and vanilla so the whole place smells of it, with crater lakes "
          "inland and a fringe of small islands offshore.",
    fact="Nosy Be supplies a large share of the world's ylang-ylang oil; the "
         "distilleries are roadside sheds and the trees are pruned into "
         "umbrellas so the flowers can be picked by hand.",
    tip="Climb Mount Passot for sunset over the crater lakes — the road up is "
        "rough but short, and the lakes are held sacred so nobody swims in "
        "them."),
"ranomafana": dict(
    name="Ranomafana National Park", slug="Ranomafana_National_Park",
    country="Madagascar", region="Vatovavy", type="nature", tag="hidden",
    emoji="🐒", sounds=["wilderness.mp3"],
    highlights=[("Namorona River", None),
                ("Ranomafana hot springs", None),
                ("Vohiparara", None)],
    blurb="Steep montane rainforest in the southeast, permanently wet and "
          "loud with frogs, dropping into a river gorge with hot springs at the "
          "bottom. Twelve lemur species live here and most walking is up or "
          "down.",
    fact="The park was created in 1991 after the golden bamboo lemur — an "
         "animal previously unknown to science — was found in this forest and "
         "nowhere else.",
    tip="Do a night walk on the road at the park edge: mouse lemurs, chameleons "
        "and leaf-tailed geckos are all in the first hundred metres, and it "
        "costs a fraction of a day trek."),

# ============================== MAURITIUS ==============================
"port-louis": dict(
    name="Port Louis", slug="Port_Louis", country="Mauritius",
    region="Port Louis District", type="city", tag="hidden", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Aapravasi Ghat", "Aapravasi_Ghat"),
                ("Champ de Mars Racecourse", "Champ_de_Mars_Racecourse"),
                ("Caudan Waterfront", None),
                ("Central Market", None)],
    blurb="A harbour capital pressed between the sea and a ring of jagged "
          "volcanic peaks, with a Chinatown, a colonial waterfront, Tamil and "
          "Creole quarters, and mountains standing directly at the end of the "
          "main streets.",
    fact="The Champ de Mars has been racing horses since 1812, which makes it "
         "the oldest racecourse in the southern hemisphere and the second "
         "oldest anywhere.",
    tip="Aapravasi Ghat is the stone landing where nearly half a million "
        "indentured labourers first stepped ashore — sixteen steps, and one of "
        "the quietest World Heritage sites you will visit."),
"le-morne": dict(
    name="Le Morne Brabant", slug="Le_Morne_Brabant", country="Mauritius",
    region="Rivière Noire District", type="mountain", tag="famous",
    emoji="🏔️", sounds=["ocean-waves.mp3"],
    highlights=[("Le Morne Cultural Landscape", None),
                ("Îlot Fourneau", None),
                ("Le Morne lagoon", None)],
    blurb="A basalt monolith rising 556 m straight out of a turquoise lagoon "
          "at the island's southwest tip, with a flat inaccessible top and "
          "sheer sides — and offshore, an underwater sand channel that from "
          "the air looks exactly like a waterfall.",
    fact="The mountain was a refuge for people escaping slavery, who lived in "
         "the caves and on the summit; it is protected as a cultural landscape "
         "for that reason rather than a scenic one.",
    tip="The climb is a steep two hours and the last section needs a guide — "
        "but the base trail alone reaches a viewpoint over the whole lagoon."),
"chamarel": dict(
    name="Chamarel", slug="Chamarel", country="Mauritius",
    region="Rivière Noire District", type="village", tag="hidden", emoji="🌈",
    sounds=["waterfall.mp3"],
    highlights=[("Seven Coloured Earths", "Seven_Coloured_Earths"),
                ("Chamarel Waterfall", None),
                ("Black River Gorges National Park",
                 "Black_River_Gorges_National_Park")],
    blurb="A village on a high plateau in the southwest, above a 100 m "
          "waterfall and beside a small field of bare dunes in seven distinct "
          "colours — red, brown, violet, blue — that never mix, even after "
          "rain.",
    fact="The colours come from basalt weathered into iron and aluminium "
         "oxides with different densities; scoop them together in a jar and "
         "they separate back into layers.",
    tip="The Black River Gorges start just up the road and hold the last of "
        "the island's native forest, with a viewpoint over the whole southwest "
        "coast."),

# ============================== SEYCHELLES ==============================
"victoria-seychelles": dict(
    name="Victoria", slug="Victoria,_Seychelles", country="Seychelles",
    region="Mahé", type="city", tag="hidden", emoji="🕰️",
    sounds=["ocean-waves.mp3"], search_name="Victoria Seychelles",
    highlights=[("Clock Tower of Victoria", None),
                ("Sir Selwyn Selwyn-Clarke Market", None),
                ("Seychelles National Botanical Gardens", None),
                ("Morne Seychellois", "Morne_Seychellois")],
    blurb="One of the smallest capital cities in the world — you can walk "
          "across it in a quarter of an hour — sitting under forested granite "
          "peaks on the northeast coast of Mahé, with a small clock tower at "
          "the only real junction.",
    fact="The clock tower is a scaled-down copy of one on Vauxhall Bridge Road "
         "in London, erected in 1903 and still the point everyone gives "
         "directions from.",
    tip="The market is finished by early afternoon; go before nine for the "
        "fish, then walk up to the botanical gardens where the giant tortoises "
        "are free to wander."),
"anse-source-dargent": dict(
    name="Anse Source d'Argent", slug="Anse_Source_d'Argent",
    country="Seychelles", region="La Digue", type="coastal", tag="famous",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    highlights=[("La Digue", "La_Digue"),
                ("L'Union Estate", None),
                ("Grand Anse", None)],
    blurb="A shallow, glass-clear beach on La Digue broken up by enormous "
          "weathered granite boulders — smooth, pink-grey, rounded like "
          "sculpture — with a reef so close in that the water barely moves.",
    fact="Those boulders are 750-million-year-old granite: the Seychelles are "
         "the only mid-ocean islands in the world made of continental rock "
         "rather than coral or lava.",
    tip="There are no cars on La Digue to speak of — hire a bicycle at the "
        "jetty and ride the flat coast road, which is how everyone gets "
        "everywhere."),
"vallee-de-mai": dict(
    name="Vallée de Mai", slug="Vallée_de_Mai", country="Seychelles",
    region="Praslin", type="nature", tag="famous", emoji="🌴",
    sounds=["wilderness.mp3"],
    highlights=[("Praslin", "Praslin"),
                ("Fond Ferdinand", None),
                ("Anse Lazio", None)],
    blurb="A small valley of primeval palm forest on Praslin, left more or "
          "less as it was — six endemic palm species, no undergrowth to speak "
          "of, and a canopy that closes so completely the floor stays dim at "
          "midday.",
    fact="It grows the coco de mer, whose nut is the largest seed of any plant "
         "on earth at up to 25 kg, and which General Gordon believed made this "
         "valley the original Garden of Eden.",
    tip="Go at opening time and stand still for a few minutes — the black "
        "parrot, which lives only on Praslin, is heard long before it is "
        "seen."),

# ============================== COMOROS ==============================
"moroni": dict(
    name="Moroni", slug="Moroni,_Comoros", country="Comoros",
    region="Grande Comore", type="city", tag="hidden", emoji="🕌",
    sounds=["ocean-waves.mp3"], search_name="Moroni Comoros",
    highlights=[("Old Friday Mosque", None),
                ("Medina of Moroni", None),
                ("Mount Karthala", "Mount_Karthala"),
                ("Volo Volo Market", None)],
    blurb="A small capital of white and coral-stone houses on a black lava "
          "shore, with a 17th-century mosque right at the harbour wall and one "
          "of the world's largest active craters two hours' walk above the "
          "town.",
    fact="Karthala's caldera is over three kilometres across and the volcano "
         "erupts every decade or so — the ash falls on the capital, which sits "
         "on its western flank.",
    tip="The medina behind the port is a genuine maze of alleys about a metre "
        "wide; go with someone from the neighbourhood and come out at the "
        "market."),

# ============================== MALAWI ==============================
"lake-malawi": dict(
    name="Lake Malawi", slug="Lake_Malawi", country="Malawi",
    region="Northern Region", type="nature", tag="famous", emoji="🐠",
    sounds=["wind.mp3"],
    highlights=[("Likoma Island", "Likoma_Island"),
                ("Cape Maclear", "Cape_Maclear"),
                ("Nkhata Bay", "Nkhata_Bay")],
    blurb="A freshwater lake 580 km long filling the floor of the Rift, with "
          "beaches, rock islands and clear warm water — Livingstone called it "
          "the lake of stars for the lamps of the night fishermen strung across "
          "it after dark.",
    fact="It holds more species of fish than any other lake on earth — "
         "somewhere around a thousand cichlids, almost all of them found "
         "nowhere else, most evolved here within the last two million years.",
    tip="Likoma Island, far out towards the Mozambican shore, has an Anglican "
        "cathedral the size of Winchester's standing in a village of a few "
        "thousand people."),
"zomba-plateau": dict(
    name="Zomba Plateau", slug="Zomba_Plateau", country="Malawi",
    region="Southern Region", type="mountain", tag="hidden", emoji="⛰️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Zomba", "Zomba,_Malawi"),
                ("Emperor's View", None),
                ("Mulunguzi Dam", None),
                ("Williams Falls", None)],
    blurb="A flat-topped massif rising 1,000 m above the old colonial capital, "
          "with cedar and pine forest, trout streams, waterfalls off the rim "
          "and viewpoints looking out over the whole southern half of the "
          "country.",
    fact="Zomba was Malawi's capital until 1975, and the plateau road above it "
         "was built so that officials could escape the heat — the old "
         "Government House is still up on the ridge.",
    tip="Walk the rim path between Emperor's View and Queen's View rather than "
        "driving between them; it is an hour through forest with the drop on "
        "your right the whole way."),

# ============================== MOZAMBIQUE ==============================
"ilha-de-mocambique": dict(
    name="Island of Mozambique", slug="Island_of_Mozambique",
    country="Mozambique", region="Nampula Province", type="island",
    tag="famous", emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Fort São Sebastião", None),
                ("Chapel of Nossa Senhora de Baluarte", None),
                ("Stone Town of Mozambique", None),
                ("Macuti Town", None)],
    blurb="A coral island three kilometres long, joined to the mainland by a "
          "single-lane bridge, that was the Portuguese capital of East Africa "
          "for four centuries — stone and lime palaces at one end, thatched "
          "Macuti houses at the other, and no room for anything else.",
    fact="The chapel at the island's tip, finished in 1522, is the oldest "
         "European building standing in the southern hemisphere.",
    tip="Walk the whole island end to end at low tide along the shore — it "
        "takes about an hour and the fort's sea wall is only reachable that "
        "way."),
"maputo": dict(
    name="Maputo", slug="Maputo", country="Mozambique", region="Maputo City",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Maputo railway station", "Maputo_railway_station"),
                ("Casa de Ferro", "Casa_de_Ferro"),
                ("Fortress of Maputo", None),
                ("Mercado Central", None)],
    blurb="A capital of jacaranda-lined avenues and faded Portuguese "
          "modernism on a bay at the far south of the country, with a "
          "waterfront of grilled prawns and one of the most beautiful railway "
          "stations anywhere.",
    fact="The Casa de Ferro — a prefabricated iron house shipped out in the "
         "1890s — is attributed to Gustave Eiffel's studio, and is completely "
         "uninhabitable in the local climate, which was noticed immediately.",
    tip="The station's café sits under the copper dome on the main concourse; "
        "trains still leave from the platforms beside it."),
"bazaruto": dict(
    name="Bazaruto Archipelago", slug="Bazaruto_Archipelago",
    country="Mozambique", region="Inhambane Province", type="island",
    tag="hidden", emoji="🐬", sounds=["ocean-waves.mp3"],
    highlights=[("Bazaruto Island", None),
                ("Two Mile Reef", None),
                ("Vilankulos", None)],
    blurb="Five sand islands off the central coast with dunes tens of metres "
          "high, freshwater lakes behind them and a shelf of shallow turquoise "
          "water between the archipelago and the mainland.",
    fact="These waters hold the last viable dugong population in the western "
         "Indian Ocean — a few hundred animals grazing seagrass beds inside the "
         "park boundary.",
    tip="Walk over the dunes on Bazaruto itself: from the crest you can see "
        "the open Indian Ocean on one side and the flats on the other at the "
        "same time."),
# ============================== ZAMBIA ==============================
"livingstone": dict(
    name="Livingstone", slug="Livingstone,_Zambia", country="Zambia",
    region="Southern Province", type="city", tag="hidden", emoji="🚂",
    sounds=["waterfall.mp3"], search_name="Livingstone Zambia",
    highlights=[("Victoria Falls", "Victoria_Falls"),
                ("Victoria Falls Bridge", "Victoria_Falls_Bridge"),
                ("Mosi-oa-Tunya National Park", "Mosi-oa-Tunya_National_Park"),
                ("Livingstone Museum", "Livingstone_Museum")],
    blurb="The Zambian town at the falls — low colonial-era buildings along a "
          "single wide main street, ten kilometres from the gorge, and the "
          "place where the railway from the south stopped and the bridge "
          "began.",
    fact="The 1905 steel arch below the falls was assembled from both banks "
         "and met in the middle to within a few millimetres; trains, cars and "
         "bungee jumpers all still use it.",
    tip="From the Zambian side you can walk out onto Knife-Edge Bridge and be "
        "soaked through in thirty seconds when the river is high."),
"south-luangwa": dict(
    name="South Luangwa", slug="South_Luangwa_National_Park", country="Zambia",
    region="Eastern Province", type="nature", tag="famous", emoji="🐆",
    sounds=["wilderness.mp3"],
    highlights=[("Luangwa River", None),
                ("Mfuwe", None),
                ("Nsefu Sector", None)],
    blurb="A broad valley of oxbow lagoons and ebony groves along a river that "
          "moves its channel every flood — one of the densest concentrations of "
          "leopard anywhere, and the place where the walking safari was "
          "invented.",
    fact="Guided walking safaris began here in the 1950s; parks elsewhere "
         "copied the idea, but Luangwa is still where most of the guides are "
         "trained.",
    tip="In October the river drops to sand and pools, and the game "
        "concentrates on what water is left — hot, but the most animals you "
        "will ever see per kilometre."),
"lusaka": dict(
    name="Lusaka", slug="Lusaka", country="Zambia", region="Lusaka Province",
    type="city", tag="hidden", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Lusaka National Museum", None),
                ("Kabwata Cultural Village", None),
                ("Munda Wanga Environmental Park", None),
                ("Cairo Road", None)],
    blurb="A flat, spread-out capital on a plateau at 1,280 m, built around "
          "one long central avenue named for the far end of a road that was "
          "meant to run the length of the continent.",
    fact="Lusaka was a railway siding of a few hundred people in 1930 and was "
         "chosen as capital precisely because it was central, high and "
         "healthy — the city was designed before it existed.",
    tip="The Sunday craft market at Arcades is where the copper, malachite and "
        "basketwork actually gets sold, and the prices are not tourist "
        "prices."),

# ============================== ZIMBABWE ==============================
"victoria-falls": dict(
    name="Victoria Falls", slug="Victoria_Falls", country="Zimbabwe",
    region="Matabeleland North", type="nature", tag="famous", emoji="💦",
    sounds=["waterfall.mp3"],
    highlights=[("Devil's Pool", None),
                ("Victoria Falls Bridge", "Victoria_Falls_Bridge"),
                ("Batoka Gorge", None),
                ("Rainforest walk", None)],
    blurb="The Zambezi drops 108 m into a slot in the basalt along a front "
          "1,700 m wide — not the tallest waterfall nor the widest, but the "
          "largest single sheet of falling water on earth, and the spray from "
          "it grows a rainforest on the opposite rim.",
    fact="The local name, Mosi-oa-Tunya, means 'the smoke that thunders': in "
         "full flood the column of mist rises 400 m and can be seen from "
         "fifty kilometres away.",
    tip="Walk the rainforest path along the Zimbabwean rim end to end — it "
        "faces the falls square on, and every viewpoint is a different section "
        "of the curtain."),
"great-zimbabwe": dict(
    name="Great Zimbabwe", slug="Great_Zimbabwe", country="Zimbabwe",
    region="Masvingo Province", type="ruin", tag="famous", emoji="🪨",
    sounds=["wilderness.mp3"],
    highlights=[("Great Enclosure", None),
                ("Hill Complex", None),
                ("Conical Tower", None),
                ("Valley Ruins", None)],
    blurb="The stone capital of a kingdom that traded gold to the Indian Ocean "
          "from the 11th century — curving walls up to 11 m high and 5 m thick, "
          "built of dressed granite blocks laid without mortar, standing among "
          "boulders and msasa trees.",
    fact="The country took its name from this site; colonial authorities spent "
         "decades insisting it could not have been built locally, and the "
         "archaeology has never supported them.",
    tip="Climb the Hill Complex first, by the steep original stairway between "
        "the boulders rather than the modern path, then look down on the Great "
        "Enclosure."),
"harare": dict(
    name="Harare", slug="Harare", country="Zimbabwe", region="Harare Province",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("National Gallery of Zimbabwe", "National_Gallery_of_Zimbabwe"),
                ("Mbare Musika", None),
                ("Harare Gardens", None),
                ("Kopje", None)],
    blurb="A high, dry capital at 1,490 m laid out on a grid with jacarandas "
          "along the avenues, which flower purple over the whole city for "
          "about three weeks in October.",
    fact="The National Gallery has been the centre of Shona stone sculpture "
         "since the 1950s — the movement was largely built around its workshop "
         "and its exhibitions.",
    tip="Mbare Musika is the biggest market in the country and its music "
        "stalls are where new releases are actually heard first."),
"matobo": dict(
    name="Matobo Hills", slug="Matobo_National_Park", country="Zimbabwe",
    region="Matabeleland South", type="nature", tag="hidden", emoji="🪨",
    sounds=["wilderness.mp3"],
    highlights=[("Matobo Hills", "Matobo_Hills"),
                ("World's View", None),
                ("Nswatugi Cave", None)],
    blurb="A landscape of granite left standing after everything softer eroded "
          "away — domes, castle kopjes and balancing rocks stacked in "
          "improbable piles over 3,000 km², with caves full of rock paintings "
          "underneath them.",
    fact="Matobo has one of the highest densities of rock art in the world, "
         "some of it 13,000 years old, and one of the densest black eagle "
         "populations anywhere.",
    tip="Sunset at World's View, on the bare dome where Cecil Rhodes is "
        "buried, is the classic — but Nswatugi Cave nearby has better "
        "paintings and no crowd."),

# ============================== BOTSWANA ==============================
"okavango-delta": dict(
    name="Okavango Delta", slug="Okavango_Delta", country="Botswana",
    region="North-West District", type="nature", tag="famous", emoji="🛶",
    sounds=["wilderness.mp3"],
    highlights=[("Moremi Game Reserve", "Moremi_Game_Reserve"),
                ("Chief's Island", None),
                ("Maun", "Maun")],
    blurb="A river that never reaches the sea: the Okavango runs south out of "
          "Angola and spreads across the Kalahari into 15,000 km² of "
          "channels, reed islands and floodplain, where it evaporates.",
    fact="The flood arrives at the delta's far end in the middle of the dry "
         "season, months after the rain that caused it fell 1,200 km "
         "upstream — so the water is highest when the land is driest.",
    tip="A mokoro is a dugout poled from the stern; an hour of it at water "
        "level, with reeds closing over the channel, is worth more than a week "
        "of driving."),
"chobe": dict(
    name="Chobe National Park", slug="Chobe_National_Park", country="Botswana",
    region="Chobe District", type="nature", tag="famous", emoji="🐘",
    sounds=["wilderness.mp3"],
    highlights=[("Chobe River", "Chobe_River"),
                ("Savuti", "Savuti"),
                ("Kasane", "Kasane")],
    blurb="Riverfront, floodplain and marsh in the far north, holding one of "
          "the largest elephant populations on earth — herds come down to the "
          "Chobe in the late afternoon in hundreds, and the boats sit still in "
          "the middle of it.",
    fact="Northern Botswana holds well over 100,000 elephants, and in the dry "
         "season a large share of them are within reach of this one river.",
    tip="Do the river by boat rather than by vehicle: you end up level with "
        "the animals, downwind, and much closer than any road allows."),
"makgadikgadi": dict(
    name="Makgadikgadi Pan", slug="Makgadikgadi_Pan", country="Botswana",
    region="Central District", type="desert", tag="hidden", emoji="🧂",
    sounds=["wind.mp3"],
    highlights=[("Kubu Island", "Kubu_Island"),
                ("Nxai Pan National Park", "Nxai_Pan_National_Park"),
                ("Baines' Baobabs", None)],
    blurb="The bed of a lake that dried up thousands of years ago — one of the "
          "largest salt flats in the world, so flat and so empty that in the "
          "dry season there is no feature of any kind between you and the "
          "horizon in any direction.",
    fact="Kubu Island is a granite outcrop standing on the pan with baobabs "
          "growing out of it and a beach of fossil water-worn pebbles around "
          "its base, hundreds of kilometres from any water.",
    tip="Sleep out on the pan itself in the dry months: there is no light and "
        "no sound at all, which people find harder than they expect."),
"gaborone": dict(
    name="Gaborone", slug="Gaborone", country="Botswana",
    region="South-East District", type="city", tag="hidden", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Three Dikgosi Monument", "Three_Dikgosi_Monument"),
                ("Kgale Hill", None),
                ("Gaborone Dam", None),
                ("Botswana National Museum", None)],
    blurb="A capital built from scratch in three years before independence in "
          "1966, on a site chosen for its water — low, spread out, ringed by "
          "hills, and grown from a village of a few thousand into the country's "
          "only large city.",
    fact="The Three Dikgosi Monument honours the chiefs who travelled to "
         "London in 1895 to argue against their territory being handed to a "
         "mining company — and won.",
    tip="Kgale Hill is a 45-minute scramble from the edge of town and gives "
        "the whole city, the dam and the surrounding bush in one view."),
"tsodilo": dict(
    name="Tsodilo Hills", slug="Tsodilo", country="Botswana",
    region="North-West District", type="ruin", tag="hidden", emoji="🎨",
    sounds=["desert-wind.mp3"],
    highlights=[("Male Hill", None),
                ("Rhino Trail", None),
                ("Laurens van der Post Panel", None)],
    blurb="Four quartzite hills standing out of flat Kalahari sand in the "
          "northwest, carrying more than 4,500 rock paintings across 10 km² — "
          "the densest concentration of rock art anywhere in the world.",
    fact="The hills have been occupied for around 100,000 years, and the "
         "paintings on them were made over tens of thousands of those — an "
         "unbroken record on a single rock face.",
    tip="Walk the Rhino Trail in the early morning; the panels face different "
        "directions and only some of them are legible in low light."),

# ============================== NAMIBIA ==============================
"sossusvlei": dict(
    name="Sossusvlei", slug="Sossusvlei", country="Namibia",
    region="Hardap Region", type="desert", tag="famous", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Deadvlei", "Deadvlei"),
                ("Sesriem Canyon", "Sesriem_Canyon"),
                ("Big Daddy", None),
                ("Elim Dune", None)],
    blurb="A clay pan at the end of a dry river surrounded by star dunes up to "
          "325 m high, coloured deep orange by iron oxide — among the tallest "
          "sand dunes on earth, in one of the oldest deserts.",
    fact="Deadvlei's camel thorn trees died around 900 years ago when the dune "
         "field cut off the river, and have not decomposed since: it is too "
         "dry for the wood to rot.",
    tip="Be at the gate at sunrise so you reach Deadvlei while the far dune "
        "wall is still in shadow — black trees, white pan, orange sand, no "
        "sky."),
"etosha": dict(
    name="Etosha National Park", slug="Etosha_National_Park",
    country="Namibia", region="Kunene Region", type="nature", tag="famous",
    emoji="🦓", sounds=["wilderness.mp3"],
    highlights=[("Etosha pan", "Etosha_pan"),
                ("Okaukuejo", None),
                ("Halali", None)],
    blurb="A salt pan 130 km long, dry and blinding white for most of the "
          "year, ringed by scrub where the game concentrates at a handful of "
          "waterholes — which is why Etosha is the easiest place in Africa to "
          "sit still and let the animals come to you.",
    fact="The pan is so large and so flat that it is visible from orbit, and "
         "in a wet enough year it floods shallowly and draws flamingos to "
         "breed in the middle of it.",
    tip="The floodlit waterhole at Okaukuejo runs all night — rhino, elephant "
        "and lion come through in sequence, and the best hour is usually well "
        "after midnight."),
"swakopmund": dict(
    name="Swakopmund", slug="Swakopmund", country="Namibia",
    region="Erongo Region", type="coastal", tag="hidden", emoji="🌫️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Swakopmund Jetty", None),
                ("Woermannhaus", None),
                ("Walvis Bay", "Walvis_Bay"),
                ("Dune 7", None)],
    blurb="A German colonial seaside town — half-timbering, a lighthouse, a "
          "Lutheran church — standing where the Namib desert runs straight "
          "into the cold Atlantic, usually under fog, with dunes at the end of "
          "the last street.",
    fact="The Benguela current is cold enough to condense fog most mornings, "
         "and that fog is the only reliable water source for everything living "
         "in this stretch of desert.",
    tip="Walk out on the old jetty at dusk when the fog is coming in — the "
        "town disappears behind you within a couple of hundred metres."),
"fish-river-canyon": dict(
    name="Fish River Canyon", slug="Fish_River_Canyon", country="Namibia",
    region="ǁKaras Region", type="nature", tag="famous", emoji="🏞️",
    sounds=["wind.mp3"],
    highlights=[("Ai-Ais Hot Springs", "Ai-Ais_Hot_Springs"),
                ("Hobas", None),
                ("Hell's Corner", None)],
    blurb="The largest canyon in Africa: 160 km long, up to 27 km wide and "
          "550 m deep, cut through bare rock in the far south, with a river at "
          "the bottom that is a chain of pools for most of the year.",
    fact="The five-day hike along the canyon floor can only be walked between "
         "May and September — outside that window the heat and flash floods "
         "make it genuinely lethal.",
    tip="Even without the hike, the rim viewpoints at Hobas at sunrise show "
        "the meanders in relief, which the midday flat light destroys."),
"skeleton-coast": dict(
    name="Skeleton Coast", slug="Skeleton_Coast", country="Namibia",
    region="Kunene Region", type="coastal", tag="hidden", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Hoanib River", "Hoanib_River"),
                ("Terrace Bay", None),
                ("Shipwrecks of the Skeleton Coast", None)],
    blurb="Five hundred kilometres of fog-bound shore where desert meets a "
          "cold, violent sea — wrecked hulls half-buried in sand, whale bone "
          "on the beach, and a name given by the people who had to walk inland "
          "from those wrecks.",
    fact="The Portuguese called it the Gates of Hell: a ship driven ashore "
         "here could be landed safely and still leave a crew hundreds of "
         "kilometres from any water.",
    tip="Cape Cross holds a colony of up to 200,000 fur seals — you smell and "
        "hear it several minutes before you can see it."),
"windhoek": dict(
    name="Windhoek", slug="Windhoek", country="Namibia",
    region="Khomas Region", type="city", tag="hidden", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Christuskirche", "Christ_Church,_Windhoek"),
                ("Alte Feste", "Alte_Feste"),
                ("Independence Memorial Museum", None),
                ("Katutura", "Katutura")],
    blurb="A small, dry, orderly capital in a bowl of hills at 1,700 m, where "
          "German colonial churches and forts stand a few streets from a "
          "modern parliament, and the bush starts at the ring road.",
    fact="Windhoek's water has been recycled directly from sewage to drinking "
         "supply since 1968 — the first city in the world to do it, out of "
         "sheer necessity.",
    tip="Eat at a joint in Katutura rather than in the centre; the township's "
        "food and music scene is the actual social life of the city."),

# ============================== SOUTH AFRICA (additions) ==============================
"durban": dict(
    name="Durban", slug="Durban", country="South Africa",
    region="KwaZulu-Natal", type="coastal", tag="famous", emoji="🏄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Golden Mile", None),
                ("uShaka Marine World", "UShaka_Marine_World"),
                ("Juma Musjid Mosque", "Grey_Street_Mosque"),
                ("Victoria Street Market", None)],
    blurb="A warm, subtropical port on the Indian Ocean with a six-kilometre "
          "beachfront promenade, Africa's busiest harbour behind it, and the "
          "largest Indian population of any city outside India.",
    fact="Bunny chow — a hollowed loaf filled with curry — was invented here, "
         "and the argument about which shop does it properly is a genuine "
         "civic institution.",
    tip="Walk the Golden Mile from uShaka north at dawn; the surfers, the "
        "swimmers and the fishermen are all out before the heat."),
"drakensberg": dict(
    name="Drakensberg", slug="Drakensberg", country="South Africa",
    region="KwaZulu-Natal", type="mountain", tag="famous", emoji="⛰️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Amphitheatre", "Amphitheatre_(Drakensberg)"),
                ("Tugela Falls", "Tugela_Falls"),
                ("Cathedral Peak", "Cathedral_Peak"),
                ("Giant's Castle", None)],
    blurb="A basalt escarpment running 1,000 km along the Lesotho border, "
          "rising in places as a single unbroken wall five kilometres wide and "
          "1,200 m high, with grassland below it and San rock paintings in the "
          "caves at its foot.",
    fact="Tugela Falls drops off the Amphitheatre's lip in five leaps totalling "
         "948 m — by several measurements the tallest waterfall in the world, "
         "though it is seasonal.",
    tip="The chain ladders route up the back of the Amphitheatre gets you to "
        "the top of the falls in a few hours; you look straight down the drop "
        "from the stream itself."),
"garden-route": dict(
    name="Garden Route", slug="Garden_Route", country="South Africa",
    region="Western Cape", type="nature", tag="famous", emoji="🌊",
    sounds=["ocean-waves.mp3"],
    highlights=[("Knysna", "Knysna"),
                ("Tsitsikamma", "Tsitsikamma"),
                ("Plettenberg Bay", "Plettenberg_Bay"),
                ("Storms River Mouth", None)],
    blurb="Three hundred kilometres of coast between the Outeniqua mountains "
          "and the Indian Ocean — indigenous forest, lagoons, sandstone heads "
          "and river gorges, with the road running the whole length of it.",
    fact="Tsitsikamma's forest holds yellowwoods over 800 years old, and the "
         "coastal section was South Africa's first marine protected area, "
         "declared in 1964.",
    tip="Walk the first hour of the Otter Trail from Storms River Mouth — it "
        "needs no permit and includes the suspension bridges over the gorge."),
"stellenbosch": dict(
    name="Stellenbosch", slug="Stellenbosch", country="South Africa",
    region="Western Cape", type="village", tag="hidden", emoji="🍇",
    sounds=["european-plaza.mp3"],
    highlights=[("Dorp Street", None),
                ("Stellenbosch University", "Stellenbosch_University"),
                ("Jonkershoek Nature Reserve", "Jonkershoek_Nature_Reserve"),
                ("Moederkerk", None)],
    blurb="An oak-lined university town in a valley of vineyards an hour from "
          "Cape Town, with whitewashed Cape Dutch gables, mountains on three "
          "sides, and wine estates that start at the end of the streets.",
    fact="Founded in 1679, it is the second-oldest European settlement in the "
         "country, and Dorp Street has the longest row of old Cape Dutch "
         "buildings anywhere.",
    tip="Jonkershoek, fifteen minutes out of town, is a horseshoe of mountains "
        "with a loop road and waterfall trails — the vineyards get the visitors "
        "and this does not."),
"robben-island": dict(
    name="Robben Island", slug="Robben_Island", country="South Africa",
    region="Western Cape", type="island", tag="famous", emoji="🚢",
    sounds=["ocean-waves.mp3"],
    highlights=[("Robben Island Prison", None),
                ("Robben Island Lighthouse", None),
                ("Limestone quarry", None)],
    blurb="A low, flat island in Table Bay, seven kilometres offshore, used as "
          "a prison for four centuries and as a political prison for thirty "
          "years — with Table Mountain filling the horizon from every point on "
          "it.",
    fact="Nelson Mandela spent eighteen of his twenty-seven years here, in a "
         "cell measuring about two and a half metres by two; the tours are led "
         "by men who were imprisoned in the same block.",
    tip="Sit on the left of the ferry going out and the right coming back — "
        "the view of the mountain from the water is the one the prisoners "
        "described."),
"blyde-river-canyon": dict(
    name="Blyde River Canyon", slug="Blyde_River_Canyon",
    country="South Africa", region="Mpumalanga", type="nature", tag="famous",
    emoji="🏞️", sounds=["waterfall.mp3"],
    highlights=[("Bourke's Luck Potholes", None),
                ("Three Rondavels", None),
                ("God's Window", None)],
    blurb="A 25 km gorge cut into the edge of the escarpment, green rather "
          "than bare — one of the largest canyons in the world and probably "
          "the largest green one, with the drop-off to the lowveld running "
          "beside it.",
    fact="At Bourke's Luck Potholes the Treur river joins the Blyde and has "
         "drilled cylindrical shafts metres deep into the rock, using nothing "
         "but trapped pebbles spinning in the current.",
    tip="The Three Rondavels viewpoint is best in the late afternoon; God's "
        "Window is famous but is in cloud more often than not."),
"pretoria": dict(
    name="Pretoria", slug="Pretoria", country="South Africa", region="Gauteng",
    type="city", tag="famous", emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Union Buildings", "Union_Buildings"),
                ("Voortrekker Monument", "Voortrekker_Monument"),
                ("Church Square", "Church_Square,_Pretoria"),
                ("Freedom Park", "Freedom_Park,_Pretoria")],
    blurb="The administrative capital, an hour north of Johannesburg and much "
          "quieter — sandstone government buildings on a terraced hill above "
          "the city, and 70,000 jacaranda trees that turn every street purple "
          "in late October.",
    fact="The Union Buildings' terraced gardens were designed as an "
         "amphitheatre facing the city, which is why Mandela's 1994 "
         "inauguration could be held on the steps in front of a crowd.",
    tip="Freedom Park and the Voortrekker Monument face each other across a "
        "valley and are deliberately linked by a road — visiting both in one "
        "afternoon is the point."),
"soweto": dict(
    name="Soweto", slug="Soweto", country="South Africa", region="Gauteng",
    type="city", tag="famous", emoji="✊", sounds=["city-hum.mp3"],
    highlights=[("Vilakazi Street", None),
                ("Hector Pieterson Memorial", None),
                ("Regina Mundi", None),
                ("Orlando Towers", None)],
    blurb="A city in its own right on Johannesburg's southwest edge, built as "
          "a township and now home to over a million people — matchbox houses, "
          "shebeens, two cooling towers painted as a mural, and the street "
          "where the 1976 uprising began.",
    fact="Vilakazi Street is the only street in the world to have housed two "
         "Nobel Peace Prize winners: Nelson Mandela and Desmond Tutu, a few "
         "doors apart.",
    tip="Regina Mundi church still has bullet holes in its ceiling and a "
        "broken marble altar from police raids during the uprising; the guides "
        "there were present."),
"addo": dict(
    name="Addo Elephant National Park", slug="Addo_Elephant_National_Park",
    country="South Africa", region="Eastern Cape", type="nature",
    tag="hidden", emoji="🐘", sounds=["wilderness.mp3"],
    highlights=[("Zuurberg", None),
                ("Sundays River", None),
                ("Hapoor Dam", None)],
    blurb="Dense thicket and rolling hills in the Eastern Cape, set aside in "
          "1931 when eleven elephants were all that remained in the region — "
          "now several hundred, in a park that has been extended to run from "
          "the semi-desert down to the sea.",
    fact="Addo is the only park in the world that can claim the Big Seven: the "
         "usual five, plus southern right whales and great white sharks in its "
         "marine section.",
    tip="Sit at Hapoor waterhole rather than driving loops — in the dry season "
        "the herds arrive in sequence and you can watch the queuing order "
        "sort itself out."),

# ============================== LESOTHO ==============================
"maseru": dict(
    name="Maseru", slug="Maseru", country="Lesotho", region="Maseru District",
    type="city", tag="hidden", emoji="🏙️", sounds=["mountain-wind.mp3"],
    highlights=[("Thaba Bosiu", "Thaba_Bosiu"),
                ("Maseru Bridge", None),
                ("Basotho Hat", None),
                ("Qeme Plateau", None)],
    blurb="A small capital on the Caledon river, right on the South African "
          "border, at 1,600 m — the lowest point in a country whose entire "
          "territory sits above that line, which is true of nowhere else on "
          "earth.",
    fact="Thaba Bosiu, half an hour east, is the flat-topped mountain "
         "stronghold that was never taken in the 19th-century wars and is the "
         "reason Lesotho exists as a country at all.",
    tip="Ride out to a village on a Basotho pony; they are bred for the "
        "mountains and are still the practical way to get between highland "
        "settlements."),
"sani-pass": dict(
    name="Sani Pass", slug="Sani_Pass", country="Lesotho",
    region="Mokhotlong District", type="mountain", tag="hidden", emoji="🚙",
    sounds=["mountain-wind.mp3"],
    highlights=[("Sani Top", None),
                ("Thabana Ntlenyana", "Thabana_Ntlenyana"),
                ("Drakensberg escarpment", None)],
    blurb="A rough switchback road climbing the Drakensberg wall from South "
          "Africa into Lesotho — 1,300 m of ascent in eight kilometres, "
          "unsurfaced hairpins, and a border post at 2,876 m where the "
          "temperature drops as you arrive.",
    fact="The pub at the top bills itself as the highest in Africa, and the "
         "pass is regularly closed by snow — in a country most people picture "
         "as hot.",
    tip="Do it in a vehicle with low range and a driver who knows it, and stop "
        "at the top of the last hairpin looking back down: the whole "
        "escarpment stacks up behind you."),
"maletsunyane": dict(
    name="Maletsunyane Falls", slug="Maletsunyane_Falls", country="Lesotho",
    region="Maseru District", type="nature", tag="hidden", emoji="💦",
    sounds=["waterfall.mp3"],
    highlights=[("Semonkong", "Semonkong"),
                ("Maletsunyane River", None)],
    blurb="A single 192 m drop off a basalt lip in the highlands near "
          "Semonkong — 'the place of smoke' — where the river falls clear of "
          "the rock into a gorge and freezes into a column of ice in the "
          "coldest winters.",
    fact="The gorge beside it carries the world's longest commercially "
         "operated single-drop abseil, at 204 m from the cliff edge to the "
         "river.",
    tip="Ride out from Semonkong on a pony rather than driving to the "
        "viewpoint — the approach along the plateau edge is most of the "
        "experience."),

# ============================== ESWATINI ==============================
"mbabane": dict(
    name="Mbabane", slug="Mbabane", country="Eswatini", region="Hhohho Region",
    type="city", tag="hidden", emoji="🏙️", sounds=["mountain-wind.mp3"],
    highlights=[("Sibebe Rock", "Sibebe"),
                ("Ezulwini Valley", "Ezulwini_Valley"),
                ("Swazi Market", None),
                ("Mantenga Falls", None)],
    blurb="A small highland capital in the Dlangeni hills at 1,150 m, cool and "
          "green, sitting at the head of a valley whose name means 'place of "
          "heaven' and which holds most of the country's craft workshops.",
    fact="Sibebe, just north of town, is a single granite dome — the second-"
         "largest monolith in the world after Uluru, and the largest exposed "
         "granite pluton anywhere.",
    tip="The Swazi Market's candle and basket stalls are the real thing rather "
        "than an import shop, and the walk up Sibebe takes about two hours "
        "from the road."),
"mlilwane": dict(
    name="Mlilwane Wildlife Sanctuary", slug="Mlilwane_Wildlife_Sanctuary",
    country="Eswatini", region="Manzini Region", type="nature", tag="hidden",
    emoji="🦓", sounds=["wilderness.mp3"],
    highlights=[("Execution Rock", None),
                ("Ezulwini Valley", "Ezulwini_Valley"),
                ("Mlilwane Hill", None)],
    blurb="Eswatini's oldest protected area, a former tin mine and farm turned "
          "back into bush in the 1960s, with no big predators — which means you "
          "can walk, cycle or ride a horse through herds of zebra, warthog and "
          "antelope without a vehicle.",
    fact="The sanctuary was created by one farmer who fenced his land and "
         "restocked it himself; it became the model for conservation across the "
         "whole country.",
    tip="Ride out at dawn — the animals ignore a horse completely, and you get "
        "closer on horseback than any game drive manages."),
}

# ---------------------------------------------------------------------------
# FILL — the records africa.json already holds, with holes in them.
#
# Eight of the original 23 places are skeletons: a name, a coordinate and
# nothing else. An empty `highlights` is the expensive hole — enrich_monuments
# spends highlights as its search terms, so a place with none has a monuments
# tab that can never fill, no matter how many times the enrichers run. Three
# more are complete except for `region`, which passport.js prints under the
# place name and which currently renders as a blank line.
#
# `fill()` only writes fields that are empty, so listing a field here that the
# record already has is a no-op rather than an overwrite. Cairo keeps its seven
# curated highlights for exactly that reason.
# ---------------------------------------------------------------------------
FILL = {

# --- Morocco ---------------------------------------------------------------
"marrakesh": dict(
    region="Marrakesh-Safi",
    highlights=[("Jemaa el-Fnaa", "Jemaa_el-Fnaa"),
                ("Koutoubia Mosque", "Koutoubia_Mosque"),
                ("Bahia Palace", "Bahia_Palace"),
                ("Saadian Tombs", "Saadian_Tombs"),
                ("Ben Youssef Madrasa", "Ben_Youssef_Madrasa"),
                ("El Badi Palace", "El_Badi_Palace"),
                ("Majorelle Garden", "Majorelle_Garden")],
    blurb="The red city under the Atlas, founded in 1070 and walled in rammed "
          "earth the colour of the plain it stands on. Inside the walls is a "
          "medina that has kept its shape for nine centuries; outside them, "
          "snow sits on the mountains for half the year.",
    fact="Jemaa el-Fnaa empties and refills twice a day — orange carts and "
         "snake charmers by afternoon, then a hundred food stalls wheeled in "
         "at dusk onto ground that was bare an hour earlier.",
    tip="The rooftop cafés on the square's south side charge for a mint tea "
        "and give you the whole thing from above, which is the only angle "
        "where the scale of it reads."),

"fez": dict(
    region="Fes-Meknes",
    highlights=[("Al-Qarawiyyin", "University_of_al-Qarawiyyin"),
                ("Bou Inania Madrasa", "Bou_Inania_Madrasa"),
                ("Bab Bou Jeloud", "Bab_Bou_Jeloud"),
                ("Fes el Bali", "Fes_el_Bali"),
                ("Al-Attarine Madrasa", "Al-Attarine_Madrasa"),
                ("Chouara Tannery", None),
                ("Merenid Tombs", None)],
    blurb="Morocco's oldest imperial city and the one that never modernised "
          "its centre. Fes el Bali is the largest car-free urban area in the "
          "world — nine thousand lanes too narrow for anything wider than a "
          "donkey, still carrying the whole traffic of a working city.",
    fact="Al-Qarawiyyin was founded in 859 by Fatima al-Fihri and has taught "
         "continuously ever since, which makes it the oldest degree-granting "
         "university still operating anywhere.",
    tip="The tanneries are viewed from the leather shops' terraces above "
        "them; take the sprig of mint they hand you at the door and hold it "
        "under your nose the whole time."),

# --- Egypt -----------------------------------------------------------------
"giza-pyramids": dict(
    region="Giza Governorate",
    highlights=[("Great Pyramid of Giza", "Great_Pyramid_of_Giza"),
                ("Great Sphinx of Giza", "Great_Sphinx_of_Giza"),
                ("Pyramid of Khafre", "Pyramid_of_Khafre"),
                ("Pyramid of Menkaure", "Pyramid_of_Menkaure"),
                ("Grand Egyptian Museum", "Grand_Egyptian_Museum"),
                ("Valley Temple of Khafre", None)],
    blurb="Three pyramids and a lion-bodied sentinel on the desert edge, "
          "built in about eighty years around 2560 BC and left standing ever "
          "since. The suburbs of Giza now reach the fence, so the plateau is "
          "a step off a city street rather than a journey.",
    fact="The Great Pyramid held the record for the tallest structure on "
         "Earth for roughly 3,800 years — longer than the span between its "
         "losing the title and today.",
    tip="Walk out to the panorama point on the desert road southwest of the "
        "complex; it is the one spot where all three pyramids line up and no "
        "modern building is in the frame."),

"cairo": dict(
    region="Cairo Governorate",
    blurb="A thousand-year capital stacked on top of a two-thousand-year one, "
          "split by the Nile and pressed against the desert. Fatimid minarets, "
          "Coptic churches, a Mamluk citadel and twenty million people share a "
          "city whose Arabic name simply means 'the victorious'.",
    fact="Cairo has more standing Islamic monuments than any other city — "
         "over six hundred registered ones, most of them in the square "
         "kilometre around al-Muizz Street.",
    tip="Climb the minaret of Bab Zuweila at the medieval south gate. It is a "
        "tight spiral and almost nobody does it, and the top puts you level "
        "with the roofs of Islamic Cairo."),

"luxor": dict(
    region="Luxor Governorate",
    highlights=[("Karnak", "Karnak"),
                ("Luxor Temple", "Luxor_Temple"),
                ("Valley of the Kings", "Valley_of_the_Kings"),
                ("Mortuary Temple of Hatshepsut",
                 "Mortuary_Temple_of_Hatshepsut"),
                ("Colossi of Memnon", "Colossi_of_Memnon"),
                ("Valley of the Queens", "Valley_of_the_Queens"),
                ("Luxor Museum", "Luxor_Museum")],
    blurb="Ancient Thebes, with the living town on the east bank and the dead "
          "on the west, exactly as the Egyptians arranged it. The result is a "
          "working Nile city that happens to have the densest concentration "
          "of monumental ruins on the planet inside its limits.",
    fact="Karnak's hypostyle hall holds 134 columns over five acres; the tall "
         "central ones are 21 m high and wide enough at the top for fifty "
         "people to stand on a single capital.",
    tip="Cross on the local ferry rather than a tour boat and hire a bicycle "
        "on the west bank — the road between the Colossi and the valleys runs "
        "flat through sugarcane and takes an easy morning."),

"aswan": dict(
    region="Aswan Governorate",
    highlights=[("Philae", "Philae"),
                ("Aswan Dam", "Aswan_Dam"),
                ("Elephantine", "Elephantine"),
                ("Unfinished Obelisk", "Unfinished_obelisk"),
                ("Nubian Museum", "Nubian_Museum"),
                ("Kitchener's Island", None)],
    blurb="Egypt's southern frontier town, where the Nile breaks into "
          "granite islands and the desert comes down to the water on both "
          "sides. It is the quietest of the Nile cities, and the one where "
          "Nubian rather than Cairene culture sets the tone.",
    fact="The Unfinished Obelisk still lies in its quarry — it would have "
         "been 42 m and nearly 1,200 tonnes, the largest ever cut, until a "
         "crack ran through it and the crew walked away.",
    tip="Take a felucca out at sunset to the west bank dunes below the Tombs "
        "of the Nobles. There is no engine noise, and the light on the "
        "granite is the reason people stay a week here."),

# --- Senegal ---------------------------------------------------------------
"dakar": dict(region="Dakar Region"),

"goree-island": dict(
    region="Dakar Region",
    highlights=[("House of Slaves", "House_of_Slaves"),
                ("Castel of Gorée", None),
                ("Fort d'Estrées", None),
                ("IFAN Historical Museum", None),
                ("Saint-Charles Borromée Church", None)],
    blurb="A 900-metre island of ochre houses and bougainvillaea twenty "
          "minutes off Dakar, held in turn by the Portuguese, Dutch, English "
          "and French between 1444 and 1848. No cars, no tarmac, and a "
          "silence that is the whole point of going.",
    fact="Gorée was UNESCO's first West African World Heritage Site, listed "
         "in 1978 as a memory of the Atlantic slave trade rather than for "
         "the architecture the listing describes.",
    tip="Stay past the last afternoon ferry crowd. The island empties, the "
        "residents come back out onto the steps, and it becomes a village "
        "again rather than a monument."),

# --- Ethiopia --------------------------------------------------------------
"addis-ababa": dict(region="Addis Ababa"),

"lalibela": dict(
    region="Amhara Region",
    highlights=[("Church of Saint George", "Church_of_Saint_George,_Lalibela"),
                ("Biete Medhane Alem", None),
                ("Biete Maryam", None),
                ("Asheton Maryam Monastery", None),
                ("Yemrehanna Krestos", None)],
    blurb="Eleven churches cut downward into solid volcanic rock in the "
          "12th century — not built and not caves, but carved free of the "
          "hillside from the roof down, with trenches, tunnels and drainage "
          "channels cut around them. All eleven are still in daily use.",
    fact="Bete Giyorgis is a single cross-shaped block 15 m deep, released "
         "from the bedrock with hand tools and joined to the surface only by "
         "a sloping tunnel you have to stoop through.",
    tip="Come for the 5 a.m. service on any morning, not just a feast day. "
        "The trenches fill with white-shawled worshippers and candlelight "
        "before the sun reaches the roofs."),

"gondar": dict(
    region="Amhara Region",
    highlights=[("Fasil Ghebbi", "Fasil_Ghebbi"),
                ("Debre Berhan Selassie", None),
                ("Fasilides' Bath", None),
                ("Kuskuam", None),
                ("Gondar Castle", None)],
    blurb="Ethiopia's imperial capital from 1636, and a place that looks "
          "like nowhere else on the continent: a walled compound of stone "
          "castles with round towers and battlements, built by emperors who "
          "had never seen Europe.",
    fact="Debre Berhan Selassie's ceiling is covered in eighty winged "
         "cherub faces, all with the same wide eyes, painted in the 17th "
         "century and never repainted since.",
    tip="Fasilides' Bath is a dry stone pool most of the year, its walls "
        "grown through by fig roots — worth the walk out of town even when "
        "there is no water in it."),

# --- South Africa ----------------------------------------------------------
"johannesburg": dict(region="Gauteng"),
}


def flag(code):
    """ISO alpha-2 -> flag emoji, the same derivation build_countries.py uses."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def country_slug(name):
    return COUNTRY_SLUG.get(name, name.replace(" ", "_"))


def slugs_wanted():
    """Every slug this batch needs an answer about, place-level and highlight."""
    out = []
    for spec in NEW.values():
        out.append(spec["slug"])
        out.append(country_slug(spec["country"]))
        out += [s for _, s in spec["highlights"] if s]
    for spec in FILL.values():
        out += [s for _, s in spec.get("highlights", []) if s]
    return out


class Notes:
    """Collects one line per verdict so the dry run reads like verify_wiki."""

    def __init__(self):
        self.rows = []
        self.unresolved = 0

    def add(self, kind, where, what, why=""):
        self.rows.append((kind, where, what, why))
        if kind == "UNRESOLVED":
            self.unresolved += 1

    def print(self):
        order = {"UNRESOLVED": 0, "NOCOORD": 1, "OUTSIDE": 2, "COUNTRY": 3,
                 "MISSING": 4, "SELF": 5, "FAR": 6, "REDIRECT": 7, "FIXENC": 8}
        for kind, where, what, why in sorted(
                self.rows, key=lambda r: (order.get(r[0], 9), r[1], r[2])):
            print(f"{kind:<10} {where:<26} {what:<44} {why}")
        counts = {}
        for kind, *_ in self.rows:
            counts[kind] = counts.get(kind, 0) + 1
        if counts:
            print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


def link(slug, got, notes, where, own=None):
    """The canonical title to store for `slug`, or None to keep the chip text-only.

    A highlight that resolves to the record's own article is worse than a dead
    link — it promises a second place and delivers the one you are standing in.
    """
    e = got.get(slug) or {}
    if "title" not in e and not e.get("missing"):
        notes.add("UNRESOLVED", where, slug, "no answer from the API — rerun")
        return None
    if e.get("missing"):
        notes.add("MISSING", where, slug, "no article — kept as a text chip")
        return None
    title = e["title"]
    if own and title == own:
        notes.add("SELF", where, slug, "resolves to the place itself — unlinked")
        return None
    if e.get("redirect"):
        notes.add("REDIRECT", where, slug, f"-> {title}")
    return title


def highlights(spec, got, notes, where, own):
    out = []
    for name, slug in spec.get("highlights", []):
        h = {"name": name}
        t = link(slug, got, notes, where, own) if slug else None
        if t:
            h["wikipedia_slug"] = t
        out.append(h)
    return out


def far_check(loc, hl, got, notes, where):
    """Every highlight with a coordinate, measured against the record itself."""
    if loc.get("type") in AREA_TYPES:
        return
    here = loc.get("coordinates") or {}
    if here.get("lat") is None:
        return
    for h in hl:
        s = h.get("wikipedia_slug")
        e = got.get(s) or {}
        if e.get("lat") is None:
            continue
        d = haversine((here["lat"], here["lng"]), (e["lat"], e["lng"]))
        if d > FAR_KM:
            notes.add("FAR", where, f"{h['name']} [{s}]",
                      f"{d:,.0f} km from {loc['name']}")


def country_check(pid, spec, e, got, notes):
    """P17 against the country we claim. A WARNING — see the module docstring."""
    want = got.get(country_slug(spec["country"])) or {}
    mine, theirs = e.get("country_qid"), want.get("qid")
    if not theirs:
        notes.add("COUNTRY", pid, spec["country"],
                  "no QID for the country article — check by hand")
        return
    if not mine:
        notes.add("COUNTRY", pid, e.get("title", spec["slug"]),
                  "article has no P17 — check by hand")
        return
    if mine != theirs:
        notes.add("COUNTRY", pid, e.get("title", spec["slug"]),
                  f"P17 is {mine}, {spec['country']} is {theirs} — check by hand")


def make(pid, spec, got, notes):
    """A complete record from a NEW entry, or None if it cannot be trusted."""
    title = link(spec["slug"], got, notes, pid)
    if not title:
        notes.add("NOCOORD", pid, spec["slug"], "no article — place not added")
        return None
    e = got[spec["slug"]]
    lat, lng = e.get("lat"), e.get("lng")
    if lat is None:
        notes.add("NOCOORD", pid, title, "no P625 — place not added")
        return None
    if not (AFRICA_BOX[0] <= lat <= AFRICA_BOX[1]
            and AFRICA_BOX[2] <= lng <= AFRICA_BOX[3]):
        notes.add("OUTSIDE", pid, title,
                  f"P625 is {lat:.3f},{lng:.3f} — not Africa")
        return None
    country_check(pid, spec, e, got, notes)

    code = COUNTRY_CODE[spec["country"]]
    loc = {
        "id": pid,
        "name": spec["name"],
        "country": spec["country"],
        "country_code": code,
        "country_flag": flag(code),
        "continent": "Africa",
        "region": spec["region"],
        "type": spec["type"],
        "tag": spec["tag"],
        "emoji": spec["emoji"],
        "coordinates": {"lat": lat, "lng": lng},
        "street_view": {"lat": lat, "lng": lng,
                        "heading": 0, "pitch": 0, "fov": 90},
        "wikipedia_slug": title,
        "sounds": list(spec["sounds"]),
        "highlights": highlights(spec, got, notes, pid, title),
        "blurb": spec["blurb"],
        "fun_fact": spec["fact"],
        "hidden_gem_tip": spec["tip"],
    }
    # `search_name` sharpens the media/monument query when the bare name has a
    # namesake somewhere else. No downstream title guard can catch a namesake,
    # so it has to be said here, at the point where we know.
    if spec.get("search_name"):
        loc["search_name"] = spec["search_name"]
    far_check(loc, loc["highlights"], got, notes, pid)
    return loc


def fill(loc, spec, got, notes):
    """Fill only what is empty. Returns the field names actually written."""
    wrote = []
    if spec.get("region") and not loc.get("region"):
        loc["region"] = spec["region"]
        wrote.append("region")
    if spec.get("highlights") and not loc.get("highlights"):
        loc["highlights"] = highlights(spec, got, notes, loc["id"],
                                       loc.get("wikipedia_slug"))
        far_check(loc, loc["highlights"], got, notes, loc["id"])
        wrote.append("highlights")
    for key, src in (("blurb", "blurb"), ("fun_fact", "fact"),
                     ("hidden_gem_tip", "tip"), ("search_name", "search_name")):
        if spec.get(src) and not loc.get(key):
            loc[key] = spec[src]
            wrote.append(key)
    return wrote


def fix_encoding(locs, notes):
    """`Maracan%C3%A3_Stadium` is a URL, not a title.

    MediaWiki decodes a percent-encoded slug and answers anyway, so an audit
    never sees it — but every consumer that concatenates it into a URL is one
    encode away from a 404. Decode it back to the title it always was.
    """
    n = 0
    for loc in locs:
        for holder in [loc] + list(loc.get("highlights") or []):
            s = holder.get("wikipedia_slug")
            if s and "%" in s:
                dec = urllib.parse.unquote(s)
                if dec != s:
                    holder["wikipedia_slug"] = dec
                    notes.add("FIXENC", loc["id"], s, f"-> {dec}")
                    n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore the slug cache and ask Wikipedia again")
    args = ap.parse_args()

    doc = json.loads(TARGET.read_text(encoding="utf-8"))
    locs = doc["locations"]
    by_id = {l["id"]: l for l in locs}

    unknown = [p for p in FILL if p not in by_id]
    if unknown:
        sys.exit(f"FILL names places that are not in the file: {unknown}")
    clash = [p for p in NEW if p in by_id]
    if clash:
        sys.exit(f"NEW would collide with existing ids: {clash}")
    nocode = sorted({s["country"] for s in NEW.values()} - set(COUNTRY_CODE))
    if nocode:
        sys.exit(f"NEW names countries with no ISO code here: {nocode}")

    want = slugs_wanted()
    print(f"resolving {len(set(want))} slug(s) against Wikipedia/Wikidata …")
    got = Resolver(refresh=args.refresh).resolve(want)

    notes = Notes()
    added, filled = [], []
    for pid, spec in NEW.items():
        loc = make(pid, spec, got, notes)
        if loc:
            added.append(loc)
    for pid, spec in FILL.items():
        wrote = fill(by_id[pid], spec, got, notes)
        if wrote:
            filled.append((pid, wrote))
    enc = fix_encoding(locs + added, notes)

    notes.print()
    print(f"\n{len(added)}/{len(NEW)} new place(s), {len(filled)} filled, "
          f"{enc} slug(s) decoded")
    for pid, wrote in filled:
        print(f"  fill {pid:<26} {', '.join(wrote)}")
    skipped = [p for p in NEW if p not in {l['id'] for l in added}]
    if skipped:
        print(f"  ⚠ not added: {skipped}")
    have = {l["country"] for l in locs + added}
    print(f"  countries in the file after this run: {len(have)}")

    if notes.unresolved:
        # A throttled request is not a verdict. Refuse to write a half-checked
        # file rather than silently drop links the API never answered about.
        sys.exit(f"\n{notes.unresolved} slug(s) unresolved — rerun before --apply")
    if not args.apply:
        print("\ndry run — pass --apply to write")
        return

    doc["locations"] = locs + added
    TARGET.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"✓ wrote {len(doc['locations'])} locations -> "
          f"{TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
