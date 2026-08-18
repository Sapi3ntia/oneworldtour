#!/usr/bin/env python3
"""
build_oceania.py — the Oceania batch (2026-08).

WHAT WAS WRONG
    Oceania was the thinnest region in the atlas by a wider margin than Africa
    ever was: **11 places across 2 of ~20 countries**, in a 27 KB file. Six
    Australian places for a continent-sized country, five New Zealand ones,
    and *nothing at all* for the whole of the Pacific — no Papua New Guinea,
    no Fiji, no Vanuatu, no Samoa, no Tonga, no French Polynesia, no
    Micronesia beyond the single Nan Madol record parked in `ancient.json`.

    A third of the planet's surface was Sydney, Melbourne, Uluru, the Reef,
    Cairns, Perth, Auckland, Queenstown, Wellington, Rotorua and Milford
    Sound. The country registry knew about exactly three Oceanian countries
    (AU, NZ, FM), so even the browse axis had nowhere to go.

WHAT THIS DOES
    Adds the new places and fills the one skeleton in a single pass, the same
    shape as `build_africa.py` / `build_latinamerica.py`. Editorial choice is
    ours — which island, which landform, what is worth saying — but every
    **coordinate comes from Wikidata P625** and every **slug is resolved live**
    and stored as the article's canonical title, per README "Filling a region
    out". Nothing here is recalled from memory except the prose.

    Re-runnable and additive: a place that already exists keeps every field it
    already has (and always keeps `walk`/`webcam`/`window`/`monuments` — those
    belong to the scene pipeline, not to us). Only empty fields get filled.

THE ANTIMERIDIAN, AND WHY THE AFRICA BOX SHAPE DOES NOT FIT
    Every previous batch could refuse a bad slug with one rectangle, because
    every previous region fits inside one. Oceania does not: it runs from the
    Cocos Islands at 96.8°E east across the 180th meridian to Pitcairn at
    130.1°**W**. A single `lng_min <= lng <= lng_max` test either spans the
    entire globe (and refuses nothing) or splits the region in half (and
    refuses Tahiti). So the box here is **two longitude ranges** joined by
    `or`, and `in_box()` is the only place that knows it.

    The box is still only a coarse net. Widened west far enough to hold the
    Cocos Islands, it also holds Java and Sumatra; widened north far enough
    to hold Saipan, it holds the Philippine Sea. The **hard** namesake guard
    here is the same one Africa needed — **Wikidata P17 (country)**, resolved
    live for the country articles themselves so no QID is typed from memory.

    P17 is a WARNING, not a refusal, and Oceania is the region where that
    matters most. Nouméa's P17 is France; Papeete's is France; Hagåtña's is
    the United States; Adamstown's is the United Kingdom. Every one of those
    is a correct article with a surprising P17, because the browse axis here
    is the **territory** (its own ISO code, its own flag) and Wikidata's is
    the sovereign state. Refusing them would lose the entire Pacific.

    A mismatch we *expect* is declared in EXPECT_P17 and printed as a quiet
    note rather than a warning, so the COUNTRY lines that remain are the ones
    a human should actually read.

Run:  python3 tools/build_oceania.py            # report only
      python3 tools/build_oceania.py --apply
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wiki import Resolver, haversine

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "data" / "oceania.json"

# How far a record may sit from its own article's P625 before we want a human
# to look. An `area` type legitimately sits far from its centroid point, and
# Oceania is full of them — an atoll's article points at the lagoon's middle,
# an archipelago's at the sea between its islands.
FAR_KM = 60.0
AREA_TYPES = {"nature", "desert", "island", "mountain", "coastal"}

# These strings are not free-form. `build_countries.py` counts a country's
# places by matching `loc["country"]` against the registry's *canonical name*,
# so a spelling that drifts here leaves the country showing zero places while
# quietly holding a dozen. Every name below is copied from COUNTRIES in
# build_countries.py, spelling and all.
#
# Territories get their own row rather than being filed under the sovereign
# state, and that is deliberate: the browse axis is Continent → Country →
# Place, so filing Bora Bora under "France" would hide it inside Europe. Each
# has a real ISO-3166-1 alpha-2 code, so the flag still derives rather than
# being hand-typed.
COUNTRY_CODE = {
    "Australia": "AU", "New Zealand": "NZ", "Papua New Guinea": "PG",
    "Fiji": "FJ", "Solomon Islands": "SB", "Vanuatu": "VU",
    "New Caledonia": "NC", "Samoa": "WS", "American Samoa": "AS",
    "Tonga": "TO", "Cook Islands": "CK", "French Polynesia": "PF",
    "Niue": "NU", "Kiribati": "KI", "Tuvalu": "TV", "Nauru": "NR",
    "Palau": "PW", "Marshall Islands": "MH", "Micronesia": "FM",
    "Guam": "GU", "Northern Mariana Islands": "MP",
    "Norfolk Island": "NF", "Pitcairn Islands": "PN",
}

# The article title to resolve for each country, where it is not the canonical
# name with underscores. Resolving these gives us the expected P17 QID without
# a single QID typed from memory.
COUNTRY_SLUG = {
    "Micronesia": "Federated_States_of_Micronesia",
    "Pitcairn Islands": "Pitcairn_Islands",
    "Norfolk Island": "Norfolk_Island",
}

# Territories whose P17 legitimately answers the sovereign state rather than
# the territory. Declared so the report stays readable — see the docstring.
# The value is the country article whose QID we accept *instead*.
EXPECT_P17 = {
    "New Caledonia": "France",
    "French Polynesia": "France",
    "Guam": "United_States",
    "Northern Mariana Islands": "United_States",
    "American Samoa": "United_States",
    "Norfolk Island": "Australia",
    "Pitcairn Islands": "United_Kingdom",
    "Cook Islands": "New_Zealand",
    "Niue": "New_Zealand",
}

# Two ranges, joined by `or` in in_box(). West edge holds the Cocos (Keeling)
# Islands at 96.8°E; east edge holds Pitcairn at 130.1°W. North edge holds the
# Northern Marianas (~20.5°N); south edge holds Macquarie Island (~54.6°S).
# See the module docstring: this is a coarse net, not the namesake guard.
OCEANIA_LAT = (-55.0, 21.0)
OCEANIA_LNG = ((96.5, 180.0), (-180.0, -124.0))


# ---------------------------------------------------------------------------
# THE CURATED CONTENT.
#
# highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, a
# dish, a dance, an era or a festival. Oceania makes that rule easy to break:
# "Māori", "Aboriginal", "Dreaming", "Haka", "Kava", "Lapita", "Huli" all read
# like places and are all peoples, practices or eras. Each highlight below is
# a thing that stands somewhere, so a video of it can exist.
# (See enrich_monuments.NOT_A_MONUMENT.)
#
# A `None` slug is deliberate: the UI renders highlights as text chips, so a
# name with no link costs nothing and a dead link is rot.
#
# `search_name` is set wherever the bare name has a namesake somewhere else.
# Oceania is the worst region in the atlas for this, because British settlers
# reused British names wholesale: Newcastle, Perth, Launceston, Grampians,
# Nelson, Christchurch, Richmond, Kingston. No downstream title guard can
# catch a namesake, so it is said here, at the only point where we know.
# ---------------------------------------------------------------------------
NEW = {
# ========================= AUSTRALIA — NSW & ACT =========================
"canberra": dict(
    name="Canberra", slug="Canberra", country="Australia",
    region="Australian Capital Territory", type="city", tag="famous",
    emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Parliament House", "Parliament_House,_Canberra"),
                ("Australian War Memorial", "Australian_War_Memorial"),
                ("Lake Burley Griffin", "Lake_Burley_Griffin"),
                ("National Gallery of Australia", "National_Gallery_of_Australia"),
                ("Australian National Botanic Gardens",
                 "Australian_National_Botanic_Gardens"),
                ("Mount Ainslie", "Mount_Ainslie")],
    blurb="A capital designed from nothing in 1913 by two Chicago architects "
          "who won a competition, laid out as circles and radiating avenues on "
          "sheep country halfway between the two cities that could not agree "
          "which of them should have it. Everything is on an axis, and the "
          "axis points at a hill.",
    fact="Walter Burley Griffin and Marion Mahony Griffin's winning plan aimed "
         "the land axis from Mount Ainslie through the parliamentary triangle "
         "to Mount Bimberi — so the whole city is aimed at a mountain 60 km "
         "away that most residents have never climbed.",
    tip="Walk up Mount Ainslie at dusk rather than driving. From the summit "
        "the entire designed geometry snaps into place at once, which is the "
        "only way Canberra ever makes sense."),

"newcastle-nsw": dict(
    name="Newcastle", slug="Newcastle,_New_South_Wales", country="Australia",
    region="New South Wales", type="coastal", tag="hidden", emoji="🌊",
    sounds=["ocean-waves.mp3"], search_name="Newcastle NSW Australia",
    highlights=[("Nobbys Head", "Nobbys_Head"),
                ("Newcastle Ocean Baths", "Newcastle_Ocean_Baths"),
                ("Fort Scratchley", "Fort_Scratchley"),
                ("Merewether Beach", "Merewether,_New_South_Wales"),
                ("Christ Church Cathedral", "Christ_Church_Cathedral,_Newcastle")],
    blurb="The world's largest coal export port with a surf beach in the "
          "middle of it. Newcastle spent a century as a steel town, lost the "
          "steelworks in 1999, and turned the working harbour edge into a "
          "coastline of ocean baths and headland walks.",
    fact="Fort Scratchley fired on a Japanese submarine shelling the city in "
         "June 1942 — the only Australian coastal battery ever to return fire "
         "at an enemy vessel.",
    tip="Do the Bathers Way from Nobbys to Merewether at first light. It is "
        "6 km of clifftop with three sets of ocean baths on it, and the "
        "swimmers are in the water before the sun clears the horizon."),

"wollongong": dict(
    name="Wollongong", slug="Wollongong", country="Australia",
    region="New South Wales", type="coastal", tag="hidden", emoji="🪂",
    sounds=["ocean-waves.mp3"],
    highlights=[("Sea Cliff Bridge", "Sea_Cliff_Bridge"),
                ("Nan Tien Temple", "Nan_Tien_Temple"),
                ("Wollongong Head Lighthouse", "Wollongong_Head_Lighthouse"),
                ("Mount Keira", "Mount_Keira"),
                ("Bald Hill", "Bald_Hill_(Australia)")],
    blurb="A city pinned between an escarpment and the sea on a strip so "
          "narrow that the road had to be built out over the water. The "
          "Illawarra ranges rise 500 m directly behind the suburbs, and every "
          "lookout on them faces a beach.",
    fact="The Sea Cliff Bridge exists because the old cliff road kept being "
         "buried by rockfalls; rather than cut further into the slope, the "
         "engineers curved 665 m of roadway out over the ocean and left the "
         "cliff alone.",
    tip="Bald Hill above Stanwell Park is where hang gliders launch all "
        "afternoon. Stand at the fence for twenty minutes and you will see "
        "the whole coastline the bridge crosses, from above it."),

"byron-bay": dict(
    name="Byron Bay", slug="Byron_Bay,_New_South_Wales", country="Australia",
    region="New South Wales", type="coastal", tag="famous", emoji="🏄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cape Byron Lighthouse", "Cape_Byron_Light"),
                ("Cape Byron", "Cape_Byron"),
                ("Wategos Beach", None),
                ("Main Beach", None),
                ("Mount Warning", "Mount_Warning")],
    blurb="The easternmost point of mainland Australia, a whaling station "
          "until 1962 and a surf town ever since. The lighthouse stands on a "
          "headland that the humpback migration rounds twice a year, close "
          "enough in to watch from the path.",
    fact="Cape Byron is the first place on the Australian mainland to see the "
         "sunrise, and the lighthouse on it is the country's most powerful — "
         "its beam is rated at over two million candela.",
    tip="Do the cape circuit anticlockwise before six. You reach the "
        "easternmost marker with the sun coming straight out of the sea, and "
        "the town is still asleep behind you."),

"blue-mountains": dict(
    name="Blue Mountains", slug="Blue_Mountains_(New_South_Wales)",
    country="Australia", region="New South Wales", type="mountain",
    tag="famous", emoji="🏞️", sounds=["mountain-wind.mp3"],
    search_name="Blue Mountains Australia",
    highlights=[("Three Sisters", "Three_Sisters_(Australia)"),
                ("Katoomba", "Katoomba,_New_South_Wales"),
                ("Jenolan Caves", "Jenolan_Caves"),
                ("Wentworth Falls", "Wentworth_Falls,_New_South_Wales"),
                ("Grand Canyon Track", None),
                ("Mount Solitary", "Mount_Solitary")],
    blurb="Not mountains so much as a dissected sandstone plateau, cut by "
          "valleys 700 m deep and filled edge to edge with eucalyptus. The "
          "haze that names them is real — oil from the leaves scatters light "
          "blue across the whole basin on a still day.",
    fact="The Jenolan Caves have been dated at around 340 million years, "
         "which makes them the oldest discovered open cave system on Earth — "
         "older than the mountains they sit under.",
    tip="Take the Grand Canyon track down from Evans Lookout instead of "
        "queuing at Echo Point. It drops into a fern-walled slot canyon with "
        "waterfalls over the path and almost nobody in it."),

"jervis-bay": dict(
    name="Jervis Bay", slug="Jervis_Bay", country="Australia",
    region="New South Wales", type="coastal", tag="hidden", emoji="🐬",
    sounds=["ocean-waves.mp3"],
    highlights=[("Hyams Beach", "Hyams_Beach,_New_South_Wales"),
                ("Booderee National Park", "Booderee_National_Park"),
                ("Point Perpendicular Lighthouse", "Point_Perpendicular_Light"),
                ("Cape St George Lighthouse", "Cape_St_George_Lighthouse"),
                ("Huskisson", "Huskisson,_New_South_Wales")],
    blurb="A near-enclosed bay of white sand and clear water three hours "
          "south of Sydney, with a bottlenose dolphin population that lives "
          "in it year-round. The southern shore is national park held under "
          "an Aboriginal land grant and leased back.",
    fact="Hyams Beach sand is quartz ground so fine and so free of iron that "
         "it squeaks underfoot, and the beach spent years in the Guinness "
         "book as the whitest in the world.",
    tip="Walk out to the ruined Cape St George lighthouse. It was built on "
        "the wrong headland in 1860, wrecked ships instead of saving them, "
        "and was demolished by naval gunnery practice — the stumps are still "
        "there on the cliff."),

"hunter-valley": dict(
    name="Hunter Valley", slug="Hunter_Region", country="Australia",
    region="New South Wales", type="village", tag="hidden", emoji="🍇",
    sounds=["wilderness.mp3"],
    highlights=[("Pokolbin", "Pokolbin,_New_South_Wales"),
                ("Cessnock", "Cessnock,_New_South_Wales"),
                ("Maitland", "Maitland,_New_South_Wales"),
                ("Hunter Valley Gardens", "Hunter_Valley_Gardens"),
                ("Broke", "Broke,_New_South_Wales")],
    blurb="Australia's oldest wine region, planted in the 1820s on a floor of "
          "old volcanic soil under the Brokenback Range. It is too humid and "
          "too warm on paper to make great wine, and makes a Semillon that "
          "nowhere else can.",
    fact="Hunter Semillon is picked early and low in alcohol, tastes of "
         "almost nothing young, and after ten years in bottle turns to "
         "toast and honey without ever having seen an oak barrel.",
    tip="Go on a weekday in winter. The cellar doors are empty, the "
        "Brokenback ridge holds mist until mid-morning, and the tasting is a "
        "conversation instead of a queue."),

"broken-hill": dict(
    name="Broken Hill", slug="Broken_Hill", country="Australia",
    region="New South Wales", type="desert", tag="hidden", emoji="⛏️",
    sounds=["desert-wind.mp3"],
    highlights=[("Line of Lode Miners Memorial", None),
                ("Silverton", "Silverton,_New_South_Wales"),
                ("Living Desert Sculptures", None),
                ("Mundi Mundi Plain", None),
                ("Palace Hotel", "Palace_Hotel,_Broken_Hill")],
    blurb="A silver-lead-zinc town 1,100 km inland, built on one of the "
          "richest ore bodies ever found and still mining it after 140 years. "
          "The streets are named for minerals, the light is flat and enormous, "
          "and the desert starts at the last house.",
    fact="Broken Hill is the only Australian city listed on the National "
         "Heritage List in its entirety, and it keeps South Australian time "
         "rather than New South Wales time because Adelaide is closer than "
         "Sydney.",
    tip="Drive the 25 km out to Silverton and keep going to the Mundi Mundi "
        "lookout at sunset. The plain below it is flat enough that you can "
        "see the curve of the earth on the horizon."),

"mungo-national-park": dict(
    name="Mungo National Park", slug="Mungo_National_Park",
    country="Australia", region="New South Wales", type="desert",
    tag="hidden", emoji="🏜️", sounds=["desert-wind.mp3"],
    highlights=[("Walls of China", None),
                ("Lake Mungo", "Lake_Mungo"),
                ("Willandra Lakes Region", "Willandra_Lakes_Region"),
                ("Mungo Woolshed", None)],
    blurb="A dry lake bed in the far west of New South Wales whose eastern "
          "shore has eroded into a 33 km crescent of white and orange clay "
          "dunes. The lake last held water about 14,000 years ago; everything "
          "the wind uncovers is older than that.",
    fact="Mungo Lady and Mungo Man were found eroding out of these dunes and "
         "date to roughly 42,000 years — the oldest known human cremation "
         "anywhere, and evidence of ritual burial on this lake shore before "
         "Europe had cave paintings.",
    tip="The dunes are closed to unaccompanied visitors, and that is the "
        "point: go with an Aboriginal Discovery ranger, who will read the "
        "eroding layers to you rather than letting you walk over them."),

"kosciuszko-national-park": dict(
    name="Kosciuszko National Park", slug="Kosciuszko_National_Park",
    country="Australia", region="New South Wales", type="mountain",
    tag="hidden", emoji="🏔️", sounds=["mountain-wind.mp3"],
    highlights=[("Mount Kosciuszko", "Mount_Kosciuszko"),
                ("Thredbo", "Thredbo,_New_South_Wales"),
                ("Charlotte Pass", "Charlotte_Pass,_New_South_Wales"),
                ("Blue Lake", "Blue_Lake_(New_South_Wales)"),
                ("Yarrangobilly Caves", "Yarrangobilly_Caves"),
                ("Snowy River", "Snowy_River")],
    blurb="The roof of Australia, which is 2,228 m — low enough that the "
          "summit is a walk on a raised steel path, high enough that the tops "
          "hold snow for four months and grow alpine herbfields found nowhere "
          "else on the continent.",
    fact="Australia has five glacial lakes and all five are within a few "
         "kilometres of each other here, gouged during the last ice age by "
         "the only glaciers the mainland ever had.",
    tip="Go up in January, not July. The snowgums are bare-limbed white, the "
        "herbfields flower all at once, and Blue Lake — a 28 m deep cirque "
        "lake — is a 5 km detour almost nobody on the summit walk takes."),

"lord-howe-island": dict(
    name="Lord Howe Island", slug="Lord_Howe_Island", country="Australia",
    region="New South Wales", type="island", tag="hidden", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Mount Gower", "Mount_Gower"),
                ("Ball's Pyramid", "Ball's_Pyramid"),
                ("Mount Lidgbird", "Mount_Lidgbird"),
                ("Lord Howe Island Lagoon", None),
                ("Malabar Hill", None)],
    blurb="A crescent of eroded volcano 600 km off the New South Wales coast, "
          "11 km long, with two forested peaks at its southern end and the "
          "world's southernmost coral reef in its lagoon. Four hundred people "
          "live there and only 400 visitors are allowed at a time.",
    fact="Ball's Pyramid, the 562 m sea stack 20 km away, is the tallest "
         "volcanic stack on Earth — and a single bush on it held the last "
         "24 Lord Howe Island stick insects, a species declared extinct for "
         "80 years until they were found again in 2001.",
    tip="Climb Mount Gower with the licensed guide — it is a full day on "
        "ropes and roots through cloud forest, and the summit mist is where "
        "the providence petrels come down to your feet if you call them."),

# ========================= AUSTRALIA — VICTORIA =========================
"great-ocean-road": dict(
    name="Great Ocean Road", slug="Great_Ocean_Road", country="Australia",
    region="Victoria", type="coastal", tag="famous", emoji="🛣️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Twelve Apostles", "The_Twelve_Apostles_(Victoria)"),
                ("Loch Ard Gorge", "Loch_Ard_Gorge"),
                ("London Arch", "London_Arch"),
                ("Cape Otway Lighthouse", "Cape_Otway_Lighthouse"),
                ("Lorne", "Lorne,_Victoria"),
                ("Bells Beach", "Bells_Beach,_Victoria")],
    blurb="243 km of coast road built by returned soldiers between 1919 and "
          "1932, by hand, as a war memorial and a job. It runs from surf "
          "beaches through temperate rainforest and comes out on a limestone "
          "shore that the Southern Ocean is actively demolishing.",
    fact="It is the world's largest war memorial, dedicated to the dead of "
          "the First World War — and the men who built it were the ones who "
          "came back.",
    tip="Drive it east to west, so the ocean is on your side of the car the "
        "whole way, and stop at Gibson Steps to stand at the *base* of the "
        "Apostles rather than on the viewing platform above them."),

"grampians": dict(
    name="Grampians", slug="Grampians_National_Park", country="Australia",
    region="Victoria", type="mountain", tag="hidden", emoji="🪨",
    sounds=["mountain-wind.mp3"],
    search_name="Grampians National Park Victoria Australia",
    highlights=[("The Pinnacle", None),
                ("MacKenzie Falls", ""),
                ("Halls Gap", "Halls_Gap,_Victoria"),
                ("Mount William", "Mount_William_(Victoria)"),
                ("Boroka Lookout", None),
                ("Grampians National Park", "Grampians_National_Park")],
    blurb="A set of sandstone ranges rising abruptly out of flat western "
          "Victorian farmland, tilted so that each ridge is a gentle slope on "
          "one side and a sheer wall on the other. Gariwerd, to the Jardwadjali "
          "and Djab Wurrung, holds most of southeastern Australia's surviving "
          "rock art.",
    fact="The ranges take their European name from the Scottish Grampians, "
         "which is why a search for them returns the Highlands — the "
         "Australian ones are 480 million years older and about a fifth as "
         "tall.",
    tip="Do the Pinnacle from the Wonderland car park rather than the short "
        "way. The track threads the Grand Canyon and Silent Street, two slots "
        "barely shoulder-wide, before it puts you on the overhang."),

"wilsons-promontory": dict(
    name="Wilsons Promontory", slug="Wilsons_Promontory", country="Australia",
    region="Victoria", type="coastal", tag="hidden", emoji="🥾",
    sounds=["ocean-waves.mp3"],
    highlights=[("Squeaky Beach", None),
                ("Mount Oberon", ""),
                ("Tidal River", "Tidal_River,_Victoria"),
                ("South East Point Lighthouse", "Wilsons_Promontory_Lighthouse"),
                ("Whisky Bay", None)],
    blurb="The southernmost point of mainland Australia: a granite headland "
          "of orange boulders, white quartz beaches and wind-cut heath, joined "
          "to Victoria by a sand isthmus that was dry land to Tasmania until "
          "the sea came up 12,000 years ago.",
    fact="Squeaky Beach really does squeak — the sand is near-pure quartz in "
         "grains of almost identical size, so they slide against each other "
         "and resonate rather than grinding.",
    tip="Walk the 19 km down to the lighthouse and stay the night in the "
        "keepers' cottages. You get the southern tip of a continent to "
        "yourself after the last day-walker has turned around."),

"ballarat": dict(
    name="Ballarat", slug="Ballarat", country="Australia", region="Victoria",
    type="city", tag="hidden", emoji="🪙", sounds=["city-hum.mp3"],
    highlights=[("Sovereign Hill", "Sovereign_Hill"),
                ("Eureka Stockade", "Eureka_Rebellion"),
                ("Ballarat Botanical Gardens", "Ballarat_Botanical_Gardens"),
                ("Art Gallery of Ballarat", "Art_Gallery_of_Ballarat"),
                ("Lake Wendouree", "Lake_Wendouree"),
                ("Lydiard Street", None)],
    blurb="The richest alluvial goldfield the world has ever seen, and a city "
          "built out of the proceeds in one furious decade after 1851. Lydiard "
          "Street's verandahs, theatre and banks are all 1860s and all still "
          "standing, because the money stopped as suddenly as it started.",
    fact="The Welcome Nugget was pulled out of a Ballarat shaft in 1858 at "
         "69 kg — and the miners' revolt here in 1854, put down in fifteen "
         "minutes, is where Australian democracy dates its manhood suffrage "
         "from.",
    tip="Sovereign Hill is a reconstruction, but the diggings below it are "
        "not — the ground behind the town is still cratered with the shafts "
        "and mullock heaps of the 1850s, and you can walk them for free."),

"bendigo": dict(
    name="Bendigo", slug="Bendigo", country="Australia", region="Victoria",
    type="city", tag="hidden", emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Sacred Heart Cathedral", "Sacred_Heart_Cathedral,_Bendigo"),
                ("Central Deborah Gold Mine", "Central_Deborah_Gold_Mine"),
                ("Golden Dragon Museum", "Golden_Dragon_Museum"),
                ("Bendigo Town Hall", "Bendigo_Town_Hall"),
                ("Rosalind Park", "Rosalind_Park")],
    blurb="The other great Victorian goldfield, and the one that kept "
          "producing — 780 tonnes of gold out of quartz reefs that ran deeper "
          "than anyone expected. The result is a provincial city with a "
          "sandstone cathedral, a tram network and a Chinese museum.",
    fact="Sacred Heart Cathedral was begun in 1896 and only finished in 2001; "
         "it is the largest cathedral in Australia outside a state capital, "
         "and its spire went up a century after its foundations.",
    tip="Go 61 m underground at the Central Deborah on the mine tour. It is "
        "one of 5,000 shafts sunk under this city, and the only one you can "
        "still ride the cage into."),

"phillip-island": dict(
    name="Phillip Island", slug="Phillip_Island", country="Australia",
    region="Victoria", type="island", tag="hidden", emoji="🐧",
    sounds=["ocean-waves.mp3"],
    highlights=[("The Nobbies", None),
                ("Cape Woolamai", "Cape_Woolamai"),
                ("Churchill Island", "Churchill_Island"),
                ("Phillip Island Grand Prix Circuit",
                 "Phillip_Island_Grand_Prix_Circuit"),
                ("Cowes", "Cowes,_Victoria")],
    blurb="A 100 km² island in Western Port two hours from Melbourne, with a "
          "motorcycle circuit on one side and a little penguin colony on the "
          "other. The penguins come ashore at the same beach every evening of "
          "the year, in the dark, in their thousands.",
    fact="The Summerland colony is about 40,000 little penguins — the "
         "smallest penguin species in the world at 33 cm — and the state "
         "bought back and demolished an entire housing estate over 25 years "
         "to give them their nesting ground back.",
    tip="Skip the floodlit grandstand and book the Cape Woolamai or "
        "guided-ranger option further along the beach. Same birds, no crowd, "
        "and they walk past close enough to hear."),

"geelong": dict(
    name="Geelong", slug="Geelong", country="Australia", region="Victoria",
    type="city", tag="hidden", emoji="⚓", sounds=["city-hum.mp3"],
    highlights=[("Eastern Beach", None),
                ("Geelong Waterfront", None),
                ("Barwon River", "Barwon_River_(Victoria)"),
                ("Point Lonsdale Lighthouse", "Point_Lonsdale_Lighthouse"),
                ("You Yangs", "You_Yangs")],
    blurb="Victoria's second city, on Corio Bay at the mouth of Port Phillip, "
          "built on wool and then on Ford. Its 1930s art deco sea baths were "
          "rebuilt in the 1990s and the whole waterfront turned back toward "
          "the water it had spent a century using as a wharf.",
    fact="The waterfront is lined with 104 carved bollards — repurposed pier "
         "timbers painted as swimmers, sailors, brass bands and lifesavers by "
         "one artist over six years.",
    tip="Follow the bollard trail out along the promenade and then cross to "
        "the You Yangs, half an hour inland: a granite ridge on a flat plain "
        "with the whole bay and the city laid out below."),

# ========================= AUSTRALIA — QUEENSLAND =========================
"brisbane": dict(
    name="Brisbane", slug="Brisbane", country="Australia",
    region="Queensland", type="city", tag="famous", emoji="🌇",
    sounds=["city-hum.mp3"],
    highlights=[("Story Bridge", "Story_Bridge"),
                ("South Bank Parklands", "South_Bank_Parklands"),
                ("Mount Coot-tha", "Mount_Coot-tha"),
                ("Kangaroo Point Cliffs", "Kangaroo_Point,_Queensland"),
                ("Brisbane City Hall", "Brisbane_City_Hall"),
                ("Queensland Cultural Centre", "Queensland_Cultural_Centre")],
    blurb="A subtropical river city that bends around itself so tightly the "
          "ferries cross the same water four times. Convict settlement in "
          "1824, a big country town for a century and a half, and now the "
          "fastest-growing capital in the country.",
    fact="South Bank has a artificial beach with real sand and a lifeguard in "
         "the middle of the central business district — built on the site of "
         "World Expo 88 and kept when the fair was pulled down.",
    tip="Climb the Kangaroo Point cliffs path at dusk. They are quarried "
        "volcanic rock right on the river, floodlit for climbers, and they "
        "put the whole skyline across the water in front of you."),

"gold-coast": dict(
    name="Gold Coast", slug="Gold_Coast,_Queensland", country="Australia",
    region="Queensland", type="coastal", tag="famous", emoji="🏙️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Surfers Paradise", "Surfers_Paradise,_Queensland"),
                ("Q1", "Q1_(building)"),
                ("Burleigh Heads", "Burleigh_Heads,_Queensland"),
                ("Currumbin", "Currumbin,_Queensland"),
                ("Springbrook National Park", "Springbrook_National_Park"),
                ("Natural Bridge", None)],
    blurb="57 km of continuous surf beach with a wall of towers along it and "
          "subtropical rainforest twenty minutes inland. It is Australia's "
          "most concentrated skyline outside Sydney and its most concentrated "
          "sand, in the same place.",
    fact="Q1 was the world's tallest residential tower when it topped out in "
         "2005 at 322 m, and its shadow reaches so far up the beach in winter "
         "that building heights are now regulated by it.",
    tip="Get out of the towers and into Springbrook. The Natural Bridge is a "
        "waterfall that has punched through a cave roof, and after dark in "
        "summer the cave ceiling is lit by glow-worms."),

"whitsunday-islands": dict(
    name="Whitsunday Islands", slug="Whitsunday_Islands", country="Australia",
    region="Queensland", type="island", tag="famous", emoji="⛵",
    sounds=["ocean-waves.mp3"],
    highlights=[("Whitehaven Beach", "Whitehaven_Beach"),
                ("Hill Inlet", None),
                ("Hamilton Island", "Hamilton_Island_(Queensland)"),
                ("Hook Island", "Hook_Island"),
                ("Airlie Beach", "Airlie_Beach,_Queensland")],
    blurb="74 islands inside the Great Barrier Reef, close enough together "
          "that the water between them stays flat — which is why this is where "
          "Australia goes sailing. They are drowned mountain tops, not coral, "
          "so they are steep, green and fringed with sand.",
    fact="Whitehaven Beach is 98% pure silica, so fine it will not hold heat "
         "and stays cool underfoot at midday — and it is abrasive enough that "
         "people have traditionally used it to clean jewellery.",
    tip="The famous swirl is not visible from the beach. Walk up to the Hill "
        "Inlet lookout at the northern end on a falling tide, when the "
        "current is dragging white sand through green water."),

"daintree-rainforest": dict(
    name="Daintree Rainforest", slug="Daintree_Rainforest",
    country="Australia", region="Queensland", type="nature", tag="famous",
    emoji="🌿", sounds=["wilderness.mp3"],
    highlights=[("Cape Tribulation", "Cape_Tribulation,_Queensland"),
                ("Mossman Gorge", "Mossman_Gorge"),
                ("Daintree River", "Daintree_River"),
                ("Thornton Peak", "Thornton_Peak"),
                ("Daintree National Park", "Daintree_National_Park")],
    blurb="The oldest continuously surviving tropical rainforest on the "
          "planet, about 180 million years of it, running straight down to a "
          "reef — the only place on Earth where two World Heritage sites meet "
          "at the tideline.",
    fact="Its plants include the idiot fruit, a flowering tree so primitive "
         "it was thought extinct until 1970 and is now treated as one of the "
         "closest living things to the first flowering plants.",
    tip="Cross on the Daintree ferry and drive to Cape Tribulation, then walk "
        "the Dubuji boardwalk at dusk. The forest noise starts before the "
        "light goes, and the cassowaries use the road at that hour."),

"port-douglas": dict(
    name="Port Douglas", slug="Port_Douglas", country="Australia",
    region="Queensland", type="coastal", tag="hidden", emoji="🌴",
    sounds=["ocean-waves.mp3"],
    highlights=[("Four Mile Beach", None),
                ("St Mary's by the Sea", None),
                ("Flagstaff Hill", None),
                ("Wildlife Habitat Port Douglas", None),
                ("Low Isles", "Low_Isles")],
    blurb="A gold-rush port that shrank to 100 people after a cyclone in 1911 "
          "and was rediscovered in the 1980s as the closest town to both the "
          "reef's outer edge and the Daintree. One main street, one very long "
          "beach, and boats leaving at eight.",
    fact="Port Douglas is the shortest run to the outer Great Barrier Reef "
         "from anywhere on the Queensland coast — the Agincourt ribbon reefs "
         "are about 90 minutes out, right on the continental shelf edge.",
    tip="Walk up Flagstaff Hill early. It puts Four Mile Beach and the "
        "Coral Sea on one side and the Mowbray valley on the other, and it is "
        "the only high ground in town."),

"townsville": dict(
    name="Townsville", slug="Townsville", country="Australia",
    region="Queensland", type="coastal", tag="hidden", emoji="🐠",
    sounds=["ocean-waves.mp3"],
    highlights=[("Castle Hill", "Castle_Hill,_Townsville"),
                ("Magnetic Island", "Magnetic_Island"),
                ("The Strand", "The_Strand,_Townsville"),
                ("Reef HQ", "Reef_HQ"),
                ("Museum of Tropical Queensland",
                 "Museum_of_Tropical_Queensland")],
    blurb="The dry tropics: a north Queensland city that gets its rain in "
          "three months and spends the other nine brown and blue, under a "
          "pink granite monolith that sits in the middle of the suburbs.",
    fact="Castle Hill is 286 m — fourteen metres short of the definition of a "
         "mountain, and there was a long-running local campaign to truck up "
         "enough fill to promote it.",
    tip="Take the twenty-minute ferry to Magnetic Island and walk the Forts "
        "track. Wartime observation posts on the ridge, and the granite "
        "boulders below them hold one of the densest wild koala populations "
        "in the north."),

"kgari-fraser-island": dict(
    name="K'gari (Fraser Island)", slug="K'gari", country="Australia",
    region="Queensland", type="island", tag="famous", emoji="🏝️",
    sounds=["ocean-waves.mp3"], search_name="Fraser Island K'gari Queensland",
    highlights=[("Lake McKenzie", None),
                ("Seventy-Five Mile Beach", None),
                ("Maheno shipwreck", "SS_Maheno"),
                ("Champagne Pools", None),
                ("Central Station", None)],
    blurb="The largest sand island in the world, 123 km long, with rainforest "
          "growing straight out of dune sand and more than a hundred "
          "freshwater lakes perched above sea level in it. There are no sealed "
          "roads; the beach is a gazetted highway.",
    fact="Its perched lakes sit in hollows lined with compacted organic "
         "matter that holds rainwater above the water table — Lake Boomanjin "
         "is the largest of its kind on Earth, and half the world's perched "
         "dune lakes are on this one island.",
    tip="Drive Seventy-Five Mile Beach on a falling tide only, and stop at "
        "Eli Creek. It empties several million litres of clear water an hour "
        "into the surf, and you can float down it."),

"noosa": dict(
    name="Noosa Heads", slug="Noosa_Heads,_Queensland", country="Australia",
    region="Queensland", type="coastal", tag="hidden", emoji="🌊",
    sounds=["ocean-waves.mp3"],
    highlights=[("Noosa National Park", "Noosa_National_Park"),
                ("Hastings Street", None),
                ("Laguna Bay", None),
                ("Noosa River", "Noosa_River"),
                ("Mount Coolum", "Mount_Coolum")],
    blurb="A north-facing point on the Sunshine Coast where the surf wraps "
          "around a headland of pandanus and the town behind it has a "
          "building-height limit of three storeys. It is the anti-Gold Coast, "
          "by local ordinance.",
    fact="Noosa is one of only twelve UNESCO Biosphere Reserves in Australia, "
         "and the national park inside the town limits carries koalas in the "
         "trees over a beach walk.",
    tip="Do the coastal track past Boiling Pot to Alexandria Bay early. The "
        "point breaks are lined up below you the whole way, and the far end "
        "is a beach the town never reaches."),

"lamington-national-park": dict(
    name="Lamington National Park", slug="Lamington_National_Park",
    country="Australia", region="Queensland", type="nature", tag="hidden",
    emoji="🌳", sounds=["wilderness.mp3"],
    highlights=[("Binna Burra", "Binna_Burra"),
                ("O'Reilly's", None),
                ("Elabana Falls", None),
                ("Mount Bithongabel", None),
                ("Tweed Volcano", "Tweed_Volcano")],
    blurb="Rainforest on the rim of an extinct shield volcano, 900 m up on "
          "the Queensland–New South Wales border, with Antarctic beech trees "
          "that have been growing on the same root systems for two thousand "
          "years.",
    fact="The plateau is one wall of the Tweed Volcano's caldera — a crater "
         "over 40 km across, one of the largest erosion calderas in the "
         "world, with Mount Warning standing in the middle of it.",
    tip="Walk the Border Track from Binna Burra to O'Reilly's — 21 km along "
        "the caldera rim, in cloud forest most of the way, with the crater "
        "opening below you every time the trees break."),

"carnarvon-gorge": dict(
    name="Carnarvon Gorge", slug="Carnarvon_Gorge", country="Australia",
    region="Queensland", type="nature", tag="hidden", emoji="🏞️",
    sounds=["wilderness.mp3"],
    highlights=[("Cathedral Cave", None),
                ("Art Gallery", None),
                ("Ward's Canyon", None),
                ("Moss Garden", None),
                ("Carnarvon National Park", "Carnarvon_National_Park")],
    blurb="A 30 km white sandstone gorge cut into the dry central Queensland "
          "highlands, holding a creek, cabbage palms and king ferns in a "
          "landscape that is otherwise cattle country. Side canyons open off "
          "it like rooms.",
    fact="The Art Gallery panel carries around 2,000 engravings, ochre "
         "stencils and freehand paintings across 62 m of rock face — one of "
         "the most significant rock art sites in Australia, and still in the "
         "open air.",
    tip="Ward's Canyon holds the king fern, the largest fern on Earth, with "
        "fronds up to 5 m — a relict population surviving in one shaded slot "
        "because nowhere else nearby stays wet enough."),

"cape-york": dict(
    name="Cape York Peninsula", slug="Cape_York_Peninsula",
    country="Australia", region="Queensland", type="nature", tag="hidden",
    emoji="🧭", sounds=["wilderness.mp3"],
    highlights=[("Cape York", "Cape_York_(Queensland)"),
                ("Jardine River", "Jardine_River"),
                ("Weipa", "Weipa,_Queensland"),
                ("Thursday Island", "Thursday_Island"),
                ("Quinkan rock art", "Quinkan_rock_art")],
    blurb="The northernmost 1,000 km of the Australian mainland, a wedge of "
          "savanna, rainforest and river crossings pointing at New Guinea. "
          "The road is unsealed, the rivers are tidal and crocodile country, "
          "and the tip is a rock you walk onto.",
    fact="Cape York is 150 km from Papua New Guinea across the Torres Strait, "
         "and during the last ice age there was no strait — you could have "
         "walked the whole way.",
    tip="The Old Telegraph Track is the drive people come for, but the "
        "Quinkan galleries near Laura are the reason to stop: tens of "
        "thousands of years of painted rock shelters in the sandstone."),

"mount-isa": dict(
    name="Mount Isa", slug="Mount_Isa", country="Australia",
    region="Queensland", type="city", tag="hidden", emoji="⛏️",
    sounds=["desert-wind.mp3"],
    highlights=[("Mount Isa Mines", "Mount_Isa_Mines"),
                ("Lake Moondarra", "Lake_Moondarra"),
                ("Riversleigh", "Riversleigh")],
    blurb="A mining city in the middle of the Queensland outback whose local "
          "government area is the size of Switzerland and holds 20,000 people. "
          "The smelter stack is 270 m tall and visible from an hour's drive "
          "away in every direction.",
    fact="Mount Isa's city limits enclose about 43,000 km² — for a long time "
         "the largest city by area in the world, and still one of the "
         "emptiest.",
    tip="Drive north to Boodjamulla, where Lawn Hill Gorge cuts a green "
        "ribbon of palms and turquoise water through red rock — and the "
        "Riversleigh fossil beds beside it hold 25 million years of "
        "marsupials in limestone."),
# ---------------- Australia — South Australia ----------------
"adelaide": dict(
    name="Adelaide", slug="Adelaide", country="Australia",
    region="South Australia", type="city", tag="famous", emoji="🍷",
    sounds=["city-hum.mp3"],
    highlights=[("Adelaide Oval", "Adelaide_Oval"),
                ("Adelaide Central Market", "Adelaide_Central_Market"),
                ("North Terrace", "North_Terrace,_Adelaide"),
                ("Adelaide Botanic Garden", "Adelaide_Botanic_Garden"),
                ("Glenelg", "Glenelg,_South_Australia")],
    blurb="A city laid out in 1837 as a perfect grid inside an unbroken ring "
          "of parkland, so every road out of the centre passes through green "
          "before it reaches a suburb. Wine country starts twenty minutes "
          "from the CBD in three different directions.",
    fact="Adelaide is the only Australian capital founded entirely by free "
         "settlers — no convict transportation was ever sent here.",
    tip="Ride the 1929 tram to Glenelg at dusk; it runs from the middle of "
        "the grid straight onto a beach that faces west, which in Australia "
        "means the rare thing of a sunset over water."),
"barossa-valley": dict(
    name="Barossa Valley", slug="Barossa_Valley", country="Australia",
    region="South Australia", type="nature", tag="famous", emoji="🍇",
    sounds=["wilderness.mp3"],
    highlights=[("Tanunda", "Tanunda,_South_Australia"),
                ("Angaston", "Angaston,_South_Australia"),
                ("Seppeltsfield", "Seppeltsfield"),
                ("Penfolds", "Penfolds")],
    blurb="An hour northeast of Adelaide, a valley settled by Silesian "
          "Lutherans in the 1840s who planted vines that were never hit by "
          "phylloxera. Some Shiraz here grows on rootstock older than any "
          "surviving vineyard in Europe.",
    fact="The Barossa holds the oldest continuously producing Shiraz vines on "
         "Earth, planted in 1843 and still bearing fruit every vintage.",
    tip="Drive the Seppeltsfield road in April, when the date palms planted "
        "down both sides during the Depression are backlit and the fortified "
        "cellar can pour you a tawny from your own birth year."),
"kangaroo-island": dict(
    name="Kangaroo Island", slug="Kangaroo_Island", country="Australia",
    region="South Australia", type="island", tag="hidden", emoji="🦘",
    sounds=["ocean-waves.mp3"],
    highlights=[("Remarkable Rocks", "Remarkable_Rocks"),
                ("Admirals Arch", ""),
                ("Seal Bay Conservation Park", "Seal_Bay_Conservation_Park"),
                ("Kingscote", "Kingscote,_South_Australia")],
    blurb="Australia's third-largest island, cut off from the mainland about "
          "10,000 years ago, which left it with no foxes and no rabbits. A "
          "third of it is protected, and the wildlife behaves as though it "
          "has never been hunted.",
    fact="Kangaroo Island's Ligurian bees are the last pure population of "
         "that strain anywhere in the world — the island has been a declared "
         "bee sanctuary since 1885.",
    tip="Walk out onto the beach at Seal Bay with a guide at low tide, where "
        "an Australian sea lion colony sleeps on the sand between six-day "
        "fishing trips to the edge of the continental shelf."),
"flinders-ranges": dict(
    name="Flinders Ranges", slug="Flinders_Ranges", country="Australia",
    region="South Australia", type="mountain", tag="hidden", emoji="⛰️",
    sounds=["desert-wind.mp3"],
    highlights=[("Wilpena Pound", "Wilpena_Pound"),
                ("Ikara-Flinders Ranges National Park",
                 "Ikara–Flinders_Ranges_National_Park"),
                ("Brachina Gorge", ""),
                ("Arkaroola", "Arkaroola")],
    blurb="A 430 km spine of folded red rock running north out of the wheat "
          "country into the desert. Its centrepiece, Wilpena Pound, is a "
          "natural amphitheatre of quartzite ridges eight kilometres across "
          "with a single creek-bed entrance.",
    fact="Brachina Gorge cuts through 130 million years of seafloor in a few "
         "kilometres of road, including the rock layer that defines the "
         "Ediacaran — the first new geological period named in 120 years.",
    tip="Be on the St Mary Peak trail before sunrise; the light comes over "
        "the eastern rim and fills the Pound like liquid, and the yellow-"
        "footed rock-wallabies are still out on the scree."),
"coober-pedy": dict(
    name="Coober Pedy", slug="Coober_Pedy", country="Australia",
    region="South Australia", type="desert", tag="quirky", emoji="💎",
    sounds=["desert-wind.mp3"],
    highlights=[("Breakaways Conservation Park",
                 "Kanku-Breakaways_Conservation_Park"),
                ("Serbian Orthodox Church, Coober Pedy",
                 "Serbian_Orthodox_Church,_Coober_Pedy"),
                ("Dog Fence", "Dingo_Fence"),
                ("Moon Plain", "Coober_Pedy")],
    blurb="An opal-mining town in the South Australian desert where more than "
          "half the residents live underground in dugouts cut into the "
          "sandstone hills, because summer surface temperatures pass 45 °C "
          "and the rock holds a steady 23 °C year round.",
    fact="Coober Pedy supplies most of the world's gem-quality opal, and its "
         "name comes from Kokatha words often rendered as kupa-piti — "
         "roughly, white man in a hole.",
    tip="Go 30 km north to the Breakaways at last light, where flat-topped "
        "mesas of ochre and white sit on a plain that was seabed 70 million "
        "years ago — and stay for a sky with no town glow in it."),
"nullarbor-plain": dict(
    name="Nullarbor Plain", slug="Nullarbor_Plain", country="Australia",
    region="South Australia", type="desert", tag="hidden", emoji="🛣️",
    sounds=["desert-wind.mp3"],
    highlights=[("Eyre Highway", "Eyre_Highway"),
                ("Bunda Cliffs", "Bunda_Cliffs"),
                ("Head of Bight", "Head_of_Bight"),
                ("Trans-Australian Railway", "Trans-Australian_Railway")],
    blurb="The world's largest single slab of limestone, 200,000 km² of it, "
          "so flat and so treeless that the railway across it runs 478 km "
          "without a single curve. The southern edge simply stops in cliffs "
          "above the Southern Ocean.",
    fact="Nullarbor is not an Aboriginal word — it is dog Latin, nullus "
         "arbor, no tree, coined by a surveyor in 1867.",
    tip="Pull off the Eyre Highway at the Bunda Cliffs between June and "
        "October: southern right whales calve directly below the lookout at "
        "the Head of Bight, close enough to hear them breathe."),
"lake-eyre": dict(
    name="Lake Eyre", slug="Lake_Eyre", country="Australia",
    search_name="Lake Eyre Kati Thanda South Australia",
    region="South Australia", type="desert", tag="hidden", emoji="🧂",
    sounds=["desert-wind.mp3"],
    highlights=[("Kati Thanda-Lake Eyre National Park",
                 "Kati_Thanda-Lake_Eyre_National_Park"),
                ("Marree", "Marree,_South_Australia"),
                ("Oodnadatta Track", "Oodnadatta_Track"),
                ("William Creek", "William_Creek"),
                ("Lake Eyre Basin", "Lake_Eyre_basin")],
    blurb="The lowest point in Australia, 15 m below sea level, and a salt "
          "pan the size of a small country that is dry almost all the time. "
          "Every few decades Queensland monsoon rain arrives down a thousand "
          "kilometres of channel and fills it.",
    fact="When Kati Thanda floods it becomes Australia's largest lake and "
         "pelicans arrive in tens of thousands — birds that were, days "
         "before, hundreds of kilometres away on the coast.",
    tip="Take the scenic flight from William Creek rather than driving to the "
        "shore; from 500 m the salt crust shows braided pink and white "
        "channels that are invisible from ground level."),
"port-lincoln": dict(
    name="Port Lincoln", slug="Port_Lincoln", country="Australia",
    region="South Australia", type="coastal", tag="hidden", emoji="🦈",
    sounds=["ocean-waves.mp3"],
    highlights=[("Boston Bay", "Boston_Bay"),
                ("Lincoln National Park", "Lincoln_National_Park"),
                ("Coffin Bay National Park", "Coffin_Bay_National_Park"),
                ("Neptune Islands", "Neptune_Islands")],
    blurb="A tuna port on the tip of the Eyre Peninsula, sitting on a natural "
          "harbour three times the size of Sydney's. It was nearly chosen as "
          "South Australia's capital and lost out for want of fresh water.",
    fact="The Neptune Islands offshore hold the largest colony of New Zealand "
         "fur seals in Australia, which is why they are the only place in the "
         "country licensed for great white shark cage diving.",
    tip="Drive an hour west to Coffin Bay and eat the oysters standing in the "
        "shallows they were pulled from — the lease racks are visible from "
        "the shore where you're shucking."),

# ---------------- Australia — Western Australia ----------------
"fremantle": dict(
    name="Fremantle", slug="Fremantle", country="Australia",
    region="Western Australia", type="city", tag="hidden", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Fremantle Prison", "Fremantle_Prison"),
                ("Fremantle Markets", "Fremantle_Markets"),
                ("Round House", "Round_House_(Western_Australia)"),
                ("Western Australian Museum",
                 "Western_Australian_Museum")],
    blurb="The port at the mouth of the Swan River, and one of the best-"
          "preserved 19th-century streetscapes anywhere — because Perth's "
          "building booms kept passing it by until the 1987 America's Cup "
          "arrived and everyone repainted at once.",
    fact="Fremantle Prison, built by the convicts who would be locked in it, "
         "held prisoners until 1991 and is Western Australia's only World "
         "Heritage-listed building.",
    tip="Take the tunnels tour under the prison, where you board a small boat "
        "and are paddled through flooded 1850s water-supply shafts 20 m below "
        "the cell blocks."),
"rottnest-island": dict(
    name="Rottnest Island", slug="Rottnest_Island", country="Australia",
    region="Western Australia", type="island", tag="famous", emoji="🐭",
    sounds=["ocean-waves.mp3"],
    highlights=[("Wadjemup Lighthouse", "Wadjemup_Lighthouse"),
                ("The Basin", "Rottnest_Island"),
                ("Oliver Hill Battery", "Oliver_Hill_Battery")],
    blurb="A car-free island 18 km off Fremantle, ringed by 63 beaches and "
          "twenty bays, where everyone moves by bicycle. Its Noongar name is "
          "Wadjemup, the place across the water, and it was connected to the "
          "mainland until sea levels rose 7,000 years ago.",
    fact="A Dutch captain in 1696 mistook the island's quokkas for giant rats "
         "and named the place Rottnest — rat's nest — which is how a very "
         "photogenic marsupial ended up with an insult for an address.",
    tip="Ride to the West End before the ferry crowds; New Zealand fur seals "
        "haul out on the rocks below the lookout, and between September and "
        "December humpbacks pass close enough to see without binoculars."),
"margaret-river": dict(
    name="Margaret River", slug="Margaret_River,_Western_Australia",
    country="Australia", region="Western Australia", type="nature",
    tag="famous", emoji="🍷",
    sounds=["wilderness.mp3"],
    highlights=[("Jewel Cave", ""),
                ("Cape Leeuwin Lighthouse", "Cape_Leeuwin_Lighthouse"),
                ("Boranup Forest", "Boranup,_Western_Australia"),
                ("Surfers Point", "Margaret_River,_Western_Australia")],
    blurb="A stretch of the far southwest where karri forest, limestone caves "
          "and 130 wineries sit between two capes, and world-tour surf breaks "
          "sit at the end of the vineyard roads. The region grows about 3% of "
          "Australia's wine and takes a fifth of its premium market.",
    fact="Cape Leeuwin, at the southern end, is where the Indian and Southern "
         "Oceans are officially deemed to meet — the two swells arrive at an "
         "angle you can see from the lighthouse gallery.",
    tip="Skip the show caves for Giants Cave, where you're handed a torch and "
        "a helmet and go down 86 steps on your own, with no guide and no "
        "lighting rig."),
"esperance": dict(
    name="Esperance", slug="Esperance,_Western_Australia",
    country="Australia", region="Western Australia", type="coastal",
    tag="hidden", emoji="🏖️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cape Le Grand National Park",
                 "Cape_Le_Grand_National_Park"),
                ("Lucky Bay", "Lucky_Bay"),
                ("Recherche Archipelago", "Recherche_Archipelago"),
                ("Lake Hillier", "Lake_Hillier")],
    blurb="A town on the Southern Ocean with a hundred islands scattered "
          "offshore and some of the whitest sand ever measured. The quartz "
          "grains are so fine and so round that walking on them squeaks.",
    fact="Lake Hillier, on Middle Island offshore, is permanently bubblegum "
         "pink — and stays pink in a glass of water, which rules out any "
         "trick of the light.",
    tip="Drive onto the sand at Lucky Bay at low tide; kangaroos come down to "
        "the beach in the early morning and lie in the shade of the dunes "
        "with the surf ten metres away."),
"ningaloo-reef": dict(
    name="Ningaloo Reef", slug="Ningaloo_Coast", country="Australia",
    search_name="Ningaloo Reef Exmouth Western Australia",
    region="Western Australia", type="coastal", tag="famous", emoji="🐋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cape Range National Park", "Cape_Range_National_Park"),
                ("Exmouth", "Exmouth,_Western_Australia"),
                ("Turquoise Bay", "Ningaloo_Coast"),
                ("Coral Bay", "Coral_Bay,_Western_Australia")],
    blurb="A 260 km fringing reef that comes so close to shore you can wade "
          "off the beach and be over coral in twenty strokes. Unlike the "
          "Great Barrier Reef there is no lagoon crossing and no boat "
          "required.",
    fact="Ningaloo is one of very few places where whale sharks gather "
         "predictably every year — they arrive from March after the coral "
         "mass-spawns on the autumn full moon.",
    tip="Swim Turquoise Bay's drift: enter at the southern end, let the "
        "current carry you over the bommies, and get out at the sandbar "
        "before it pushes you into the channel."),
"karijini-national-park": dict(
    name="Karijini National Park", slug="Karijini_National_Park",
    country="Australia", region="Western Australia", type="nature",
    tag="hidden", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Hamersley Range", "Hamersley_Range"),
                ("Mount Bruce", "Mount_Bruce_(Western_Australia)"),
                ("Dales Gorge", "Karijini_National_Park"),
                ("Hancock Gorge", "Karijini_National_Park")],
    blurb="In the Pilbara, a plateau of spinifex split by gorges up to 100 m "
          "deep, cut into rock that is 2.5 billion years old. From the rim "
          "you see nothing; the whole park is below your feet.",
    fact="Karijini's banded iron formations were laid down when the first "
         "photosynthetic bacteria began oxygenating the oceans — the red and "
         "grey bands are literally rust from the atmosphere's first oxygen.",
    tip="Do the Hancock Gorge descent to Kermits Pool, where the walls narrow "
        "to shoulder width and you shuffle along a polished chute with a foot "
        "on each side of the water."),
"purnululu-national-park": dict(
    name="Bungle Bungle Range", slug="Purnululu_National_Park",
    country="Australia", region="Western Australia", type="nature",
    tag="hidden", emoji="🍯",
    sounds=["desert-wind.mp3"],
    highlights=[("Cathedral Gorge", "Purnululu_National_Park"),
                ("Echidna Chasm", "Purnululu_National_Park"),
                ("Kimberley", "Kimberley_(Western_Australia)")],
    blurb="A maze of sandstone domes banded orange and black in the East "
          "Kimberley, weathered over 20 million years into shapes like stacked "
          "beehives. Between them run chasms so narrow the sun reaches the "
          "floor for about half an hour a day.",
    fact="The Bungle Bungles were known to Aboriginal people for millennia and "
         "to a few local stockmen, but were unknown to the wider world until a "
         "documentary crew filmed them from the air in 1983.",
    tip="Walk into Cathedral Gorge in the middle of the day — a natural domed "
        "chamber with a sand floor and acoustics that make a spoken sentence "
        "hang for several seconds."),
"shark-bay": dict(
    name="Shark Bay", slug="Shark_Bay", country="Australia",
    region="Western Australia", type="coastal", tag="hidden", emoji="🐬",
    sounds=["ocean-waves.mp3"],
    highlights=[("Hamelin Pool Marine Nature Reserve",
                 "Hamelin_Pool_Marine_Nature_Reserve"),
                ("Monkey Mia", "Monkey_Mia"),
                ("Shell Beach", "Shell_Beach,_Western_Australia"),
                ("François Peron National Park",
                 "Francois_Peron_National_Park")],
    blurb="A World Heritage bay on the westernmost point of the continent, "
          "holding the largest seagrass meadow on Earth and water so salty in "
          "its inner reaches that almost nothing can graze there.",
    fact="Hamelin Pool's stromatolites are living colonies of the same "
         "cyanobacteria that dominated Earth for two billion years — the "
         "closest thing to a window onto the planet's earliest life.",
    tip="Stand on Shell Beach, where instead of sand there are 4,000-year "
        "drifts of tiny white cockle shells up to 10 m deep — quarried in "
        "blocks and used to build the old buildings in Denham."),
"broome": dict(
    name="Broome", slug="Broome,_Western_Australia", country="Australia",
    region="Western Australia", type="coastal", tag="famous", emoji="🐪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cable Beach", "Cable_Beach,_Western_Australia"),
                ("Gantheaume Point", "Gantheaume_Point"),
                ("Sun Pictures", "Sun_Pictures"),
                ("Chinatown, Broome", "")],
    blurb="A pearling town on the Kimberley coast where 22 m tides expose "
          "dinosaur footprints and a 22 km beach faces due west. Its "
          "cemeteries hold Japanese, Malay, Chinese and Filipino divers from "
          "the days when Broome supplied most of the world's pearl shell.",
    fact="On full-moon nights from March to October the reflection off the "
         "exposed mudflats makes a rippled ladder of light up to the moon — "
         "locals call it the Staircase to the Moon.",
    tip="Watch a film at Sun Pictures, the oldest continuously operating "
        "open-air cinema in the world, sitting in a canvas deckchair while "
        "planes on approach to Broome airport cross the screen."),
"the-pinnacles": dict(
    name="The Pinnacles", slug="Pinnacles_(Western_Australia)",
    country="Australia", search_name="Pinnacles Desert Nambung Western Australia",
    region="Western Australia", type="desert", tag="quirky", emoji="🗿",
    sounds=["desert-wind.mp3"],
    highlights=[("Nambung National Park", "Nambung_National_Park"),
                ("Cervantes", "Cervantes,_Western_Australia"),
                ("Lancelin", "Lancelin,_Western_Australia")],
    blurb="Thousands of limestone spires standing out of yellow sand two "
          "hours north of Perth, some five metres tall, some the size of a "
          "fist. They were buried until a few thousand years ago, when the "
          "wind stripped the dunes off them.",
    fact="Geologists still argue about how the Pinnacles formed — whether "
         "they are casts of ancient tree roots, dissolved remnants of a "
         "limestone sheet, or both at once.",
    tip="Come at moonrise rather than midday: the field runs east-west, and "
        "low light turns every spire into a long shadow across the sand."),
"wave-rock": dict(
    name="Wave Rock", slug="Wave_Rock", country="Australia",
    region="Western Australia", type="nature", tag="quirky", emoji="🌊",
    sounds=["desert-wind.mp3"],
    highlights=[("Hyden", "Hyden,_Western_Australia"),
                ("Mulka's Cave", "Mulka's_Cave")],
    blurb="A granite cliff 15 m high and 110 m long, undercut and streaked "
          "into the exact shape of a breaking wave, standing on the edge of "
          "the wheatbelt four hours east of Perth.",
    fact="The wave shape was carved underground: groundwater rotted the base "
         "of the granite while it was still buried, and erosion later "
         "stripped away the soil to reveal the curve.",
    tip="Follow the path to the top of the rock, where a low stone wall built "
        "in 1928 still channels rainwater to the town dam — a working piece "
        "of engineering laid along the crest of the wave."),
"kalgoorlie": dict(
    name="Kalgoorlie", slug="Kalgoorlie", country="Australia",
    region="Western Australia", type="city", tag="hidden", emoji="🪙",
    sounds=["desert-wind.mp3"],
    highlights=[("Super Pit gold mine", "Super_Pit_gold_mine"),
                ("Hannan Street", "Kalgoorlie"),
                ("Goldfields Water Supply Scheme",
                 "Goldfields_Water_Supply_Scheme"),
                ("Coolgardie", "Coolgardie,_Western_Australia")],
    blurb="A goldfields city built on the richest square mile of gold-bearing "
          "ground ever found. Its main street was made wide enough to turn a "
          "camel train, and it still is, lined with two-storey verandahs from "
          "the 1890s boom.",
    fact="Kalgoorlie's water arrives through a 560 km pipeline from Perth, "
         "designed by C. Y. O'Connor in 1903 — an engineering feat so "
         "ridiculed at the time that its designer died before it worked.",
    tip="Stand at the Super Pit lookout when a blast is scheduled; the hole "
        "is 3.5 km long and 600 m deep, and the haul trucks on the far wall "
        "look like grains of rice."),
# ---------------- Australia — Tasmania ----------------
"hobart": dict(
    name="Hobart", slug="Hobart", country="Australia",
    region="Tasmania", type="city", tag="famous", emoji="🏔️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Salamanca Place", "Salamanca_Place"),
                ("Museum of Old and New Art", "Museum_of_Old_and_New_Art"),
                ("kunanyi / Mount Wellington", "Kunanyi_/_Mount_Wellington"),
                ("Battery Point", "Battery_Point,_Tasmania"),
                ("Constitution Dock", "Hobart")],
    blurb="Australia's second-oldest capital, wedged between a deep-water "
          "harbour and a 1,271 m mountain that can hold snow in February. "
          "Georgian sandstone warehouses still line the waterfront where "
          "whalers unloaded.",
    fact="Hobart is the closest city in the world to Antarctica with a "
         "resupply port — Australian, French and Chinese icebreakers all sail "
         "for the ice from its docks.",
    tip="Take the ferry up the Derwent to MONA, a museum dug three storeys "
        "into a sandstone cliff, where you go in at the top and work "
        "downwards with no map and no wall labels."),
"cradle-mountain": dict(
    name="Cradle Mountain", slug="Cradle_Mountain", country="Australia",
    region="Tasmania", type="mountain", tag="famous", emoji="🥾",
    sounds=["wilderness.mp3"],
    highlights=[("Dove Lake", "Dove_Lake_(Tasmania)"),
                ("Overland Track", "Overland_Track"),
                ("Cradle Mountain-Lake St Clair National Park",
                 "Cradle_Mountain-Lake_St_Clair_National_Park"),
                ("Lake St Clair", "Lake_St_Clair_(Tasmania)")],
    blurb="A jagged dolerite ridge above a glacial lake in Tasmania's central "
          "highlands, and the northern end of the Overland Track — 65 km of "
          "boardwalk and buttongrass to the deepest lake in Australia.",
    fact="The mountain is named for its shape as seen from the north, where "
         "the two summit crags and the dip between them look like a miner's "
         "cradle for washing gold.",
    tip="Walk the Dove Lake circuit anticlockwise in the last hour of light, "
        "when the Ballroom Forest — moss, myrtle-beech and no undergrowth — "
        "goes completely still and wombats come out onto the track."),
"freycinet-national-park": dict(
    name="Freycinet", slug="Freycinet_National_Park", country="Australia",
    region="Tasmania", type="coastal", tag="famous", emoji="🦪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Wineglass Bay", "Wineglass_Bay"),
                ("The Hazards", "Freycinet_National_Park"),
                ("Coles Bay", "Coles_Bay,_Tasmania"),
                ("Cape Tourville Lighthouse", "Freycinet_National_Park")],
    blurb="A peninsula of pink granite peaks on Tasmania's east coast, with a "
          "perfect crescent of white sand — Wineglass Bay — hidden behind "
          "them. The rock glows because of the potassium feldspar in it.",
    fact="Wineglass Bay is thought to be named not for its shape but for the "
         "whaling that turned its water red in the 1820s.",
    tip="Climb to the saddle lookout, then keep going down the far side and "
        "walk the length of the beach to Hazards Beach — most day-trippers "
        "photograph the bay from above and never set foot on it."),
"port-arthur": dict(
    name="Port Arthur", slug="Port_Arthur,_Tasmania", country="Australia",
    region="Tasmania", type="ancient", tag="famous", emoji="⛓️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Port Arthur Historic Site",
                 "Port_Arthur_Historic_Site"),
                ("Isle of the Dead", "Isle_of_the_Dead_(Tasmania)"),
                ("Tasman Peninsula", "Tasman_Peninsula"),
                ("Eaglehawk Neck", "Eaglehawk_Neck")],
    blurb="A convict settlement on a peninsula joined to Tasmania by a strip "
          "of land 30 m wide, guarded by a line of chained dogs. Between 1830 "
          "and 1877 it held Britain's hardest-case reoffenders in what was "
          "designed as an inescapable machine.",
    fact="The Separate Prison here ran on total silence and isolation — an "
          "experiment in psychological punishment that filled the site's own "
          "asylum next door.",
    tip="Book the after-dark lantern tour, which walks the ruins by "
        "candlelight and ends in buildings the daytime ticket never opens."),
"launceston": dict(
    name="Launceston", slug="Launceston,_Tasmania", country="Australia",
    region="Tasmania", type="city", tag="hidden", emoji="🌉",
    sounds=["city-hum.mp3"],
    highlights=[("Cataract Gorge", "Cataract_Gorge"),
                ("Queen Victoria Museum and Art Gallery",
                 "Queen_Victoria_Museum_and_Art_Gallery"),
                ("Tamar Valley", "Tamar_Valley"),
                ("City Park", "City_Park,_Launceston")],
    blurb="Australia's third-oldest city, at the head of the Tamar estuary in "
          "northern Tasmania, with a gorge of dolerite cliffs and rapids "
          "beginning a fifteen-minute walk from the main street.",
    fact="The chairlift across Cataract Gorge has the longest single span of "
         "any chairlift in the world — 308 m with no supporting tower.",
    tip="Walk the Zig Zag track on the gorge's south side at dusk; the "
        "Victorian rotunda and swimming pool below are floodlit, and peacocks "
        "roost in the trees along the path."),
"bay-of-fires": dict(
    name="Bay of Fires", slug="Bay_of_Fires", country="Australia",
    region="Tasmania", type="coastal", tag="hidden", emoji="🧡",
    sounds=["ocean-waves.mp3"],
    highlights=[("Binalong Bay", "Binalong_Bay"),
                ("Mount William National Park",
                 "Mount_William_National_Park"),
                ("St Helens", "St_Helens,_Tasmania")],
    blurb="Fifty kilometres of white sand and clear water on Tasmania's "
          "northeast corner, where the granite boulders along the shoreline "
          "are covered in a bright orange lichen.",
    fact="The bay was named in 1773 by a navigator who saw Aboriginal fires "
         "burning along the coast — nothing to do with the orange rocks that "
         "everyone now assumes are the reason.",
    tip="Camp free at Cosy Corner or Sloop Reef; the sites sit behind the "
        "dunes with no lights, and this coast faces east into a sunrise over "
        "open ocean with Chile at the far end."),
"bruny-island": dict(
    name="Bruny Island", slug="Bruny_Island", country="Australia",
    region="Tasmania", type="island", tag="hidden", emoji="🐧",
    sounds=["ocean-waves.mp3"],
    highlights=[("The Neck", "Bruny_Island"),
                ("Cape Bruny Lighthouse", "Cape_Bruny_Lighthouse"),
                ("South Bruny National Park",
                 "South_Bruny_National_Park"),
                ("D'Entrecasteaux Channel", "D'Entrecasteaux_Channel")],
    blurb="Two islands joined by a sand isthmus a few hundred metres wide, "
          "reached by a twenty-minute ferry south of Hobart. Cheese, oysters "
          "and whisky at one end; 300 m sea cliffs at the other.",
    fact="Bruny is one of the few places where the rare white morph of the "
         "Bear's brush-tailed possum lives — and where white wallabies breed "
         "true in the wild.",
    tip="Stand on the Neck's viewing platform after sunset from October to "
        "February, when short-tailed shearwaters and little penguins come "
        "ashore through the marram grass under your feet."),

# ---------------- Australia — Northern Territory ----------------
"darwin": dict(
    name="Darwin", slug="Darwin,_Northern_Territory", country="Australia",
    region="Northern Territory", type="city", tag="famous", emoji="🌴",
    sounds=["wilderness.mp3"],
    highlights=[("Mindil Beach", "Mindil_Beach"),
                ("Darwin Waterfront", "Darwin_Waterfront_Precinct"),
                ("Museum and Art Gallery of the Northern Territory",
                 "Museum_and_Art_Gallery_of_the_Northern_Territory"),
                ("Charles Darwin National Park",
                 "Charles_Darwin_National_Park")],
    blurb="Australia's tropical capital, closer to Jakarta than to Canberra, "
          "with two seasons — the Dry and the Build-up — and a population "
          "drawn from more than sixty ancestries.",
    fact="Darwin was bombed 64 times in the Second World War, the first raid "
         "dropping more ordnance than Pearl Harbor, then flattened again by "
         "Cyclone Tracy on Christmas Eve 1974.",
    tip="Go to the Mindil Beach sunset market on a Thursday, buy laksa, and "
        "walk it down to the sand — the whole crowd turns to face the water "
        "as the sun drops into the Timor Sea."),
"kakadu-national-park": dict(
    name="Kakadu National Park", slug="Kakadu_National_Park",
    country="Australia", region="Northern Territory", type="nature",
    tag="famous", emoji="🐊",
    sounds=["wilderness.mp3"],
    highlights=[("Ubirr", "Ubirr"),
                ("Nourlangie Rock", "Nourlangie_Rock"),
                ("Jim Jim Falls", "Jim_Jim_Falls"),
                ("Yellow Water", "Kakadu_National_Park"),
                ("Jabiru", "Jabiru,_Northern_Territory")],
    blurb="Nearly 20,000 km² of floodplain, stone country and monsoon forest "
          "in the Top End, jointly managed with the Bininj and Mungguy people "
          "who have lived here for around 65,000 years.",
    fact="Kakadu holds one of the longest historical records of any people on "
         "Earth — rock art galleries that include extinct thylacines, and "
         "later, sailing ships with anchors.",
    tip="Climb Ubirr for sunset over the Nadab floodplain and look for the "
        "painting of the thylacine, an animal that has not existed on the "
        "mainland for more than 2,000 years."),
"alice-springs": dict(
    name="Alice Springs", slug="Alice_Springs", country="Australia",
    region="Northern Territory", type="desert", tag="famous", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Todd River", "Todd_River"),
                ("Anzac Hill", "Alice_Springs"),
                ("Alice Springs Telegraph Station",
                 "Alice_Springs_Telegraph_Station"),
                ("West MacDonnell Ranges", "MacDonnell_Ranges"),
                ("Larapinta Trail", "Larapinta_Trail")],
    blurb="The town in the exact middle of the continent, in a gap in the "
          "MacDonnell Ranges, founded as a repeater station on the Overland "
          "Telegraph line that first connected Australia to the world.",
    fact="The Henley-on-Todd Regatta is run in the bed of a river that is "
         "almost always dry — competitors carry bottomless boats and run.",
    tip="Drive west along Namatjira Drive to Ormiston Gorge and swim in the "
        "permanent waterhole; it is deep, meltingly cold, and rimmed by "
        "500 m walls of red quartzite."),
"kata-tjuta": dict(
    name="Kata Tjuta", slug="Kata_Tjuta", country="Australia",
    region="Northern Territory", type="desert", tag="famous", emoji="🪨",
    sounds=["desert-wind.mp3"],
    highlights=[("Valley of the Winds", "Kata_Tjuta"),
                ("Uluru-Kata Tjuta National Park",
                 "Uluru-Kata_Tjuta_National_Park"),
                ("Walpa Gorge", "Kata_Tjuta")],
    blurb="Thirty-six domes of conglomerate rock rising out of the desert "
          "40 km west of Uluru, the tallest of them 546 m above the plain — "
          "almost 200 m higher than Uluru itself.",
    fact="Kata Tjuta means many heads in Pitjantjatjara; the rock is a "
         "cemented jumble of boulders and cobbles, quite different from "
         "Uluru's single slab of sandstone.",
    tip="Start the Valley of the Winds walk at first light and go to the "
        "second lookout — between the domes the wind funnels hard enough to "
        "hear, which is exactly what Walpa means."),
"kings-canyon-nt": dict(
    name="Kings Canyon", slug="Kings_Canyon_(Northern_Territory)",
    country="Australia", search_name="Kings Canyon Watarrka Northern Territory",
    region="Northern Territory", type="desert", tag="hidden", emoji="🧗",
    sounds=["desert-wind.mp3"],
    highlights=[("Watarrka National Park", "Watarrka_National_Park"),
                ("Garden of Eden", "Kings_Canyon_(Northern_Territory)"),
                ("Mereenie Loop", "")],
    blurb="A sandstone gorge in Watarrka National Park with sheer 100 m walls "
          "and a rim of weathered domes, hiding a permanent waterhole and a "
          "stand of prehistoric cycads in a side canyon.",
    fact="The cycads in the Garden of Eden are relicts of a wetter Australia "
         "and can live more than a thousand years — a rainforest remnant "
         "surviving in the middle of a desert.",
    tip="Do the rim walk clockwise so the steep climb comes first while it is "
        "cool, then descend the wooden stairs into the Garden of Eden and "
        "swim before the tour buses arrive."),
"nitmiluk-national-park": dict(
    name="Nitmiluk Gorge", slug="Nitmiluk_National_Park",
    country="Australia", region="Northern Territory", type="nature",
    tag="hidden", emoji="🛶",
    sounds=["wilderness.mp3"],
    highlights=[("Katherine River", "Katherine_River"),
                ("Katherine", "Katherine,_Northern_Territory"),
                ("Edith Falls", "Nitmiluk_National_Park"),
                ("Jatbula Trail", "Jatbula_Trail")],
    blurb="Thirteen sandstone gorges cut in sequence by the Katherine River, "
          "owned by the Jawoyn people and separated by rapids you have to "
          "carry a canoe over to reach the next one.",
    fact="Nitmiluk means place of the cicada dreaming — and in the wet season "
         "the river rises so far that the gorge walls flood to a level you "
         "can see marked on the rock.",
    tip="Hire a canoe rather than take the cruise, and paddle to the third "
        "gorge in the early morning while the water is glass and freshwater "
        "crocodiles are basking on the ledges."),
"litchfield-national-park": dict(
    name="Litchfield National Park", slug="Litchfield_National_Park",
    country="Australia", region="Northern Territory", type="nature",
    tag="hidden", emoji="💦",
    sounds=["waterfall.mp3"],
    highlights=[("Wangi Falls", "Litchfield_National_Park"),
                ("Florence Falls", "Litchfield_National_Park"),
                ("Magnetic termite mounds", "Amitermes_meridionalis"),
                ("Tolmer Falls", "Litchfield_National_Park")],
    blurb="A sandstone plateau ninety minutes south of Darwin whose edges leak "
          "waterfalls all year, dropping into plunge pools that — unlike most "
          "of the Top End — are safe to swim in.",
    fact="Litchfield's magnetic termite mounds are all aligned north-south "
         "like a field of gravestones, a two-metre-tall solution to keeping "
         "an internal temperature steady in the tropics.",
    tip="Swim at Buley Rockhole rather than the main falls — a staircase of "
        "small cascades and rock bowls where you can pick a pool at your own "
        "temperature and depth."),
"katherine": dict(
    name="Katherine", slug="Katherine,_Northern_Territory",
    country="Australia", region="Northern Territory", type="city",
    tag="hidden", emoji="🌾",
    sounds=["wilderness.mp3"],
    highlights=[("Katherine Hot Springs", "Katherine,_Northern_Territory"),
                ("Cutta Cutta Caves Nature Park",
                 "Cutta_Cutta_Caves_Nature_Park"),
                ("Katherine River", "Katherine_River")],
    blurb="The Territory's fourth-largest town and the crossroads where the "
          "Stuart Highway meets the road to Western Australia — the last "
          "place with a supermarket for a very long way in three directions.",
    fact="Katherine sits on the line where the tropical Top End gives way to "
         "the arid centre; locals say it's where the outback starts.",
    tip="Slip into the Katherine Hot Springs at dawn — a chain of thermal "
        "pools under paperbarks right beside town, 30 °C year round and free "
        "to use."),
"tennant-creek": dict(
    name="Devils Marbles", slug="Karlu_Karlu_/_Devils_Marbles_Conservation_Reserve",
    country="Australia", search_name="Devils Marbles Karlu Karlu Northern Territory",
    region="Northern Territory", type="desert", tag="quirky", emoji="🔮",
    sounds=["desert-wind.mp3"],
    highlights=[("Tennant Creek", "Tennant_Creek"),
                ("Stuart Highway", "Stuart_Highway"),
                ("Wycliffe Well", "Wycliffe_Well")],
    blurb="A scatter of enormous rounded granite boulders on a shallow valley "
          "floor beside the Stuart Highway, some balanced on top of each "
          "other, some split cleanly in half as though sawn.",
    fact="The rounding is onion-skin weathering: the granite cooled "
         "underground, cracked into blocks, then shed curved shells layer by "
         "layer once erosion exposed it.",
    tip="Camp on site for one night. At sunrise and sunset the boulders go "
        "the colour of hot coals, and in between there is nothing to do but "
        "watch a sky with no horizon obstruction in any direction."),

# ---------------- Australia — external territories ----------------
"christmas-island": dict(
    name="Christmas Island", slug="Christmas_Island", country="Australia",
    region="Christmas Island", type="island", tag="quirky", emoji="🦀",
    sounds=["wilderness.mp3"],
    highlights=[("Flying Fish Cove", "Flying_Fish_Cove"),
                ("Christmas Island National Park",
                 "Christmas_Island_National_Park"),
                ("Dales", "Christmas_Island_National_Park")],
    blurb="An Australian territory 350 km south of Java, a limestone plateau "
          "of rainforest ringed by cliffs, where two-thirds of the island is "
          "national park and the population is Chinese, Malay and European in "
          "roughly equal parts.",
    fact="Every year around 50 million red crabs migrate from the forest to "
         "the sea to spawn, and the island closes roads and builds crab "
         "bridges to let them pass.",
    tip="Time a visit to the first rains of the wet season, usually October "
        "or November, when the migration starts — the forest floor and then "
        "whole roads turn solid red and moving."),
"norfolk-island": dict(
    name="Norfolk Island", slug="Norfolk_Island", country="Norfolk Island",
    region="Norfolk Island", type="island", tag="hidden", emoji="🌲",
    sounds=["ocean-waves.mp3"],
    highlights=[("Kingston and Arthur's Vale Historic Area",
                 "Kingston_and_Arthur's_Vale_Historic_Area"),
                ("Norfolk Island National Park",
                 "Norfolk_Island_National_Park"),
                ("Mount Pitt", "Mount_Pitt")],
    blurb="A small volcanic island in the Tasman Sea, settled first by "
          "Polynesians, then twice as a British penal station, and finally in "
          "1856 by the entire population of Pitcairn — descendants of the "
          "Bounty mutineers, who still make up much of the island.",
    fact="Norfolk has its own language, Norf'k, a blend of 18th-century "
         "seafaring English and Tahitian carried here from Pitcairn, and it "
         "is taught in the island's school.",
    tip="Walk the Kingston foreshore at low tide, where Georgian convict "
        "buildings, a Polynesian archaeological site and the Bounty "
        "descendants' cemetery sit within a few hundred metres of each "
        "other."),
# ---------------- New Zealand — South Island ----------------
"christchurch": dict(
    name="Christchurch", slug="Christchurch", country="New Zealand",
    search_name="Christchurch New Zealand", region="Canterbury",
    type="city", tag="famous", emoji="🌷",
    sounds=["city-hum.mp3"],
    highlights=[("Christchurch Botanic Gardens",
                 "Christchurch_Botanic_Gardens"),
                ("Christchurch Cathedral", "ChristChurch_Cathedral,_Christchurch"),
                ("Hagley Park", "Hagley_Park,_Christchurch"),
                ("Avon River", "Avon_River_/_Ōtākaro"),
                ("Christchurch Tram", "Christchurch_tramway_system")],
    blurb="The largest city in the South Island, laid out in 1850 as an "
          "Anglican colony and rebuilt from the ground up after the "
          "earthquakes of 2010 and 2011 — a city of Gothic stone and new "
          "architecture standing side by side.",
    fact="The transitional Cardboard Cathedral, built after the quake, is "
         "held up by 98 cardboard tubes and was designed to last 50 years.",
    tip="Punt the Avon through Hagley Park in autumn, when the English oaks "
        "planted by the first settlers turn and the riverbanks go gold for "
        "about three weeks."),
"dunedin": dict(
    name="Dunedin", slug="Dunedin", country="New Zealand",
    search_name="Dunedin New Zealand", region="Otago",
    type="city", tag="hidden", emoji="🏰",
    sounds=["ocean-waves.mp3"],
    highlights=[("Dunedin Railway Station", "Dunedin_railway_station"),
                ("Larnach Castle", "Larnach_Castle"),
                ("Otago Peninsula", "Otago_Peninsula"),
                ("Baldwin Street", "Baldwin_Street"),
                ("University of Otago", "University_of_Otago")],
    blurb="A Scottish city at the head of a long harbour — Dunedin is Gaelic "
          "for Edinburgh — that was New Zealand's richest and largest during "
          "the 1860s gold rush, which is why it has the country's grandest "
          "Victorian buildings and its oldest university.",
    fact="The Otago Peninsula holds the only mainland breeding colony of "
         "royal albatross in the world; the birds have a three-metre "
         "wingspan and glide in over the harbour heads.",
    tip="Walk up Baldwin Street, briefly the world's steepest street at a "
        "1-in-2.86 grade, then go out to Sandfly Bay at dusk for yellow-eyed "
        "penguins coming ashore through the dunes."),
"aoraki-mount-cook": dict(
    name="Aoraki / Mount Cook", slug="Aoraki_/_Mount_Cook",
    country="New Zealand", region="Canterbury", type="mountain",
    tag="famous", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Aoraki / Mount Cook National Park",
                 "Aoraki_/_Mount_Cook_National_Park"),
                ("Tasman Glacier", "Tasman_Glacier"),
                ("Hooker Valley Track", "Hooker_Valley_Track"),
                ("Mount Cook Village", "Mount_Cook_Village")],
    blurb="New Zealand's highest mountain at 3,724 m, standing over a valley "
          "of glacial rivers and terminal lakes. Nineteen of the country's "
          "twenty-odd 3,000 m peaks are in the park around it.",
    fact="Aoraki lost about ten metres of height in 1991 when a rock and ice "
         "avalanche took the top off the summit — and has since lost more as "
         "the ice cap settles.",
    tip="Walk the Hooker Valley Track in the last two hours of daylight; it "
        "crosses three swing bridges and ends at a lake with icebergs in it, "
        "and the whole return trip fits before dark in summer."),
"lake-tekapo": dict(
    name="Lake Tekapo", slug="Lake_Tekapo", country="New Zealand",
    region="Canterbury", type="nature", tag="famous", emoji="🌌",
    sounds=["mountain-wind.mp3"],
    highlights=[("Church of the Good Shepherd",
                 "Church_of_the_Good_Shepherd,_Lake_Tekapo"),
                ("Mount John Observatory", "Mount_John_University_Observatory"),
                ("Aoraki Mackenzie International Dark Sky Reserve",
                 "Aoraki_Mackenzie_International_Dark_Sky_Reserve"),
                ("Mackenzie Basin", "Mackenzie_Basin")],
    blurb="A turquoise glacial lake in the high Mackenzie Country, its colour "
          "from rock flour ground fine by glaciers and held in suspension. In "
          "November the lupins along the shore flower in sheets of purple and "
          "pink.",
    fact="The lake sits inside the Aoraki Mackenzie Dark Sky Reserve, where "
          "outdoor lighting has been regulated since 1981 — one of the "
          "darkest accessible skies in the southern hemisphere.",
    tip="Go up Mount John after midnight in winter: the Magellanic Clouds and "
        "the galactic core are directly overhead, and the observatory runs "
        "tours that put you on the telescope."),
"wanaka": dict(
    name="Wanaka", slug="Wanaka", country="New Zealand",
    region="Otago", type="nature", tag="hidden", emoji="🌳",
    sounds=["mountain-wind.mp3"],
    highlights=[("Lake Wanaka", "Lake_Wanaka"),
                ("Roys Peak", "Roys_Peak"),
                ("Mount Aspiring National Park",
                 "Mount_Aspiring_National_Park"),
                ("Rob Roy Glacier", "Rob_Roy_Glacier")],
    blurb="A lakeside town an hour over the hill from Queenstown, with the "
          "same alpine scenery and about a third of the noise. Mount Aspiring "
          "National Park begins at the far end of the lake.",
    fact="#ThatWanakaTree — a lone crack willow growing out of the lake — "
         "started as a fence post that took root, and now has its own "
         "protective bylaw.",
    tip="Climb Roys Peak for sunrise; it's a relentless 1,200 m of zigzag "
        "farm track, and the famous ridge viewpoint is 45 minutes below the "
        "summit, so most people photograph it and turn around."),
"kaikoura": dict(
    name="Kaikōura", slug="Kaikōura", country="New Zealand",
    region="Canterbury", type="coastal", tag="famous", emoji="🐳",
    sounds=["ocean-waves.mp3"],
    highlights=[("Kaikōura Ranges", "Kaikōura_Ranges"),
                ("Ōhau Point", "Ōhau_Point"),
                ("Kaikōura Peninsula", "Kaikōura_Peninsula")],
    blurb="A town where 2,600 m mountains come down almost to the beach and "
          "the seafloor drops into a kilometre-deep submarine canyon just off "
          "the coast — which puts deep-ocean feeding grounds within twenty "
          "minutes of the wharf.",
    fact="Sperm whales are resident here year round, an unusual thing "
         "anywhere, because the Kaikōura Canyon funnels cold nutrient-rich "
         "water straight up against the continental shelf.",
    tip="Swim with dusky dolphins rather than watching them — pods of several "
        "hundred, and they stay only as long as you keep making noise and "
        "diving, so the encounter is genuinely on their terms."),
"franz-josef-glacier": dict(
    name="Franz Josef Glacier", slug="Franz_Josef_Glacier",
    country="New Zealand", region="West Coast", type="mountain",
    tag="famous", emoji="🧊",
    sounds=["mountain-wind.mp3"],
    highlights=[("Westland Tai Poutini National Park",
                 "Westland_Tai_Poutini_National_Park"),
                ("Fox Glacier", "Fox_Glacier"),
                ("Lake Matheson", "Lake_Matheson")],
    blurb="A glacier that flows out of the Southern Alps and ends in temperate "
          "rainforest 300 m above sea level — one of very few in the world "
          "that descends into a forest of tree ferns.",
    fact="Franz Josef advances and retreats unusually fast because the "
         "West Coast dumps up to 12 m of snow a year on its neve — in the "
         "1980s it advanced a metre a day.",
    tip="Drive twenty minutes south to Lake Matheson at dawn and walk the "
        "loop; on a still morning it reflects both Aoraki and Mount Tasman, "
        "the two highest peaks in the country, in one frame."),
"abel-tasman-national-park": dict(
    name="Abel Tasman National Park", slug="Abel_Tasman_National_Park",
    country="New Zealand", region="Tasman", type="coastal", tag="famous",
    emoji="🛶",
    sounds=["ocean-waves.mp3"],
    highlights=[("Abel Tasman Coast Track", "Abel_Tasman_Coast_Track"),
                ("Tonga Island Marine Reserve",
                 "Tonga_Island_Marine_Reserve"),
                ("Tōtaranui", "Tōtaranui")],
    blurb="New Zealand's smallest national park and its sunniest, a string of "
          "golden granite beaches and tidal estuaries linked by a 60 km coast "
          "track along the top of the South Island.",
    fact="Two crossings on the coast track are tidal and can only be walked "
         "within a couple of hours of low water — the timetable, not the "
         "distance, decides where you sleep.",
    tip="Kayak out and camp at Bark Bay, then walk back; the water taxis let "
        "you do one leg by boat, and the seal colony at Tonga Island is only "
        "approachable from the water."),
"marlborough-sounds": dict(
    name="Marlborough Sounds", slug="Marlborough_Sounds",
    country="New Zealand", region="Marlborough", type="coastal",
    tag="hidden", emoji="⛵",
    sounds=["ocean-waves.mp3"],
    highlights=[("Queen Charlotte Track", "Queen_Charlotte_Track"),
                ("Picton", "Picton,_New_Zealand"),
                ("Ship Cove", "Ship_Cove,_New_Zealand"),
                ("Blenheim", "Blenheim,_New_Zealand")],
    blurb="A drowned river system at the top of the South Island where the sea "
          "has flooded the valleys, leaving 1,500 km of coastline in a region "
          "you could drive across in an hour if the roads went straight.",
    fact="Ship Cove was James Cook's favourite anchorage in the Pacific; he "
         "returned five times, and it is where he released pigs that gave New "
         "Zealand its wild 'Captain Cookers'.",
    tip="Ride the mail boat out of Picton, which spends a full day delivering "
        "post to houses with no road access — the only way to see the inner "
        "sounds the way the people who live there do."),
"punakaiki": dict(
    name="Pancake Rocks", slug="Punakaiki", country="New Zealand",
    search_name="Punakaiki Pancake Rocks West Coast New Zealand",
    region="West Coast", type="coastal", tag="quirky", emoji="🥞",
    sounds=["ocean-waves.mp3"],
    highlights=[("Paparoa National Park", "Paparoa_National_Park"),
                ("Paparoa Track", "Paparoa_Track"),
                ("Greymouth", "Greymouth")],
    blurb="Limestone stacks on the wild West Coast eroded into what look "
          "exactly like piles of pancakes, with blowholes underneath that "
          "fire spray thirty metres up when a westerly swell is running.",
    fact="Nobody has fully explained the layering — the alternating hard and "
         "soft bands formed 30 million years ago on the seabed by a process "
         "geologists still call, honestly, poorly understood.",
    tip="Come at high tide with an onshore wind. At any other time it is a "
        "pleasant rock formation; in those conditions the ground shakes and "
        "the surge roars up through the chimneys."),
"arthurs-pass": dict(
    name="Arthur's Pass", slug="Arthur's_Pass_National_Park",
    country="New Zealand", region="Canterbury", type="mountain",
    tag="hidden", emoji="🚂",
    sounds=["mountain-wind.mp3"],
    highlights=[("TranzAlpine", "TranzAlpine"),
                ("Ōtira Viaduct", "Otira_Viaduct"),
                ("Devils Punchbowl Falls", "Arthur's_Pass_National_Park"),
                ("Kura Tawhiti / Castle Hill", "Castle_Hill,_New_Zealand")],
    blurb="The highest road crossing of the Southern Alps, where beech forest "
          "on the wet western side gives way to tussock and braided rivers in "
          "the space of a few kilometres.",
    fact="The kea that patrol the car parks here are the world's only alpine "
         "parrot, intelligent enough to solve multi-step puzzles and "
         "destructive enough to strip the rubber from a windscreen.",
    tip="Take the TranzAlpine train from Christchurch instead of driving; the "
        "open-air viewing carriage goes through the Ōtira Tunnel and along "
        "the Waimakariri gorges the road never touches."),
"the-catlins": dict(
    name="The Catlins", slug="The_Catlins", country="New Zealand",
    region="Southland", type="coastal", tag="hidden", emoji="🦭",
    sounds=["ocean-waves.mp3"],
    highlights=[("Nugget Point", "Nugget_Point"),
                ("Purakaunui Falls", "Purakaunui_Falls"),
                ("Curio Bay", "Curio_Bay"),
                ("Cathedral Caves", "Cathedral_Caves")],
    blurb="A rough, empty stretch of coast between Dunedin and Invercargill, "
          "with podocarp forest running down to cliffs, waterfalls in every "
          "second valley, and more sea lions than people.",
    fact="At Curio Bay a 180-million-year-old Jurassic forest lies fossilised "
          "in the wave platform — petrified stumps still rooted where they "
          "grew, exposed only at low tide.",
    tip="Walk the Nugget Point track at first light, then time Cathedral "
        "Caves for the two hours around low water — they are 30 m high and "
        "flood completely at any other time."),
"stewart-island": dict(
    name="Stewart Island", slug="Stewart_Island", country="New Zealand",
    region="Southland", type="island", tag="hidden", emoji="🥝",
    sounds=["wilderness.mp3"],
    highlights=[("Rakiura National Park", "Rakiura_National_Park"),
                ("Oban", "Oban,_New_Zealand"),
                ("Ulva Island", "Ulva_Island_(New_Zealand)"),
                ("Rakiura Track", "Rakiura_Track")],
    blurb="New Zealand's third main island, 30 km south of the mainland, "
          "with 400 residents, 20 km of road and 85% of its area in national "
          "park. Its Māori name, Rakiura, means glowing skies.",
    fact="Stewart Island is one of the few places where wild kiwi are "
         "regularly seen in daylight — the local subspecies forages on "
         "beaches in the afternoon.",
    tip="Take the water taxi to Ulva Island, a predator-free open sanctuary "
        "where saddleback, kākā and rifleman come within arm's reach because "
        "nothing there has ever hunted them."),
"akaroa": dict(
    name="Akaroa", slug="Akaroa", country="New Zealand",
    region="Canterbury", type="coastal", tag="hidden", emoji="🇫🇷",
    sounds=["ocean-waves.mp3"],
    highlights=[("Banks Peninsula", "Banks_Peninsula"),
                ("Akaroa Harbour", "Akaroa_Harbour"),
                ("Hector's dolphin", "Hector's_dolphin")],
    blurb="A harbour town in the flooded crater of an extinct volcano on Banks "
          "Peninsula, settled by French colonists in 1840 — the street names "
          "are still rue this and rue that.",
    fact="The French settlers arrived a few days after Britain claimed the "
         "South Island; had the weather been kinder, the South Island's "
         "history might have run in French.",
    tip="Go out on the harbour for Hector's dolphins — the world's smallest "
        "marine dolphin, found nowhere but New Zealand, and only about 1.4 m "
        "long with a rounded fin like a Mickey Mouse ear."),
"nelson": dict(
    name="Nelson", slug="Nelson,_New_Zealand", country="New Zealand",
    search_name="Nelson New Zealand city", region="Tasman", type="city",
    tag="hidden", emoji="🎨",
    sounds=["ocean-waves.mp3"],
    highlights=[("Christ Church Cathedral, Nelson",
                 "Christ_Church_Cathedral,_Nelson"),
                ("Boulder Bank", "Boulder_Bank"),
                ("Tahunanui", "Tahunanui"),
                ("Kahurangi National Park", "Kahurangi_National_Park")],
    blurb="New Zealand's sunniest city, at the top of the South Island, with "
          "three national parks within reach and a craft-and-art scene out of "
          "proportion to its 50,000 people.",
    fact="A surveyor's calculation puts the geographic centre of New Zealand "
         "on a hill above the town — the marker is a 20-minute walk from the "
         "botanical gardens.",
    tip="Drive the Takaka Hill to Golden Bay and swim at Te Waikoropupū "
        "Springs — some of the clearest fresh water ever measured, with "
        "horizontal visibility of 63 m."),
"doubtful-sound": dict(
    name="Doubtful Sound", slug="Doubtful_Sound_/_Patea",
    country="New Zealand", region="Fiordland", type="nature", tag="hidden",
    emoji="🌫️",
    sounds=["waterfall.mp3"],
    highlights=[("Fiordland National Park", "Fiordland_National_Park"),
                ("Lake Manapouri", "Lake_Manapouri"),
                ("Manapouri Power Station", "Manapouri_Power_Station")],
    blurb="Milford's bigger, quieter neighbour: three times longer, ten times "
          "the surface area, and reachable only by crossing a lake and then a "
          "mountain pass by road, which keeps the crowds off it.",
    fact="Cook named it Doubtful Harbour because he doubted he could sail "
         "back out again if he sailed in — the wind funnels one way down the "
         "fiord.",
    tip="Take an overnight cruise and ask the skipper for the sound of "
        "silence: engines off, generators off, no one speaking, in a fiord "
        "with 1,500 m walls and nothing but waterfalls."),
# ---------------- New Zealand — North Island ----------------
"tongariro-national-park": dict(
    name="Tongariro National Park", slug="Tongariro_National_Park",
    country="New Zealand", region="Manawatū-Whanganui", type="mountain",
    tag="famous", emoji="🌋",
    sounds=["mountain-wind.mp3"],
    highlights=[("Tongariro Alpine Crossing",
                 "Tongariro_Alpine_Crossing"),
                ("Mount Ngauruhoe", "Mount_Ngauruhoe"),
                ("Mount Ruapehu", "Mount_Ruapehu"),
                ("Mount Tongariro", "Mount_Tongariro"),
                ("Whakapapa", "Whakapapa_skifield")],
    blurb="Three active volcanoes on the central plateau of the North Island, "
          "gifted to the nation by Ngāti Tūwharetoa in 1887 to protect them — "
          "which made this the fourth national park established anywhere in "
          "the world.",
    fact="Tongariro is one of only a few places with dual World Heritage "
         "status, listed for its landscape and for its meaning to Māori, who "
         "regard the peaks as ancestors.",
    tip="Walk the Alpine Crossing east to west and start before dawn; you "
        "reach the Emerald Lakes — bright green from dissolved minerals, "
        "steaming from vents — before the day's crowd catches up."),
"lake-taupo": dict(
    name="Lake Taupō", slug="Lake_Taupō", country="New Zealand",
    region="Waikato", type="nature", tag="famous", emoji="🎣",
    sounds=["ocean-waves.mp3"],
    highlights=[("Taupō", "Taupō"),
                ("Huka Falls", "Huka_Falls"),
                ("Craters of the Moon", "Craters_of_the_Moon_(geothermal_site)"),
                ("Waikato River", "Waikato_River")],
    blurb="New Zealand's largest lake, the size of Singapore, sitting in the "
          "caldera of a supervolcano. The country's biggest river drains out "
          "of one corner and immediately squeezes into a 15 m gorge.",
    fact="The Taupō eruption of around 232 AD was the most violent on Earth "
         "in the last 5,000 years — Roman and Chinese chroniclers both "
         "recorded red skies that year.",
    tip="Walk the Huka Falls path upstream at first light: 220,000 litres a "
        "second forced through a channel narrow enough to jump, in water so "
        "aerated it is the colour of blue milk."),
"waitomo-caves": dict(
    name="Waitomo Caves", slug="Waitomo_Glowworm_Caves",
    country="New Zealand", region="Waikato", type="nature", tag="famous",
    emoji="✨",
    sounds=["waterfall.mp3"],
    highlights=[("Waitomo", "Waitomo"),
                ("Ruakuri Cave", "Ruakuri_Cave"),
                ("Marokopa Falls", "Marokopa_Falls")],
    blurb="A limestone cave system under King Country farmland whose ceilings "
          "are lit blue-green by tens of thousands of glow-worms — the larvae "
          "of a fungus gnat found only in New Zealand.",
    fact="The glow is a lure: each larva hangs sticky fishing lines below "
         "itself and the brighter it shines, the hungrier it is.",
    tip="Do the black-water rafting trip rather than the boat tour — you jump "
        "backwards down an underground waterfall in a wetsuit and float the "
        "rest on an inner tube with your headlamp off."),
"bay-of-islands": dict(
    name="Bay of Islands", slug="Bay_of_Islands", country="New Zealand",
    region="Northland", type="coastal", tag="famous", emoji="⛵",
    sounds=["ocean-waves.mp3"],
    highlights=[("Waitangi Treaty Grounds", "Waitangi_Treaty_Grounds"),
                ("Russell", "Russell,_New_Zealand"),
                ("Paihia", "Paihia"),
                ("Cape Brett", "Cape_Brett"),
                ("Kerikeri", "Kerikeri")],
    blurb="A subtropical bay in the far north scattered with 144 islands, and "
          "the cradle of modern New Zealand — the Treaty of Waitangi was "
          "signed on the lawn above the water here in 1840.",
    fact="Russell, the sleepy village across the water, was New Zealand's "
         "first European settlement and had such a reputation among whalers "
         "that it was known as the hell hole of the Pacific.",
    tip="Sail out to the Hole in the Rock at Cape Brett — a passage worn "
        "clean through a rock island that a boat can only pass through when "
        "the swell is small enough."),
"coromandel-peninsula": dict(
    name="Coromandel Peninsula", slug="Coromandel_Peninsula",
    country="New Zealand", region="Waikato", type="coastal", tag="famous",
    emoji="🏖️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cathedral Cove", "Cathedral_Cove"),
                ("Hot Water Beach", "Hot_Water_Beach"),
                ("Coromandel", "Coromandel,_New_Zealand"),
                ("Driving Creek Railway", "Driving_Creek_Railway")],
    blurb="A mountainous finger of land two hours from Auckland, with kauri "
          "forest along its spine, old gold workings in the hills and a "
          "coastline of pōhutukawa trees leaning over white sand.",
    fact="At Hot Water Beach, geothermal water rises through the sand — for "
         "two hours either side of low tide you can dig your own hot pool on "
         "the beach and sit in it.",
    tip="Bring a spade to Hot Water Beach, and be there at the right tide: "
        "the spring is only exposed in a patch a few metres wide, and at any "
        "other hour the sea is over it."),
"rotorua-wai-o-tapu": dict(
    name="Wai-O-Tapu", slug="Wai-O-Tapu", country="New Zealand",
    search_name="Wai-O-Tapu thermal wonderland Rotorua",
    region="Bay of Plenty", type="nature", tag="quirky", emoji="🧪",
    sounds=["waterfall.mp3"],
    highlights=[("Lady Knox Geyser", "Wai-O-Tapu"),
                ("Champagne Pool", "Champagne_Pool"),
                ("Taupō Volcanic Zone", "Taupō_Volcanic_Zone")],
    blurb="A geothermal field south of Rotorua where collapsed craters, "
          "sinter terraces and mineral pools come in colours — orange, "
          "green, sulphur yellow — that look artificially saturated and are "
          "not.",
    fact="The Champagne Pool is 65 m across and 62 m deep, holds water at "
         "74 °C, and its orange rim is arsenic and antimony sulphides "
         "precipitating out of solution.",
    tip="Walk the far loop to the Devil's Bath, a crater lake of an "
        "unnatural lime green that changes shade week to week with the "
        "amount of suspended sulphur in it."),
"napier": dict(
    name="Napier", slug="Napier,_New_Zealand", country="New Zealand",
    search_name="Napier New Zealand art deco", region="Hawke's Bay",
    type="city", tag="quirky", emoji="🏛️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Marine Parade", "Marine_Parade,_Napier"),
                ("Napier Hill", "Napier_Hill"),
                ("Cape Kidnappers", "Cape_Kidnappers"),
                ("Hawke's Bay", "Hawke's_Bay_Region")],
    blurb="A city levelled by an earthquake in 1931 and rebuilt in three "
          "years flat, entirely in the style of the moment — which is why it "
          "is now one of the most complete Art Deco townscapes on Earth.",
    fact="The same 1931 quake lifted 40 km² of seabed out of the harbour; "
         "Napier's airport stands on ground that was underwater before the "
         "shaking started.",
    tip="Drive out to Cape Kidnappers for the world's largest mainland "
        "gannet colony — thousands of birds nesting an arm's length apart on "
        "a cliff edge, reachable along the beach at low tide."),
"mount-taranaki": dict(
    name="Mount Taranaki", slug="Mount_Taranaki", country="New Zealand",
    region="Taranaki", type="mountain", tag="hidden", emoji="🗻",
    sounds=["mountain-wind.mp3"],
    highlights=[("Egmont National Park", "Egmont_National_Park"),
                ("New Plymouth", "New_Plymouth"),
                ("Pouakai Tarns", "Pouakai_Range"),
                ("Dawson Falls", "Dawson_Falls")],
    blurb="An almost perfectly symmetrical 2,518 m stratovolcano standing "
          "alone on the west coast of the North Island, with a circle of "
          "protected rainforest around it visible from space as a green disc "
          "in green farmland.",
    fact="In 2023 Taranaki was granted legal personhood under New Zealand "
         "law — the mountain is now a legal entity with its own rights and "
         "guardians.",
    tip="Hike to the Pouakai Tarns and be there at dawn: on a windless "
        "morning a tarn barely bigger than a swimming pool reflects the whole "
        "cone."),
"cape-reinga": dict(
    name="Cape Reinga", slug="Cape_Reinga", country="New Zealand",
    region="Northland", type="coastal", tag="hidden", emoji="🧭",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cape Reinga Lighthouse", "Cape_Reinga_Lighthouse"),
                ("Ninety Mile Beach", "Ninety_Mile_Beach,_New_Zealand"),
                ("Te Paki Sand Dunes", "Te_Paki_Sand_Dunes")],
    blurb="The far northwestern tip of New Zealand, where the Tasman Sea and "
          "the Pacific Ocean collide in a visible line of standing waves off "
          "the point.",
    fact="In Māori belief this is where the spirits of the dead depart, "
         "climbing down the roots of an 800-year-old pōhutukawa on the "
         "headland to begin the journey to Hawaiki.",
    tip="Stop at the Te Paki stream on the way and toboggan the giant sand "
        "dunes — they run 150 m down to a stream you can drive along to reach "
        "Ninety Mile Beach."),
"piha": dict(
    name="Piha", slug="Piha", country="New Zealand",
    region="Auckland", type="coastal", tag="hidden", emoji="🏄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Lion Rock", "Lion_Rock_(New_Zealand)"),
                ("Waitākere Ranges", "Waitākere_Ranges"),
                ("Karekare", "Karekare")],
    blurb="A black-sand surf beach 40 minutes west of Auckland, backed by the "
          "rainforest of the Waitākere Ranges and split by a volcanic plug "
          "the locals climb at sunset.",
    fact="The sand is black because it is iron-rich titanomagnetite eroded "
         "from Taranaki's volcanoes and carried up the coast — on a hot day "
         "it is genuinely too hot to stand on.",
    tip="Walk the Kitekite Falls track behind the village in the morning, "
        "then swim between the flags — Piha's rips are strong enough that the "
        "local surf club had its own television series."),
"hobbiton": dict(
    name="Hobbiton", slug="Hobbiton_Movie_Set", country="New Zealand",
    region="Waikato", type="city", tag="quirky", emoji="🍄",
    sounds=["wilderness.mp3"],
    highlights=[("Matamata", "Matamata"),
                ("Waikato", "Waikato")],
    blurb="Forty-four hobbit holes built into a sheep farm's hillside near "
          "Matamata, rebuilt in permanent materials after the first film and "
          "left standing ever since.",
    fact="The oak above Bag End in the first trilogy was artificial: a dead "
         "tree cut up, trucked in, rebuilt, and hung with 250,000 hand-"
         "painted silk leaves.",
    tip="Book the evening banquet tour, which keeps you on set after the day "
        "groups leave, and you walk back through the lanes with the windows "
        "of every hole lit."),
"whanganui-river": dict(
    name="Whanganui River", slug="Whanganui_River", country="New Zealand",
    region="Manawatū-Whanganui", type="nature", tag="hidden", emoji="🛶",
    sounds=["waterfall.mp3"],
    highlights=[("Whanganui National Park", "Whanganui_National_Park"),
                ("Bridge to Nowhere", "Bridge_to_Nowhere_(New_Zealand)"),
                ("Whanganui", "Whanganui")],
    blurb="The longest navigable river in New Zealand, running 290 km through "
          "gorges and bush from the volcanic plateau to the sea, once the "
          "main highway into the interior.",
    fact="In 2017 the Whanganui became the first river in the world granted "
         "legal personhood, with two guardians appointed to speak for it in "
         "court.",
    tip="Paddle the Whanganui Journey — a Great Walk you do in a canoe — and "
        "stop to walk 40 minutes into the bush to the Bridge to Nowhere, a "
        "concrete road bridge in rainforest with no road at either end."),
"tauranga": dict(
    name="Mount Maunganui", slug="Mount_Maunganui", country="New Zealand",
    region="Bay of Plenty", type="coastal", tag="hidden", emoji="🌅",
    sounds=["ocean-waves.mp3"],
    highlights=[("Mauao", "Mauao"),
                ("Tauranga", "Tauranga"),
                ("Matakana Island", "Matakana_Island")],
    blurb="A beach suburb on a sandy isthmus with ocean on one side, harbour "
          "on the other, and a 232 m extinct volcanic cone at the end of it "
          "that half the town walks up before work.",
    fact="Mauao means caught by the dawn — in the local account the hill was "
         "being dragged to the sea by patupaiarehe when the sun rose and "
         "fixed it in place.",
    tip="Climb the summit track for sunrise, then soak in the saltwater hot "
        "pools at the foot of the mount, fed from a bore 600 m down."),
"invercargill": dict(
    name="Bluff", slug="Bluff,_New_Zealand", country="New Zealand",
    search_name="Bluff Southland New Zealand", region="Southland",
    type="coastal", tag="hidden", emoji="🦪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Stirling Point", "Bluff,_New_Zealand"),
                ("Invercargill", "Invercargill"),
                ("Foveaux Strait", "Foveaux_Strait")],
    blurb="The southernmost town on the New Zealand mainland, an oyster port "
          "on a windswept peninsula where State Highway 1 finally runs out at "
          "a signpost pointing to the rest of the world.",
    fact="Bluff oysters are dredged from the wild in Foveaux Strait under a "
         "quota, in a season that opens in March — no farm has ever managed "
         "to reproduce them.",
    tip="Walk the Foveaux Walkway around the headland into the westerly; the "
        "next land in that direction is South America, and the swell arriving "
        "has crossed the whole Southern Ocean to get here."),
"gisborne": dict(
    name="Gisborne", slug="Gisborne,_New_Zealand", country="New Zealand",
    search_name="Gisborne New Zealand", region="Gisborne", type="city",
    tag="hidden", emoji="🌄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Tolaga Bay Wharf", "Tolaga_Bay"),
                ("Kaiti Hill", "Titirangi_(hill)"),
                ("Wainui Beach", "Wainui_Beach")],
    blurb="On the east coast facing the dateline, Gisborne is one of the first "
          "cities in the world to see each sunrise, and the place where Cook "
          "first set foot in New Zealand in 1769.",
    fact="Tolaga Bay's wharf up the coast is 660 m long — built that far out "
         "because the bay is too shallow for ships anywhere nearer the "
         "shore.",
    tip="Drive north up the East Cape road; it is one of the emptiest and "
        "most Māori parts of the country, and the lighthouse at the cape "
        "takes 700 steps to reach."),
# ---------------- Papua New Guinea ----------------
"port-moresby": dict(
    name="Port Moresby", slug="Port_Moresby", country="Papua New Guinea",
    region="National Capital District", type="city", tag="hidden",
    emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Parliament House, Port Moresby",
                 "National_Parliament_of_Papua_New_Guinea"),
                ("Papua New Guinea National Museum and Art Gallery",
                 "Papua_New_Guinea_National_Museum_and_Art_Gallery"),
                ("Ela Beach", "Port_Moresby"),
                ("Varirata National Park", "")],
    blurb="The capital of a country with more than 800 living languages, "
          "spread around a deep natural harbour on the dry southern coast — "
          "unreachable by road from most of the nation it governs.",
    fact="Papua New Guinea has about 12% of the world's languages in 0.1% of "
         "its land area, which is why Tok Pisin, a creole, does the work of "
         "a national tongue.",
    tip="Drive an hour up to Varirata National Park on the Sogeri plateau, "
        "where the escarpment drops away to the coast and Raggiana birds-of-"
        "paradise display in the trees at dawn."),
"mount-hagen": dict(
    name="Mount Hagen", slug="Mount_Hagen", country="Papua New Guinea",
    region="Western Highlands", type="city", tag="hidden", emoji="🪶",
    sounds=["wilderness.mp3"],
    highlights=[("Wahgi Valley", ""),
                ("Kuk Swamp", "Kuk_Early_Agricultural_Site"),
                ("Western Highlands Province", "Western_Highlands_Province")],
    blurb="The main town of the New Guinea highlands at 1,700 m, in a valley "
          "whose existence was unknown to the outside world until Australian "
          "gold prospectors walked into it in 1933 and found a million people "
          "farming there.",
    fact="Kuk Swamp nearby holds evidence of agriculture from 9,000 years "
         "ago — independent invention of farming, on a par with the Fertile "
         "Crescent and completely separate from it.",
    tip="Come for the Mount Hagen Show in August, when scores of clans arrive "
        "in full sing-sing dress — bird-of-paradise plumes, ochre, shell — "
        "for what began as a colonial attempt to stop them fighting."),
"rabaul": dict(
    name="Rabaul", slug="Rabaul", country="Papua New Guinea",
    region="East New Britain", type="city", tag="hidden", emoji="🌋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Tavurvur", "Tavurvur"),
                ("Simpson Harbour", "Simpson_Harbour"),
                ("Kokopo", "Kokopo"),
                ("Rabaul Caldera", "Rabaul_Caldera")],
    blurb="A town sitting inside a flooded volcanic caldera on New Britain, "
          "buried in ash by a twin eruption in 1994 that emptied it "
          "overnight. Much of it was never rebuilt, and one cone is still "
          "steaming across the harbour.",
    fact="Rabaul was Japan's main South Pacific base in 1943, with around "
         "100,000 troops and more than 500 km of tunnels dug into the "
         "volcanic rock beneath the town.",
    tip="Take a boat across Simpson Harbour at first light to the black ash "
        "beach below Tavurvur, and climb the cone — the crater rim is warm "
        "underfoot and vents sulphur while you stand on it."),
"sepik-river": dict(
    name="Sepik River", slug="Sepik", country="Papua New Guinea",
    search_name="Sepik River Papua New Guinea",
    region="East Sepik", type="nature", tag="hidden", emoji="🐊",
    sounds=["wilderness.mp3"],
    highlights=[("Wewak", "Wewak"),
                ("Ambunti", "Ambunti"),
                ("Chambri Lakes", "Chambri_Lakes")],
    blurb="A 1,100 km river running through lowland swamp forest without a "
          "single bridge or dam over its whole length, and the centre of one "
          "of the great carving traditions on Earth.",
    fact="Sepik haus tambaran — spirit houses — can stand 25 m tall with "
         "carved gable faces, and the men of some villages still take "
         "crocodile-skin scarification across the back and shoulders.",
    tip="Travel the middle river by motor canoe village to village; there is "
        "no road and no schedule, and the carvings are sold where they are "
        "made rather than in a gallery in town."),
"kokoda-track": dict(
    name="Kokoda Track", slug="Kokoda_Track", country="Papua New Guinea",
    region="Oro Province", type="mountain", tag="hidden", emoji="🥾",
    sounds=["wilderness.mp3"],
    highlights=[("Owen Stanley Range", "Owen_Stanley_Range"),
                ("Kokoda", "Kokoda,_Papua_New_Guinea"),
                ("Isurava", "Battle_of_Isurava")],
    blurb="A 96 km foot track over the Owen Stanley Range through jungle and "
          "cloud forest, climbing and descending more than 6,000 m in total — "
          "and the site of the 1942 campaign that stopped the Japanese "
          "advance on Port Moresby.",
    fact="The track has been a trade and mail route for far longer than it "
         "has been a battlefield; it was a colonial mail path before the war "
         "and a local route long before that.",
    tip="Walk it south to north with a Koiari or Orokaiva guide from a village "
        "on the route — the fee goes to the communities the track passes "
        "through, and they know where every wartime relic still lies."),
"tari": dict(
    name="Tari", slug="Tari,_Papua_New_Guinea", country="Papua New Guinea",
    search_name="Tari Huli wigmen Papua New Guinea",
    region="Hela Province", type="city", tag="hidden", emoji="🎭",
    sounds=["wilderness.mp3"],
    highlights=[("Hela Province", "Hela_Province"),
                ("Ambua", "Tari,_Papua_New_Guinea")],
    blurb="A highland basin at 1,600 m and the home of the Huli, whose young "
          "men attend wig schools for eighteen months to grow and shape "
          "ceremonial headdresses from their own hair.",
    fact="The Tari valley sits on the flyway of more than a dozen bird-of-"
         "paradise species, including the ribbon-tailed astrapia whose two "
         "tail feathers are three times the length of its body.",
    tip="Stay up at Ambua on the ridge and be on the forest track before "
        "dawn; the display trees are known and used year after year, and the "
        "birds arrive at the same branch at the same hour."),
"trobriand-islands": dict(
    name="Trobriand Islands", slug="Trobriand_Islands",
    country="Papua New Guinea", region="Milne Bay", type="island",
    tag="hidden", emoji="🐚",
    sounds=["ocean-waves.mp3"],
    highlights=[("Kiriwina", "Kiriwina"),
                ("Kula ring", "Kula_ring"),
                ("Milne Bay Province", "Milne_Bay_Province")],
    blurb="A low coral archipelago off the eastern tip of New Guinea, "
          "matrilineal, famous for yam cults and for a ceremonial exchange "
          "network that has circled these seas for centuries.",
    fact="The Kula ring moves shell necklaces clockwise and armbands "
         "counter-clockwise between islands hundreds of kilometres apart; the "
         "objects are never kept, only passed on, and studying it founded "
         "modern anthropological fieldwork.",
    tip="Time a visit for the yam harvest between June and August, when "
        "decorated yam houses are filled in public and the milamala dancing "
        "runs for weeks."),

# ---------------- Solomon Islands ----------------
"honiara": dict(
    name="Honiara", slug="Honiara", country="Solomon Islands",
    region="Guadalcanal", type="city", tag="hidden", emoji="🌺",
    sounds=["ocean-waves.mp3"],
    highlights=[("Guadalcanal", "Guadalcanal"),
                ("Henderson Field", "Honiara_International_Airport"),
                ("Iron Bottom Sound", "Ironbottom_Sound"),
                ("Bonegi Beach", "Guadalcanal")],
    blurb="The capital of the Solomons, built beside the airstrip that half "
          "the Pacific War was fought over. The strait offshore holds so many "
          "sunken warships that sailors renamed it Ironbottom Sound.",
    fact="More than fifty ships and hundreds of aircraft from both sides lie "
         "in the water between Guadalcanal and Savo — several within snorkel "
         "depth of the beach.",
    tip="Swim out from Bonegi Beach to the Hirokawa Maru: a Japanese "
        "transport lying with its bow in three metres of water, coral-covered "
        "and reachable without a boat or a tank."),
"marovo-lagoon": dict(
    name="Marovo Lagoon", slug="Marovo_Lagoon", country="Solomon Islands",
    region="Western Province", type="coastal", tag="hidden", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("New Georgia Islands", "New_Georgia_Islands"),
                ("Vangunu", "Vangunu"),
                ("Gizo", "Gizo")],
    blurb="The largest saltwater lagoon in the world enclosed by a double "
          "barrier reef, 700 km² of flat green water studded with hundreds of "
          "forested islands in the Western Solomons.",
    fact="Marovo's carvers work in kerosene wood and ebony, inlaying shell, "
         "and sell from canoes that paddle out to whatever boat happens to "
         "be anchored in the lagoon.",
    tip="Stay in a village homestay rather than a resort — most of the "
        "lagoon's land is under customary ownership, and the family you stay "
        "with will take you to the reef passes themselves."),
"rennell-island": dict(
    name="Rennell Island", slug="Rennell_Island", country="Solomon Islands",
    region="Rennell and Bellona", type="island", tag="hidden", emoji="🦜",
    sounds=["wilderness.mp3"],
    highlights=[("Lake Tegano", "Lake_Tegano"),
                ("East Rennell", "East_Rennell")],
    blurb="The largest raised coral atoll on Earth, an island of fossil reef "
          "lifted clear of the sea, with the Pacific's biggest insular lake "
          "sitting in what used to be its lagoon.",
    fact="East Rennell is the only World Heritage site inscribed on land "
         "under customary ownership — and the only one whose community can "
         "vote on how it is managed.",
    tip="Canoe on Lake Tegano among its limestone islets; the water is "
        "brackish, the surrounding forest holds birds found nowhere else, and "
        "getting here means a small plane and then a long truck ride."),

# ---------------- Vanuatu ----------------
"port-vila": dict(
    name="Port Vila", slug="Port_Vila", country="Vanuatu",
    region="Efate", type="city", tag="hidden", emoji="🥥",
    sounds=["ocean-waves.mp3"],
    highlights=[("Efate", "Efate"),
                ("Mele Cascades", "Mele,_Vanuatu"),
                ("Iririki", "Iririki"),
                ("National Museum of Vanuatu",
                 "Vanuatu_Cultural_Centre")],
    blurb="Vanuatu's capital, on a harbour on Efate, in a country that was "
          "jointly governed by Britain and France until 1980 — with two "
          "police forces, two school systems and two sets of laws running at "
          "once.",
    fact="Vanuatu has more languages per head than anywhere on Earth: about "
         "110 for 300,000 people, and Bislama, an English-based creole, "
         "bridges them.",
    tip="Ask at the Cultural Centre about sand drawing — a graphic tradition "
        "where a continuous line traced in sand encodes a story or a song, "
        "and lifting the finger spoils it."),
"mount-yasur": dict(
    name="Mount Yasur", slug="Mount_Yasur", country="Vanuatu",
    region="Tanna", type="mountain", tag="famous", emoji="🌋",
    sounds=["mountain-wind.mp3"],
    highlights=[("Tanna Island", "Tanna_Island"),
                ("John Frum", "John_Frum"),
                ("Yakel", "Tanna_Island")],
    blurb="One of the most accessible active volcanoes anywhere — a short "
          "drive and a ten-minute walk puts you on a crater rim above vents "
          "that have been erupting continuously for at least 800 years.",
    fact="Captain Cook navigated to Tanna in 1774 by Yasur's glow, using it "
          "as a lighthouse from far out at sea.",
    tip="Go up at dusk. In daylight it is grey smoke; after dark each "
        "explosion throws incandescent bombs above the rim and you feel the "
        "concussion in your chest before you hear it."),
"espiritu-santo": dict(
    name="Espiritu Santo", slug="Espiritu_Santo", country="Vanuatu",
    region="Sanma", type="island", tag="hidden", emoji="🤿",
    sounds=["ocean-waves.mp3"],
    highlights=[("Luganville", "Luganville"),
                ("SS President Coolidge", "SS_President_Coolidge"),
                ("Champagne Beach", "Champagne_Beach"),
                ("Millennium Cave", "Espiritu_Santo")],
    blurb="Vanuatu's largest island, where blue holes of impossibly clear "
          "fresh water sit in the jungle and a 200 m luxury liner turned "
          "troopship lies on its side just off the town beach.",
    fact="The SS President Coolidge sank in 1942 after striking friendly "
         "mines; it is the largest easily accessible shipwreck in the world, "
         "starting 20 m from shore in diveable depth.",
    tip="Swim in the Nanda Blue Hole — spring-fed fresh water so clear the "
        "bottom at 10 m looks arm's length away, with a rope swing off an "
        "overhanging banyan."),
"pentecost-island": dict(
    name="Pentecost Island", slug="Pentecost_Island", country="Vanuatu",
    region="Penama", type="island", tag="quirky", emoji="🪢",
    sounds=["wilderness.mp3"],
    highlights=[("Land diving", "Land_diving"),
                ("Penama Province", "Penama_Province")],
    blurb="A long narrow island in northern Vanuatu where, every year between "
          "April and June, men jump head-first from wooden towers up to 30 m "
          "tall with vines tied to their ankles.",
    fact="Naghol, the land dive, is the direct ancestor of bungee jumping — "
         "except the vines have no elasticity and the diver's head is meant "
         "to brush the tilled earth.",
    tip="The season is fixed by the yam harvest, not the calendar, so check "
        "before booking flights; the ritual is a fertility rite for the crop "
        "and cannot be staged out of season."),

# ---------------- New Caledonia ----------------
"noumea": dict(
    name="Nouméa", slug="Nouméa", country="New Caledonia",
    region="South Province", type="city", tag="hidden", emoji="🥖",
    sounds=["ocean-waves.mp3"],
    highlights=[("Tjibaou Cultural Centre", "Tjibaou_Cultural_Centre"),
                ("Anse Vata", "Nouméa"),
                ("Amédée Lighthouse", "Amédée_Lighthouse"),
                ("New Caledonia barrier reef",
                 "New_Caledonian_barrier_reef")],
    blurb="A French city in Melanesia, with boulangeries and pétanque courts "
          "on a peninsula inside the world's second-largest barrier reef and "
          "its largest enclosed lagoon.",
    fact="The Tjibaou Cultural Centre's ten curved timber cases, designed by "
         "Renzo Piano, are shaped as unfinished Kanak huts — deliberately "
         "left looking as though still under construction.",
    tip="Take the boat out to Amédée, a 56 m cast-iron lighthouse prefabricated "
        "in Paris in 1865, shipped in pieces and bolted together on a sand "
        "islet in the middle of the lagoon."),
"isle-of-pines": dict(
    name="Isle of Pines", slug="Isle_of_Pines_(New_Caledonia)",
    country="New Caledonia", search_name="Isle of Pines New Caledonia",
    region="Loyalty Islands", type="island", tag="hidden", emoji="🌲",
    sounds=["ocean-waves.mp3"],
    highlights=[("Baie d'Oro", "Isle_of_Pines_(New_Caledonia)"),
                ("Vao", "Isle_of_Pines_(New_Caledonia)"),
                ("Araucaria columnaris", "Araucaria_columnaris")],
    blurb="An island south of the New Caledonian mainland ringed with white "
          "sand and lined with 60 m columnar pines that grow straight as "
          "masts — Cook saw them from the sea and named the place for them.",
    fact="The natural pool at Oro is a shallow lagoon connected to the ocean "
         "only through a gap in the rock, so it fills and empties with the "
         "tide and holds warm, glass-clear water full of fish.",
    tip="Walk in to the piscine naturelle through the pine forest rather than "
        "taking the boat; the path comes out at the far end and you can drift "
        "the length of the pool back to the entrance."),
"ouvea": dict(
    name="Ouvéa", slug="Ouvéa", country="New Caledonia",
    search_name="Ouvéa Loyalty Islands New Caledonia",
    region="Loyalty Islands", type="island", tag="hidden", emoji="🏖️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Loyalty Islands", "Loyalty_Islands"),
                ("Lifou", "Lifou")],
    blurb="A crescent atoll in the Loyalty Islands with a 25 km unbroken "
          "beach along its inner curve — a single strip of white sand facing "
          "a lagoon and backed by coconut palms the whole way.",
    fact="Ouvéa is one of the few places in Melanesia where a Polynesian "
         "language is spoken alongside the local Kanak one, brought by "
         "settlers from Wallis several centuries ago.",
    tip="Cross the Mouli bridge at the southern end and look down before you "
        "swim: reef sharks and rays cruise the channel beneath it in water so "
        "clear the shadow of the bridge is sharp on the sand."),
# ---------------- Fiji ----------------
"suva": dict(
    name="Suva", slug="Suva", country="Fiji",
    region="Viti Levu", type="city", tag="hidden", emoji="🏛️",
    sounds=["city-hum.mp3"],
    highlights=[("Fiji Museum", "Fiji_Museum"),
                ("Thurston Gardens", "Thurston_Gardens"),
                ("University of the South Pacific",
                 "University_of_the_South_Pacific"),
                ("Colo-i-Suva Forest Park", "Colo-i-Suva_Forest_Reserve")],
    blurb="The capital of Fiji and the largest city in the South Pacific "
          "outside Australia and New Zealand — a green, rainy, colonial-era "
          "port on the wet side of Viti Levu, and the region's university "
          "town.",
    fact="The Fiji Museum holds the rudder of the Bounty and a shoe belonging "
         "to Thomas Baker, a missionary eaten in 1867 — the leather having "
         "proved inedible.",
    tip="Escape the heat at Colo-i-Suva, fifteen minutes uphill from the "
        "city, where a chain of forest pools and a rope swing sit under mahogany "
        "planted by the colonial forestry service."),
"nadi": dict(
    name="Nadi", slug="Nadi", country="Fiji",
    region="Viti Levu", type="city", tag="famous", emoji="🌺",
    sounds=["ocean-waves.mp3"],
    highlights=[("Sri Siva Subramaniya Temple",
                 "Sri_Siva_Subramaniya_Temple"),
                ("Sabeto", "Nadi"),
                ("Denarau", "Denarau")],
    blurb="Fiji's gateway on the dry western side of Viti Levu, where nearly "
          "every visitor lands and most immediately leave for the islands — "
          "which is a shame, because the town has the largest Hindu temple in "
          "the southern hemisphere.",
    fact="Nearly 40% of Fiji's population descends from indentured labourers "
         "brought from India between 1879 and 1916, which is why a Dravidian "
         "temple stands at the end of Nadi's main street.",
    tip="Take the back road up to the Sabeto hot springs and mud pools — "
        "you coat yourself in grey mud, dry in the sun, then rinse off in a "
        "series of increasingly hot pools."),
"yasawa-islands": dict(
    name="Yasawa Islands", slug="Yasawa_Islands", country="Fiji",
    region="Western Division", type="island", tag="famous", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Nacula", "Nacula"),
                ("Sawa-i-Lau", ""),
                ("Mamanuca Islands", "Mamanuca_Islands")],
    blurb="A chain of twenty volcanic islands running northwest from Viti "
          "Levu, closed to tourists until 1987 and still reached by a single "
          "daily catamaran that stops island by island.",
    fact="Sawa-i-Lau's limestone caves hold a chamber you reach by diving "
         "under a rock arch and surfacing inside — traditionally the burial "
         "place of a local chiefly line.",
    tip="Ride the Yasawa Flyer one way and stay at village-owned budget "
        "places rather than a resort; the boat is the bus, and you can hop "
        "off wherever the day's weather looks best."),
"mamanuca-islands": dict(
    name="Mamanuca Islands", slug="Mamanuca_Islands", country="Fiji",
    region="Western Division", type="island", tag="famous", emoji="🥥",
    sounds=["ocean-waves.mp3"],
    highlights=[("Monuriki", "Monuriki"),
                ("Malolo Lailai", "Malolo_Lailai"),
                ("Tavarua", "Tavarua")],
    blurb="A ring of twenty small volcanic and coral islands half an hour by "
          "boat from Nadi, some no bigger than a sandbar with a few palms on "
          "them.",
    fact="Monuriki is the uninhabited island where Cast Away was filmed; it "
         "is now managed as a reserve for the Fijian crested iguana, and "
         "landing is limited.",
    tip="Boat out to Cloudbreak on a big southwest swell just to watch — it "
        "breaks over shallow reef five kilometres from any land, with nothing "
        "around it but open ocean."),
"taveuni": dict(
    name="Taveuni", slug="Taveuni", country="Fiji",
    region="Northern Division", type="island", tag="hidden", emoji="🌈",
    sounds=["wilderness.mp3"],
    highlights=[("Bouma National Heritage Park", ""),
                ("Rainbow Reef", "Rainbow_Reef"),
                ("Lavena Coastal Walk", ""),
                ("Somosomo Strait", "Somosomo_Strait")],
    blurb="Fiji's garden island, a volcanic ridge running the length of it "
          "that catches enough rain to keep four-fifths under forest, with "
          "the country's best soft-coral diving in the strait alongside.",
    fact="The 180th meridian runs across Taveuni, and there is a marked spot "
         "where you can stand with a foot in each of two calendar days — "
         "though Fiji's official time zone quietly ignores it.",
    tip="Dive the Great White Wall in the Somosomo Strait on a running tide: "
        "a vertical face of soft coral that goes ghost-white in ambient blue "
        "light and only opens when the current is strong."),
"levuka": dict(
    name="Levuka", slug="Levuka", country="Fiji",
    region="Ovalau", type="ancient", tag="hidden", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Ovalau", "Ovalau"),
                ("Levuka Historical Port Town",
                 "Levuka")],
    blurb="Fiji's first colonial capital on the island of Ovalau, a single "
          "street of timber shopfronts under a green wall of cliffs, largely "
          "unchanged since the capital moved to Suva in 1877 and left it "
          "behind.",
    fact="Levuka is a World Heritage site as a rare surviving example of a "
         "late colonial Pacific port town — its buildings low and wooden "
         "because they were built by traders, not by an empire.",
    tip="Walk up Mission Hill's 199 concrete steps at sunrise for the view "
        "down the whole street and out over the reef the whalers used to "
        "anchor behind."),

# ---------------- Samoa & American Samoa ----------------
"apia": dict(
    name="Apia", slug="Apia", country="Samoa",
    region="Upolu", type="city", tag="hidden", emoji="⛪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Robert Louis Stevenson Museum",
                 "Robert_Louis_Stevenson_Museum"),
                ("Mount Vaea", "Mount_Vaea"),
                ("Immaculate Conception Cathedral, Apia",
                 "Immaculate_Conception_Cathedral,_Apia"),
                ("Upolu", "Upolu")],
    blurb="Samoa's capital and only city, on a harbour on Upolu, where the "
          "fa'a Samoa — the Samoan way, built on extended family and chiefly "
          "title — still organises daily life far more than the state does.",
    fact="Robert Louis Stevenson spent his last years above Apia, was made a "
         "chief by Samoans who called him Tusitala, teller of tales, and is "
         "buried at the top of Mount Vaea.",
    tip="Climb the hour to Stevenson's tomb early; the epitaph he wrote for "
        "himself is cut into the stone, and the view runs over the whole "
        "north coast."),
"savaii": dict(
    name="Savai'i", slug="Savai'i", country="Samoa",
    region="Savai'i", type="island", tag="hidden", emoji="🌋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Alofaaga Blowholes", "Alofaaga_Blowholes"),
                ("Saleaula", "Saleaula"),
                ("Mount Silisili", "Silisili"),
                ("Falealupo", "Falealupo")],
    blurb="The largest island in Samoa and the largest in Polynesia outside "
          "New Zealand and Hawaii, still mostly villages, lava fields and "
          "rainforest, with a shield volcano down the middle.",
    fact="At Saleaula a 1905 lava flow ran straight through a village and "
         "filled a stone church to the windows, leaving a lava pool in the "
         "nave that hardened where it stood.",
    tip="Go to the Alofaaga blowholes with a few coconuts; the local guides "
        "throw them into the vents at the right moment and the sea fires "
        "them thirty metres into the air."),
"pago-pago": dict(
    name="Pago Pago", slug="Pago_Pago", country="American Samoa",
    region="Tutuila", type="city", tag="hidden", emoji="⛰️",
    sounds=["ocean-waves.mp3"],
    highlights=[("National Park of American Samoa",
                 "National_Park_of_American_Samoa"),
                ("Mount ʻAlava", "Mount_ʻAlava"),
                ("Tutuila", "Tutuila"),
                ("Rainmaker Mountain", "Rainmaker_Mountain")],
    blurb="A US territory capital at the head of a drowned volcanic crater "
          "that makes one of the deepest natural harbours in the Pacific, "
          "with green walls rising straight out of the water on three sides.",
    fact="Rainmaker Mountain traps so much cloud against the harbour that "
         "Pago Pago is one of the wettest permanently inhabited places on "
         "Earth, at around 5,000 mm a year.",
    tip="Hike the Mount ʻAlava trail to where the old cable-car pylon stands; "
        "the tramway across the harbour was dismantled after a crash in 1980 "
        "and the view it was built for is still there."),
"ofu-beach": dict(
    name="Ofu Beach", slug="Ofu-Olosega", country="American Samoa",
    search_name="Ofu Beach American Samoa Manu'a",
    region="Manu'a", type="coastal", tag="hidden", emoji="🐠",
    sounds=["ocean-waves.mp3"],
    highlights=[("Manu'a Islands", "Manuʻa_Islands"),
                ("Taʻū", "Taʻū"),
                ("National Park of American Samoa",
                 "National_Park_of_American_Samoa")],
    blurb="A four-kilometre beach on a tiny island in the Manu'a group, "
          "backed by 500 m peaks and fronted by a reef you can wade to — and "
          "almost never anyone else on it.",
    fact="Ofu's corals survive lagoon temperatures above 34 °C that would "
         "bleach reefs anywhere else, which has made them one of the most "
         "studied populations in climate science.",
    tip="Getting here means a small plane or a boat from Tutuila that runs "
        "when it runs — bring more food than you need, and stay longer than "
        "you planned, because the schedule will decide anyway."),

# ---------------- Tonga ----------------
"nukualofa": dict(
    name="Nuku'alofa", slug="Nukuʻalofa", country="Tonga",
    region="Tongatapu", type="city", tag="hidden", emoji="👑",
    sounds=["ocean-waves.mp3"],
    highlights=[("Royal Palace, Nukuʻalofa",
                 "Royal_Palace,_Tonga"),
                ("Haʻamonga ʻa Maui", "Haʻamonga_ʻa_Maui"),
                ("Mapu a Vaea", "Mapu_a_Vaea"),
                ("Tongatapu", "Tongatapu")],
    blurb="The capital of the only Pacific nation never colonised, and still "
          "a kingdom — the white timber royal palace stands on the waterfront "
          "behind a low fence and a lawn.",
    fact="Haʻamonga ʻa Maui, a coral trilithon raised around 1200 AD, weighs "
         "some 30 tonnes and is aligned to the solstice sunrise — a Pacific "
         "stone calendar.",
    tip="Drive the south coast to the Mapuʻa ʻa Vaea blowholes, where five "
        "kilometres of shoreline vent at once on a decent swell and the "
        "spray goes up in a line as far as you can see."),
"vavau": dict(
    name="Vava'u", slug="Vavaʻu", country="Tonga",
    region="Vava'u", type="island", tag="hidden", emoji="🐋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Neiafu", "Neiafu_(Vavaʻu)"),
                ("Swallows Cave", "Vavaʻu"),
                ("Port of Refuge", "Vavaʻu")],
    blurb="A maze of some sixty limestone islands in northern Tonga around a "
          "deep, sheltered harbour — one of the great cruising grounds of the "
          "Pacific, and a humpback nursery.",
    fact="Tonga is one of very few countries that permits swimming with "
         "humpback whales; mothers bring their calves into these sheltered "
         "channels from July to October to nurse.",
    tip="Ask a licensed operator for the mother-and-calf encounters rather "
        "than a heat run — you slip in quietly, four at a time, and the calf "
        "usually comes to look at you."),
"haapai": dict(
    name="Ha'apai", slug="Haʻapai", country="Tonga",
    region="Ha'apai", type="island", tag="hidden", emoji="🌾",
    sounds=["ocean-waves.mp3"],
    highlights=[("Lifuka", "Lifuka"),
                ("Kao", "Kao_(island)"),
                ("Tofua", "Tofua")],
    blurb="Tonga's middle group: sixty low coral islands and two volcanic "
          "cones, with barely any elevation, almost no tourism, and beaches "
          "that run for kilometres without a building on them.",
    fact="The mutiny on the Bounty happened in these waters in 1789; Bligh "
         "was set adrift within sight of Tofua and began from here the "
         "6,700 km open-boat voyage that got him to Timor.",
    tip="Base yourself on Lifuka and hire a boat to the outer sand cays; the "
        "group has no hills to shelter behind, so pick a day when the trade "
        "wind has dropped."),
# ---------------- Cook Islands & Niue ----------------
"rarotonga": dict(
    name="Rarotonga", slug="Rarotonga", country="Cook Islands",
    region="Rarotonga", type="island", tag="famous", emoji="🌴",
    sounds=["ocean-waves.mp3"],
    highlights=[("Avarua", "Avarua"),
                ("Te Rua Manga", "Te_Rua_Manga"),
                ("Muri Lagoon", "Rarotonga")],
    blurb="The main Cook Island: a jagged volcanic core wrapped in a coastal "
          "plain and a lagoon, with one 32 km road around the outside and two "
          "bus routes — clockwise and anti-clockwise.",
    fact="The great Māori migration canoes that reached New Zealand are held "
         "in tradition to have left from Rarotonga's Avana harbour around the "
         "13th century.",
    tip="Do the cross-island track over the saddle beside Te Rua Manga, the "
        "Needle — you start on the north coast and come down a stream bed on "
        "the south, and it is the only way through the interior."),
"aitutaki": dict(
    name="Aitutaki", slug="Aitutaki", country="Cook Islands",
    region="Aitutaki", type="island", tag="famous", emoji="💙",
    sounds=["ocean-waves.mp3"],
    highlights=[("One Foot Island", "One_Foot_Island"),
                ("Arutanga", "Arutanga"),
                ("Maunga Pu", "Aitutaki")],
    blurb="A triangular lagoon 45 km around with fifteen motu strung along "
          "its reef and a small volcanic island in one corner — often called "
          "the most beautiful lagoon in the world, and hard to argue with.",
    fact="One Foot Island has a post office on a sandbar that will stamp your "
         "passport, which makes it one of the smallest inhabited postal "
         "addresses anywhere.",
    tip="Take a lagoon cruise that stops at Maina in the far corner rather "
        "than only One Foot; the sand there is a bar in the middle of open "
        "lagoon and you swim to it from the boat."),
"atiu": dict(
    name="Atiu", slug="Atiu", country="Cook Islands",
    region="Atiu", type="island", tag="hidden", emoji="☕",
    sounds=["wilderness.mp3"],
    highlights=[("Anatakitaki Cave", "Atiu"),
                ("Makatea", "Makatea")],
    blurb="A raised coral island with a fossil-reef ring of jagged makatea "
          "limestone around a volcanic centre, 500 people, five villages, and "
          "coffee grown here since the missionaries planted it.",
    fact="Anatakitaki cave is home to the kopeka, a swiftlet that navigates "
         "in total darkness by echolocation — one of only a handful of birds "
         "in the world that can.",
    tip="Go to a tumunu, the island's bush-beer drinking circle, held in a "
        "clearing with a strict order of serving that descends from pre-"
        "missionary kava ritual."),
"niue": dict(
    name="Niue", slug="Niue", country="Niue",
    region="Niue", type="island", tag="hidden", emoji="🐋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Alofi", "Alofi"),
                ("Talava Arches", "Niue"),
                ("Matapa Chasm", "Niue"),
                ("Limu Pools", "Niue")],
    blurb="One of the world's largest raised coral atolls and one of its "
          "smallest countries: 1,600 people on a single rock with no rivers, "
          "no beaches to speak of, and chasms and sea caves instead.",
    fact="Because there is no runoff from soil or rivers, Niue's water is "
         "among the clearest in the world — horizontal visibility of 80 m is "
         "routine.",
    tip="Snorkel the Limu Pools where fresh groundwater seeps up through the "
        "salt; the two waters mix in visible shimmering layers you can swim "
        "in and out of."),

# ---------------- French Polynesia ----------------
"papeete": dict(
    name="Papeete", slug="Papeete", country="French Polynesia",
    region="Tahiti", type="city", tag="hidden", emoji="🌸",
    sounds=["city-hum.mp3"],
    highlights=[("Tahiti", "Tahiti"),
                ("Marché de Papeete", "Papeete"),
                ("Musée de Tahiti et des Îles",
                 "Musée_de_Tahiti_et_des_Îles"),
                ("Teahupoʻo", "Teahupoʻo")],
    blurb="The capital of French Polynesia on Tahiti, and the hub every "
          "island in five archipelagos connects through — a working port with "
          "a market, a waterfront of food trucks, and mountains straight "
          "behind it.",
    fact="Teahupo'o, an hour down the coast, breaks over a shallow reef into "
         "one of the heaviest waves on Earth, and hosted the surfing at the "
         "2024 Olympics — 15,000 km from Paris.",
    tip="Eat at the roulottes on Place Vaiete after dark, where vans park in "
        "a square and serve chow mein, poisson cru and crêpes to the same "
        "queue."),
"bora-bora": dict(
    name="Bora Bora", slug="Bora_Bora", country="French Polynesia",
    region="Leeward Islands", type="island", tag="famous", emoji="💎",
    sounds=["ocean-waves.mp3"],
    highlights=[("Mount Otemanu", "Mount_Otemanu"),
                ("Vaitape", "Vaitape"),
                ("Matira Beach", "Bora_Bora")],
    blurb="The remains of an extinct volcano standing in a turquoise lagoon "
          "ringed by motu — the image most people hold of the South Pacific, "
          "and the place that invented the overwater bungalow in 1967.",
    fact="Mount Otemanu's 727 m basalt plug has never been properly summited: "
         "the rock at the top is too rotten to climb safely.",
    tip="Circle the island by bicycle on the flat 32 km coast road instead of "
        "taking a lagoon tour — you pass the wartime American coastal guns "
        "still sitting in the hills above Anau."),
"moorea": dict(
    name="Moorea", slug="Moorea", country="French Polynesia",
    region="Windward Islands", type="island", tag="famous", emoji="🍍",
    sounds=["ocean-waves.mp3"],
    highlights=[("Belvedere Lookout", "Moorea"),
                ("Mount Rotui", ""),
                ("Cook's Bay", "Cook's_Bay_(Moorea)"),
                ("Ōpūnohu Bay", "Opunohu_Bay")],
    blurb="A heart-shaped island half an hour by ferry from Tahiti, with two "
          "deep parallel bays cut into its north coast and a jagged ridge of "
          "spires between them.",
    fact="The bay everyone calls Cook's Bay is not where Cook anchored — he "
         "used Ōpūnohu next door, and the names got swapped somewhere in the "
         "19th century.",
    tip="Drive up to the Belvedere at first light, then walk down through the "
        "agricultural school's pineapple fields past the restored marae in "
        "the Ōpūnohu valley."),
"huahine": dict(
    name="Huahine", slug="Huahine", country="French Polynesia",
    region="Leeward Islands", type="island", tag="hidden", emoji="🐟",
    sounds=["wilderness.mp3"],
    highlights=[("Maeva", ""),
                ("Fare", "Fare,_French_Polynesia"),
                ("Marae", "Marae")],
    blurb="Two islands joined by a bridge, quiet and agricultural, with more "
          "surviving pre-European temple sites than anywhere else in the "
          "Society Islands.",
    fact="The stone fish traps in Lake Fauna Nui at Maeva are V-shaped coral "
         "walls built centuries ago and still in use — among the oldest "
         "working structures in Polynesia.",
    tip="Cycle the Maeva shoreline where more than thirty marae stand in a "
        "row along the lake, each belonging to a different family of the "
        "island's old ruling council."),
"rangiroa": dict(
    name="Rangiroa", slug="Rangiroa", country="French Polynesia",
    region="Tuamotus", type="island", tag="hidden", emoji="🦈",
    sounds=["ocean-waves.mp3"],
    highlights=[("Tuamotu Archipelago", "Tuamotus"),
                ("Avatoru", "Avatoru"),
                ("Tiputa Pass", "Rangiroa")],
    blurb="One of the largest atolls in the world — its lagoon could hold the "
          "whole island of Tahiti — a 200 km necklace of motu enclosing water "
          "so wide you cannot see across it.",
    fact="Only two passes connect the lagoon to the ocean, so the entire tidal "
         "exchange of a lagoon that size squeezes through them, which is why "
         "the drift dive at Tiputa is world famous.",
    tip="Ride the incoming tide through Tiputa Pass with a divemaster: you "
        "are carried in at walking pace past grey reef sharks holding station "
        "in the current, and dolphins that surf the pass for fun."),
"fakarava": dict(
    name="Fakarava", slug="Fakarava", country="French Polynesia",
    region="Tuamotus", type="island", tag="hidden", emoji="🤿",
    sounds=["ocean-waves.mp3"],
    highlights=[("Rotoava", ""),
                ("Tetamanu", "Fakarava"),
                ("Tuamotus", "Tuamotus")],
    blurb="A rectangular atoll and UNESCO biosphere reserve in the Tuamotus, "
          "with a southern pass so rich in sharks that divers count them in "
          "the hundreds on a single dive.",
    fact="Every June and July, thousands of camouflage groupers spawn in "
         "Fakarava's south pass, drawing around 700 grey reef sharks into a "
         "channel a few hundred metres wide.",
    tip="Stay at Tetamanu in the abandoned old village at the south pass, "
        "where the 19th-century coral-block church still stands and the "
        "guesthouse pontoon is the dive entry."),
"nuku-hiva": dict(
    name="Nuku Hiva", slug="Nuku_Hiva", country="French Polynesia",
    region="Marquesas", type="island", tag="hidden", emoji="🗿",
    sounds=["wilderness.mp3"],
    highlights=[("Marquesas Islands", "Marquesas_Islands"),
                ("Taiohae", "Taiohae"),
                ("Vaipo Waterfall", "Nuku_Hiva"),
                ("Tiki", "Tiki")],
    blurb="The largest of the Marquesas, 1,400 km northeast of Tahiti: no "
          "lagoon, no barrier reef, just volcanic ridges dropping straight "
          "into deep ocean and valleys full of stone tiki and old temple "
          "platforms.",
    fact="Herman Melville jumped ship here in 1842 and spent a month in the "
         "Taipivai valley, which became his first book, Typee — the one that "
         "made him famous long before Moby-Dick.",
    tip="Ride horseback across the Toovii plateau; the Marquesan horses came "
        "from Chile in 1842 and the high grassland they graze looks nothing "
        "like the coast a few kilometres below."),

# ---------------- Pitcairn ----------------
"pitcairn": dict(
    name="Adamstown", slug="Adamstown,_Pitcairn_Islands",
    country="Pitcairn Islands", search_name="Pitcairn Island Adamstown",
    region="Pitcairn", type="island", tag="quirky", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Pitcairn Islands", "Pitcairn_Islands"),
                ("Bounty Bay", "Bounty_Bay"),
                ("HMS Bounty", "HMS_Bounty")],
    blurb="The only settlement on Pitcairn, and the capital of the least "
          "populous jurisdiction on Earth — a few dozen people, most of them "
          "descended from the Bounty mutineers who burned the ship in the bay "
          "below in 1790.",
    fact="Pitcairn's exclusive economic zone is a marine reserve of 840,000 "
         "km² — roughly 8,000 km² of protected ocean for every resident.",
    tip="There is no airstrip; you reach Pitcairn on a supply ship from "
        "Mangareva, about 32 hours each way, and the schedule means most "
        "visitors stay a fortnight or more."),
# ---------------- Kiribati, Tuvalu, Nauru ----------------
"tarawa": dict(
    name="Tarawa", slug="Tarawa", country="Kiribati",
    region="Gilbert Islands", type="island", tag="hidden", emoji="🐡",
    sounds=["ocean-waves.mp3"],
    highlights=[("South Tarawa", "South_Tarawa"),
                ("Betio", "Betio"),
                ("Gilbert Islands", "Gilbert_Islands")],
    blurb="The capital atoll of Kiribati — a chain of islets around a lagoon, "
          "nowhere more than a few metres above the sea, holding half the "
          "country's population on a strip of land you can walk across in "
          "minutes.",
    fact="Kiribati straddles the equator and, until it moved the date line "
         "east in 1995, was the only country permanently split across two "
         "calendar days.",
    tip="Walk out to the Japanese coastal guns and bunkers still standing on "
        "Betio's beaches, where one of the bloodiest amphibious battles of "
        "the Pacific War was fought over 76 hours in 1943."),
"kiritimati": dict(
    name="Kiritimati", slug="Kiritimati", country="Kiribati",
    search_name="Kiritimati Christmas Island Kiribati",
    region="Line Islands", type="island", tag="quirky", emoji="🎄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Line Islands", "Line_Islands"),
                ("London, Kiribati", "London,_Kiribati")],
    blurb="The largest coral atoll in the world by land area, in the Line "
          "Islands, with villages named London, Paris and Poland, and the "
          "earliest time zone on the planet.",
    fact="Kiritimati is the first inhabited place on Earth to see each new "
         "year — UTC+14, a full 26 hours ahead of the last.",
    tip="Fly-fish the flats at dawn for bonefish; the lagoon shallows here "
        "are among the most productive in the world and the guides walk you "
        "out from shore rather than taking a boat."),
"funafuti": dict(
    name="Funafuti", slug="Funafuti", country="Tuvalu",
    region="Funafuti", type="island", tag="hidden", emoji="✈️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Funafuti Conservation Area",
                 "Funafuti_Conservation_Area"),
                ("Vaiaku", "Vaiaku"),
                ("Tuvalu", "Tuvalu")],
    blurb="The capital atoll of Tuvalu, the world's fourth-smallest country, "
          "where the airstrip doubles as the town's main public space — "
          "football, volleyball and evening strolling, cleared twice a week "
          "when a plane is due.",
    fact="Tuvalu earns a significant share of its national revenue from "
         "licensing the .tv internet domain, which happened to be assigned to "
         "it by alphabetical accident.",
    tip="Go out to the conservation area on the western reef by boat; it is "
        "the only part of the atoll where the coral is protected, and the "
        "islets there are nesting grounds for green turtles."),
"nauru": dict(
    name="Nauru", slug="Nauru", country="Nauru",
    region="Nauru", type="island", tag="hidden", emoji="🪨",
    sounds=["ocean-waves.mp3"],
    highlights=[("Yaren District", "Yaren_District"),
                ("Buada Lagoon", "Buada_Lagoon"),
                ("Command Ridge", "Command_Ridge")],
    blurb="The world's smallest republic: a single raised coral island of "
          "21 km², whose interior was strip-mined for phosphate until the "
          "centre of the country became a moonscape of limestone pinnacles.",
    fact="In the late 1970s Nauru had one of the highest per-capita incomes "
         "in the world from bird droppings compressed over millennia; the "
         "phosphate ran out and the money with it.",
    tip="Climb Command Ridge, the island's high point at 65 m, where a "
        "Japanese wartime radio bunker and twin guns look out over the mined "
        "plateau — the clearest view of what the mining did."),

# ---------------- Palau, Marshalls, Micronesia ----------------
"koror": dict(
    name="Koror", slug="Koror", country="Palau",
    region="Koror", type="city", tag="hidden", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Belau National Museum", "Belau_National_Museum"),
                ("Rock Islands", "Rock_Islands"),
                ("Babeldaob", "Babeldaob")],
    blurb="Palau's largest town and former capital, on a small island linked "
          "by bridge to the big volcanic one — the base for reaching a lagoon "
          "that is essentially one enormous marine park.",
    fact="Palau created the world's first shark sanctuary in 2009 and now "
         "requires every arriving visitor to sign an eco-pledge, stamped into "
         "their passport and addressed to the children of Palau.",
    tip="Look for a bai, the traditional men's meeting house, with its "
        "painted gable of storyboards — the museum has one reconstructed to "
        "full size with no nails in it."),
"rock-islands": dict(
    name="Rock Islands", slug="Rock_Islands", country="Palau",
    search_name="Rock Islands Palau", region="Koror", type="coastal",
    tag="famous", emoji="🍄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Jellyfish Lake", "Jellyfish_Lake"),
                ("Ngeruktabel", "Rock_Islands"),
                ("German Channel", "Rock_Islands")],
    blurb="Several hundred mushroom-shaped limestone islets in a turquoise "
          "lagoon, undercut at the waterline by the sea and by grazing "
          "snails, and capped with dense green forest.",
    fact="Jellyfish Lake holds millions of golden jellyfish that migrate "
         "across it daily following the sun, and have lost most of their "
         "sting after generations in a lake with no predators.",
    tip="Snorkel — never dive — in Jellyfish Lake; bubbles harm the animals, "
        "so tanks are banned, and you drift among them in the top few metres "
        "with nothing but a mask."),
"peleliu": dict(
    name="Peleliu", slug="Peleliu", country="Palau",
    region="Peleliu", type="island", tag="hidden", emoji="🪖",
    sounds=["wilderness.mp3"],
    highlights=[("Battle of Peleliu", "Battle_of_Peleliu"),
                ("Bloody Nose Ridge", "Battle_of_Peleliu"),
                ("Orange Beach", "Peleliu")],
    blurb="A flat coral island south of Koror, forested and quiet, where a "
          "battle expected to take four days took two and a half months in "
          "1944 and left the ridges honeycombed with caves.",
    fact="Peleliu's coral limestone hid more than 500 fortified caves — the "
         "island is one of the most intact Second World War battlefields "
         "anywhere, with wrecked tanks still where they stopped.",
    tip="Dive the drop-offs on the west side, then walk Bloody Nose Ridge in "
        "the same day; the jungle has grown back over the ridge but the "
        "trenches and cave mouths are still open."),
"majuro": dict(
    name="Majuro", slug="Majuro", country="Marshall Islands",
    region="Majuro", type="island", tag="hidden", emoji="🛶",
    sounds=["ocean-waves.mp3"],
    highlights=[("Alele Museum", "Alele_Museum"),
                ("Laura", "Laura,_Marshall_Islands"),
                ("Marshall Islands", "Marshall_Islands")],
    blurb="The capital atoll of the Marshall Islands: 64 islets around a "
          "lagoon, connected by a single road that runs 50 km with ocean on "
          "one side and lagoon on the other, often only a hundred metres "
          "apart.",
    fact="Marshallese navigators built stick charts from palm ribs and shells "
         "that mapped not islands but the way ocean swells bend around them — "
         "a chart of wave interference, memorised and left ashore.",
    tip="Drive to Laura at the western end, where the atoll is at its widest "
        "and highest and there is an actual beach — the only place on Majuro "
        "that feels like more than a sandbar."),
"bikini-atoll": dict(
    name="Bikini Atoll", slug="Bikini_Atoll", country="Marshall Islands",
    region="Ralik Chain", type="island", tag="hidden", emoji="☢️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Operation Crossroads", "Operation_Crossroads"),
                ("USS Saratoga", "USS_Saratoga_(CV-3)"),
                ("Castle Bravo", "Castle_Bravo")],
    blurb="An atoll in the northern Marshalls whose people were moved off in "
          "1946 for what became 23 nuclear tests, and who have never been "
          "able to move back.",
    fact="The lagoon is a World Heritage site and a ships' graveyard: an "
         "aircraft carrier and a battleship sit upright in clear water, sunk "
         "by the tests they were placed there to survive.",
    tip="Reaching Bikini requires permits and a live-aboard charter, and the "
        "lagoon is dived while the land stays off-limits — the coral has "
        "recovered far better than the soil."),
"pohnpei": dict(
    name="Pohnpei", slug="Pohnpei", country="Micronesia",
    region="Pohnpei", type="island", tag="hidden", emoji="🌧️",
    sounds=["wilderness.mp3"],
    highlights=[("Kolonia", "Kolonia"),
                ("Sokehs Rock", "Sokehs"),
                ("Kepirohi Falls", "Pohnpei")],
    blurb="A high volcanic island in the Federated States of Micronesia, one "
          "of the wettest places on Earth, where the interior rainforest is "
          "so steep and so constantly rained on that much of it has never "
          "been cleared.",
    fact="Pohnpei's interior receives up to 10,000 mm of rain a year, and "
         "the island's sakau — kava — is prepared on flat basalt stones in a "
         "ritual that opens most formal occasions.",
    tip="Climb Sokehs Rock above Kolonia in the early morning; the basalt "
        "monolith rises 200 m straight out of the lagoon and the trail passes "
        "Japanese wartime guns still in their emplacements."),
"chuuk-lagoon": dict(
    name="Chuuk Lagoon", slug="Chuuk_Lagoon", country="Micronesia",
    region="Chuuk", type="coastal", tag="hidden", emoji="⚓",
    sounds=["ocean-waves.mp3"],
    highlights=[("Weno", "Weno"),
                ("Operation Hailstone", "Operation_Hailstone"),
                ("Chuuk State", "Chuuk_State")],
    blurb="A vast lagoon enclosing high volcanic islands, and the greatest "
          "wreck-diving site in the world — Japan's main Pacific anchorage "
          "until a two-day American air raid in February 1944 sank the fleet "
          "where it lay.",
    fact="More than fifty ships and 250 aircraft went down in the lagoon, "
         "many still holding cargo — trucks, bottles, aircraft engines — "
         "sitting in the holds where they were stowed.",
    tip="Dive the Fujikawa Maru, whose hold still contains Zero fighter "
        "fuselages and whose masts reach to within a few metres of the "
        "surface, colonised by eighty years of coral."),
"yap": dict(
    name="Yap", slug="Yap", country="Micronesia",
    region="Yap", type="island", tag="quirky", emoji="🪙",
    sounds=["wilderness.mp3"],
    highlights=[("Rai stones", "Rai_stones"),
                ("Colonia", "Colonia,_Yap"),
                ("Yap State", "Yap_State")],
    blurb="An island group in the western Carolines that kept its "
          "chiefly system, its stone paths and its stone money through every "
          "colonial administration that arrived — Spanish, German, Japanese "
          "and American in turn.",
    fact="Yapese rai are limestone discs up to 3.6 m across, quarried in "
         "Palau and shipped home by canoe; ownership transfers by agreement "
         "while the stone stays put, including one on the seabed that everyone "
         "still counts.",
    tip="Drive the outer villages and look for the stone money banks — rows "
        "of rai standing along a village path, each with a known owner and a "
        "known story of how it was fetched."),

# ---------------- Guam & Northern Marianas ----------------
"hagatna": dict(
    name="Hagåtña", slug="Hagåtña,_Guam", country="Guam",
    region="Guam", type="city", tag="hidden", emoji="🌴",
    sounds=["ocean-waves.mp3"],
    highlights=[("Plaza de España", "Plaza_de_España_(Hagåtña)"),
                ("Latte stone", "Latte_stone"),
                ("Dulce Nombre de Maria Cathedral Basilica",
                 "Dulce_Nombre_de_Maria_Cathedral_Basilica"),
                ("Two Lovers Point", "Two_Lovers_Point")],
    blurb="The capital of Guam and the oldest continuously occupied European-"
          "founded settlement in the Pacific — Spanish for three centuries, "
          "Japanese for three years, American since, and CHamoru throughout.",
    fact="Latte stones — pillars with a capstone shaped like a half coconut — "
         "held up CHamoru houses from about 900 AD, and a set of them stands "
         "in a park in the middle of the capital.",
    tip="Walk the Latte Stone Park and the Spanish plaza in one loop, then "
        "look at the seawall: Hagåtña was flattened in the 1944 bombardment, "
        "and almost everything old here is a survivor or a rebuild."),
"tumon": dict(
    name="Tumon", slug="Tumon,_Guam", country="Guam",
    region="Guam", type="coastal", tag="hidden", emoji="🐠",
    sounds=["ocean-waves.mp3"],
    highlights=[("Tumon Bay", "Tumon,_Guam"),
                ("Ritidian Point", "Ritidian_Point"),
                ("Guam", "Guam")],
    blurb="Guam's hotel strip on a crescent bay of white sand and protected "
          "reef flat, the busiest few kilometres in Micronesia and where "
          "most of the island's visitors from Japan and Korea stay.",
    fact="Guam is on the edge of the Mariana Trench, so the deepest point on "
         "Earth lies about 300 km from a beach where the water is "
         "waist-deep for a hundred metres.",
    tip="Drive to the far north to Ritidian Point instead — a wildlife refuge "
        "with an empty beach, latte stones in the limestone forest behind it, "
        "and caves with ancient pictographs."),
"saipan": dict(
    name="Saipan", slug="Saipan", country="Northern Mariana Islands",
    region="Saipan", type="island", tag="hidden", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Managaha", "Managaha"),
                ("Banzai Cliff", "Banzai_Cliff"),
                ("Mount Tapochau", "Mount_Tapochau"),
                ("The Grotto", "")],
    blurb="The largest of the Northern Marianas, with a sheltered lagoon on "
          "one side, cliffs on the other, and the scars of 1944 everywhere in "
          "between.",
    fact="The Grotto is a collapsed limestone cavern connected to the open "
         "ocean by three underwater tunnels — you climb down 100 steps and "
         "dive into a pool that surges with the swell.",
    tip="Drive up Mount Tapochau at midday, the island's 474 m high point, "
        "where on a clear day you can see the whole island and Tinian across "
        "the channel at once."),
"tinian": dict(
    name="Tinian", slug="Tinian", country="Northern Mariana Islands",
    region="Tinian", type="island", tag="hidden", emoji="✈️",
    sounds=["ocean-waves.mp3"],
    highlights=[("North Field", "North_Field_(Tinian)"),
                ("House of Taga", "House_of_Taga"),
                ("Tinian Municipality", "Tinian")],
    blurb="A small, flat, mostly empty island south of Saipan, where in 1945 "
          "the largest airfield in the world operated four parallel 2.6 km "
          "runways cut into the coral.",
    fact="The House of Taga holds the largest latte stones ever raised — "
         "pillars around five metres tall, quarried and erected by CHamoru "
         "builders roughly a thousand years ago.",
    tip="Ride out to North Field, now overgrown, where the runways still run "
        "arrow-straight through the tangan-tangan scrub and the atomic bomb "
        "loading pits sit under glass beside them."),
}

# Existing skeletons. `fill()` only ever writes a field that is empty, so a
# rerun is a no-op and nothing a scene pipeline wrote is ever clobbered.
#
# `sydney` is the only record in the file with holes. The rest are complete;
# the entries below add `search_name` to the four whose bare names have a
# louder namesake elsewhere — Perth (Scotland), Queenstown (South Africa,
# Singapore, Maryland), Wellington (Somerset, Florida, Colorado) and Auckland
# (Auckland Park, and every "Auckland" street in England) — which sharpens the
# YouTube query the media and monument enrichers spend the name on.
FILL = {
    "sydney": dict(
        region="New South Wales",
        blurb="A harbour city built around one of the largest natural "
              "harbours on Earth, with 240 km of shoreline folded into bays, "
              "headlands and beaches — the ferry network is a form of public "
              "transport and a sightseeing tour at the same time.",
        fact="The Opera House's shells were unbuildable as designed until the "
             "engineers realised every one of them could be cut from the "
             "surface of a single imaginary sphere — which is why they nest "
             "so exactly.",
        tip="Walk the Bondi to Coogee coastal path early on a weekday: six "
            "kilometres of cliff-top track past a clifftop cemetery and the "
            "sea baths at Bronte, with the whole city out of sight behind "
            "you."),
    "perth": dict(search_name="Perth Western Australia"),
    "queenstown": dict(search_name="Queenstown New Zealand"),
    "wellington": dict(search_name="Wellington New Zealand"),
    "auckland": dict(search_name="Auckland New Zealand"),
}


def flag(code):
    """ISO alpha-2 -> flag emoji, the same derivation build_countries.py uses."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def country_slug(name):
    return COUNTRY_SLUG.get(name, name.replace(" ", "_"))


def in_box(lat, lng):
    """The Oceania net — two longitude ranges, because the region crosses 180°.

    See the module docstring. A single rectangle cannot express this region;
    treating it as one is how you either refuse Tahiti or refuse nothing.
    """
    if not (OCEANIA_LAT[0] <= lat <= OCEANIA_LAT[1]):
        return False
    return any(lo <= lng <= hi for lo, hi in OCEANIA_LNG)


def slugs_wanted():
    """Every slug this batch needs an answer about, place-level and highlight."""
    out = []
    for spec in NEW.values():
        out.append(spec["slug"])
        out.append(country_slug(spec["country"]))
        out += [s for _, s in spec["highlights"] if s]
    for spec in FILL.values():
        out += [s for _, s in spec.get("highlights", []) if s]
    # The sovereign states named in EXPECT_P17 are QIDs we have to *compare*
    # against, so they get resolved live too rather than typed from memory.
    out += list(EXPECT_P17.values())
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
                 "MISSING": 4, "SELF": 5, "FAR": 6, "REDIRECT": 7,
                 "FIXENC": 8, "TERRITORY": 9}
        for kind, where, what, why in sorted(
                self.rows, key=lambda r: (order.get(r[0], 10), r[1], r[2])):
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
    """P17 against the country we claim. A WARNING — see the module docstring.

    A Pacific territory legitimately answers its sovereign state here. When
    that is exactly what we expect, say so quietly as TERRITORY and move on,
    so the COUNTRY lines left over are the ones worth reading.
    """
    name = spec["country"]
    want = got.get(country_slug(name)) or {}
    mine, theirs = e.get("country_qid"), want.get("qid")
    if not theirs:
        notes.add("COUNTRY", pid, name,
                  "no QID for the country article — check by hand")
        return
    if not mine:
        notes.add("COUNTRY", pid, e.get("title", spec["slug"]),
                  "article has no P17 — check by hand")
        return
    if mine == theirs:
        return
    sovereign = EXPECT_P17.get(name)
    if sovereign:
        sov_qid = (got.get(sovereign) or {}).get("qid")
        if sov_qid and mine == sov_qid:
            notes.add("TERRITORY", pid, e.get("title", spec["slug"]),
                      f"P17 is {sovereign} — expected for {name}")
            return
    notes.add("COUNTRY", pid, e.get("title", spec["slug"]),
              f"P17 is {mine}, {name} is {theirs} — check by hand")


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
    if not in_box(lat, lng):
        notes.add("OUTSIDE", pid, title,
                  f"P625 is {lat:.3f},{lng:.3f} — not Oceania")
        return None
    country_check(pid, spec, e, got, notes)

    code = COUNTRY_CODE[spec["country"]]
    loc = {
        "id": pid,
        "name": spec["name"],
        "country": spec["country"],
        "country_code": code,
        "country_flag": flag(code),
        "continent": "Oceania",
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
