#!/usr/bin/env python3
"""
build_canada.py — the Canada batch (2026-08).

WHAT WAS WRONG
    36 places for the second-largest country on Earth, and **19 of them were
    Grand River conservation areas inside one Ontario watershed**. Strip that
    watershed out and Canada was seventeen records: Niagara, the CN Tower,
    Old Québec, Banff, Stanley Park, Peggy's Cove, Tofino, Churchill, Dawson
    City, Lunenburg, the Icefields Parkway, Hopewell Rocks and four more
    Ontario parks.

    So: no Vancouver, no Montréal, no Toronto (the CN Tower stood in for it),
    no Ottawa, no Calgary, no Halifax, no St. John's, no Winnipeg. Four of the
    ten provinces had **nothing at all** — Saskatchewan, Manitoba (Churchill
    is the only Manitoba record and it is 1,000 km north of anyone),
    Newfoundland and Labrador, Prince Edward Island. Two of the three
    territories were empty: the Northwest Territories and **Nunavut**, which
    is a fifth of Canada's land area and had zero places.

    The north was the biggest hole. One record — Dawson City — for 3.9
    million km² of Yukon, NWT and Nunavut.

WHAT THIS DOES
    Adds the new places and repairs the ones already here, in one pass, on the
    frame `tools/regionbuild.py` now holds (extracted from build_africa.py /
    build_oceania.py for exactly this batch). Editorial choice is ours — which
    lake, which outport, what is worth saying — but every **coordinate comes
    from Wikidata P625** and every **slug is resolved live** and stored as the
    article's canonical title, per README "Filling a region out". Nothing here
    is recalled from memory except the prose.

THE GUARD THIS REGION NEEDED THAT NO PREVIOUS ONE DID
    Every earlier batch could lean on the country as its namesake guard,
    because the region was a continent and a namesake was almost always in a
    different country: Lagos/Lagos, Tripoli/Tripoli, Victoria/Victoria.

    Canada's worst collisions are **internal**. Windsor is in Ontario, Nova
    Scotia and Quebec. Victoria is a BC capital and a Newfoundland outport.
    There is a Sydney in Nova Scotia, a Hamilton, a Kingston, a Stratford, a
    Perth, a Delta, a Richmond, a Chatham, a London and a Paris — all in
    Ontario, all with a louder namesake elsewhere in the world *and* a quieter
    one in the next province over. P17 answers "Canada" for the right article
    and for the wrong one. A box around Canada contains both.

    So the box test moved down a level: `PROVINCE_BOX` checks the resolved
    P625 against the province the record claims. Like P17 it is a WARNING —
    Wood Buffalo is Alberta *and* the Northwest Territories, and a park on a
    border is not a bug. See regionbuild.subregion_check().

    The other half of the same problem lands before the search rather than
    after it: `search_name`. Sydney, Nova Scotia loses to Sydney, Australia on
    any query; Jasper loses to Jasper, Indiana; Halifax to Halifax, England;
    Kingston to Kingston, Jamaica; Windsor to Windsor Castle; London and Paris
    to the obvious. 40 records here carry one, plus every one of the 36
    already in the file.

`province` → `region`
    The file was the last one in the atlas still calling this field `province`.
    `passport.js` reads `l.region || l.province`, so nothing was broken on
    screen — but `enrich_media.wrong_place_title()` reads `place["region"]`
    and nothing else, so every Canadian record was invisible to the guard that
    compares a video's stated province against the place's own. The migration
    is a rename in place, run before anything else.

Run:  python3 tools/build_canada.py                 # report only
      python3 tools/build_canada.py --apply
      python3 tools/build_canada.py --only bala,dorset --apply
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regionbuild as rb

COUNTRY_CODE = {"Canada": "CA"}          # copied from build_countries.COUNTRIES

# The coarse net. Canada runs from Middle Island in Lake Erie (41.68°N) to
# Cape Columbia on Ellesmere (83.1°N), and from the Yukon–Alaska line at
# 141°W to Cape Spear at 52.6°W. Unlike Oceania this fits in one rectangle —
# the country stops 11° short of the antimeridian. The *hard* refusal; the
# namesake work is done by PROVINCE_BOX and search_name below.
CA_LAT = (41.0, 84.0)
CA_LNG = (-141.5, -52.0)


def in_box(lat, lng):
    return CA_LAT[0] <= lat <= CA_LAT[1] and CA_LNG[0] <= lng <= CA_LNG[1]


# The guard the continental batches never needed — see the module docstring.
# Hand-drawn and padded, because it is a warning and a place legitimately sits
# on a border. Every string here is also the user-visible `region` shown under
# the place name on the passport page, so it reads as a Canadian would write it.
PROVINCE_BOX = {
    "British Columbia":          (47.9, 60.6, -139.5, -113.5),
    "Alberta":                   (48.5, 60.6, -120.6, -109.5),
    "Saskatchewan":              (48.5, 60.6, -110.6, -100.9),
    "Manitoba":                  (48.5, 60.6, -102.6, -88.4),
    "Ontario":                   (41.5, 57.1, -95.6, -73.9),
    # Muskoka gets its own row rather than being folded into Ontario, for the
    # same reason the Grand River conservation areas earned their own trip:
    # the batch is *about* the cluster, and a box this small is the only thing
    # that would notice a Bala, Windermere or Dorset resolving to the English
    # original. The string still contains "Ontario", which is what the media
    # vetter's province check reads.
    "Muskoka District, Ontario": (44.4, 45.9, -80.6, -78.5),
    "Quebec":                    (44.9, 62.8, -80.1, -56.9),
    "New Brunswick":             (44.4, 48.2, -69.3, -63.6),
    "Nova Scotia":               (43.2, 47.2, -66.6, -59.4),
    "Prince Edward Island":      (45.8, 47.2, -64.6, -61.8),
    "Newfoundland and Labrador": (46.5, 60.6, -68.0, -52.4),
    "Yukon":                     (59.8, 69.8, -141.2, -123.4),
    "Northwest Territories":     (59.8, 79.0, -136.7, -101.4),
    "Nunavut":                   (51.4, 83.3, -121.6, -60.9),
}

REGION = rb.Region(
    target="canada.json",
    continent="North America",
    country_code=COUNTRY_CODE,
    in_box=in_box,
    subregion_box=PROVINCE_BOX,
)


# ---------------------------------------------------------------------------
# THE CURATED CONTENT.
#
# highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, an
# animal, an era, a phenomenon or an event. Canada makes that rule easy to
# break: "Polar Bears", "Northern Lights", "Klondike Gold Rush", "Group of
# Seven", "Sable Island horses", "Inuit", "Mennonite", "Acadians", "Stampede"
# all read like places on the page and are none of them things a camera can be
# pointed at. `enrich_monuments.py` spends every highlight as a YouTube search
# term, so each one below is something that stands somewhere.
# (See enrich_monuments.NOT_A_MONUMENT, and REPAIR at the bottom of this file
# for the five records already shipped that broke the rule.)
#
# A `None` slug is deliberate: the UI renders highlights as text chips, so a
# name with no link costs nothing and a dead link is rot.
#
# `search_name` is set wherever the bare name has a louder namesake. Canada is
# the worst region in the atlas for this and it is worse in two directions at
# once — abroad (Sydney, Halifax, Windsor, London, Paris, Hamilton, Kingston,
# Jasper, Victoria, Perth, Dorset, Windermere, Tobermory, Killarney) and one
# province over (Windsor ON/NS/QC, Victoria BC/NL, Trinity, Baddeck's Sydney).
# No downstream title guard can catch a namesake, so it is said here.
# ---------------------------------------------------------------------------
NEW = {
# ========================= BRITISH COLUMBIA =========================
"vancouver": dict(
    name="Vancouver", slug="Vancouver", country="Canada",
    region="British Columbia", type="city", tag="famous",
    emoji="🌲", sounds=["city-hum.mp3"],
    search_name="Vancouver British Columbia",
    highlights=[("Granville Island", "Granville_Island"),
                ("Gastown", "Gastown"),
                ("Capilano Suspension Bridge", "Capilano_Suspension_Bridge"),
                ("Grouse Mountain", "Grouse_Mountain"),
                ("Science World", "Science_World_(Vancouver)"),
                ("Queen Elizabeth Park", "Queen_Elizabeth_Park,_British_Columbia")],
    blurb="A city of 2.6 million wedged between the Coast Mountains and the "
          "Pacific, on a delta so tight that the downtown peninsula is 3 km "
          "across and the ski hills are visible from the office windows. "
          "Roughly half the population speaks a first language other than "
          "English, and it shows in every block of the east side.",
    fact="Vancouver has no freeway through its downtown. A planned system was "
         "killed by neighbourhood opposition in 1968 and never revived, which "
         "is the single biggest reason the West End still exists.",
    tip="Take the SeaBus to Lonsdale Quay at dusk — twelve minutes, costs a "
        "normal transit fare, and gives you the skyline view the harbour "
        "tours charge for."),
"victoria-bc": dict(
    name="Victoria", slug="Victoria,_British_Columbia", country="Canada",
    region="British Columbia", type="city", tag="famous",
    emoji="🌺", sounds=["ocean-waves.mp3"],
    search_name="Victoria British Columbia",
    highlights=[("British Columbia Parliament Buildings",
                 "British_Columbia_Parliament_Buildings"),
                ("Butchart Gardens", "Butchart_Gardens"),
                ("Fairmont Empress", "The_Empress_(hotel)"),
                ("Beacon Hill Park", "Beacon_Hill_Park"),
                ("Fisherman's Wharf", None)],
    blurb="The provincial capital sits on the southern tip of Vancouver "
          "Island, closer to Seattle than to the mainland city that governs "
          "from it. Mild enough that palms and Garry oaks share the same "
          "street, and stubbornly, self-consciously English about it.",
    fact="Victoria has the mildest winters of any Canadian city — the annual "
         "flower count in February exists so residents can tally blossoms "
         "while the rest of the country is under snow.",
    tip="Walk the Songhees waterfront path on the far side of the harbour. "
        "It is where the postcard view of the Parliament Buildings and the "
        "Empress is actually taken from, and it has no crowd."),
"whistler": dict(
    name="Whistler", slug="Whistler,_British_Columbia", country="Canada",
    region="British Columbia", type="mountain", tag="famous",
    emoji="🎿", sounds=["mountain-wind.mp3"],
    highlights=[("Whistler Blackcomb", "Whistler_Blackcomb"),
                ("Peak 2 Peak Gondola", "Peak_2_Peak_Gondola"),
                ("Whistler Mountain", "Whistler_Mountain"),
                ("Blackcomb Peak", "Blackcomb_Peak"),
                ("Green Lake", None)],
    blurb="Two mountains, 8,100 acres of lift-served terrain and a purpose-"
          "built pedestrian village at the bottom of them, 120 km up the "
          "Sea-to-Sky Highway from Vancouver. It hosted the 2010 Olympic "
          "alpine events and has been North America's busiest ski resort "
          "most seasons since.",
    fact="The Peak 2 Peak gondola spans 3.024 km between the two mountains "
         "without a single support tower — the longest unsupported lift span "
         "in the world, 436 m above the valley floor.",
    tip="Ride the Valley Trail on a bike in summer. It is 40 km of paved car-"
        "free path linking every lake in the valley, and Lost Lake at 8 a.m. "
        "belongs to whoever gets there first."),
"kelowna": dict(
    name="Kelowna", slug="Kelowna", country="Canada",
    region="British Columbia", type="city", tag="hidden",
    emoji="🍇", sounds=["city-hum.mp3"],
    highlights=[("Okanagan Lake", "Okanagan_Lake"),
                ("Myra Canyon Trestles", "Kettle_Valley_Railway"),
                ("Knox Mountain Park", None),
                ("Big White", "Big_White_Ski_Resort")],
    blurb="The centre of the Okanagan, a 135 km trench of lake and benchland "
          "that is Canada's warmest wine country and its only place that "
          "reads as desert on one slope and orchard on the other. The lake "
          "is 232 m deep and never quite warms up.",
    fact="Okanagan Lake has its own monster. Ogopogo predates the Loch Ness "
         "story in print, and the provincial government once insured a "
         "sighting reward against a claim nobody collected.",
    tip="Ride the Myra Canyon section of the Kettle Valley Rail Trail: 18 "
        "trestles and two tunnels around a canyon rim, on a railbed graded "
        "for steam engines, so it is effectively flat."),
"haida-gwaii": dict(
    name="Haida Gwaii", slug="Haida_Gwaii", country="Canada",
    region="British Columbia", type="island", tag="hidden",
    emoji="🪶", sounds=["ocean-waves.mp3"],
    highlights=[("SG̱ang Gwaay", "SGang_Gwaay"),
                ("Gwaii Haanas", "Gwaii_Haanas_National_Park_Reserve"),
                ("Naikoon Provincial Park", "Naikoon_Provincial_Park"),
                ("Skidegate", "Skidegate")],
    blurb="An archipelago of 150 islands 100 km off the north coast, "
          "isolated long enough through the last ice age that it carries "
          "plants and subspecies found nowhere else. It has been Haida "
          "territory for at least 12,500 years and was renamed from the "
          "Queen Charlotte Islands in 2010.",
    fact="The mortuary poles still standing at SG̱ang Gwaay are deliberately "
         "not maintained. The Haida decision is that they return to the "
         "forest on their own schedule, and UNESCO listed the village on "
         "those terms.",
    tip="Gwaii Haanas has no road, no dock and a visitor cap. If you cannot "
        "get a spot, Tow Hill at the north end of Graham Island is free, "
        "reachable by car and gives you the same Hecate Strait weather."),
"yoho": dict(
    name="Yoho National Park", slug="Yoho_National_Park", country="Canada",
    region="British Columbia", type="nature", tag="famous",
    emoji="💧", sounds=["waterfall.mp3"],
    highlights=[("Emerald Lake", "Emerald_Lake_(British_Columbia)"),
                ("Takakkaw Falls", "Takakkaw_Falls"),
                ("Burgess Shale", "Burgess_Shale"),
                ("Natural Bridge", None),
                ("Spiral Tunnels", "Spiral_Tunnels")],
    blurb="The west side of the same mountains Banff sits on, and quieter for "
          "it: 1,313 km² of the Kicking Horse valley, with a 254 m waterfall "
          "fed straight off the Daly Glacier and a fossil bed that rewrote "
          "what we know about early animal life.",
    fact="The Burgess Shale preserves soft-bodied animals from 508 million "
         "years ago in such detail that guts and eyes survive. Nothing else "
         "on Earth of that age comes close.",
    tip="Takakkaw Falls is loudest in late July when the glacier melt peaks. "
        "The access road has two switchbacks so tight that buses have to "
        "reverse through them — go early and go small."),
"kootenay-np": dict(
    name="Kootenay National Park", slug="Kootenay_National_Park",
    country="Canada", region="British Columbia", type="nature", tag="hidden",
    emoji="♨️", sounds=["mountain-wind.mp3"],
    highlights=[("Radium Hot Springs", "Radium_Hot_Springs,_British_Columbia"),
                ("Marble Canyon", "Marble_Canyon_(British_Columbia)"),
                ("The Paint Pots", None),
                ("Vermilion Pass", "Vermilion_Pass")],
    blurb="A park that exists because of a road: British Columbia traded the "
          "land to the federal government in 1920 in exchange for finishing "
          "the highway through it. It is a 8 km-wide ribbon either side of "
          "that road, running from a hot spring in a canyon to the "
          "Continental Divide.",
    fact="The Paint Pots are ochre beds the Ktunaxa quarried for pigment for "
         "centuries; European settlers later mined the same ochre "
         "industrially and abandoned the works, and the rusting equipment "
         "is still in the meadow.",
    tip="Drive it northbound from Radium. You climb out of a red-rock canyon "
        "into burned lodgepole regrowth and finish on the Divide, which is "
        "the whole park's geology in ninety minutes."),
"rogers-pass": dict(
    name="Rogers Pass", slug="Rogers_Pass_(British_Columbia)", country="Canada",
    region="British Columbia", type="mountain", tag="hidden",
    emoji="🚂", sounds=["mountain-wind.mp3"],
    highlights=[("Glacier National Park", "Glacier_National_Park_(Canada)"),
                ("Connaught Tunnel", "Connaught_Tunnel"),
                ("Mount Macdonald Tunnel", "Mount_Macdonald_Tunnel"),
                ("Illecillewaet Glacier", "Illecillewaet_Glacier")],
    blurb="The Selkirk crossing that finished the Canadian Pacific Railway in "
          "1885 and then spent thirty years trying to kill it. Avalanches "
          "buried the line so often the railway gave up and tunnelled under "
          "the pass instead; the highway that still runs over the top is the "
          "most heavily avalanche-controlled road in the world.",
    fact="Parks Canada and the Canadian Armed Forces shell the slopes above "
         "the highway with 105 mm howitzers to bring avalanches down on "
         "purpose — the longest-running mobile avalanche control programme "
         "anywhere.",
    tip="Stop at the Rogers Pass Discovery Centre and walk the Abandoned "
        "Rails trail behind it. You are on the original 1885 grade, with the "
        "snowshed foundations still in the trees."),
"wells-gray": dict(
    name="Wells Gray Provincial Park", slug="Wells_Gray_Provincial_Park",
    country="Canada", region="British Columbia", type="nature", tag="hidden",
    emoji="🌊", sounds=["waterfall.mp3"],
    highlights=[("Helmcken Falls", "Helmcken_Falls"),
                ("Dawson Falls", "Dawson_Falls"),
                ("Clearwater Lake", None),
                ("Spahats Creek Falls", None)],
    blurb="Five and a half thousand square kilometres of volcanic plateau "
          "north of Kamloops, known locally as the waterfall park because "
          "the lava flows left the rivers falling off a series of hard "
          "ledges. Almost none of it is reachable by car, which is why "
          "almost nobody is in it.",
    fact="In deep winter the spray from Helmcken Falls freezes into a hollow "
         "ice cone at the base that can reach 60 m — taller than the "
         "buildings in the nearest town, and it melts away every spring.",
    tip="The Helmcken viewpoint is a 200 m walk from a car park, which is why "
        "it is busy. The rim trail carries on past it for 8 km along the "
        "canyon and almost everyone turns back at the railing."),
"mount-robson": dict(
    name="Mount Robson", slug="Mount_Robson", country="Canada",
    region="British Columbia", type="mountain", tag="famous",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Berg Lake", "Berg_Lake"),
                ("Mount Robson Provincial Park", "Mount_Robson_Provincial_Park"),
                ("Kinney Lake", None),
                ("Yellowhead Pass", "Yellowhead_Pass")],
    blurb="At 3,954 m the highest peak in the Canadian Rockies, and unusual "
          "in rising almost 3,000 m straight off the valley floor beside the "
          "highway — most big mountains hide behind foothills. It makes its "
          "own weather and is clear of cloud maybe one day in ten.",
    fact="Berg Lake is named for the icebergs that calve into it off the "
         "Berg Glacier, which is one of the few glaciers in the Rockies that "
         "still reaches a lake to calve into at all.",
    tip="If the summit is in cloud, wait at the visitor centre rather than "
        "driving on. The mountain routinely clears for twenty minutes in the "
        "early evening when the valley cools."),
"joffre-lakes": dict(
    name="Joffre Lakes", slug="Joffre_Lakes_Provincial_Park", country="Canada",
    region="British Columbia", type="nature", tag="famous",
    emoji="💠", sounds=["mountain-wind.mp3"],
    highlights=[("Matier Glacier", None),
                ("Duffey Lake Road", None),
                ("Pemberton", "Pemberton,_British_Columbia")],
    blurb="Three lakes stacked up a glacial staircase above the Duffey Lake "
          "road, each one a more saturated turquoise than the last because "
          "of rock flour ground off the Matier Glacier above them. The whole "
          "climb is 10 km return and 400 m up.",
    fact="The park closes for weeks each year at the request of the Lílwat "
         "and N'Quatqua Nations, whose territory it is, so that harvesting "
         "can happen without thousands of hikers on the trail. The closure "
         "is published in advance and is not negotiable.",
    tip="The lower lake is 300 m from the car park and is the one on every "
        "photograph. Carry on to the upper lake and the glacier is directly "
        "above you, calving, with a tenth of the people."),
"sea-to-sky": dict(
    name="Sea-to-Sky Highway", slug="British_Columbia_Highway_99",
    country="Canada", region="British Columbia", type="coastal", tag="famous",
    emoji="🛣️", sounds=["ocean-waves.mp3"],
    highlights=[("Shannon Falls", "Shannon_Falls"),
                ("Stawamus Chief", "Stawamus_Chief"),
                ("Sea to Sky Gondola", "Sea_to_Sky_Gondola"),
                ("Brandywine Falls", "Brandywine_Falls_Provincial_Park"),
                ("Britannia Mine Museum", "Britannia_Mine_Museum")],
    blurb="The 100 km of Highway 99 between Horseshoe Bay and Whistler, "
          "pinned between Howe Sound and the granite of the Coast Range. "
          "Rebuilt for the 2010 Olympics, so the road is now as good as the "
          "view, which was not previously true.",
    fact="The Stawamus Chief beside the road is one of the largest granite "
         "monoliths on Earth — a single 700 m dome of it, and people are "
         "climbing the face above the traffic most summer afternoons.",
    tip="Pull in at Porteau Cove rather than the signed viewpoints. It is a "
        "provincial park with a beach, it is free, and the sound narrows "
        "there so both shores are close."),
"barkerville": dict(
    name="Barkerville", slug="Barkerville", country="Canada",
    region="British Columbia", type="history", tag="hidden",
    emoji="⛏️", sounds=["wilderness.mp3"],
    highlights=[("Cottonwood House", "Cottonwood_House_Historic_Site"),
                ("Bowron Lake Provincial Park", "Bowron_Lake_Provincial_Park"),
                ("Wells", "Wells,_British_Columbia"),
                ("Williams Creek", None)],
    blurb="A gold-rush town of 1862 preserved as 107 standing buildings at "
          "1,265 m in the Cariboo Mountains, at the end of a road that goes "
          "nowhere else. At its height it claimed to be the largest town "
          "north of San Francisco and west of Chicago; the claim was "
          "probably false and the town believed it anyway.",
    fact="Barkerville's Chinatown was one of the largest in North America "
         "outside the coast cities, and the Chee Kung Tong building still "
         "standing on the main street is the oldest of its kind in Canada.",
    tip="Stay in Wells, 8 km away. It is a working village of 200 people "
        "with a good bakery and no admission gate, and you can be at "
        "Barkerville's door when it opens."),
"osoyoos": dict(
    name="Osoyoos", slug="Osoyoos", country="Canada",
    region="British Columbia", type="desert", tag="hidden",
    emoji="🌵", sounds=["desert-wind.mp3"],
    highlights=[("Osoyoos Lake", "Osoyoos_Lake"),
                ("Spotted Lake", "Spotted_Lake"),
                ("Nk'Mip Desert Cultural Centre", None),
                ("Anarchist Mountain", None)],
    blurb="The hottest, driest place in Canada, on the border, at the bottom "
          "of the Okanagan trench. This is the northern tip of the Great "
          "Basin's shrub-steppe — antelope-brush, rattlesnakes, burrowing "
          "owls — and it is the only ecosystem of its kind the country has.",
    fact="Osoyoos Lake is the warmest freshwater lake in Canada, routinely "
         "24°C in summer, which is why a town of 5,000 has more motel rooms "
         "than most cities ten times its size.",
    tip="Drive up Anarchist Mountain on Highway 3 for six switchbacks and "
        "then stop. The whole valley, the lake and the border line through "
        "it are laid out below you, and the pull-out is free."),
"telegraph-cove": dict(
    name="Telegraph Cove", slug="Telegraph_Cove", country="Canada",
    region="British Columbia", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Johnstone Strait", "Johnstone_Strait"),
                ("Robson Bight", "Robson_Bight"),
                ("Broughton Archipelago", "Broughton_Archipelago"),
                ("Alert Bay", "Alert_Bay")],
    blurb="A boardwalk village on stilts at the north end of Vancouver "
          "Island — twenty-odd painted buildings on pilings around one small "
          "cove, originally the end of a telegraph line, now the launching "
          "point for the best orca watching in the country.",
    fact="Robson Bight, a few kilometres east, has gravel beaches that "
         "northern resident orcas use to rub themselves. It is a closed "
         "ecological reserve — boats must stay out, and the whales use it "
         "anyway, which is the point.",
    tip="Go in August. The resident pods are following the salmon into "
        "Johnstone Strait then, and from the boardwalk you can sometimes "
        "hear blows before you see anything."),
"great-bear-rainforest": dict(
    name="Great Bear Rainforest", slug="Great_Bear_Rainforest",
    country="Canada", region="British Columbia", type="nature", tag="hidden",
    emoji="🌧️", sounds=["wilderness.mp3"],
    highlights=[("Princess Royal Island", "Princess_Royal_Island"),
                ("Bella Coola", "Bella_Coola"),
                ("Khutzeymateen Provincial Park", "Khutzeymateen_Provincial_Park"),
                ("Bella Bella", "Bella_Bella,_British_Columbia")],
    blurb="Six point four million hectares of temperate rainforest along the "
          "central and north coast — the largest intact stretch of it left "
          "on Earth. A 2016 agreement between First Nations, the province "
          "and the logging industry put 85% of it off limits to industrial "
          "logging permanently.",
    fact="The spirit bear is a black bear carrying a recessive gene that "
         "makes roughly one in ten of them cream-coloured on some islands "
         "here — the highest concentration anywhere, and the reason the "
         "Kitasoo/Xai'xais never told outsiders they existed.",
    tip="There is no road. Bella Coola is the one place you can drive to, "
        "down the Hill — an unpaved 18% grade off the Chilcotin plateau "
        "that most rental agreements quietly forbid."),
"prince-rupert": dict(
    name="Prince Rupert", slug="Prince_Rupert,_British_Columbia",
    country="Canada", region="British Columbia", type="coastal", tag="hidden",
    emoji="🌧️", sounds=["ocean-waves.mp3"],
    highlights=[("Museum of Northern British Columbia", None),
                ("Cow Bay", None),
                ("North Pacific Cannery", "North_Pacific_Cannery_National_Historic_Site"),
                ("Khutzeymateen Provincial Park", "Khutzeymateen_Provincial_Park")],
    blurb="The deepest ice-free harbour on North America's west coast and the "
          "wettest city in Canada — about 2.6 m of rain a year. Built as the "
          "Pacific terminus of a second transcontinental railway whose "
          "founder went down with the Titanic before it opened.",
    fact="Prince Rupert is closer to Tokyo than Vancouver is, by about a "
         "day's sailing, which is the entire economic argument for the port "
         "and has been since 1910.",
    tip="Take the ferry to Alaska or Haida Gwaii even for one leg. The "
        "Inside Passage north of here is the reason the town exists, and a "
        "walk-on foot passenger fare is a fraction of a cruise."),
"salt-spring-island": dict(
    name="Salt Spring Island", slug="Saltspring_Island", country="Canada",
    region="British Columbia", type="island", tag="hidden",
    emoji="🐑", sounds=["ocean-waves.mp3"],
    highlights=[("Ganges", "Ganges,_British_Columbia"),
                ("Mount Maxwell", None),
                ("Ruckle Provincial Park", "Ruckle_Provincial_Park"),
                ("Gulf Islands National Park Reserve",
                 "Gulf_Islands_National_Park_Reserve")],
    blurb="The largest and busiest of the Gulf Islands, in the rain shadow "
          "of Vancouver Island — dry-belt Douglas fir, arbutus peeling red "
          "off the rock, sheep on the hills and a Saturday market that has "
          "been the island's actual economy since 1978.",
    fact="Some of the island's first settlers were Black families who came "
         "from California in 1858 at the invitation of the colonial "
         "governor, on the promise of land and full citizenship. Their "
         "descendants are still here.",
    tip="Take the Fulford ferry from Swartz Bay rather than the Long Harbour "
        "one. It is the shortest crossing, lands you in the quieter half of "
        "the island, and Ruckle Park is fifteen minutes from the dock."),
"nelson-bc": dict(
    name="Nelson", slug="Nelson,_British_Columbia", country="Canada",
    region="British Columbia", type="city", tag="hidden",
    emoji="🎭", sounds=["city-hum.mp3"],
    search_name="Nelson British Columbia",
    highlights=[("Baker Street", None),
                ("Kootenay Lake", "Kootenay_Lake"),
                ("Whitewater Ski Resort", "Whitewater_Ski_Resort"),
                ("Nelson Court House", None)],
    blurb="A silver-boom town of 1897 built up a hillside above the west arm "
          "of Kootenay Lake, with something like 350 heritage buildings "
          "still standing because the boom ended before anyone could "
          "redevelop them. Draft resisters arrived in the 1960s and never "
          "left.",
    fact="Nelson's downtown is so intact that Steve Martin's *Roxanne* was "
         "filmed here in 1986 using the real streets as the set, and the "
         "fire hall in the film is the working fire hall.",
    tip="Ride Streetcar 23 along the waterfront. It is the city's original "
        "1906 tram, restored by volunteers, and it runs on a short stretch "
        "of the old right-of-way for the price of a coffee."),
"bugaboos": dict(
    name="Bugaboo Provincial Park", slug="Bugaboo_Provincial_Park",
    country="Canada", region="British Columbia", type="mountain", tag="hidden",
    emoji="🗿", sounds=["mountain-wind.mp3"],
    highlights=[("Bugaboo Spire", "Bugaboo_Spire"),
                ("Snowpatch Spire", "Snowpatch_Spire"),
                ("Conrad Kain Hut", None),
                ("Purcell Mountains", "Purcell_Mountains")],
    blurb="A cluster of granite spires standing straight out of a glacier in "
          "the Purcells — Bugaboo, Snowpatch, Pigeon, Howser — with faces of "
          "700 m and no approach that is not up ice. It is one of the "
          "handful of alpine rock destinations in the world climbers travel "
          "internationally for.",
    fact="Cars left at the trailhead have to be fenced in chicken wire. "
         "Porcupines here have learned to chew brake lines and tyres for the "
         "salt, and the wire is stacked at the car park for you to use.",
    tip="You do not have to climb anything. The hut trail is 5 km and 700 m "
        "up, ends at the toe of the Bugaboo Glacier, and puts you directly "
        "under Snowpatch's east face."),
"hells-gate": dict(
    name="Hell's Gate", slug="Hells_Gate_(British_Columbia)", country="Canada",
    region="British Columbia", type="nature", tag="hidden",
    emoji="🌊", sounds=["waterfall.mp3"],
    highlights=[("Fraser Canyon", "Fraser_Canyon"),
                ("Fraser River", "Fraser_River"),
                ("Cariboo Road", "Cariboo_Road")],
    blurb="The narrowest point of the Fraser Canyon, where the whole river "
          "is forced through a 35 m gap and drops through it at 7.6 million "
          "litres a second. An airtram crosses the gorge; below it the water "
          "is genuinely frightening to look at.",
    fact="Railway blasting in 1914 dumped rock into the gap and blocked the "
         "salmon run almost completely, collapsing the Fraser sockeye "
         "fishery for decades. The concrete fishways bolted to the canyon "
         "walls were built in the 1940s to undo it and are still working.",
    tip="Simon Fraser wrote in 1808 that no human being should ever venture "
        "here. Read the plaque with his sentence on it while standing on the "
        "suspension bridge, which is the correct way to receive it."),
"alert-bay": dict(
    name="Alert Bay", slug="Alert_Bay", country="Canada",
    region="British Columbia", type="village", tag="hidden",
    emoji="🪶", sounds=["ocean-waves.mp3"],
    highlights=[("U'mista Cultural Centre", "U'mista_Cultural_Centre"),
                ("Cormorant Island", "Cormorant_Island_(British_Columbia)"),
                ("Namgis Burial Grounds", None),
                ("Johnstone Strait", "Johnstone_Strait")],
    blurb="A village on Cormorant Island shared by the 'Namgis First Nation "
          "and a former cannery settlement, reachable by a 45-minute ferry. "
          "It holds one of the world's tallest totem poles and the best "
          "collection of Kwakwaka'wakw potlatch regalia anywhere.",
    fact="The U'mista collection is repatriated: masks and coppers seized by "
         "the government in a 1921 potlatch prosecution, scattered to "
         "museums and private collectors, and negotiated back one by one "
         "over fifty years. *U'mista* means the return of something taken.",
    tip="The burial grounds along the road are not a viewpoint. Photograph "
        "them from the road, do not enter, and go to U'mista instead — the "
        "masks there are shown in the order the potlatch uses them."),
"pacific-rim": dict(
    name="Pacific Rim National Park Reserve",
    slug="Pacific_Rim_National_Park_Reserve", country="Canada",
    region="British Columbia", type="coastal", tag="famous",
    emoji="🏄", sounds=["ocean-waves.mp3"],
    highlights=[("Long Beach", None),
                ("West Coast Trail", "West_Coast_Trail"),
                ("Broken Group Islands", "Broken_Group_Islands"),
                ("Ucluelet", "Ucluelet")],
    blurb="Three separate pieces of Vancouver Island's Pacific side: 16 km "
          "of open beach, a hundred islands in a sound, and the 75 km West "
          "Coast Trail. The whole coast averages more than 3 m of rain a "
          "year and the forest behind the sand shows it.",
    fact="The West Coast Trail was cut in 1907 as a lifesaving route — the "
         "shore either side had wrecked so many ships it was known as the "
         "Graveyard of the Pacific, and the path existed so survivors could "
         "walk to a lighthouse.",
    tip="Come in the winter for the storms, not despite them. Storm watching "
        "is an actual local season, the lodges price for it, and a 6 m swell "
        "against Long Beach is louder than you expect."),

# ============================== ALBERTA ==============================
"calgary": dict(
    name="Calgary", slug="Calgary", country="Canada",
    region="Alberta", type="city", tag="famous",
    emoji="🤠", sounds=["city-hum.mp3"],
    highlights=[("Calgary Tower", "Calgary_Tower"),
                ("Stampede Park", "Stampede_Park"),
                ("Studio Bell", "Studio_Bell"),
                ("Prince's Island Park", "Prince's_Island_Park"),
                ("Peace Bridge", "Peace_Bridge_(Calgary)"),
                ("Heritage Park Historical Village",
                 "Heritage_Park_Historical_Village")],
    blurb="An oil city on the prairie an hour from the Rockies, which is the "
          "whole of its character: glass towers, a downtown that empties at "
          "six, and a population that drives west every weekend. It has the "
          "most extensive elevated indoor walkway system in the world "
          "because of what January does here.",
    fact="A chinook — a dry wind falling off the mountains — can raise "
         "Calgary's temperature by 25°C in an hour. The record is a rise of "
         "27°C in the city in a single afternoon in January.",
    tip="Walk the +15 network in winter. Eighteen kilometres of enclosed "
        "bridges fifteen feet above the street, free, connecting most of "
        "downtown — you can cross the core without a coat."),
"edmonton": dict(
    name="Edmonton", slug="Edmonton", country="Canada",
    region="Alberta", type="city", tag="famous",
    emoji="🛍️", sounds=["city-hum.mp3"],
    highlights=[("West Edmonton Mall", "West_Edmonton_Mall"),
                ("Alberta Legislature Building", "Alberta_Legislature_Building"),
                ("Fort Edmonton Park", "Fort_Edmonton_Park"),
                ("Muttart Conservatory", "Muttart_Conservatory"),
                ("High Level Bridge", "High_Level_Bridge_(Edmonton)")],
    blurb="The northernmost city of a million people in North America, built "
          "around a river valley that is 22 times the size of Central Park "
          "and runs unbroken through the middle of it. Everything about the "
          "place is organised around a very short summer and a very "
          "committed winter.",
    fact="Edmonton's river valley is the largest stretch of urban parkland "
         "on the continent — 7,400 hectares, 160 km of trail, and you can "
         "walk from the university to the far east end without leaving it.",
    tip="Go to the Muttart Conservatory's four glass pyramids at night in "
        "January. They are lit from inside, the tropical one is 30°C, and "
        "the walk back across the river is the point."),
"jasper": dict(
    name="Jasper", slug="Jasper,_Alberta", country="Canada",
    region="Alberta", type="mountain", tag="famous",
    emoji="🐻", sounds=["mountain-wind.mp3"],
    search_name="Jasper Alberta",
    highlights=[("Maligne Lake", "Maligne_Lake"),
                ("Maligne Canyon", "Maligne_Canyon"),
                ("Athabasca Falls", "Athabasca_Falls"),
                ("Jasper SkyTram", "Jasper_Skytram"),
                ("Mount Edith Cavell", "Mount_Edith_Cavell"),
                ("Medicine Lake", "Medicine_Lake_(Alberta)")],
    blurb="The northern end of the Rockies parks and the biggest of them — "
          "11,000 km², roughly the size of Jamaica, with one town of 4,500 "
          "in the middle. Quieter and rougher than Banff, and the wildlife "
          "on the road is not a promotional claim.",
    fact="Medicine Lake is not really a lake. It drains through a cave "
         "system under its own bed and empties completely most autumns — one "
         "of the largest sinking rivers in the Western Hemisphere, "
         "resurfacing 16 km downstream.",
    tip="Maligne Canyon in deep winter is walked *inside*, on the frozen "
        "floor of the gorge, under ice curtains and the bridges you crossed "
        "in summer. Guided only, and worth it."),
"moraine-lake": dict(
    name="Moraine Lake", slug="Moraine_Lake", country="Canada",
    region="Alberta", type="nature", tag="famous",
    emoji="💙", sounds=["mountain-wind.mp3"],
    highlights=[("Valley of the Ten Peaks", "Valley_of_the_Ten_Peaks"),
                ("Consolation Lakes", None),
                ("Larch Valley", None),
                ("Mount Temple", "Mount_Temple_(Alberta)")],
    blurb="A rockslide-dammed lake at 1,884 m under ten peaks, and the most "
          "photographed water in Canada — it was on the back of the twenty "
          "dollar note for two decades. The colour is rock flour suspended "
          "in glacial meltwater and it changes weekly through the summer.",
    fact="Personal vehicles have been banned from the road since 2023. The "
         "car park filled by 4 a.m. and cars queued for kilometres, so Parks "
         "Canada closed it to everything but shuttles, buses and bicycles.",
    tip="Late September, when the larches in Larch Valley turn. It is the "
        "only conifer here that goes gold and drops its needles, and the "
        "hike above the lake is timed to a window of about ten days."),
"drumheller": dict(
    name="Drumheller", slug="Drumheller", country="Canada",
    region="Alberta", type="desert", tag="famous",
    emoji="🦕", sounds=["desert-wind.mp3"],
    highlights=[("Royal Tyrrell Museum", "Royal_Tyrrell_Museum"),
                ("Horseshoe Canyon", "Horseshoe_Canyon_(Alberta)"),
                ("Atlas Coal Mine", "Atlas_Coal_Mine"),
                ("Star Mine Suspension Bridge", None),
                ("Hoodoos", None)],
    blurb="You drive across flat wheat prairie and then the ground simply "
          "falls away into 120 m of striped badland. The Red Deer River cut "
          "down through 70 million years of sediment here and the layers it "
          "exposed hold one of the richest dinosaur fossil beds on Earth.",
    fact="More than fifty dinosaur species have been dug out of the valley "
         "and its surroundings — more distinct species from one small area "
         "than almost anywhere in the world.",
    tip="The Tyrrell is the reason most people come, but drive the Hoodoo "
        "Trail east to East Coulee and cross the Star Mine footbridge. It "
        "is a 1930s miners' bridge over the river, free, and usually empty."),
"dinosaur-provincial-park": dict(
    name="Dinosaur Provincial Park", slug="Dinosaur_Provincial_Park",
    country="Canada", region="Alberta", type="desert", tag="hidden",
    emoji="🦴", sounds=["desert-wind.mp3"],
    highlights=[("Red Deer River", "Red_Deer_River"),
                ("Brooks", "Brooks,_Alberta"),
                ("Red Deer River", "Red_Deer_River")],
    blurb="A UNESCO site two hours downstream of Drumheller and far stranger "
          "— 80 km² of raw badland with no road through most of it. Over "
          "sixty dinosaur species have come out of these coulees, and bones "
          "are visible weathering out of the ground on the marked trails.",
    fact="The bone bed density here is among the highest anywhere on Earth: "
         "in places a single quarry has yielded hundreds of individuals of "
         "one herding species, killed together in a flood.",
    tip="Most of the park is a restricted natural preserve you may only "
        "enter with a guide. Book the bus tour weeks ahead — the public "
        "loop road is a fraction of what is out there."),
"waterton-lakes": dict(
    name="Waterton Lakes National Park", slug="Waterton_Lakes_National_Park",
    country="Canada", region="Alberta", type="nature", tag="hidden",
    emoji="🏔️", sounds=["mountain-wind.mp3"],
    highlights=[("Prince of Wales Hotel", "Prince_of_Wales_Hotel"),
                ("Upper Waterton Lake", "Waterton_Lake"),
                ("Red Rock Canyon", None),
                ("Cameron Falls", None),
                ("Crypt Lake Trail", "Crypt_Lake_Trail")],
    blurb="Where the prairie hits the mountains with no foothills in "
          "between — you can stand with one foot on grassland and look "
          "straight up 1,200 m of rock. Joined to Montana's Glacier park in "
          "1932 as the world's first International Peace Park.",
    fact="Waterton is the windiest place in Alberta. The Prince of Wales "
         "Hotel was built on an exposed knoll in 1927 and shifted 20 cm on "
         "its foundations during construction; it has been braced ever "
         "since and still creaks audibly in a gale.",
    tip="The Crypt Lake hike involves a boat, a ladder, a natural tunnel you "
        "crawl through and a cable traverse, then a lake straddling the "
        "border. It is a full day and there is no other way in."),
"head-smashed-in": dict(
    name="Head-Smashed-In Buffalo Jump", slug="Head-Smashed-In_Buffalo_Jump",
    country="Canada", region="Alberta", type="history", tag="hidden",
    emoji="🦬", sounds=["desert-wind.mp3"],
    highlights=[("Porcupine Hills", None),
                ("Oldman River", "Oldman_River"),
                ("Fort Macleod", "Fort_Macleod")],
    blurb="A sandstone cliff on the edge of the Porcupine Hills that "
          "Blackfoot peoples used to hunt bison for at least 5,700 years — "
          "driving herds along carefully built stone drive lanes to the "
          "drop. The bone deposit below the cliff is 11 m deep.",
    fact="The name does not describe the buffalo. Blackfoot oral history "
         "says a young man stood under the cliff to watch the animals fall "
         "and was found with his skull crushed against the rock.",
    tip="The interpretive centre is built into the cliff face itself so it "
        "is invisible from the plain, and it was designed with the "
        "Blackfoot Confederacy. Start at the top level and walk down; the "
        "story is told in that order on purpose."),
"writing-on-stone": dict(
    name="Writing-on-Stone", slug="Writing-on-Stone_Provincial_Park",
    country="Canada", region="Alberta", type="history", tag="hidden",
    emoji="🪨", sounds=["desert-wind.mp3"],
    highlights=[("Milk River", "Milk_River_(Alberta–Montana)"),
                ("Sweet Grass Hills", "Sweet_Grass_Hills"),
                ("Hoodoos", None)],
    blurb="Áísínai'pi — 'it is written' — is the largest concentration of "
          "rock art on the North American plains: thousands of petroglyphs "
          "and paintings cut into soft sandstone hoodoos along the Milk "
          "River, some of them centuries old, some recording the arrival of "
          "horses and then of guns.",
    fact="One panel shows a battle with more than 250 individual figures, "
         "horses and firearms in it — a narrative record of a specific "
         "event, carved by people who were there.",
    tip="The main archaeological preserve can only be entered on a guided "
        "tour, and there are only a few a day in summer. Book before you "
        "drive: it is two and a half hours from the nearest city."),
"canmore": dict(
    name="Canmore", slug="Canmore,_Alberta", country="Canada",
    region="Alberta", type="mountain", tag="hidden",
    emoji="🧗", sounds=["mountain-wind.mp3"],
    highlights=[("Three Sisters", "Three_Sisters_(Alberta)"),
                ("Ha Ling Peak", "Ha_Ling_Peak"),
                ("Grassi Lakes", None),
                ("Bow Valley", "Bow_Valley")],
    blurb="A coal town until 1979 and a mountain town ever since, twenty "
          "minutes outside the Banff park gate — which means no park pass, "
          "cheaper beds and the same skyline. The Three Sisters stand "
          "directly over the main street.",
    fact="Ha Ling Peak is named for a Chinese cook who climbed it in 1896 on "
         "a $50 bet that he could summit and return in ten hours. He did it "
         "in about five and went back up the next day with witnesses.",
    tip="Walk the Grassi Lakes trail — an hour, two green pools, and old "
        "pictographs on the rock at the top. Take the 'more difficult' fork; "
        "it goes up beside a waterfall instead of along a service road."),
"abraham-lake": dict(
    name="Abraham Lake", slug="Abraham_Lake", country="Canada",
    region="Alberta", type="nature", tag="hidden",
    emoji="🫧", sounds=["mountain-wind.mp3"],
    highlights=[("David Thompson Highway", "Alberta_Highway_11"),
                ("Bighorn Dam", "Bighorn_Dam"),
                ("Kootenay Plains", None),
                ("Cline River", None)],
    blurb="A reservoir on the North Saskatchewan east of the Icefields, made "
          "in 1972 by the Bighorn Dam. It is famous for one winter "
          "phenomenon: methane rising off decaying plants on the lakebed "
          "freezes into stacked white discs that hang suspended in "
          "exceptionally clear ice.",
    fact="The bubbles are flammable. They are marsh gas, trapped in layers "
         "as the ice thickens, and when the surface cracks in spring the "
         "escaping methane can be lit — which is precisely why walking on "
         "the lake is more dangerous than it looks.",
    tip="The ice is best in January and February, and it is best where the "
        "wind keeps snow off it — Preacher's Point. Check thickness with "
        "somebody local; the current under this reservoir never stops."),
"lake-minnewanka": dict(
    name="Lake Minnewanka", slug="Lake_Minnewanka", country="Canada",
    region="Alberta", type="nature", tag="hidden",
    emoji="🛶", sounds=["mountain-wind.mp3"],
    highlights=[("Bankhead", "Bankhead,_Alberta"),
                ("Devil's Gap", None),
                ("Cascade Mountain", "Cascade_Mountain_(Alberta)"),
                ("Two Jack Lake", None)],
    blurb="The largest lake in Banff National Park, 21 km long, ten minutes "
          "from the town and far emptier than Lake Louise. The Nakoda name "
          "means Water of the Spirits, and the valley has been used for "
          "10,000 years.",
    fact="There is a resort village on the bottom of it. Damming in 1941 "
         "raised the lake 30 m and drowned Minnewanka Landing — streets, "
         "foundations, a hotel wharf — and scuba divers visit the "
         "submerged town in summer.",
    tip="Drive the Lake Minnewanka loop road at dawn for the bighorn sheep, "
        "then stop at Bankhead on the way back: a coal town abandoned in "
        "1922, with its concrete plant still standing in the trees."),
"elk-island": dict(
    name="Elk Island National Park", slug="Elk_Island_National_Park",
    country="Canada", region="Alberta", type="nature", tag="hidden",
    emoji="🦬", sounds=["wilderness.mp3"],
    highlights=[("Astotin Lake", None),
                ("Beaver Hills", "Beaver_Hills_(Alberta)"),
                ("Ukrainian Cultural Heritage Village",
                 "Ukrainian_Cultural_Heritage_Village")],
    blurb="A completely fenced 194 km² island of aspen parkland forty "
          "minutes east of Edmonton, and the reason plains bison still "
          "exist in numbers. Canada's first federally protected wildlife "
          "area, fenced in 1906 to hold elk and then used to save a species.",
    fact="Almost every conservation herd of plains bison in North America "
         "descends from animals shipped out of Elk Island. It has sent "
         "founder stock to Montana, Alaska, Russia and back to Banff.",
    tip="It is a Dark Sky Preserve half an hour from a million people. Drive "
        "in after dark in September, park at Astotin Lake, and let your eyes "
        "adjust for twenty minutes before you look up."),
"cypress-hills": dict(
    name="Cypress Hills", slug="Cypress_Hills_(Canada)", country="Canada",
    region="Alberta", type="nature", tag="hidden",
    emoji="🌲", sounds=["wilderness.mp3"],
    highlights=[("Fort Walsh", "Fort_Walsh"),
                ("Conglomerate Cliffs", None),
                ("Reesor Lake", None),
                ("Medicine Hat", "Medicine_Hat")],
    blurb="A plateau straddling the Alberta–Saskatchewan border that rises "
          "600 m above the surrounding prairie and is high enough to grow "
          "lodgepole pine — an island of montane forest with grassland on "
          "every side, and the highest ground in Canada between the Rockies "
          "and Labrador.",
    fact="The hills were never glaciated. Ice went round them, so plants and "
         "insects survived here that were wiped out everywhere else on the "
         "plains, and some of the species have their nearest relatives 500 "
         "km away in the Rockies.",
    tip="Fort Walsh, on the Saskatchewan side, is where the North-West "
        "Mounted Police were headquartered after the 1873 Cypress Hills "
        "Massacre. The reconstructed post sits in the valley where it "
        "happened."),
"peyto-lake": dict(
    name="Peyto Lake", slug="Peyto_Lake", country="Canada",
    region="Alberta", type="nature", tag="famous",
    emoji="🐺", sounds=["mountain-wind.mp3"],
    highlights=[("Bow Lake", "Bow_Lake_(Alberta)"),
                ("Mistaya Canyon", None),
                ("Peyto Glacier", "Peyto_Glacier"),
                ("Icefields Parkway", "Icefields_Parkway")],
    blurb="A wolf-shaped lake of impossible turquoise seen from Bow Summit, "
          "the highest point on the Icefields Parkway at 2,088 m. The colour "
          "peaks in midsummer when glacial flour off the Peyto Glacier is "
          "flowing at its heaviest.",
    fact="It is named for Bill Peyto, a Banff trail guide who once released "
         "a live lynx inside a crowded bar to clear it, and who is said to "
         "have left notes on his cabin door telling visitors what to do "
         "about the bear trap inside.",
    tip="The rebuilt viewing platform gets a bus every few minutes. Carry on "
        "up the old Bow Summit lookout trail another twenty minutes for the "
        "same lake, the glacier behind it, and nobody."),
"wood-buffalo": dict(
    name="Wood Buffalo National Park", slug="Wood_Buffalo_National_Park",
    country="Canada", region="Alberta", type="nature", tag="hidden",
    emoji="🦬", sounds=["wilderness.mp3"],
    highlights=[("Peace-Athabasca Delta", "Peace–Athabasca_Delta"),
                ("Salt Plains", None),
                ("Fort Smith", "Fort_Smith,_Northwest_Territories"),
                ("Pine Lake", None)],
    blurb="The largest national park in Canada and one of the largest on "
          "Earth — 44,807 km², bigger than Switzerland, straddling the "
          "Alberta–Northwest Territories line. It protects the world's "
          "biggest free-roaming bison herd and the only natural nesting "
          "ground of the whooping crane.",
    fact="It holds the largest dark-sky preserve in the world, and a beaver "
         "dam inside it is 850 m long — visible from orbit, and found on "
         "satellite imagery in 2007 before anyone had walked to it.",
    tip="The salt plains viewpoint off the Fort Smith road looks like snow "
        "in August. It is salt, left by springs draining an ancient seabed, "
        "and you can walk out onto it barefoot."),

# ============================ SASKATCHEWAN ============================
"saskatoon": dict(
    name="Saskatoon", slug="Saskatoon", country="Canada",
    region="Saskatchewan", type="city", tag="hidden",
    emoji="🌉", sounds=["city-hum.mp3"],
    highlights=[("Broadway Bridge", "Broadway_Bridge_(Saskatoon)"),
                ("Wanuskewin Heritage Park", "Wanuskewin_Heritage_Park"),
                ("Meewasin Valley Trail", None),
                ("Remai Modern", "Remai_Modern"),
                ("Delta Bessborough", "Delta_Bessborough")],
    blurb="Saskatchewan's largest city, built on both banks of the South "
          "Saskatchewan River with seven bridges over it — the riverbank is "
          "continuous parkland for 60 km, which is most of what people who "
          "live here will tell you about first.",
    fact="Saskatoon was founded in 1883 as a temperance colony. The "
         "settlers came from Ontario intending to build a dry community on "
         "the prairie, and the plan lasted about a decade.",
    tip="Wanuskewin, on the northern edge of the city, has 6,400 years of "
        "continuous human use — older than the pyramids — and bison were "
        "returned to the site in 2019 for the first time in 150 years."),
"regina": dict(
    name="Regina", slug="Regina,_Saskatchewan", country="Canada",
    region="Saskatchewan", type="city", tag="hidden",
    emoji="🏛️", sounds=["city-hum.mp3"],
    search_name="Regina Saskatchewan",
    highlights=[("Saskatchewan Legislative Building",
                 "Saskatchewan_Legislative_Building"),
                ("Wascana Centre", "Wascana_Centre"),
                ("RCMP Heritage Centre", "RCMP_Heritage_Centre"),
                ("Government House", "Government_House_(Saskatchewan)")],
    blurb="The provincial capital, on flat treeless plain, around a lake "
          "that was dug rather than found. Every tree in the city was "
          "planted by somebody — about 300,000 of them — which makes this "
          "one of the largest urban forests in the world grown from nothing.",
    fact="It was called Pile of Bones until 1882, after the heaps of bison "
         "skeletons left at the creek crossing. The name was changed for "
         "Queen Victoria by her daughter, who was married to the "
         "Governor General.",
    tip="Every RCMP cadet in Canada is trained at Depot Division here, and "
        "the Sunset Retreat ceremony on summer Tuesdays is free and open — "
        "the same drill, on the same square, since 1885."),
"grasslands-np": dict(
    name="Grasslands National Park", slug="Grasslands_National_Park",
    country="Canada", region="Saskatchewan", type="nature", tag="hidden",
    emoji="🌾", sounds=["wind.mp3"],
    highlights=[("70 Mile Butte", None),
                ("Frenchman River", "Frenchman_River"),
                ("Val Marie", "Val_Marie,_Saskatchewan"),
                ("Killdeer Badlands", None)],
    blurb="The only place in Canada that protects mixed-grass prairie the "
          "way it was — no fences, no crops, black-tailed prairie dog towns, "
          "and reintroduced plains bison walking through it. Two separate "
          "blocks along the Montana border, and the emptiest national park "
          "in the country.",
    fact="It is one of the darkest Dark Sky Preserves in Canada. On a "
         "moonless night the Milky Way casts a shadow here, and the nearest "
         "town light is 40 km away.",
    tip="Drive the Ecotour road in the West Block at dusk with the windows "
        "down. Prairie dogs are the only colony in the country, and the "
        "sound of the town calling is what the plains used to be."),
"prince-albert-np": dict(
    name="Prince Albert National Park", slug="Prince_Albert_National_Park",
    country="Canada", region="Saskatchewan", type="nature", tag="hidden",
    emoji="🌲", sounds=["wilderness.mp3"],
    highlights=[("Waskesiu Lake", "Waskesiu_Lake"),
                ("Grey Owl's Cabin", None),
                ("Lake Audy", None),
                ("Boundary Bog", None)],
    blurb="Where the prairie gives out and the boreal forest starts, 3,874 "
          "km² of it, with a free-ranging plains bison herd in the "
          "south-west corner and the second-largest white pelican colony in "
          "North America on a lake closed to all human entry.",
    fact="Archie Belaney lived here as Grey Owl, the celebrated Indigenous "
         "conservationist who turned out on his death in 1938 to be an "
         "Englishman from Hastings. The beaver lodge he built into his cabin "
         "wall is still there.",
    tip="The cabin is a 20 km hike or a paddle down Kingsmere Lake. Most "
        "people do it as an overnight; the rail-cart portage at the north "
        "end of the lake is part of the fun."),
"athabasca-sand-dunes": dict(
    name="Athabasca Sand Dunes", slug="Athabasca_Sand_Dunes_Provincial_Park",
    country="Canada", region="Saskatchewan", type="desert", tag="hidden",
    emoji="🏜️", sounds=["desert-wind.mp3"],
    highlights=[("Lake Athabasca", "Lake_Athabasca"),
                ("William River", None),
                ("Canadian Shield", "Canadian_Shield")],
    blurb="Active sand dunes 30 m high on the south shore of Lake Athabasca, "
          "at 59°N — the most northerly major dune field in the world, and "
          "100 km from the nearest road. They stretch 100 km along the lake "
          "and are moving.",
    fact="Ten plant species here grow nowhere else on Earth. They are "
         "endemics that evolved in place since the ice sheets left, on sand "
         "that has been shifting for 8,000 years.",
    tip="There is no road, no trail and no facility. Access is float plane "
        "from Fort McMurray or Stony Rapids, and the park asks visitors to "
        "walk in the wet sand at the waterline so the dune faces are left "
        "unmarked."),
"batoche": dict(
    name="Batoche", slug="Batoche,_Saskatchewan", country="Canada",
    region="Saskatchewan", type="history", tag="hidden",
    emoji="⚔️", sounds=["wind.mp3"],
    highlights=[("South Saskatchewan River", "South_Saskatchewan_River"),
                ("Church of Saint Antoine de Padoue", None),
                ("Duck Lake", "Duck_Lake,_Saskatchewan"),
                ("Fish Creek", None)],
    blurb="The Métis village on the South Saskatchewan where the North-West "
          "Resistance ended in May 1885 — four days of fighting against a "
          "government force ten times its size, and the last armed conflict "
          "fought on Canadian soil. The rifle pits are still visible in the "
          "grass.",
    fact="The church and rectory still standing carry bullet holes from the "
         "battle. They were never patched, on purpose, and are pointed out "
         "rather than explained.",
    tip="Walk the river lots. The long narrow strips running back from the "
        "water are the Métis survey system, laid out so every family "
        "reached the river — and they are still legible on the ground and "
        "from the air."),
"moose-jaw": dict(
    name="Moose Jaw", slug="Moose_Jaw", country="Canada",
    region="Saskatchewan", type="city", tag="hidden",
    emoji="🕳️", sounds=["city-hum.mp3"],
    highlights=[("Tunnels of Moose Jaw", None),
                ("Mac the Moose", "Mac_the_Moose"),
                ("Temple Gardens Mineral Spa", None),
                ("Crescent Park", None)],
    blurb="A railway and rumrunning town of 33,000 with a network of "
          "tunnels under its downtown, a geothermal spa drilled into a "
          "Jurassic aquifer, and about forty large murals painted on the "
          "brick. It has always been slightly more interesting than its "
          "size suggests.",
    fact="Mac the Moose, 10 m tall at the tourist office, lost the title of "
         "world's tallest moose to a Norwegian sculpture in 2015. The town "
         "raised money, added antlers in 2019, and took it back.",
    tip="Prohibition-era Chicago connections here are half legend and half "
        "record. Take the tunnel tour anyway — the Chinese immigrant "
        "labourers' story told in the other half of it is the real one."),
"big-muddy-badlands": dict(
    name="Big Muddy Badlands", slug="Big_Muddy_Badlands", country="Canada",
    region="Saskatchewan", type="desert", tag="hidden",
    emoji="🤠", sounds=["desert-wind.mp3"],
    highlights=[("Castle Butte", None),
                ("Big Beaver", "Big_Beaver,_Saskatchewan"),
                ("Coronach", "Coronach,_Saskatchewan")],
    blurb="A 55 km valley of eroded clay buttes running down to the Montana "
          "line, cut by glacial meltwater and then used by horse thieves for "
          "exactly the reason it looks like it was: nobody could see into it "
          "and there were caves.",
    fact="This was the northern end of the Outlaw Trail, a chain of hideouts "
         "running to Mexico. Sam Kelly's cave is still in the sandstone here "
         "and Butch Cassidy is said — unprovably — to have used the same "
         "route.",
    tip="Castle Butte is 60 m of clay standing alone on the valley floor and "
        "you can climb it. Do not do it after rain: the surface turns to "
        "grease and stays that way for a day."),

# ============================== MANITOBA ==============================
"winnipeg": dict(
    name="Winnipeg", slug="Winnipeg", country="Canada",
    region="Manitoba", type="city", tag="famous",
    emoji="🐻", sounds=["city-hum.mp3"],
    highlights=[("The Forks", "The_Forks"),
                ("Canadian Museum for Human Rights",
                 "Canadian_Museum_for_Human_Rights"),
                ("Manitoba Legislative Building",
                 "Manitoba_Legislative_Building"),
                ("Exchange District", "Exchange_District"),
                ("Assiniboine Park", "Assiniboine_Park"),
                ("Esplanade Riel", "Esplanade_Riel")],
    blurb="At the junction of the Red and Assiniboine rivers, a meeting "
          "place for 6,000 years and the coldest large city in the world "
          "after Ulaanbaatar. The Exchange District's warehouse blocks are "
          "so completely preserved that film crews use them as 1920s "
          "Chicago.",
    fact="A bear cub bought at White River, Ontario by a Winnipeg soldier in "
         "1914 was named Winnie after his home city, left at London Zoo, and "
         "met a boy called Christopher Robin.",
    tip="Skate the river trail in February. In a good year it is the "
        "longest naturally frozen skating trail on Earth, with warming huts "
        "designed by architects competing for the commission."),
"riding-mountain": dict(
    name="Riding Mountain National Park", slug="Riding_Mountain_National_Park",
    country="Canada", region="Manitoba", type="nature", tag="hidden",
    emoji="🌲", sounds=["wilderness.mp3"],
    highlights=[("Wasagaming", "Wasagaming"),
                ("Wasagaming", "Wasagaming"),
                ("Lake Audy Bison Enclosure", None),
                ("Manitoba Escarpment", "Manitoba_Escarpment")],
    blurb="An island of forested highland standing 450 m above the wheat on "
          "the Manitoba Escarpment, where three ecosystems meet: boreal "
          "forest, aspen parkland and a remnant of true prairie. The lake "
          "at the middle has a 1930s log-built resort village on it.",
    fact="Grey Owl worked here as a park naturalist before Prince Albert, "
         "and his cabin on Beaver Lodge Lake is still standing. He lasted "
         "six months — the beavers he brought did not like the water.",
    tip="The park has one of the highest densities of black bears in North "
        "America, and a plains bison herd in a fenced enclosure at Lake "
        "Audy you can drive into. Dawn, and stay in the car."),
"whiteshell": dict(
    name="Whiteshell Provincial Park", slug="Whiteshell_Provincial_Park",
    country="Canada", region="Manitoba", type="nature", tag="hidden",
    emoji="🪨", sounds=["wilderness.mp3"],
    highlights=[("Bannock Point Petroforms", None),
                ("Falcon Lake", "Falcon_Lake_(Manitoba)"),
                ("Pinawa Dam", "Pinawa_Dam_Provincial_Park"),
                ("Winnipeg River", "Winnipeg_River")],
    blurb="Two and a half thousand square kilometres of Canadian Shield "
          "against the Ontario border — bare granite, jack pine and about "
          "two hundred lakes. The rock here is some of the oldest exposed "
          "crust on the planet, roughly 2.7 billion years.",
    fact="The petroforms at Bannock Point are boulder outlines of snakes, "
         "turtles and human figures laid on bedrock by Anishinaabe peoples "
         "and still used ceremonially. They are not an exhibit; visitors "
         "are asked to leave tobacco and not to walk on them.",
    tip="Falcon Lake had Canada's most documented UFO incident in 1967 — a "
        "prospector burned in a grid pattern on his chest, investigated by "
        "the RCMP and the US Air Force. There is a monument. It is very "
        "strange."),
"gimli": dict(
    name="Gimli", slug="Gimli,_Manitoba", country="Canada",
    region="Manitoba", type="village", tag="hidden",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    highlights=[("Lake Winnipeg", "Lake_Winnipeg"),
                ("New Iceland", "New_Iceland"),
                ("Hecla Island", "Hecla_Island")],
    blurb="An Icelandic settlement on the west shore of Lake Winnipeg, "
          "founded in 1875 by refugees from a volcanic eruption and famine, "
          "which for a time governed itself as the Republic of New Iceland "
          "with its own constitution and language.",
    fact="A Boeing 767 ran out of fuel at 41,000 ft in 1983 and glided 100 "
         "km to land on Gimli's decommissioned runway, which had been turned "
         "into a drag strip with people on it. Nobody died. It is known as "
         "the Gimli Glider.",
    tip="Íslendingadagurinn, the Icelandic Festival, has run since 1890 — "
        "the oldest continuous ethnic festival in North America. Otherwise "
        "come in February, when the lake ice throws up pressure ridges."),
"hecla": dict(
    name="Hecla Island", slug="Hecla-Grindstone_Provincial_Park", country="Canada",
    region="Manitoba", type="island", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    highlights=[("Lake Winnipeg", "Lake_Winnipeg"),
                ("Gimli", "Gimli,_Manitoba"),
                ("Grindstone Point", None)],
    blurb="An island in Lake Winnipeg reached by causeway, settled by "
          "Icelanders in 1876 and largely emptied when the province "
          "expropriated it for a park in the 1970s. The village they left — "
          "church, school, fish station — has been restored and stands "
          "empty on the shore.",
    fact="Lake Winnipeg is the tenth-largest freshwater lake in the world by "
          "surface area but averages only 12 m deep, so it whips into "
          "dangerous waves faster than almost any comparable body of water.",
    tip="Grindstone Point at the north end is where the moose are, most "
        "reliably at dusk in the marsh. Bring what you need — there is one "
        "resort on the island and nothing else."),

# =============================== ONTARIO ===============================
"toronto": dict(
    name="Toronto", slug="Toronto", country="Canada",
    region="Ontario", type="city", tag="famous",
    emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Distillery District", "Distillery_District"),
                ("Kensington Market", "Kensington_Market"),
                ("St. Lawrence Market", "St._Lawrence_Market"),
                ("Royal Ontario Museum", "Royal_Ontario_Museum"),
                ("Toronto Islands", "Toronto_Islands"),
                ("Casa Loma", "Casa_Loma")],
    blurb="Canada's largest city, and by most measures the most "
          "multicultural on Earth — half the people living here were born "
          "somewhere else, and more than 160 languages are spoken. It "
          "sprawls along the Lake Ontario shore for 50 km.",
    fact="Toronto has a 30 km network of tunnels under downtown called the "
         "PATH, connecting 75 buildings. It exists because of the winter, "
         "and in January a large part of the financial district commutes "
         "without going outside.",
    tip="Take the ferry to Ward's Island. There are car-free lanes of "
        "cottages out there, lived in year-round by about 700 people, and a "
        "view back at the skyline that nobody in the towers has."),
"ottawa": dict(
    name="Ottawa", slug="Ottawa", country="Canada",
    region="Ontario", type="city", tag="famous",
    emoji="🍁", sounds=["city-hum.mp3"],
    highlights=[("Parliament Hill", "Parliament_Hill"),
                ("Rideau Canal", "Rideau_Canal"),
                ("ByWard Market", "ByWard_Market"),
                ("National Gallery of Canada", "National_Gallery_of_Canada"),
                ("Canadian War Museum", "Canadian_War_Museum")],
    blurb="The capital, chosen in 1857 by Queen Victoria partly because it "
          "sat on the language border and partly because it was far enough "
          "from the American frontier to be defensible. A lumber town that "
          "had to grow into the job.",
    fact="The Rideau Canal freezes into a 7.8 km skateway each winter and "
         "people commute to work on it. Warm winters have closed it "
         "entirely — in 2023 it did not open for a single day for the first "
         "time in 53 years.",
    tip="The Peace Tower carillon has 53 bells and is played most weekday "
        "noons, free, with the elevator up the tower running before it. "
        "Almost nobody books it."),
"algonquin": dict(
    name="Algonquin Provincial Park", slug="Algonquin_Provincial_Park",
    country="Canada", region="Ontario", type="nature", tag="famous",
    emoji="🛶", sounds=["wilderness.mp3"],
    highlights=[("Barron Canyon", None),
                ("Canoe Lake", "Canoe_Lake_(Nipissing_District)"),
                ("Highway 60", None),
                ("Lake Opeongo", "Lake_Opeongo")],
    blurb="Ontario's oldest provincial park, 7,653 km² of maple hills, "
          "spruce bog and about 2,400 lakes linked by portages. One highway "
          "crosses the southern edge; everything else is reached by canoe, "
          "and has been since 1893.",
    fact="Tom Thomson, whose paintings shaped how Canadians picture their "
         "own country, drowned on Canoe Lake here in 1917 under "
         "circumstances still argued about. He was 39.",
    tip="Go on an August Thursday for the public wolf howl — staff locate a "
        "pack, then drive several hundred people out at night to howl at it "
        "and wait. When the pack answers, the sound carries for kilometres."),
"thousand-islands": dict(
    name="Thousand Islands", slug="Thousand_Islands", country="Canada",
    region="Ontario", type="island", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Boldt Castle", "Boldt_Castle"),
                ("Gananoque", "Gananoque"),
                ("Thousand Islands Bridge", "Thousand_Islands_Bridge"),
                ("Singer Castle", "Singer_Castle")],
    blurb="1,864 islands in the St. Lawrence where it leaves Lake Ontario, "
          "split down the middle by the Canada–US border. To count as one, "
          "an island must stay above water year-round and support at least "
          "two living trees.",
    fact="Just Room Enough Island holds a single house with a tree and a "
         "few feet of yard, and is one of the smallest inhabited islands in "
         "the world. Zavikon Island next door claims the shortest "
         "international bridge — though both ends are actually in Canada.",
    tip="Boldt Castle was abandoned mid-construction in 1904 when the "
        "owner's wife died and he telegraphed the crew to stop. It sat open "
        "to the weather for 73 years before restoration began."),
"bruce-peninsula": dict(
    name="Bruce Peninsula National Park", slug="Bruce_Peninsula_National_Park",
    country="Canada", region="Ontario", type="coastal", tag="famous",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    highlights=[("The Grotto", None),
                ("Niagara Escarpment", "Niagara_Escarpment"),
                ("Bruce Trail", "Bruce_Trail"),
                ("Tobermory", "Tobermory,_Ontario"),
                ("Flowerpot Island", "Flowerpot_Island")],
    blurb="White dolomite cliffs dropping into water so clear you can watch "
          "the bottom fall away, at the top of the Niagara Escarpment where "
          "it separates Georgian Bay from Lake Huron. The colour is real and "
          "the water is 10°C in July.",
    fact="Eastern white cedars growing out of the cliff face here are among "
         "the oldest trees in eastern North America — one was dated at over "
         "1,300 years. They are a few metres tall, twisted, and were found "
         "only in 1988.",
    tip="Grotto parking must be reserved and sells out weeks ahead in "
        "summer. Come in October instead: the escarpment maples turn, the "
        "water is still clear, and you can park."),
"tobermory": dict(
    name="Tobermory", slug="Tobermory,_Ontario", country="Canada",
    region="Ontario", type="village", tag="hidden",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    search_name="Tobermory Ontario",
    highlights=[("Fathom Five National Marine Park",
                 "Fathom_Five_National_Marine_Park"),
                ("Flowerpot Island", "Flowerpot_Island"),
                ("Big Tub Lighthouse", None),
                ("Georgian Bay", "Georgian_Bay")],
    blurb="A harbour village of 900 at the tip of the Bruce Peninsula, "
          "where the ferry to Manitoulin leaves and where divers come for "
          "the wrecks — twenty-two of them in Canada's first national "
          "marine conservation area, in water clear enough to see from a "
          "glass-bottom boat.",
    fact="The Sweepstakes, a schooner sunk in 1885, lies in 6 m of water in "
         "Big Tub Harbour and is one of the best-preserved 19th-century "
         "wooden wrecks anywhere. You can see the whole hull from the "
         "surface.",
    tip="Flowerpot Island is named for two sea stacks of layered rock "
        "standing on the shore. Take the first boat, walk the loop, and "
        "catch a later one back — most people give themselves 90 minutes "
        "and rush it."),
"manitoulin": dict(
    name="Manitoulin Island", slug="Manitoulin_Island", country="Canada",
    region="Ontario", type="island", tag="hidden",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    highlights=[("Bridal Veil Falls", None),
                ("Cup and Saucer Trail", None),
                ("Wiikwemkoong", "Wiikwemkoong_Unceded_Territory"),
                ("Little Current", "Little_Current,_Ontario")],
    blurb="The largest freshwater island in the world, in Lake Huron, with "
          "108 lakes of its own on it — and one of those lakes has islands, "
          "and one of those islands has a pond. It is also home to six "
          "First Nations.",
    fact="Wiikwemkoong is the only officially unceded Indian reserve in "
         "Canada. Its people declined to sign the 1862 treaty that "
         "surrendered the rest of the island, and the land was never given "
         "up.",
    tip="The swing bridge at Little Current opens for 15 minutes on the "
        "hour all summer, stopping every car on and off the island. Locals "
        "plan around it; visitors sit and watch the boats, which is better."),
"georgian-bay": dict(
    name="Georgian Bay", slug="Georgian_Bay", country="Canada",
    region="Ontario", type="nature", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Thirty Thousand Islands", "Thirty_Thousand_Islands"),
                ("Killbear Provincial Park", "Killbear_Provincial_Park"),
                ("Parry Sound", "Parry Sound, Ontario"),
                ("Bruce Peninsula", "Bruce_Peninsula")],
    blurb="A bay so large it was nearly named the sixth Great Lake — 15,000 "
          "km² of Lake Huron behind the Bruce Peninsula, with the largest "
          "freshwater archipelago on the planet along its eastern shore: "
          "roughly 30,000 islands of bare pink granite and wind-bent pine.",
    fact="The Group of Seven painted this shoreline so often that the "
         "twisted white pines on the rock became shorthand for Canada "
         "itself. Many of the exact trees have been located and are still "
         "standing.",
    tip="Killbear's Lighthouse Point at sunset gives you the whole thing "
        "without a boat — smoothed granite, one leaning pine, and open "
        "water to the horizon."),
"killarney": dict(
    name="Killarney Provincial Park", slug="Killarney_Provincial_Park",
    country="Canada", region="Ontario", type="nature", tag="hidden",
    emoji="⛰️", sounds=["wilderness.mp3"],
    highlights=[("La Cloche Mountains", "La_Cloche_Mountains"),
                ("Silver Peak", None),
                ("George Lake", None),
                ("Killarney", "Killarney,_Ontario")],
    blurb="White quartzite ridges above lakes so clear they look empty, on "
          "the north shore of Georgian Bay. The La Cloche range is over a "
          "billion years old and was once higher than the Rockies; what is "
          "left is the hard white core.",
    fact="The park exists because A.Y. Jackson of the Group of Seven "
         "campaigned to stop logging around Trout Lake in 1933. The "
         "province protected it, and the lake was renamed O.S.A. Lake for "
         "the Ontario Society of Artists.",
    tip="The clarity is partly acid rain damage from Sudbury's smelters — "
        "the lakes went sterile in the 1970s. They are recovering now, and "
        "some have fish again for the first time in fifty years."),
"sudbury": dict(
    name="Sudbury", slug="Greater_Sudbury", country="Canada",
    region="Ontario", type="city", tag="hidden",
    emoji="🪨", sounds=["city-hum.mp3"],
    highlights=[("Big Nickel", "Big_Nickel"),
                ("Science North", "Science_North"),
                ("Sudbury Basin", "Sudbury_Basin"),
                ("Inco Superstack", "Inco_Superstack")],
    blurb="A mining city built inside a 62 km impact crater — the second "
          "largest confirmed on Earth, made by an object 10 km across about "
          "1.85 billion years ago, which is why the nickel is here at all.",
    fact="Apollo astronauts trained here in 1971, and the story that it was "
         "because Sudbury looked like the Moon is wrong. They came to learn "
         "how to read shatter cones — the rock fractures an impact leaves.",
    tip="The city has planted over 10 million trees since 1978 to reverse "
        "a century of smelter damage that stripped the hills to black rock. "
        "It is the largest regreening programme on Earth and it worked."),
"thunder-bay": dict(
    name="Thunder Bay", slug="Thunder_Bay", country="Canada",
    region="Ontario", type="city", tag="hidden",
    emoji="⛰️", sounds=["city-hum.mp3"],
    highlights=[("Sleeping Giant", "Sleeping_Giant_(Ontario)"),
                ("Kakabeka Falls", "Kakabeka_Falls"),
                ("Fort William Historical Park",
                 "Fort_William_Historical_Park"),
                ("Terry Fox Monument", None)],
    blurb="On the north shore of Lake Superior, where the grain from the "
          "prairies used to meet the ships. A mesa across the harbour lies "
          "on the water in the shape of a reclining figure, 11 km long, and "
          "the whole city is oriented to it.",
    fact="Terry Fox ended his Marathon of Hope just east of here in "
         "September 1980, after 143 days and 5,373 km, when the cancer "
         "reached his lungs. The monument stands at the spot.",
    tip="Kakabeka Falls is 40 m and boardwalked to the lip, but the gorge "
        "below is the interesting part — 1.6-billion-year-old fossils in "
        "the shale, some of the oldest visible life on the planet."),
"lake-superior-park": dict(
    name="Lake Superior Provincial Park", slug="Lake_Superior_Provincial_Park",
    country="Canada", region="Ontario", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Agawa Rock Pictographs", None),
                ("Lake Superior", "Lake_Superior"),
                ("Agawa Canyon", "Agawa_Canyon"),
                ("Old Woman Bay", None)],
    blurb="1,550 km² of Superior coastline between Sault Ste. Marie and "
          "Wawa — cobble beaches, headlands, and a lake so cold and so deep "
          "it holds 10% of the world's fresh surface water and makes its "
          "own weather.",
    fact="The Agawa Rock pictographs were painted in red ochre on a lakeside "
         "cliff by Ojibwe artists, including Mishipeshu, the horned "
         "underwater lynx said to control the lake. They have survived "
         "centuries of spray.",
    tip="You reach the paintings on a sloping ledge at the waterline. If "
        "there is any swell at all, the park closes it — and people have "
        "been swept off. Check before you drive in."),
"point-pelee": dict(
    name="Point Pelee National Park", slug="Point_Pelee_National_Park",
    country="Canada", region="Ontario", type="nature", tag="hidden",
    emoji="🦋", sounds=["wilderness.mp3"],
    highlights=[("Lake Erie", "Lake_Erie"),
                ("Leamington", "Leamington,_Ontario"),
                ("Pelee Island", "Pelee_Island")],
    blurb="A sand spit tapering into Lake Erie at the southernmost point of "
          "mainland Canada — further south than northern California — with "
          "Carolinian forest and marsh that exists nowhere else in the "
          "country.",
    fact="Monarch butterflies gather here in September before crossing the "
         "lake on their way to Mexico. In a good year they hang in clusters "
         "heavy enough to bend the branches, waiting for a north wind.",
    tip="Early May is the birding. The point funnels warblers crossing the "
        "lake into a few hundred metres of trees, and on the right morning "
        "you can see thirty species before breakfast."),
"agawa-canyon": dict(
    name="Agawa Canyon", slug="Agawa_Canyon", country="Canada",
    region="Ontario", type="nature", tag="hidden",
    emoji="🚂", sounds=["waterfall.mp3"],
    highlights=[("Algoma Central Railway", "Algoma_Central_Railway"),
                ("Sault Ste. Marie", "Sault_Ste._Marie,_Ontario"),
                ("Agawa River", None)],
    blurb="A canyon 175 km north of Sault Ste. Marie with no road to it. "
          "The only way in is a train that runs up the Algoma Central line, "
          "drops you in the bottom for two hours, and takes you back.",
    fact="The Group of Seven rented a converted boxcar and had it shunted "
         "onto sidings along this line in the early 1920s, living in it for "
         "weeks and painting whatever the siding faced.",
    tip="The last week of September and first of October is when the "
        "hardwood turns, and the train sells out months ahead. The rest of "
        "the summer it runs half empty through the same canyon."),
"petroglyphs": dict(
    name="Petroglyphs Provincial Park", slug="Petroglyphs_Provincial_Park",
    country="Canada", region="Ontario", type="history", tag="hidden",
    emoji="🪨", sounds=["wilderness.mp3"],
    highlights=[("Kinomagewapkong", None),
                ("McGinnis Lake", None),
                ("Peterborough", "Peterborough,_Ontario")],
    blurb="The largest concentration of Indigenous rock carvings in Canada "
          "— over 900 figures cut into a single sheet of white marble, "
          "carved between 900 and 1400 CE and lost under moss until 1954.",
    fact="The Ojibwe name is Kinomagewapkong, the rocks that teach. An "
         "underground stream runs beneath the outcrop, and the sound of "
         "water coming up through the fissures is understood as the reason "
         "this rock was chosen.",
    tip="Photography of the carvings is not permitted — this is a sacred "
        "site with a building put over it in 1984 to stop acid rain "
        "erasing it. McGinnis Lake nearby is one of a handful of meromictic "
        "lakes in Canada, and is turquoise."),
"niagara-on-the-lake": dict(
    name="Niagara-on-the-Lake", slug="Niagara-on-the-Lake", country="Canada",
    region="Ontario", type="town", tag="hidden",
    emoji="🍇", sounds=["city-hum.mp3"],
    highlights=[("Fort George", "Fort_George,_Ontario"),
                ("Shaw Festival", None),
                ("Niagara Escarpment", "Niagara_Escarpment"),
                ("Queenston Heights", "Queenston_Heights")],
    blurb="The first capital of Upper Canada, burned to the ground by "
          "American forces in December 1813 and rebuilt in brick — which is "
          "why an entire Georgian streetscape survives here, at the mouth of "
          "the Niagara River among the vineyards.",
    fact="Canada's first parliament sat here in 1792 and passed the first "
         "act in the British Empire limiting slavery. It did not free "
         "anyone already enslaved, but it banned bringing in more.",
    tip="Icewine is the local specialty and it is made by picking frozen "
        "grapes at −8°C, usually in January at night. Several wineries will "
        "let you come out and help if you ask well ahead."),
"prince-edward-county": dict(
    name="Prince Edward County", slug="Prince_Edward_County,_Ontario",
    country="Canada", region="Ontario", type="nature", tag="hidden",
    emoji="🍷", sounds=["ocean-waves.mp3"],
    search_name="Prince Edward County Ontario",
    highlights=[("Sandbanks Provincial Park", "Sandbanks_Provincial_Park"),
                ("Picton", "Picton,_Ontario"),
                ("Lake on the Mountain", "Lake_on_the_Mountain_Provincial_Park"),
                ("Wellington", "Wellington,_Ontario")],
    blurb="An island county in Lake Ontario, joined by bridges, that went "
          "from canning tomatoes to growing pinot noir in about twenty "
          "years. Limestone soil, a long shoreline, and the largest "
          "freshwater baymouth dune system in the world.",
    fact="Lake on the Mountain sits 60 m above Lake Ontario with no visible "
         "inflow and never drops. It was long thought bottomless; it is a "
         "collapsed karst sinkhole fed from underground.",
    tip="Sandbanks is three separate beaches and the dunes behind them run "
        "to 25 m. Day passes are capped and go online at 7 a.m.; the West "
        "Lake dunes are the ones worth the walk."),
# The shipped roster already has elora-gorge (the conservation area, slug
# Elora_Gorge) and elora-quarry. This is the village itself — a separate
# article and a separate place, the way tobermory sits beside
# bruce-peninsula.
"elora": dict(
    name="Elora", slug="Elora,_Ontario", country="Canada",
    region="Ontario", type="village", tag="hidden",
    emoji="🪨", sounds=["waterfall.mp3"],
    search_name="Elora Ontario",
    highlights=[("Elora Gorge", "Elora_Gorge"),
                ("Grand River", "Grand_River_(Ontario)"),
                ("Elora Mill", None),
                ("Fergus", "Fergus,_Ontario")],
    blurb="A stone village of 7,000 on the lip of a limestone gorge 22 m "
          "deep, where the Grand River turns a corner under a five-storey "
          "1832 mill. Almost the whole main street is cut limestone.",
    fact="The Tooth of Time, an isolated limestone pillar in the river "
         "below the mill, is what is left of the gorge wall the water has "
         "already removed. It is slowly going too.",
    tip="Tubing the gorge is the local summer institution — helmet and "
        "lifejacket required, and the conservation area rents both. The "
        "quarry caps entry and fills by mid-morning on hot weekends."),
"cheltenham-badlands": dict(
    name="Cheltenham Badlands", slug="Cheltenham_Badlands", country="Canada",
    region="Ontario", type="nature", tag="hidden",
    emoji="🔴", sounds=["wind.mp3"],
    highlights=[("Niagara Escarpment", "Niagara_Escarpment"),
                ("Bruce Trail", "Bruce_Trail"),
                ("Caledon", "Caledon,_Ontario")],
    blurb="A hillside of bare red shale striped with grey-green bands, "
          "40 minutes from Toronto and about four hectares in total — an "
          "accident of 1930s cattle farming that stripped the topsoil off "
          "Queenston shale and let it erode into gullies.",
    fact="The red is iron oxide; the green stripes are the same iron "
         "chemically reduced by groundwater seeping along the bedding "
         "planes. The whole formation is 450 million years old and was sea "
         "floor.",
    tip="Walking on the shale was closed in 2015 because visitors were "
        "wearing it away faster than erosion. There is a boardwalk now and "
        "paid parking — go on a weekday, the lot is tiny."),
"sault-ste-marie": dict(
    name="Sault Ste. Marie", slug="Sault_Ste._Marie,_Ontario",
    country="Canada", region="Ontario", type="city", tag="hidden",
    emoji="🚢", sounds=["city-hum.mp3"],
    search_name="Sault Ste Marie Ontario",
    highlights=[("Soo Locks", "Soo_Locks"),
                ("St. Marys River", "St._Marys_River_(Michigan–Ontario)"),
                ("Agawa Canyon", "Agawa_Canyon"),
                ("Bushplane Heritage Centre", None)],
    blurb="On the rapids between Lake Superior and Lake Huron, where every "
          "ship moving iron ore down the lakes has to be lowered 6 m. The "
          "locks here handle more tonnage than the Panama and Suez canals "
          "combined.",
    fact="The Canadian lock built in 1895 was the first in the world "
         "operated by electricity, and the longest lock anywhere at the "
         "time. It now carries only pleasure boats.",
    tip="The Bushplane Heritage Centre is in the old water-bomber hangar on "
        "the waterfront, and it is far better than it sounds — you walk "
        "under the aircraft, and the fire-ranging history is Ontario's own."),
"midland-huronia": dict(
    name="Sainte-Marie among the Hurons",
    slug="Sainte-Marie_among_the_Hurons", country="Canada",
    region="Ontario", type="history", tag="hidden",
    emoji="⛪", sounds=["wilderness.mp3"],
    highlights=[("Midland", "Midland,_Ontario"),
                ("Penetanguishene", "Penetanguishene"),
                ("Georgian Bay", "Georgian_Bay"),
                ("Martyrs' Shrine", None)],
    blurb="A reconstructed 1639 French Jesuit mission on the Wye River, the "
          "first European settlement in what is now Ontario. It lasted ten "
          "years before the Jesuits burned it themselves and left.",
    fact="The mission held one fifth of the entire non-Indigenous "
         "population of New France. It was abandoned in 1649 during the "
         "Haudenosaunee–Wendat war, and its people fled to Christian Island "
         "where most starved that winter.",
    tip="The site is staffed by interpreters working the forge, the canoe "
        "yard and the gardens with period methods. Ask them about the "
        "Wendat longhouse rather than the chapel — it is the half of the "
        "story most visitors skip."),
"kingston": dict(
    name="Kingston", slug="Kingston,_Ontario", country="Canada",
    region="Ontario", type="city", tag="hidden",
    emoji="🏰", sounds=["city-hum.mp3"],
    search_name="Kingston Ontario",
    highlights=[("Fort Henry", "Fort_Henry_National_Historic_Site"),
                ("Kingston City Hall", "Kingston_City_Hall"),
                ("Rideau Canal", "Rideau_Canal"),
                ("Queen's University", "Queen's_University_at_Kingston")],
    blurb="Limestone city at the foot of Lake Ontario, capital of the "
          "Province of Canada from 1841 to 1844 until it was judged too "
          "close to the American border to defend. The buildings from those "
          "three years are still the best on the street.",
    fact="Fort Henry was built to protect the Rideau Canal, itself built to "
         "bypass a river the Americans could shell. Neither was ever "
         "attacked. The fort's garrison now performs a nineteenth-century "
         "drill for tourists.",
    tip="The Kingston Penitentiary, in use from 1835 to 2013, runs tours "
        "led by retired corrections officers. They sell out fast and they "
        "are not sanitised."),
"hamilton-waterfalls": dict(
    name="Hamilton Waterfalls", slug="Hamilton,_Ontario", country="Canada",
    region="Ontario", type="nature", tag="hidden",
    emoji="💧", sounds=["waterfall.mp3"],
    search_name="Hamilton Ontario waterfalls",
    highlights=[("Webster's Falls", None),
                ("Tews Falls", None),
                ("Albion Falls", None),
                ("Devil's Punchbowl", "Devil's_Punch_Bowl_(Hamilton,_Ontario)"),
                ("Niagara Escarpment", "Niagara_Escarpment")],
    blurb="A steel city with more than a hundred waterfalls inside its "
          "boundary — every creek crossing the Niagara Escarpment drops off "
          "it, and the escarpment runs right through the middle of town.",
    fact="Tews Falls is 41 m, only a few metres shorter than Niagara, and "
         "sits ten minutes from a suburban street. Hamilton calls itself the "
         "waterfall capital of the world and no one has successfully "
         "disputed it.",
    tip="The Devil's Punchbowl is a ribbon falls in a 37 m amphitheatre of "
        "banded rock — red and grey layers laid down 400 million years "
        "apart. Shuttle-only parking on summer weekends at the big three."),
"sandbanks": dict(
    name="Sandbanks Provincial Park", slug="Sandbanks_Provincial_Park",
    country="Canada", region="Ontario", type="coastal", tag="hidden",
    emoji="🏖️", sounds=["ocean-waves.mp3"],
    highlights=[("Lake Ontario", "Lake_Ontario"),
                ("Prince Edward County", "Prince_Edward_County,_Ontario"),
                ("West Lake", None)],
    blurb="The largest baymouth barrier dune formation in the world, on "
          "Lake Ontario — sand bars that grew across two bays and then piled "
          "into dunes 25 m high, with warm shallow water on both sides.",
    fact="Under the dunes are the remains of a nineteenth-century farming "
         "community. The sand moved in after the sheltering forest was cut "
         "for fuel, buried the fields, and the families left.",
    tip="The Dunes beach at the north end is the tall one and the least "
        "crowded, because you have to walk. Outlet beach is where everyone "
        "goes and where the water is warmest."),
"rideau-canal-locks": dict(
    name="Jones Falls Locks", slug="Jones_Falls,_Ontario", country="Canada",
    region="Ontario", type="history", tag="hidden",
    emoji="⚓", sounds=["waterfall.mp3"],
    highlights=[("Rideau Canal", "Rideau_Canal"),
                ("Kingston", "Kingston,_Ontario"),
                ("Westport", "Westport,_Ontario")],
    blurb="Four locks and a stone arch dam in the woods between Ottawa and "
          "Kingston, built by hand between 1827 and 1832 as part of a "
          "202 km military canal — still operated exactly as designed, with "
          "crank handles and no motors.",
    fact="When it was finished the Jones Falls dam was the highest in North "
         "America at 19 m, built dry-laid from cut stone by Scottish masons. "
         "Hundreds of the Irish labourers on the canal died of malaria, "
         "which was endemic in the swamps here.",
    tip="Come at a lock-through and watch the staff walk the beams. The "
        "whole canal is UNESCO-listed as the best-preserved slackwater "
        "canal in the Americas, and this is the set-piece."),
"wasaga-beach": dict(
    name="Wasaga Beach", slug="Wasaga_Beach", country="Canada",
    region="Ontario", type="coastal", tag="hidden",
    emoji="🏖️", sounds=["ocean-waves.mp3"],
    highlights=[("Nottawasaga Bay", "Nottawasaga_Bay"),
                ("Georgian Bay", "Georgian_Bay"),
                ("Blue Mountain", "Blue_Mountain_(ski_resort)")],
    blurb="Fourteen kilometres of sand on Nottawasaga Bay — the longest "
          "freshwater beach in the world, shallow and warm enough to wade "
          "out a long way, and packed on any hot Saturday.",
    fact="HMS Nancy, a schooner, was sunk here by American gunboats in "
         "1814. The wreck silted up and became an island in the river, "
         "which is now the site of a museum built around the recovered hull.",
    tip="Beach Area 1 is the crowd. Walk to Areas 5 and 6 at the west end "
        "for the piping plover nesting grounds and dunes — quieter, and the "
        "sunsets are across open water."),

# ===================== MUSKOKA DISTRICT, ONTARIO ======================
# Cottage country: a dedicated cluster, the same treatment the Grand River
# watershed got. Everything here sits inside PROVINCE_BOX["Muskoka
# District, Ontario"], which is a sub-box of the Ontario box — so the
# province guard here is tighter than for the rest of the province, and a
# record that drifts to another Ontario lake of the same name will trip it.
"gravenhurst": dict(
    name="Gravenhurst", slug="Gravenhurst,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="town", tag="hidden",
    emoji="🚢", sounds=["city-hum.mp3"],
    search_name="Gravenhurst Ontario Muskoka",
    highlights=[("Muskoka Wharf", "Muskoka_Wharf"),
                ("RMS Segwun", None),
                ("Bethune Memorial House", "Bethune_Memorial_House"),
                ("Lake Muskoka", "Lake_Muskoka")],
    blurb="The southern gateway to Muskoka and the first town in the "
          "district to be incorporated — a sawmill town on Lake Muskoka "
          "that turned into the harbour the steamships worked out of, and "
          "still does.",
    fact="Norman Bethune was born here in 1890. He died of septicaemia in "
         "China in 1939 after operating on Communist troops without gloves, "
         "and is one of the very few foreigners honoured by name in Chinese "
         "schoolbooks.",
    tip="The RMS Segwun, launched 1887, is the oldest operating steamship "
        "in North America and sails from the wharf all summer. The sunset "
        "cruise is two hours and the boiler is coal-fired and visible."),
"bracebridge": dict(
    name="Bracebridge", slug="Bracebridge,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="town", tag="hidden",
    emoji="💧", sounds=["waterfall.mp3"],
    search_name="Bracebridge Ontario Muskoka",
    highlights=[("Bracebridge Falls", None),
                ("Muskoka River", "Muskoka_River"),
                ("High Falls", None),
                ("Woodchester Villa", None)],
    blurb="The district seat, built where the Muskoka River drops through "
          "the middle of town — a waterfall directly under the main street "
          "bridge, and about twenty more within a short drive.",
    fact="Bracebridge was the first town in Ontario to own its own "
         "hydroelectric plant, switched on in 1894 at the falls downtown. "
         "It is still generating.",
    tip="Santa's Village has been running on the riverbank since 1955 "
        "because the town sits almost exactly on the 45th parallel — "
        "halfway to the North Pole, which was considered a sufficient "
        "reason at the time."),
"huntsville-ontario": dict(
    name="Huntsville", slug="Huntsville,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="town", tag="hidden",
    emoji="🎨", sounds=["city-hum.mp3"],
    search_name="Huntsville Ontario Muskoka",
    highlights=[("Lake Vernon", None),
                ("Muskoka Heritage Place", None),
                ("Arrowhead Provincial Park", "Arrowhead_Provincial_Park"),
                ("Algonquin Provincial Park", "Algonquin_Provincial_Park")],
    blurb="The largest town in Muskoka and the last stop before Algonquin, "
          "on a chain of four lakes joined by locks. Group of Seven murals "
          "are painted on buildings all over the downtown, at full scale.",
    fact="The 2010 G8 summit was held just outside town at Deerhurst, which "
         "left Huntsville with a great deal of infrastructure and a very "
         "long argument about a gazebo built 100 km from the venue.",
    tip="Lion's Lookout, five minutes from the main street, gives you the "
        "whole lake system at once. Go in the first week of October."),
"port-carling": dict(
    name="Port Carling", slug="Port_Carling", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="🛥️", sounds=["ocean-waves.mp3"],
    highlights=[("Lake Muskoka", "Lake_Muskoka"),
                ("Lake Rosseau", "Lake_Rosseau"),
                ("Muskoka Lakes", "Muskoka_Lakes,_Ontario")],
    blurb="The hub of the lakes — a village built around the lock that "
          "joins Lake Muskoka to Lake Rosseau, where every boat moving "
          "between the big lakes has to pass through in front of everyone "
          "sitting on the wall.",
    fact="The lock was cut in 1871 through the rapids of an Ojibwe village "
          "site, and the community there was displaced by the construction. "
          "The village is named for the provincial minister who authorised "
          "the work.",
    tip="Sit on the lock wall on a Friday evening in July. The mahogany "
        "runabouts come through one after another, and the boat-watching is "
        "the entire local sport."),
"bala": dict(
    name="Bala", slug="Bala,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="🫐", sounds=["waterfall.mp3"],
    search_name="Bala Ontario Muskoka",
    highlights=[("Bala Falls", None),
                ("Moon River", "Moon_River_(Ontario)"),
                ("Lake Muskoka", "Lake_Muskoka")],
    blurb="A village of 500 where Lake Muskoka spills into the Moon River "
          "over two sets of falls in the middle of town. It calls itself the "
          "cranberry capital of Ontario and has the bogs to back it.",
    fact="Lucy Maud Montgomery spent two weeks here in 1922 and set her "
          "novel The Blue Castle on these lakes — the only book she ever "
          "set outside Prince Edward Island.",
    tip="The Cranberry Festival in October floats the bogs and turns them "
        "red, and you can wade in. The rest of the year Don's Bakery is the "
        "reason people stop, and the line proves it."),
"windermere-ontario": dict(
    name="Windermere", slug="Windermere,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="🏨", sounds=["ocean-waves.mp3"],
    search_name="Windermere Ontario Muskoka",
    highlights=[("Lake Rosseau", "Lake_Rosseau"),
                ("Windermere House", None),
                ("Muskoka Lakes", "Muskoka_Lakes,_Ontario")],
    blurb="A hamlet on the west shore of Lake Rosseau built around one of "
          "the last surviving grand Muskoka resort hotels — white "
          "clapboard, wraparound verandah, and a lawn running to the water.",
    fact="Windermere House burned to the ground in 1996 while a film crew "
         "was shooting there, and the fire made the movie. It was rebuilt to "
         "the original 1870s design and reopened within a year.",
    tip="The golf course beside it opened in 1921 and still plays as a "
        "9-hole with the original routing. Walk the lakeshore road at dusk "
        "instead; the boathouses along it are the real architecture here."),
"rosseau": dict(
    name="Rosseau", slug="Rosseau,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    search_name="Rosseau Ontario Muskoka",
    highlights=[("Lake Rosseau", "Lake_Rosseau"),
                ("Seguin River", None),
                ("Parry Sound", "Parry_Sound,_Ontario")],
    blurb="A crossroads village at the very top of Lake Rosseau, where the "
          "steamers used to turn around and the road north to Parry Sound "
          "starts. A general store, a beach, and not much else on purpose.",
    fact="The Rosseau Falls, a few kilometres out of the village, drop "
         "through a chute of smoothed rock that people slide down. It is "
         "unsupervised, unposted and has been a local rite for a century.",
    tip="The Saturday farmers' market in the community hall runs all "
        "summer and is where the cottage kitchens actually buy. Get there "
        "before ten."),
"bigwin-island": dict(
    name="Bigwin Island", slug="Bigwin_Island", country="Canada",
    region="Muskoka District, Ontario", type="island", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    search_name="Bigwin Island Lake of Bays Muskoka",
    highlights=[("Lake of Bays", "Lake_of_Bays"),
                ("Baysville", None),
                ("Dorset", "Dorset,_Ontario"),
                ("Huntsville", "Huntsville,_Ontario")],
    blurb="The largest island on Lake of Bays, reached only by boat, and for "
          "fifty years the address of the grandest hotel in Muskoka. Most of "
          "the island is a golf course now; the rest is the shells the hotel "
          "left behind.",
    fact="There are Indigenous burial grounds on the island and immediately "
         "offshore, drowned when industrial damming raised the lake. The "
         "first developers agreed to protect every grave and to let Chief "
         "John Bigwin be buried here with his ancestors.",
    tip="The Bigwin Inn rotunda and the dining pavilion are still standing "
        "and still roofless. Come across on the ferry from the Norway Point "
        "dock rather than driving round — the approach is the point."),
"dorset": dict(
    name="Dorset", slug="Dorset,_Ontario", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="🗼", sounds=["wilderness.mp3"],
    search_name="Dorset Ontario Muskoka",
    highlights=[("Dorset Lookout Tower", None),
                ("Lake of Bays", "Lake_of_Bays"),
                ("Algonquin Provincial Park", "Algonquin_Provincial_Park")],
    blurb="A village straddling the narrows between Lake of Bays and "
          "Trading Bay, on the boundary between two counties — the main "
          "street bridge is the district line. The last supply stop before "
          "the west side of Algonquin.",
    fact="The fire tower on the hill above town is 30 m on a 142 m ridge, "
         "and the view from the top takes in about 800 km² of forest. It "
         "was a working ranger tower until aerial patrol replaced it.",
    tip="The tower in the first two weeks of October is the best hardwood "
        "colour view in Ontario and everyone knows it — cars back up on "
        "the access road. Go on a weekday at eight."),
"torrance-barrens": dict(
    name="Torrance Barrens", slug="Torrance_Barrens",
    country="Canada", region="Muskoka District, Ontario",
    type="nature", tag="hidden",
    emoji="🌌", sounds=["wilderness.mp3"],
    highlights=[("Gravenhurst", "Gravenhurst,_Ontario"),
                ("Canadian Shield", "Canadian_Shield"),
                ("Bala", "Bala,_Ontario")],
    blurb="Nineteen square kilometres of bare Shield rock, beaver ponds and "
          "stunted pine south of Bala — open enough that the sky reaches the "
          "ground in every direction, which is exactly why it was set aside.",
    fact="This was the world's first permanent designated dark-sky preserve, "
         "established in 1999. The designation binds the surrounding "
         "townships' lighting bylaws, not just the reserve itself.",
    tip="There is no lighting, no gate and no attendant — you park on the "
        "road and walk out onto the rock. Bring a red light, and check the "
        "moon phase, because a full moon here washes everything out."),
"lake-muskoka": dict(
    name="Lake Muskoka", slug="Lake_Muskoka", country="Canada",
    region="Muskoka District, Ontario", type="nature", tag="hidden",
    emoji="🏞️", sounds=["ocean-waves.mp3"],
    highlights=[("Gravenhurst", "Gravenhurst,_Ontario"),
                ("Bracebridge", "Bracebridge,_Ontario"),
                ("Port Carling", "Port_Carling"),
                ("Bala", "Bala,_Ontario")],
    blurb="The largest of the three big lakes, 120 km² with something like "
          "80 islands in it, ringed by boathouses and granite. Four towns "
          "sit on its shore and the steamships have connected them since "
          "1866.",
    fact="Muskoka chairs — the wide-armed slanted wooden chair on every "
         "dock — are the Canadian name for what Americans call an "
         "Adirondack. The original 1903 design was for a hillside in "
         "Westport, New York, and this side of the border simply renamed it.",
    tip="The lake is deep and cold well into June. Late August is when the "
        "water is actually warm, the blackflies are long gone, and the "
        "cottage traffic on Highway 11 has thinned out."),
"lake-rosseau": dict(
    name="Lake Rosseau", slug="Lake_Rosseau", country="Canada",
    region="Muskoka District, Ontario", type="nature", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    highlights=[("Port Carling", "Port_Carling"),
                ("Rosseau", "Rosseau,_Ontario"),
                ("Windermere", "Windermere,_Ontario"),
                ("Lake Joseph", "Lake_Joseph")],
    blurb="The middle lake of the three, joined to Muskoka by the Port "
          "Carling lock and to Joseph by a cut at the top — 62 km² of deep "
          "clear water with the oldest and grandest of the cottages on it.",
    fact="The lake is named for Jean-Baptiste Rousseau, a fur trader, but "
         "the spelling drifted on the surveys and never drifted back. His "
         "name is on the map wrong and has been since 1835.",
    tip="Sailing is better here than on Muskoka — the shape funnels a "
        "reliable afternoon westerly down the length of it, which is why "
        "the sailing clubs are on this lake."),
"lake-joseph": dict(
    name="Lake Joseph", slug="Lake_Joseph", country="Canada",
    region="Muskoka District, Ontario", type="nature", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Port Carling", "Port_Carling"),
                ("Lake Rosseau", "Lake_Rosseau"),
                ("Georgian Bay", "Georgian_Bay")],
    blurb="The westernmost and quietest of the three lakes, long and "
          "narrow, with the fewest towns on it and the most rock. Locals "
          "call it Lake Joe and the water is the clearest of the three.",
    fact="Joseph and Rosseau are named for a father and son — Joseph "
         "Rousseau the elder and Jean-Baptiste, both traders on Lake "
         "Ontario. Two lakes, one family, and neither name spelled the way "
         "they spelled it.",
    tip="The narrow northern arm past Hamer Bay is where the Shield is at "
        "its most exposed — bare pink rock straight into deep water, and "
        "hardly a cottage in the last few kilometres."),
"lake-of-bays": dict(
    name="Lake of Bays", slug="Lake_of_Bays", country="Canada",
    region="Muskoka District, Ontario", type="nature", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Bigwin Island", "Bigwin_Island"),
                ("Dorset", "Dorset,_Ontario"),
                ("Huntsville", "Huntsville,_Ontario"),
                ("Bigwin Island", None)],
    blurb="The fourth big lake, east of the others and shaped like nothing "
          "in particular — arms running off in five directions, which is "
          "where the name came from. Wilder shoreline, fewer boathouses.",
    fact="The Portage Flyer, a 1.6 km railway built in 1904 to carry "
         "steamer passengers over the height of land to Peninsula Lake, was "
         "the shortest commercially operated railway in the world.",
    tip="Bigwin Island is reachable by a small ferry in summer. The 1920s "
        "resort ruins on it — ballroom, rotunda, dining pavilion — are "
        "standing open, and there is a golf course threaded between them."),
"arrowhead-provincial-park": dict(
    name="Arrowhead Provincial Park", slug="Arrowhead_Provincial_Park",
    country="Canada", region="Muskoka District, Ontario",
    type="nature", tag="hidden",
    emoji="⛸️", sounds=["wilderness.mp3"],
    highlights=[("Huntsville", "Huntsville,_Ontario"),
                ("Big Bend Lookout", None),
                ("Stubb's Falls", None)],
    blurb="A small park just north of Huntsville built around a "
          "kettle lake, with a river running through hemlock and a "
          "waterfall you can hear from the campground. In winter it becomes "
          "something else entirely.",
    fact="The 1.3 km ice trail groomed through the forest here — skating "
         "between the trees under lanterns — was copied worldwide after "
         "photographs of it spread in the 2010s. It now sells timed tickets "
         "and fills instantly.",
    tip="Summer is the better-kept secret. Stubb's Falls is a ten-minute "
        "walk, the pools below it are swimmable, and nobody is there in "
        "August because everyone associates this park with January."),
"skeleton-lake": dict(
    name="Skeleton Lake", slug="Skeleton_Lake_(Ontario)",
    country="Canada", region="Muskoka District, Ontario",
    type="nature", tag="hidden",
    emoji="💎", sounds=["wilderness.mp3"],
    search_name="Skeleton Lake Muskoka Ontario",
    highlights=[("Huntsville", "Huntsville,_Ontario"),
                ("Rosseau", "Rosseau,_Ontario"),
                ("Lake Rosseau", "Lake_Rosseau"),
                ("Canadian Shield", "Canadian_Shield")],
    blurb="A deep, cold lake seventeen kilometres west of Huntsville, split "
          "between two municipalities and reached down a road that gives no "
          "hint of it. No town on the shore, no steamer, no wharf.",
    fact="The province ran a fish hatchery on this lake until 1991 — the "
         "water is cold enough and clean enough that trout eggs raised here "
         "stocked lakes across the district.",
    tip="The public access is a small beach on the south shore and it is "
        "easy to drive past. Bring a mask: on a still morning you can see "
        "the bottom drop away under you."),
"georgian-bay-islands": dict(
    name="Georgian Bay Islands National Park",
    slug="Georgian_Bay_Islands_National_Park", country="Canada",
    region="Muskoka District, Ontario", type="island", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Beausoleil Island", "Beausoleil_Island"),
                ("Honey Harbour", "Honey_Harbour"),
                ("Thirty Thousand Islands", "Thirty_Thousand_Islands"),
                ("Georgian Bay", "Georgian_Bay")],
    blurb="Sixty-three islands in southern Georgian Bay, the smallest "
          "national park in Canada, reachable only by boat. Beausoleil "
          "Island, the largest, has the Shield on its north half and "
          "hardwood forest on its south — a geological line you can walk "
          "across.",
    fact="This park has more reptile and amphibian species than anywhere "
         "else in Canada, including the eastern massasauga, Ontario's only "
         "venomous snake. It is shy, and bites are very rare.",
    tip="The DayTripper boat from Honey Harbour is the only scheduled way "
        "over. Book it — capacity is small, and the alternative is hiring a "
        "water taxi at four times the price."),
"honey-harbour": dict(
    name="Honey Harbour", slug="Honey_Harbour", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    highlights=[("Georgian Bay Islands National Park",
                 "Georgian_Bay_Islands_National_Park"),
                ("Beausoleil Island", "Beausoleil_Island"),
                ("Georgian Bay", "Georgian_Bay")],
    blurb="A marina village at the bottom end of Georgian Bay, the jumping "
          "off point for the Thirty Thousand Islands and the national park. "
          "In winter about 600 people; in July, several thousand boats.",
    fact="Every island cottage out here is supplied by water — building "
         "materials, propane, groceries and garbage all move by barge. The "
         "barge operators are the closest thing the archipelago has to a "
         "road network.",
    tip="Take the small-craft channel north from here rather than the open "
        "bay. It threads the islands for 40 km, is marked, and is the best "
        "boating in the province."),
"port-severn": dict(
    name="Port Severn", slug="Port_Severn", country="Canada",
    region="Muskoka District, Ontario", type="village", tag="hidden",
    emoji="🛥️", sounds=["waterfall.mp3"],
    highlights=[("Trent–Severn Waterway", "Trent–Severn_Waterway"),
                ("Georgian Bay", "Georgian_Bay"),
                ("Big Chute Marine Railway", "Big_Chute_Marine_Railway")],
    blurb="Lock 45, the last lock on the Trent–Severn Waterway, where "
          "boats that started at Lake Ontario 386 km ago finally drop into "
          "Georgian Bay. The smallest lock on the system and the end of the "
          "line.",
    fact="Two locks upstream is the Big Chute, which does not lower boats "
         "at all — it lifts them out of the water in a sling on a railway "
         "and carries them 18 m down a hillside on rails. It is the only "
         "one of its kind still working in North America.",
    tip="Watch a cruiser go over the Big Chute. It takes about ten minutes, "
        "runs all day in season, and the sight of a 12 m boat crossing a "
        "road on a flatcar does not get less strange."),
"mary-lake": dict(
    name="Mary Lake", slug="Mary_Lake_(Ontario)", country="Canada",
    region="Muskoka District, Ontario", type="nature", tag="hidden",
    emoji="🏊", sounds=["waterfall.mp3"],
    search_name="Mary Lake Port Sydney Muskoka",
    highlights=[("Port Sydney", None),
                ("Muskoka River", "Muskoka_River"),
                ("Huntsville", "Huntsville,_Ontario"),
                ("Bracebridge", "Bracebridge,_Ontario")],
    blurb="The lake between Bracebridge and Huntsville, with the village of "
          "Port Sydney at its south end, where the North Muskoka River comes "
          "over a wide sheet of rock into a swimming beach. One of the best "
          "free swims in the district and it is right off the highway.",
    fact="The surveyor Alexander Murray named it in 1853 after his daughter "
         "Mary Ellen. The North Muskoka River enters at one end and leaves "
         "at the other, so the whole lake is really a wide place in a river.",
    tip="The rock slabs above the dam are warm all afternoon and shallow "
        "enough to sit in. Come on a weekday — on a hot Sunday the parking "
        "is over a kilometre back up the road."),

# =============================== QUEBEC ===============================
"montreal": dict(
    name="Montreal", slug="Montreal", country="Canada",
    region="Quebec", type="city", tag="famous",
    emoji="🥯", sounds=["city-hum.mp3"],
    highlights=[("Old Montreal", "Old_Montreal"),
                ("Mount Royal", "Mount_Royal"),
                ("Notre-Dame Basilica", "Notre-Dame_Basilica_(Montreal)"),
                ("Jean-Talon Market", "Jean-Talon_Market"),
                ("Underground City", "Underground_City,_Montreal"),
                ("Habitat 67", "Habitat_67")],
    blurb="An island city of two languages and four centuries, with a "
          "mountain in the middle of it that no building is allowed to be "
          "taller than. The second-largest French-speaking city in the "
          "world after Paris.",
    fact="Montreal has more than 30 km of pedestrian tunnel under downtown "
         "connecting metro stations, malls, universities and 1,600 shops. "
         "About half a million people a day use it, most heavily in "
         "February.",
    tip="The bagels are boiled in honey water and baked in wood, which is "
        "why they are sweeter and denser than New York's. St-Viateur and "
        "Fairmount are both open 24 hours and both claim to be first."),
"quebec-city": dict(
    name="Quebec City", slug="Quebec_City", country="Canada",
    region="Quebec", type="city", tag="famous",
    emoji="🏰", sounds=["city-hum.mp3"],
    highlights=[("Citadelle of Quebec", "Citadelle_of_Quebec"),
                ("Place Royale", "Place_Royale_(Quebec_City)"),
                ("Île d'Orléans", "Île_d'Orléans"),
                ("Montmorency Falls", "Montmorency_Falls"),
                ("Quartier Petit Champlain", "Petit_Champlain")],
    blurb="Founded in 1608 on the narrowing of the St. Lawrence that gave "
          "it its name, and the only walled city north of Mexico. The "
          "fortifications still run 4.6 km around the upper town, and you "
          "can walk the whole circuit.",
    fact="The Château Frontenac is the most photographed hotel in the world "
         "and was never a castle — it is an 1893 railway hotel, built to "
         "make the Canadian Pacific's passengers feel they had arrived "
         "somewhere European.",
    tip="Take the Escalier Casse-Cou — the breakneck stairs — down into "
        "Petit-Champlain rather than the funicular. It is the oldest "
        "stairway in the city and lands you in the right place."),
"gaspesie": dict(
    name="Gaspé Peninsula", slug="Gaspé_Peninsula", country="Canada",
    region="Quebec", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Percé Rock", "Percé_Rock"),
                ("Forillon National Park", "Forillon_National_Park"),
                ("Bonaventure Island", "Bonaventure_Island"),
                ("Chic-Choc Mountains", "Chic-Choc_Mountains")],
    blurb="The peninsula where the Appalachians run into the Gulf of St. "
          "Lawrence and stop. A single road goes all the way around it past "
          "fishing villages, sea cliffs, and mountains high enough to hold "
          "tundra and caribou at 1,200 m.",
    fact="Jacques Cartier planted a cross at Gaspé in July 1534 and claimed "
         "the land for France. The Mi'kmaq chief Donnacona objected on the "
         "spot, in front of him, and Cartier took two of his sons to France "
         "anyway.",
    tip="Bonaventure Island holds the most accessible northern gannet "
        "colony on Earth — over 100,000 birds, and the trail brings you to "
        "within a few metres of them with nothing in between."),
"perce-rock": dict(
    name="Percé Rock", slug="Percé_Rock", country="Canada",
    region="Quebec", type="coastal", tag="famous",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    highlights=[("Percé", "Percé,_Quebec"),
                ("Bonaventure Island", "Bonaventure_Island"),
                ("Gulf of Saint Lawrence", "Gulf_of_Saint_Lawrence")],
    blurb="A wall of limestone 433 m long and 88 m high standing in the sea "
          "off the Gaspé coast, with an arch punched through one end. At low "
          "tide a sandbar appears and you can walk out to the foot of it.",
    fact="There were two arches until 1845, when the outer one collapsed "
         "and left the pillar now standing separately beyond it. The rock "
         "loses about 300 tonnes a year and the remaining arch will "
         "eventually go the same way.",
    tip="The tide window for walking out is posted daily in the village and "
        "is genuinely short. Rockfall means you must stay several metres "
        "back from the base — people have been killed here doing otherwise."),
"tadoussac": dict(
    name="Tadoussac", slug="Tadoussac", country="Canada",
    region="Quebec", type="village", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Saguenay Fjord", "Saguenay_Fjord"),
                ("Saguenay–St. Lawrence Marine Park",
                 "Saguenay–St._Lawrence_Marine_Park"),
                ("Saint Lawrence River", "Saint_Lawrence_River")],
    blurb="Where the Saguenay fjord meets the St. Lawrence, and where the "
          "cold deep water is forced up over a sill — which brings krill to "
          "the surface and thirteen species of whale to eat it, close "
          "enough to see from the shore.",
    fact="Tadoussac was a trading post from 1600, making it the oldest "
         "surviving French settlement in the Americas — eight years older "
         "than Quebec City. The chapel from 1747 is the oldest wooden church "
         "in Canada.",
    tip="You do not need a boat. The rocks at Pointe de l'Islet, a "
        "ten-minute walk from the village, put you on a headland where "
        "belugas and minkes pass within 50 m on the tide."),
"saguenay-fjord": dict(
    name="Saguenay Fjord", slug="Saguenay_Fjord", country="Canada",
    region="Quebec", type="nature", tag="hidden",
    emoji="⛰️", sounds=["ocean-waves.mp3"],
    highlights=[("Tadoussac", "Tadoussac"),
                ("Cap Trinité", "Cap_Trinité"),
                ("Sainte-Rose-du-Nord", "Sainte-Rose-du-Nord"),
                ("L'Anse-Saint-Jean", "L'Anse-Saint-Jean")],
    blurb="One of the southernmost fjords in the world, 105 km of cliff "
          "walls up to 350 m above water 270 m deep, cut by ice and filled "
          "by the sea. A resident population of about 900 belugas lives in "
          "it year-round.",
    fact="The fjord's water is layered: cold salt water from the Gulf on "
         "the bottom, fresh river water on top. Arctic species live below "
         "and freshwater species above, in the same channel.",
    tip="The statue of Notre-Dame-du-Saguenay stands on a ledge 180 m up "
        "the cliff at Cap Trinité, carved in 1881 by a man who fell "
        "through the ice and survived. The trail up is 3.5 km and steep."),
"mont-tremblant": dict(
    name="Mont-Tremblant", slug="Mont-Tremblant", country="Canada",
    region="Quebec", type="mountain", tag="famous",
    emoji="🎿", sounds=["wilderness.mp3"],
    highlights=[("Mont Tremblant (mountain)", "Mont_Tremblant"),
                ("Mont-Tremblant National Park",
                 "Mont-Tremblant_National_Park"),
                ("Laurentian Mountains", "Laurentian_Mountains")],
    blurb="The highest peak in the Laurentians at 875 m, with a "
          "pedestrian village of coloured roofs at its foot and a national "
          "park of 1,510 km² behind it — six rivers, four hundred lakes and "
          "no road through the middle.",
    fact="The Algonquin name is Manitou Ewitchi Saga, the mountain of the "
         "spirit — because they believed disturbing it would make it "
         "tremble. The French translated the trembling and dropped the "
         "spirit.",
    tip="The village is a resort and reads like one. Drive twenty minutes "
        "into the park at Lac Monroe instead: same mountains, canoe rentals "
        "on a lake with no buildings on it."),
"charlevoix": dict(
    name="Charlevoix", slug="Charlevoix", country="Canada",
    region="Quebec", type="nature", tag="hidden",
    emoji="🌾", sounds=["wilderness.mp3"],
    search_name="Charlevoix Quebec",
    highlights=[("Baie-Saint-Paul", "Baie-Saint-Paul"),
                ("La Malbaie", "La_Malbaie"),
                ("Hautes-Gorges-de-la-Rivière-Malbaie National Park",
                 "Hautes-Gorges-de-la-Rivière-Malbaie_National_Park"),
                ("Isle-aux-Coudres", "Isle-aux-Coudres")],
    blurb="A region of hills and farmland dropping straight into the St. "
          "Lawrence, all of it sitting inside a 56 km meteorite crater. The "
          "rim is why the landscape suddenly rumples here and nowhere else "
          "on this shore.",
    fact="The impact was about 400 million years ago and left a central "
         "uplift that is now Mont des Éboulements. Roughly 90% of "
         "Charlevoix's population lives inside the crater, farming its floor.",
    tip="Hautes-Gorges has the highest rock walls east of the Rockies — "
        "800 m of them straight out of the river. The boat up the Malbaie "
        "is the only way to see the full height."),
"iles-de-la-madeleine": dict(
    name="Îles de la Madeleine", slug="Magdalen_Islands", country="Canada",
    region="Quebec", type="island", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Gulf of Saint Lawrence", "Gulf_of_Saint_Lawrence"),
                ("Cap-aux-Meules", "Cap-aux-Meules"),
                ("Havre-Aubert", "Havre-Aubert")],
    blurb="An archipelago in the middle of the Gulf of St. Lawrence, "
          "215 km from the Gaspé and joined to itself by long thin sand "
          "dunes. Red sandstone cliffs, coloured houses, 300 km of beach "
          "and about 12,000 people.",
    fact="More than 400 ships have wrecked on these islands, and a "
         "significant part of the local population descends from the "
         "survivors — which is why there is an English-speaking Anglican "
         "community on a French Acadian archipelago.",
    tip="The ferry from Prince Edward Island takes five hours and books up "
        "in June for August. The sea caves at Gros-Cap can be paddled into "
        "on a calm morning, and the water inside is a lit green."),
"jacques-cartier-park": dict(
    name="Jacques-Cartier National Park",
    slug="Jacques-Cartier_National_Park", country="Canada",
    region="Quebec", type="nature", tag="hidden",
    emoji="🏞️", sounds=["wilderness.mp3"],
    highlights=[("Jacques-Cartier River", "Jacques-Cartier_River"),
                ("Laurentian Mountains", "Laurentian_Mountains"),
                ("Quebec City", "Quebec_City")],
    blurb="A glacial valley 550 m deep cut into the Laurentian plateau half "
          "an hour north of Quebec City — a river running flat through the "
          "bottom of it with walls rising steeply on both sides for 30 km.",
    fact="Fog fills the valley floor most summer mornings and burns off "
         "from the top down, so from the ridge trails you look across at "
         "peaks standing out of a white river. It happens most days in "
         "August.",
    tip="Rent a canoe at the visitor centre and float the flat water "
        "downstream — the shuttle brings you back. Moose feed in the "
        "shallows early and this is the easiest place in Quebec to see one."),
"mingan-archipelago": dict(
    name="Mingan Archipelago", slug="Mingan_Archipelago", country="Canada",
    region="Quebec", type="island", tag="hidden",
    emoji="🗿", sounds=["ocean-waves.mp3"],
    highlights=[("Havre-Saint-Pierre", "Havre-Saint-Pierre"),
                ("Anticosti Island", "Anticosti_Island"),
                ("Gulf of Saint Lawrence", "Gulf_of_Saint_Lawrence")],
    blurb="Around a thousand islands and islets along the north shore of "
          "the Gulf, carrying the largest concentration of erosion "
          "monoliths in Canada — limestone pillars shaped like heads and "
          "mushrooms, standing on the beaches.",
    fact="The limestone was laid down 450 million years ago on a tropical "
         "sea floor near the equator, and is full of fossils. The monoliths "
         "were carved by waves after the ice retreated, in the last 8,000 "
         "years.",
    tip="Île Niapiskau and Quarry Island have the best monoliths and the "
        "boats run from Havre-Saint-Pierre. Puffins nest on Île aux "
        "Perroquets, which has a lighthouse you can sleep in."),
"eeyou-istchee": dict(
    name="Chisasibi", slug="Chisasibi", country="Canada",
    region="Quebec", type="village", tag="hidden",
    emoji="🪶", sounds=["wilderness.mp3"],
    highlights=[("James Bay", "James_Bay"),
                ("La Grande River", "La_Grande_River"),
                ("Robert-Bourassa generating station",
                 "Robert-Bourassa_generating_station"),
                ("Radisson", "Radisson,_Quebec")],
    blurb="A Cree community of about 5,000 near the mouth of the La Grande "
          "River on James Bay, moved here from Fort George Island in 1981 "
          "when the hydroelectric project changed the river that had "
          "supported it.",
    fact="The Robert-Bourassa station upstream has an underground machine "
         "hall 137 m below the surface and a spillway carved as a giant's "
         "staircase — ten steps, each the size of a football field, able to "
         "pass more water than the St. Lawrence.",
    tip="Chisasibi means great river in Cree. The road here — the James Bay "
        "Highway — runs 620 km with one service station in the middle, and "
        "you are required to register at the start of it."),
"chute-montmorency": dict(
    name="Montmorency Falls", slug="Montmorency_Falls", country="Canada",
    region="Quebec", type="nature", tag="famous",
    emoji="💦", sounds=["waterfall.mp3"],
    highlights=[("Île d'Orléans", "Île_d'Orléans"),
                ("Quebec City", "Quebec_City"),
                ("Saint Lawrence River", "Saint_Lawrence_River")],
    blurb="Eighty-three metres of water dropping into the St. Lawrence at "
          "the edge of Quebec City — thirty metres higher than Niagara, "
          "though far narrower. A suspension bridge crosses directly over "
          "the lip.",
    fact="In winter the spray freezes into a cone at the base called the "
         "Sugarloaf, which can reach 30 m. Nineteenth-century Quebecers "
         "climbed and tobogganed down it as a seasonal outing.",
    tip="The via ferrata takes you across the rock face beside the falling "
        "water, and the zipline crosses the gorge. Both run all summer; the "
        "487 stairs beside the falls are free and nearly as good."),
"parc-de-la-gaspesie": dict(
    name="Parc national de la Gaspésie", slug="Gaspésie_National_Park",
    country="Canada", region="Quebec", type="mountain", tag="hidden",
    emoji="🦌", sounds=["wilderness.mp3"],
    highlights=[("Chic-Choc Mountains", "Chic-Choc_Mountains"),
                ("Mount Jacques-Cartier", "Mount_Jacques-Cartier"),
                ("Appalachian Mountains", "Appalachian_Mountains")],
    blurb="The Chic-Chocs, the highest mountains in southern Quebec, "
          "holding alpine tundra above 1,000 m and 25 summits over 1,000. "
          "The Appalachian Trail's northern extension ends here.",
    fact="The last woodland caribou herd south of the St. Lawrence lives on "
         "these summits — a few dozen animals, isolated for 10,000 years "
         "since the ice retreated and left them on the high ground.",
    tip="Mont Jacques-Cartier's summit trail closes each morning until "
        "10 a.m. and the whole mountain closes in autumn, both for the "
        "caribou. Respect it — the herd is down to about thirty."),
"anticosti": dict(
    name="Anticosti Island", slug="Anticosti_Island", country="Canada",
    region="Quebec", type="island", tag="hidden",
    emoji="🦌", sounds=["ocean-waves.mp3"],
    highlights=[("Port-Menier", "Port-Menier"),
                ("Vauréal Falls", None),
                ("Gulf of Saint Lawrence", "Gulf_of_Saint_Lawrence")],
    blurb="An island the size of Corsica in the Gulf of St. Lawrence with "
          "about 200 people on it and 160,000 white-tailed deer, all "
          "descended from 220 released in 1896 by a French chocolate "
          "millionaire who owned the whole thing.",
    fact="Anticosti became a UNESCO World Heritage Site in 2023 for its "
         "fossils — the most complete record anywhere of the first mass "
         "extinction, the Ordovician–Silurian event 447 million years ago. "
         "It is written into the cliffs in sequence.",
    tip="Vauréal Falls drops 76 m into a canyon you walk up the bed of. "
        "There is one road, mostly gravel, and about 550 km of it — bring "
        "two spare tyres, which is the standard local advice."),
"lac-saint-jean": dict(
    name="Lac Saint-Jean", slug="Lac_Saint-Jean", country="Canada",
    region="Quebec", type="nature", tag="hidden",
    emoji="🫐", sounds=["ocean-waves.mp3"],
    highlights=[("Saguenay River", "Saguenay_River"),
                ("Val-Jalbert", "Val-Jalbert"),
                ("Péribonka River", "Péribonka_River"),
                ("Alma", "Alma,_Quebec")],
    blurb="A round lake 1,050 km² across at the head of the Saguenay, "
          "ringed by sand beaches and blueberry barrens. A 256 km cycle "
          "path runs all the way around it, and people swim across it in "
          "July.",
    fact="Local blueberries are so central here that Quebecers call people "
         "from the region bleuets. The word means both the berry and the "
         "person, and it is used affectionately by everyone including them.",
    tip="Val-Jalbert is a pulp-mill village abandoned in 1927 and left "
        "standing — you walk through roofless houses on the original "
        "streets, with a 72 m waterfall at the top of the hill."),
"eastern-townships": dict(
    name="Eastern Townships", slug="Estrie", country="Canada",
    region="Quebec", type="nature", tag="hidden",
    emoji="🍁", sounds=["wilderness.mp3"],
    search_name="Eastern Townships Quebec",
    highlights=[("Lake Memphremagog", "Lake_Memphremagog"),
                ("Mont-Mégantic", "Mont_Mégantic"),
                ("Magog", "Magog,_Quebec"),
                ("Saint-Benoît-du-Lac Abbey", "Saint-Benoît-du-Lac")],
    blurb="Rolling hills, covered bridges and round barns along the Vermont "
          "border, settled by Loyalists after 1783 which is why the villages "
          "have English names and speak French. Apples, cider and the "
          "province's best cheese.",
    fact="Mont-Mégantic was the world's first International Dark Sky "
         "Reserve, designated in 2007. Thirty-four municipalities changed "
         "their street lighting to get it, replacing over 3,000 fixtures.",
    tip="The Benedictine abbey on Lake Memphremagog sells the cheese its "
        "monks make and sings Gregorian chant at vespers daily, open to "
        "anyone. Both are worth arranging the day around."),
"riviere-du-loup": dict(
    name="Bas-Saint-Laurent", slug="Bas-Saint-Laurent", country="Canada",
    region="Quebec", type="coastal", tag="hidden",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    highlights=[("Rivière-du-Loup", "Rivière-du-Loup"),
                ("Kamouraska", "Kamouraska,_Quebec"),
                ("Bic National Park", "Bic_National_Park"),
                ("Rimouski", "Rimouski")],
    blurb="The south shore of the St. Lawrence downriver from Quebec, where "
          "the river becomes salt and grows wide enough that you cannot see "
          "across. Villages of silver-roofed houses, tidal flats and eel "
          "weirs still set in the mud.",
    fact="This stretch is known for having some of the finest sunsets in "
         "the world, an assessment that shows up in nineteenth-century "
         "travel writing and has been the region's tourism pitch ever "
         "since. The width of the estuary is why.",
    tip="Bic National Park has grey seals hauled out on the rocks at Cap "
        "Caribou, visible from the shore trail at low tide. Kamouraska, "
        "half an hour west, is where the light is."),

# =========================== NEW BRUNSWICK ============================
"bay-of-fundy": dict(
    name="Bay of Fundy", slug="Bay_of_Fundy", country="Canada",
    region="New Brunswick", type="coastal", tag="famous",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Hopewell Rocks", "Hopewell_Rocks"),
                ("Fundy National Park", "Fundy_National_Park"),
                ("Cape Enrage", "Cape_Enrage"),
                ("Grand Manan", "Grand_Manan")],
    blurb="The bay with the highest tides on Earth — up to 16 m twice a "
          "day, moving 160 billion tonnes of water in and out, more than "
          "every river on the planet combined discharges in the same time.",
    fact="The tides are that big because the bay's natural resonance period "
         "is almost exactly the 12-hour tidal cycle, so each incoming tide "
         "pushes the last one higher. It is a bathtub sloshing in time with "
         "the Moon.",
    tip="Whatever you plan, check the tide table first — it governs "
        "everything here, including whether the thing you drove to see is "
        "underwater. Two high tides a day, about 50 minutes later each day."),
"saint-john": dict(
    name="Saint John", slug="Saint_John,_New_Brunswick", country="Canada",
    region="New Brunswick", type="city", tag="hidden",
    emoji="🏗️", sounds=["city-hum.mp3"],
    search_name="Saint John New Brunswick",
    highlights=[("Reversing Falls", "Reversing_Falls"),
                ("Saint John City Market", "Saint_John_City_Market"),
                ("Bay of Fundy", "Bay_of_Fundy"),
                ("Irving Nature Park", None)],
    blurb="Canada's first incorporated city, 1785, built by Loyalists on "
          "the harbour where the Saint John River meets the Fundy tides. "
          "Brick and stone rebuilt after the 1877 fire that took most of it.",
    fact="At the Reversing Falls the tide runs so high that the river is "
         "forced to flow backwards twice a day, and there is a moment of "
         "slack water between where the whole thing goes flat and boats "
         "cross.",
    tip="The City Market has been trading since 1876 in a hall whose "
        "ceiling was built by shipwrights — an inverted hull, "
        "recognisably. It is the oldest continuously operating farmers' "
        "market in Canada."),
"fundy-national-park": dict(
    name="Fundy National Park", slug="Fundy_National_Park", country="Canada",
    region="New Brunswick", type="coastal", tag="hidden",
    emoji="🌲", sounds=["ocean-waves.mp3"],
    highlights=[("Bay of Fundy", "Bay_of_Fundy"),
                ("Alma", "Alma,_New_Brunswick"),
                ("Point Wolfe", None),
                ("Dickson Falls", None)],
    blurb="Two hundred and seven square kilometres where the Acadian "
          "highlands drop to the Fundy shore — twenty-five waterfalls in "
          "the forest behind, and a beach at Alma that walks out a "
          "kilometre when the tide goes.",
    fact="Atlantic salmon in the park's rivers were down to fewer than "
         "one hundred returning adults. A programme raising smolts in sea "
         "cages and releasing them has brought thousands back to the Upper "
         "Salmon River.",
    tip="Walk out onto the Alma sea floor at low tide, then come back six "
        "hours later and look at the same spot. Nothing explains a 12 m "
        "tide like standing where you stood."),
"hopewell": dict(
    name="Cape Enrage", slug="Cape_Enrage", country="Canada",
    region="New Brunswick", type="coastal", tag="hidden",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    highlights=[("Bay of Fundy", "Bay_of_Fundy"),
                ("Hopewell Rocks", "Hopewell_Rocks"),
                ("Fundy National Park", "Fundy_National_Park")],
    blurb="A headland with an 1838 lighthouse on it, named for the water "
          "off the point — a reef makes the sea break violently there in "
          "almost any wind. The cliffs below are full of fossils.",
    fact="The lighthouse was saved from demolition in 1993 by a high school "
         "physics teacher and his students, who restored it over several "
         "summers and ran it as a business. They still do.",
    tip="Rappelling down the 43 m cliff onto the beach is the thing to do "
        "here, and the beach at the bottom is only there at low tide. "
        "Fossil hunting is permitted; taking them is not."),
"hartland-bridge": dict(
    name="Hartland Covered Bridge", slug="Hartland_Bridge", country="Canada",
    region="New Brunswick", type="landmark", tag="hidden",
    emoji="🌉", sounds=["wilderness.mp3"],
    highlights=[("Saint John River", "Saint_John_River_(Bay_of_Fundy)"),
                ("Hartland", "Hartland,_New_Brunswick")],
    blurb="The longest covered bridge in the world at 391 m, seven spans "
          "across the Saint John River, built in 1901 and covered ten years "
          "later — the roof is not for romance, it is to stop the timber "
          "trusses rotting.",
    fact="When it was first built the local clergy opposed covering it, on "
         "the grounds that a long dark tunnel would encourage young couples "
         "to linger. The bridges are still nicknamed kissing bridges.",
    tip="Drive it — it carries traffic, one lane, with a wooden deck that "
        "sounds different under the tyres. Then walk it, which takes about "
        "five minutes and is better."),
"kouchibouguac": dict(
    name="Kouchibouguac National Park", slug="Kouchibouguac_National_Park",
    country="Canada", region="New Brunswick", type="coastal", tag="hidden",
    emoji="🏖️", sounds=["ocean-waves.mp3"],
    highlights=[("Northumberland Strait", "Northumberland_Strait"),
                ("Kellys Beach", None),
                ("Richibucto", "Richibucto")],
    blurb="Barrier dunes, salt marsh and lagoon on the warm side of New "
          "Brunswick — the Northumberland Strait water here reaches 20°C in "
          "August, which is as warm as the sea gets north of Virginia.",
    fact="The park was created in 1969 by expropriating 1,200 Acadian "
         "residents from seven communities. The resistance lasted years, "
         "and Parks Canada has since acknowledged it as a wrong; the "
         "displaced families' history is now part of the interpretation.",
    tip="Kellys Beach is reached by a 600 m boardwalk over the lagoon and "
        "the tern colony on the dune. Rent a kayak for the lagoon at dawn — "
        "seals, and the water is glass."),
"grand-manan": dict(
    name="Grand Manan", slug="Grand_Manan", country="Canada",
    region="New Brunswick", type="island", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Bay of Fundy", "Bay_of_Fundy"),
                ("Swallowtail Lighthouse", None),
                ("Machias Seal Island", "Machias_Seal_Island")],
    blurb="An island of 2,300 people at the mouth of the Bay of Fundy, "
          "90 minutes by ferry, with 100 m cliffs on the west side and "
          "fishing harbours on the east. Right whales feed off the "
          "south end in summer.",
    fact="Machias Seal Island, off the south-west, is claimed by both "
         "Canada and the United States and is the only genuinely disputed "
         "territory between them. Canada keeps a lighthouse staffed there "
         "largely to make the point.",
    tip="Dulse — dried seaweed — is harvested at Dark Harbour on the west "
        "side and eaten like crisps. It is an acquired taste and the island "
        "will insist you acquire it."),
"st-andrews": dict(
    name="St. Andrews", slug="Saint_Andrews,_New_Brunswick",
    country="Canada", region="New Brunswick", type="town", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    search_name="St Andrews by-the-Sea New Brunswick",
    highlights=[("Passamaquoddy Bay", "Passamaquoddy_Bay"),
                ("Kingsbrae Garden", None),
                ("Ministers Island", "Ministers_Island"),
                ("Algonquin Resort", None)],
    blurb="A Loyalist town of 1783 laid out on a grid on a peninsula in "
          "Passamaquoddy Bay, with houses that were floated up from Maine "
          "on barges when their owners decided which side of the new border "
          "they wanted to be on.",
    fact="Ministers Island, the summer estate of the CPR's William Van "
         "Horne, is reached by driving across the sea floor at low tide. "
         "Miss the window and you wait six hours; people do.",
    tip="The whale watching out of here goes to the Fundy feeding grounds "
        "and sees finbacks, minkes and sometimes right whales. Kingsbrae, "
        "in town, is one of the best public gardens in Canada."),

# ============================ NOVA SCOTIA =============================
"halifax": dict(
    name="Halifax", slug="Halifax,_Nova_Scotia", country="Canada",
    region="Nova Scotia", type="city", tag="famous",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    search_name="Halifax Nova Scotia",
    highlights=[("Halifax Citadel", "Citadel_Hill_(Fort_George)"),
                ("Halifax Waterfront Boardwalk", None),
                ("Maritime Museum of the Atlantic",
                 "Maritime_Museum_of_the_Atlantic"),
                ("Pier 21", "Pier_21"),
                ("Point Pleasant Park", "Point_Pleasant_Park")],
    blurb="The largest city in Atlantic Canada, on the second-largest "
          "natural harbour in the world, founded as a naval base in 1749 "
          "and never really stopping being one. A star fort on the hill "
          "still fires a gun at noon.",
    fact="In December 1917 a munitions ship exploded in the harbour with "
         "the force of about 2.9 kilotonnes — the largest human-made "
         "explosion before the atomic bomb. It killed nearly 2,000 people "
         "and flattened the north end.",
    tip="Boston sends Halifax a Christmas tree every year in thanks for the "
        "relief trains it sent after the explosion. It is chosen "
        "ceremonially in Nova Scotia and has arrived every year since 1971."),
"cabot-trail": dict(
    name="Cabot Trail", slug="Cabot_Trail", country="Canada",
    region="Nova Scotia", type="coastal", tag="famous",
    emoji="🛣️", sounds=["ocean-waves.mp3"],
    highlights=[("Cape Breton Highlands National Park",
                 "Cape_Breton_Highlands_National_Park"),
                ("Ingonish", "Ingonish"),
                ("Chéticamp", "Chéticamp"),
                ("Skyline Trail", None)],
    blurb="A 298 km loop around the top of Cape Breton Island, climbing "
          "headlands 400 m straight out of the Gulf and dropping into "
          "Acadian and Gaelic fishing villages on the way down. One of the "
          "great coastal drives.",
    fact="Cape Breton has more Gaelic speakers than anywhere outside "
         "Scotland, and the Gaelic College at St. Ann's teaches the "
         "language, the fiddle and the pipes. The music tradition here is "
         "older than the one it came from.",
    tip="Drive it counter-clockwise. You get the ocean-side lane on the "
        "mountain sections, which matters more than it sounds — and the "
        "Skyline Trail at sunset is where the whales are, from above."),
"cape-breton-highlands": dict(
    name="Cape Breton Highlands National Park",
    slug="Cape_Breton_Highlands_National_Park", country="Canada",
    region="Nova Scotia", type="nature", tag="hidden",
    emoji="⛰️", sounds=["ocean-waves.mp3"],
    highlights=[("Cabot Trail", "Cabot_Trail"),
                ("Skyline Trail", None),
                ("Ingonish", "Ingonish"),
                ("Pleasant Bay", "Pleasant_Bay,_Nova_Scotia")],
    blurb="A plateau of boreal forest and taiga barrens 500 m above the "
          "Gulf, ending in cliffs on three sides. One third of the Cabot "
          "Trail runs through it and the rest of it has no roads at all.",
    fact="Moose here are descended from eighteen animals brought from "
         "Alberta in the 1940s after the native population was hunted out. "
         "They now number in the thousands and are eating the forest faster "
         "than it regrows.",
    tip="The Skyline is a 7 km boardwalk loop ending on a headland "
        "800 m above the water with the road switchbacking below. Do it in "
        "the last two hours of daylight."),
"louisbourg": dict(
    name="Fortress of Louisbourg", slug="Fortress_of_Louisbourg",
    country="Canada", region="Nova Scotia", type="history", tag="hidden",
    emoji="🏰", sounds=["ocean-waves.mp3"],
    highlights=[("Cape Breton Island", "Cape_Breton_Island"),
                ("Sydney", "Sydney,_Nova_Scotia"),
                ("Louisbourg", "Louisbourg")],
    blurb="A quarter of an eighteenth-century French fortified town, "
          "rebuilt stone by stone on its own foundations — the largest "
          "historical reconstruction in North America, staffed by several "
          "hundred people in 1744 costume.",
    fact="The reconstruction was begun in 1961 to give work to coal miners "
         "laid off in Cape Breton. They were retrained as stonemasons and "
         "carpenters and spent twenty years rebuilding what the British had "
         "demolished in 1760.",
    tip="Eat in the eighteenth-century manner at one of the period "
        "kitchens: no cutlery beyond a spoon, pewter plates, and bread you "
        "tear. It is a real meal, not a novelty."),
"bay-of-fundy-ns": dict(
    name="Burntcoat Head", slug="Burntcoat,_Nova_Scotia", country="Canada",
    region="Nova Scotia", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Bay of Fundy", "Bay_of_Fundy"),
                ("Minas Basin", "Minas_Basin"),
                ("Truro", "Truro,_Nova_Scotia")],
    blurb="The head of the Minas Basin, where the Bay of Fundy tides reach "
          "their absolute maximum — the world record of 16.3 m was measured "
          "here. Twice a day the sea floor becomes a walkable landscape.",
    fact="At low tide the ocean floor here is exposed for kilometres and "
          "you can walk on it. Six hours later the same ground is under "
          "five storeys of water, and the change is fast enough to see.",
    tip="Guided low-tide walks run daily in summer and the guides are the "
        "reason to go — they know where the tide comes in from, which is "
        "not always the direction you would guess."),
"annapolis-valley": dict(
    name="Annapolis Royal", slug="Annapolis_Royal", country="Canada",
    region="Nova Scotia", type="town", tag="hidden",
    emoji="🌷", sounds=["city-hum.mp3"],
    highlights=[("Fort Anne", "Fort_Anne"),
                ("Port-Royal National Historic Site",
                 "Port-Royal_National_Historic_Site"),
                ("Annapolis Basin", "Annapolis_Basin"),
                ("Bay of Fundy", "Bay_of_Fundy")],
    blurb="The oldest continuous European settlement north of Florida, "
          "founded as Port-Royal in 1605 and fought over so often it "
          "changed hands seven times. A town of 500 with a national "
          "historic site at each end.",
    fact="North America's first tidal power station operated here from 1984 "
         "to 2019, generating from the Fundy tide. It was shut down partly "
         "because the turbine kept killing fish.",
    tip="The historic gardens grow a 1740s Acadian kitchen garden alongside "
        "Victorian and rose collections, on 17 acres above the dyked "
        "marsh — and the dykes themselves are Acadian, still working after "
        "three hundred years."),
"grand-pre": dict(
    name="Grand-Pré", slug="Grand-Pré,_Nova_Scotia", country="Canada",
    region="Nova Scotia", type="history", tag="hidden",
    emoji="🌾", sounds=["wind.mp3"],
    highlights=[("Minas Basin", "Minas_Basin"),
                ("Port-Royal National Historic Site",
                 "Port-Royal_National_Historic_Site"),
                ("Wolfville", "Wolfville"),
                ("Cape Blomidon", "Cape_Blomidon")],
    blurb="Dyked farmland reclaimed from the Fundy tide by Acadian settlers "
          "from the 1680s, and the place from which they were deported in "
          "1755. A UNESCO site that is mostly an empty field, which is the "
          "point.",
    fact="The Acadians built aboiteaux — one-way valves in the dykes that "
         "let fresh water out and kept salt water from coming in. The "
         "fields are still farmed today using the same system, three "
         "centuries on.",
    tip="Climb the Lookoff on the North Mountain above the valley. From up "
        "there you can read the whole reclaimed marsh at once and see "
        "exactly how much land they took from the sea."),
"joggins": dict(
    name="Joggins Fossil Cliffs", slug="Joggins_Fossil_Cliffs",
    country="Canada", region="Nova Scotia", type="coastal", tag="hidden",
    emoji="🦎", sounds=["ocean-waves.mp3"],
    highlights=[("Bay of Fundy", "Bay_of_Fundy"),
                ("Chignecto Bay", "Chignecto_Bay"),
                ("Amherst", "Amherst,_Nova_Scotia")],
    blurb="Fifteen kilometres of sea cliff on the Fundy shore holding the "
          "most complete fossil record of the Coal Age anywhere — 310 "
          "million years of swamp forest, exposed and refreshed by the "
          "highest tides on Earth twice a day.",
    fact="Charles Darwin cited Joggins in On the Origin of Species. The "
         "fossil trees here stand upright where they grew, and inside one "
         "of them was found Hylonomus lyelli — the earliest known reptile, "
         "and the ancestor of everything that later laid an egg on land.",
    tip="New fossils fall out of the cliff with every tide, so what is on "
        "the beach today was not there last week. Guided walks only below "
        "the cliffs, and never at a rising tide."),
"kejimkujik": dict(
    name="Kejimkujik National Park", slug="Kejimkujik_National_Park",
    country="Canada", region="Nova Scotia", type="nature", tag="hidden",
    emoji="🛶", sounds=["wilderness.mp3"],
    highlights=[("Mersey River", "Mersey_River_(Nova_Scotia)"),
                ("Liverpool", "Liverpool,_Nova_Scotia"),
                ("Annapolis Royal", "Annapolis_Royal")],
    blurb="Inland Nova Scotia — lakes, drowned forest and old growth hemlock "
          "linked by canoe routes that the Mi'kmaq used for thousands of "
          "years and that are still the only sensible way to cross the park.",
    fact="Keji is the only national park in Canada that is also a National "
         "Historic Site in its entirety, designated for 4,000 years of "
         "Mi'kmaw occupation — including petroglyphs carved into lakeside "
         "slate.",
    tip="It is a Dark Sky Preserve with almost no light within 50 km. Paddle "
        "to a backcountry site on Big Dam Lake, and take the star chart the "
        "park hands out at the gate."),
"lunenburg-area": dict(
    name="Mahone Bay", slug="Mahone_Bay,_Nova_Scotia", country="Canada",
    region="Nova Scotia", type="town", tag="hidden",
    emoji="⛪", sounds=["ocean-waves.mp3"],
    highlights=[("Lunenburg", "Lunenburg,_Nova_Scotia"),
                ("Oak Island", "Oak_Island"),
                ("Chester", "Chester,_Nova_Scotia")],
    blurb="Three wooden churches standing side by side at the head of a "
          "bay, reflected in it — the most photographed view in Nova "
          "Scotia. A shipbuilding town of 1,000 with 365 islands in the "
          "water in front of it.",
    fact="Oak Island, in this bay, has been dug for buried treasure since "
         "1795. Six people have died looking, nothing has ever been found, "
         "and the digging continues.",
    tip="Get there for the first hour of light with the tide in. The "
        "reflection needs still water and the churches face east, so the "
        "postcard is a morning shot."),
"digby-neck": dict(
    name="Digby Neck", slug="Digby_Neck", country="Canada",
    region="Nova Scotia", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Brier Island", "Brier_Island"),
                ("Balancing Rock", None),
                ("Bay of Fundy", "Bay_of_Fundy"),
                ("Digby", "Digby,_Nova_Scotia")],
    blurb="A basalt peninsula 70 km long and barely 3 km wide sticking out "
          "into the Bay of Fundy, broken into two islands at the end and "
          "joined by two short ferries that run around the clock.",
    fact="The upwelling off Brier Island at the tip concentrates plankton "
         "so reliably that humpbacks, finbacks and right whales come every "
         "summer. It is one of the most dependable whale-watching spots in "
         "the North Atlantic.",
    tip="Balancing Rock on Long Island is a 9 m column of basalt standing "
        "on end on a ledge over the sea, reached by 235 steps down. It "
        "should have fallen long ago and has not."),

# ======================= PRINCE EDWARD ISLAND ========================
"charlottetown": dict(
    name="Charlottetown", slug="Charlottetown", country="Canada",
    region="Prince Edward Island", type="city", tag="hidden",
    emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Province House", "Province_House_(Prince_Edward_Island)"),
                ("Victoria Row", None),
                ("Confederation Centre of the Arts",
                 "Confederation_Centre_of_the_Arts"),
                ("Peake's Wharf", None)],
    blurb="The smallest provincial capital in Canada, 40,000 people, and "
          "the room where the country was negotiated in September 1864 is "
          "still there with the same table in it.",
    fact="Prince Edward Island hosted the conference that created Canada "
         "and then declined to join, holding out until 1873 when a railway "
         "debt made the terms attractive. It is the birthplace of a country "
         "it initially refused to be part of.",
    tip="Anne of Green Gables has been staged at the Confederation Centre "
        "every summer since 1965 — the longest-running annual musical in "
        "the world. Buy lobster off the wharf instead if that is not your "
        "thing."),
"cavendish": dict(
    name="Cavendish", slug="Cavendish,_Prince_Edward_Island",
    country="Canada", region="Prince Edward Island", type="coastal",
    tag="hidden",
    emoji="🏠", sounds=["ocean-waves.mp3"],
    highlights=[("Green Gables", "Green_Gables"),
                ("Prince Edward Island National Park",
                 "Prince_Edward_Island_National_Park"),
                ("North Rustico", "North_Rustico")],
    blurb="Red sandstone cliffs and white sand on the island's north shore, "
          "and the farmhouse that Lucy Maud Montgomery used as Green Gables "
          "— a real house belonging to her cousins, which she walked past "
          "as a child.",
    fact="Anne of Green Gables is enormously popular in Japan, where it has "
         "been on the school curriculum since 1952. Japanese visitors come "
         "in numbers large enough that signage here is trilingual.",
    tip="The Gulf Shore Parkway runs the length of the dunes with beach "
        "access all along it. Go east to Brackley or Stanhope — same "
        "sand, a fraction of the people."),
"pei-national-park": dict(
    name="Greenwich Dunes", slug="Prince_Edward_Island_National_Park",
    country="Canada", region="Prince Edward Island", type="coastal",
    tag="hidden",
    emoji="🏖️", sounds=["ocean-waves.mp3"],
    search_name="Greenwich Dunes Prince Edward Island",
    highlights=[("St. Peters Bay", None),
                ("Gulf of Saint Lawrence", "Gulf_of_Saint_Lawrence"),
                ("Cavendish", "Cavendish,_Prince_Edward_Island")],
    blurb="A parabolic dune system at the eastern end of the national park "
          "— rare in North America, and moving. The dunes advance inland "
          "over the forest, burying trees whose dead trunks then reappear "
          "on the far side.",
    fact="Marram grass holds the sand still until something breaks it. "
         "That is why the boardwalk here floats on a pond rather than "
         "crossing the dune: one path of footprints would start a blowout.",
    tip="The floating boardwalk over Bowley Pond is 200 m and moves under "
        "you. It is the best walk on the island and takes about an hour "
        "each way from the interpretation centre."),
"confederation-bridge": dict(
    name="Confederation Bridge", slug="Confederation_Bridge",
    country="Canada", region="Prince Edward Island", type="landmark",
    tag="hidden",
    emoji="🌉", sounds=["ocean-waves.mp3"],
    highlights=[("Northumberland Strait", "Northumberland_Strait"),
                ("Borden-Carleton", "Borden-Carleton"),
                ("Cape Jourimain", None)],
    blurb="Nearly 13 km of concrete across the Northumberland Strait, the "
          "longest bridge in the world over water that freezes. It opened "
          "in 1997 and ended 130 years of ferry crossings in a single day.",
    fact="The piers have cone-shaped ice shields at the waterline that "
         "force pack ice to ride up and break under its own weight rather "
         "than hitting the column. The design was tested for a decade "
         "before anything was poured.",
    tip="You cannot walk or cycle it — there is a shuttle for that. Toll is "
        "collected only when you leave the island, which islanders point "
        "out means arriving is free."),

# ==================== NEWFOUNDLAND AND LABRADOR ======================
"st-johns": dict(
    name="St. John's", slug="St._John's,_Newfoundland_and_Labrador",
    country="Canada", region="Newfoundland and Labrador", type="city",
    tag="famous",
    emoji="🏘️", sounds=["ocean-waves.mp3"],
    search_name="St John's Newfoundland",
    highlights=[("Signal Hill", "Signal_Hill,_St._John's"),
                ("Cape Spear", "Cape_Spear"),
                ("Jellybean Row", None),
                ("George Street", "George_Street_(St._John's)"),
                ("Quidi Vidi", "Quidi_Vidi")],
    blurb="The oldest English-founded city in North America, wrapped around "
          "a harbour reached through a gap in the cliffs called the "
          "Narrows. Rows of houses painted in flat saturated colours climb "
          "the hills behind it.",
    fact="Marconi received the first transatlantic radio signal on Signal "
         "Hill in December 1901 — three dots, the letter S, sent from "
         "Cornwall. He was using a kite to hold the aerial up.",
    tip="Cape Spear, twenty minutes out, is the easternmost point of North "
        "America. Get there for sunrise and you are the first person on the "
        "continent to see it that day, which is a cheap thrill that works."),
"gros-morne": dict(
    name="Gros Morne National Park", slug="Gros_Morne_National_Park",
    country="Canada", region="Newfoundland and Labrador", type="mountain",
    tag="famous",
    emoji="⛰️", sounds=["wilderness.mp3"],
    highlights=[("Tablelands", None),
                ("Western Brook Pond", "Western_Brook_Pond"),
                ("Rocky Harbour", "Rocky_Harbour,_Newfoundland_and_Labrador"),
                ("Long Range Mountains", "Long_Range_Mountains")],
    blurb="Where the Earth's mantle is lying on the surface. The Tablelands "
          "are orange rock from 20 km down, pushed up in a continental "
          "collision 500 million years ago, and almost nothing will grow on "
          "them.",
    fact="Gros Morne helped prove plate tectonics. The rock sequence here "
         "is the clearest exposed evidence anywhere of an ocean closing and "
         "a continent being built, which is why it is a World Heritage Site.",
    tip="Western Brook Pond is a landlocked fjord with 600 m walls and "
        "water among the purest ever tested. You walk 3 km across bog to "
        "the boat, and the boat is the only way in."),
"lanse-aux-meadows": dict(
    name="L'Anse aux Meadows", slug="L'Anse_aux_Meadows", country="Canada",
    region="Newfoundland and Labrador", type="history", tag="famous",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    highlights=[("Great Northern Peninsula", "Great_Northern_Peninsula"),
                ("Strait of Belle Isle", "Strait_of_Belle_Isle"),
                ("St. Anthony", "St._Anthony,_Newfoundland_and_Labrador")],
    blurb="The only confirmed Norse settlement in North America outside "
          "Greenland — eight turf buildings on a boggy shore at the top of "
          "the Northern Peninsula, occupied briefly around the year 1000.",
    fact="A single butternut found here settles an argument: butternuts do "
         "not grow north of New Brunswick, so whoever lived at this camp "
         "sailed considerably further south than this and came back.",
    tip="Come on a grey day with wind. The reconstructed sod halls are "
        "warm inside with a fire going, and the point of the place lands "
        "much harder when the weather is doing what it usually does."),
"fogo-island": dict(
    name="Fogo Island", slug="Fogo_Island,_Newfoundland_and_Labrador",
    country="Canada", region="Newfoundland and Labrador", type="island",
    tag="hidden",
    emoji="🏚️", sounds=["ocean-waves.mp3"],
    search_name="Fogo Island Newfoundland",
    highlights=[("Joe Batt's Arm", "Joe_Batt's_Arm"),
                ("Tilting", "Tilting,_Newfoundland_and_Labrador"),
                ("Brimstone Head", None),
                ("Fogo Island Inn", "Fogo_Island_Inn")],
    blurb="An island of 2,000 off the north-east coast, reached by ferry, "
          "where the outport villages were nearly resettled away in the "
          "1960s and the residents formed a co-operative instead. It "
          "worked, and the island is still there.",
    fact="The Flat Earth Society named Brimstone Head one of the four "
         "corners of the world. The island has embraced this "
         "wholeheartedly and there is a sign.",
    tip="Six architect-designed artists' studios stand alone on the "
        "headlands, funded by the island's own charitable foundation. They "
        "are working studios, but the walks out to them are open to anyone."),
"bonavista": dict(
    name="Bonavista", slug="Bonavista,_Newfoundland_and_Labrador", country="Canada",
    region="Newfoundland and Labrador", type="town", tag="hidden",
    emoji="🐦", sounds=["ocean-waves.mp3"],
    highlights=[("Cape Bonavista Lighthouse", "Cape_Bonavista_Light"),
                ("Elliston", "Elliston,_Newfoundland_and_Labrador"),
                ("Dungeon Provincial Park", None),
                ("Trinity", "Trinity,_Newfoundland_and_Labrador")],
    blurb="A fishing town on a headland where John Cabot is said to have "
          "made landfall in 1497. Saltbox houses, a red-and-white striped "
          "lighthouse, and puffins nesting on a stack close enough to the "
          "cliff to photograph without a lens.",
    fact="Elliston, next door, calls itself the root cellar capital of the "
         "world — 135 of them dug into the hillsides, some from the 1830s, "
         "keeping vegetables through winters with no other way to store "
         "them.",
    tip="The Dungeon is a collapsed sea cave in a cow pasture, with two "
        "arches the sea comes through. There is no fence and no ticket. "
        "Stand well back from the rim; the edge is undercut."),
"twillingate": dict(
    name="Twillingate", slug="Twillingate", country="Canada",
    region="Newfoundland and Labrador", type="town", tag="hidden",
    emoji="🧊", sounds=["ocean-waves.mp3"],
    highlights=[("Long Point Lighthouse", None),
                ("Notre Dame Bay", "Notre_Dame_Bay"),
                ("Iceberg Alley", None)],
    blurb="Two islands joined by causeways in Notre Dame Bay, calling "
          "itself the iceberg capital of the world with some justification "
          "— the Labrador Current drives Greenland ice right past the "
          "headlands from May to July.",
    fact="The icebergs that reach here calved from Greenland glaciers about "
         "three years earlier and are made of snow that fell up to 15,000 "
         "years ago. Local distillers use the melt in their gin.",
    tip="Long Point Lighthouse sits on a 100 m cliff and is where "
        "everyone watches from. Check the iceberg tracking map before you "
        "commit to the drive — some years the ice never comes in."),
"trinity-nl": dict(
    name="Trinity", slug="Trinity,_Newfoundland_and_Labrador",
    country="Canada", region="Newfoundland and Labrador", type="village",
    tag="hidden",
    emoji="⛪", sounds=["ocean-waves.mp3"],
    search_name="Trinity Newfoundland",
    highlights=[("Bonavista Peninsula", "Bonavista_Peninsula"),
                ("Skerwink Trail", None),
                ("Port Rexton", "Port_Rexton")],
    blurb="A village of 130 on a sheltered harbour, one of the oldest "
          "European settlements in North America and almost entirely "
          "preserved — white clapboard, picket fences, and a church spire "
          "on a point.",
    fact="North America's first recorded smallpox inoculation was performed "
         "here in 1798 by a local clergyman, John Clinch, who had been sent "
         "the vaccine by Edward Jenner himself. They had been at school "
         "together.",
    tip="The Skerwink Trail nearby is a 5 km loop along sea stacks and "
        "cliffs that gets named among the best coastal walks in North "
        "America. It takes two hours and there is a brewery at the end."),
"battle-harbour": dict(
    name="Battle Harbour", slug="Battle_Harbour", country="Canada",
    region="Newfoundland and Labrador", type="history", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    highlights=[("Labrador", "Labrador"),
                ("Strait of Belle Isle", "Strait_of_Belle_Isle"),
                ("Mary's Harbour", "Mary's_Harbour")],
    blurb="A restored saltfish station on an island off the Labrador coast, "
          "for two centuries the unofficial capital of the coast, abandoned "
          "in 1966 and now reachable only by a boat that runs a few times a "
          "day in summer.",
    fact="Robert Peary announced from the telegraph here in 1909 that he "
         "had reached the North Pole, and gave his interviews on the "
         "premises. The building he used is standing.",
    tip="Stay the night — most of the restored buildings are lodging and "
        "the day boat leaves in the afternoon. When it goes there are "
        "about a dozen people on the island and no roads, cars or lights."),
"torngat": dict(
    name="Torngat Mountains National Park",
    slug="Torngat_Mountains_National_Park", country="Canada",
    region="Newfoundland and Labrador", type="mountain", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Labrador", "Labrador"),
                ("Nain", "Nain,_Newfoundland_and_Labrador"),
                ("Ungava Bay", "Ungava_Bay"),
                ("Torngat Mountains", "Torngat_Mountains")],
    blurb="The highest mountains in mainland Canada east of the Rockies, "
          "rising straight out of fjords at the northern tip of Labrador — "
          "9,700 km² with no roads, no trails, no campground and no "
          "residents.",
    fact="Torngat comes from Torngait, the Inuktitut word for the spirits "
         "believed to inhabit these mountains. The park is co-managed by "
         "Inuit and every visitor is accompanied by an Inuit bear guard, "
         "because polar bears are common on the shore.",
    tip="Access is charter aircraft or boat to a base camp behind an "
        "electric fence, for a few weeks each summer. Rock here is nearly "
        "four billion years old — among the oldest exposed anywhere."),
"witless-bay": dict(
    name="Witless Bay Ecological Reserve",
    slug="Witless_Bay_Ecological_Reserve", country="Canada",
    region="Newfoundland and Labrador", type="island", tag="hidden",
    emoji="🐧", sounds=["ocean-waves.mp3"],
    highlights=[("Gull Island", None),
                ("Bay Bulls", "Bay_Bulls"),
                ("Avalon Peninsula", "Avalon_Peninsula")],
    blurb="Four islands off the Avalon Peninsula holding North America's "
          "largest Atlantic puffin colony — over 260,000 pairs — plus "
          "several million Leach's storm-petrels, which is most of the "
          "world's population of that bird.",
    fact="Humpback whales come to the same water to eat capelin, which "
         "spawn on the beaches here in June. Whales, puffins and icebergs "
         "regularly appear in the same frame, which is why boats sell out.",
    tip="Late June is the overlap of all three. Fledgling pufflings "
        "sometimes come ashore disoriented by town lights in August, and "
        "local kids collect them in boxes and release them at sea."),
"red-bay": dict(
    name="Red Bay", slug="Red_Bay,_Newfoundland_and_Labrador",
    country="Canada", region="Newfoundland and Labrador", type="history",
    tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    search_name="Red Bay Labrador Basque whaling",
    highlights=[("Strait of Belle Isle", "Strait_of_Belle_Isle"),
                ("Labrador", "Labrador"),
                ("Point Amour Lighthouse", "Point_Amour_Lighthouse")],
    blurb="A Basque whaling station on the Labrador shore, worked from the "
          "1530s and the largest whale oil producer in the world for most "
          "of that century. Then it was forgotten so completely that its "
          "location was only rediscovered from a Spanish archive in 1977.",
    fact="A galleon believed to be the San Juan, sunk here in 1565, lies in "
         "10 m of water and is the best-preserved sixteenth-century ship "
         "ever found. Its image is on the Canadian archaeology profession's "
         "logo.",
    tip="A chalupa — an eight-metre whaleboat recovered whole from under "
        "the galleon — is displayed here. It is the oldest surviving small "
        "craft in the Americas and it looks entirely usable."),
"terra-nova": dict(
    name="Terra Nova National Park", slug="Terra_Nova_National_Park",
    country="Canada", region="Newfoundland and Labrador", type="nature",
    tag="hidden",
    emoji="🌲", sounds=["wilderness.mp3"],
    highlights=[("Bonavista Bay", "Bonavista_Bay"),
                ("Newman Sound", None),
                ("Glovertown", "Glovertown")],
    blurb="Newfoundland's first national park, on the sheltered fjords of "
          "Bonavista Bay — boreal forest, bog and long inlets where the "
          "sea reaches far enough inland that the water is calm and warm "
          "enough to paddle.",
    fact="Newman Sound is where scientists documented the collapse of "
         "juvenile cod stocks through the 1990s. Long-term monitoring here "
         "produced some of the clearest data on the moratorium's effects.",
    tip="The Outport Trail runs 40 km along the sound past the sites of "
        "resettled communities — cellar holes and lilac bushes where "
        "houses were, all of it emptied between 1954 and 1975."),

# ================================ YUKON ===============================
# Northern Canada starts here. Before this batch the three territories
# held exactly one place between them (dawson-city), for 40% of the
# country's land area.
"whitehorse": dict(
    name="Whitehorse", slug="Whitehorse", country="Canada",
    region="Yukon", type="city", tag="hidden",
    emoji="🌌", sounds=["arctic-wind.mp3"],
    search_name="Whitehorse Yukon",
    highlights=[("SS Klondike", "SS_Klondike"),
                ("Miles Canyon", "Miles_Canyon_Basalts"),
                ("Yukon River", "Yukon_River"),
                ("Takhini Hot Springs", None)],
    blurb="The territorial capital and by far the largest town in the "
          "north — 28,000 people, three quarters of everyone in the Yukon, "
          "on a bend of the Yukon River between two escarpments.",
    fact="It has the least air pollution of any city in the world according "
         "to the Guinness records, and it is dry enough to be classed as "
         "subarctic semi-desert. It gets less precipitation than Phoenix.",
    tip="Aurora season runs from late August to April here, and the "
        "Whitehorse latitude sits directly under the auroral oval. Drive "
        "twenty minutes out of town for a dark horizon and wait."),
"kluane": dict(
    name="Kluane National Park", slug="Kluane_National_Park_and_Reserve",
    country="Canada", region="Yukon", type="mountain", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Mount Logan", "Mount_Logan"),
                ("Kluane Lake", "Kluane_Lake"),
                ("Haines Junction", "Haines_Junction"),
                ("Saint Elias Mountains", "Saint_Elias_Mountains")],
    blurb="The largest non-polar icefield on Earth, filling most of a park "
          "of 22,000 km², with the highest mountains in Canada standing out "
          "of it. Almost none of it is reachable on foot — you fly over it "
          "or you do not see it.",
    fact="Kluane joins three adjacent parks across the Alaska and British "
         "Columbia borders to form the largest protected area in the "
         "world — 98,000 km² of continuous wilderness under one UNESCO "
         "listing.",
    tip="The flightseeing out of Haines Junction is expensive and it is the "
        "whole point of coming. From the road you see the front ranges "
        "only; the icefield behind them is invisible from the ground."),
"mount-logan": dict(
    name="Mount Logan", slug="Mount_Logan", country="Canada",
    region="Yukon", type="mountain", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Kluane National Park", "Kluane_National_Park_and_Reserve"),
                ("Saint Elias Mountains", "Saint_Elias_Mountains"),
                ("Yukon", "Yukon")],
    blurb="Canada's highest mountain at 5,959 m, and the largest mountain "
          "on Earth by base circumference — a massif with eleven peaks over "
          "5,000 m on one continuous plateau, all of it under permanent ice.",
    fact="The lowest temperature ever recorded outside Antarctica was "
         "−77.5°C, measured on Logan's plateau in May 1991. The mountain is "
         "also still growing, pushed up by tectonic uplift.",
    tip="It is named for William Logan, founder of the Geological Survey of "
        "Canada. There was a serious 2000 proposal to rename it for Pierre "
        "Trudeau; Yukoners objected so loudly it was withdrawn in weeks."),
"tombstone": dict(
    name="Tombstone Territorial Park", slug="Tombstone_Territorial_Park",
    country="Canada", region="Yukon", type="mountain", tag="hidden",
    emoji="⛰️", sounds=["arctic-wind.mp3"],
    highlights=[("Dempster Highway", "Dempster_Highway"),
                ("Tombstone Mountain", "Tombstone_Mountain"),
                ("Dawson City", "Dawson_City"),
                ("Ogilvie Mountains", "Ogilvie_Mountains")],
    blurb="Black granite spires above tundra on the Dempster Highway, "
          "2,200 km² of permafrost landscape that the ice sheets never "
          "covered — so the plants and animals here have been continuous "
          "since before the last glaciation.",
    fact="This was part of Beringia, the unglaciated refuge connecting "
         "Alaska to Siberia. Species survived here that were wiped out "
         "everywhere else in North America, and some are found nowhere "
         "else today.",
    tip="Late August into the first week of September, the tundra turns "
        "red and orange and the whole valley changes colour in about ten "
        "days. It is the single best time to be on the Dempster."),
"dempster-highway": dict(
    name="Dempster Highway", slug="Dempster_Highway", country="Canada",
    region="Yukon", type="landmark", tag="hidden",
    emoji="🛣️", sounds=["arctic-wind.mp3"],
    highlights=[("Tombstone Territorial Park", "Tombstone_Territorial_Park"),
                ("Fort McPherson", "Fort_McPherson,_Northwest_Territories"),
                ("Eagle Plains", "Eagle_Plains"),
                ("Inuvik", "Inuvik")],
    blurb="Seven hundred and thirty-six kilometres of gravel from near "
          "Dawson City to Inuvik, the only public road in Canada that "
          "crosses the Arctic Circle, with one service station in the "
          "middle at kilometre 369.",
    fact="The road is built on a two-metre gravel berm because laying it "
         "directly on the ground would melt the permafrost underneath and "
         "the road would sink. The berm is insulation, not foundation.",
    tip="Carry two full-size spares. Shale on the surface cuts sidewalls "
        "and there is no help between Eagle Plains and either end — that is "
        "not a colourful warning, it is the standard advice from the "
        "territorial government."),
"carcross": dict(
    name="Carcross", slug="Carcross", country="Canada",
    region="Yukon", type="village", tag="hidden",
    emoji="🏜️", sounds=["desert-wind.mp3"],
    highlights=[("Carcross Desert", "Carcross_Desert"),
                ("Bennett Lake", "Bennett_Lake"),
                ("White Pass and Yukon Route",
                 "White_Pass_and_Yukon_Route"),
                ("Emerald Lake", None)],
    blurb="A village of 300 at a narrows between two lakes, named for the "
          "caribou that used to cross there, with a boardwalk of "
          "gold-rush-era buildings and Tlingit carvings — and a desert "
          "beside it.",
    fact="The Carcross Desert is about a square kilometre of sand — the "
         "bed of a glacial lake, kept bare by wind off the lake. It is "
         "often called the world's smallest desert, though it is not "
         "technically a desert at all.",
    tip="Emerald Lake, 15 minutes north on the highway, gets its colour "
        "from marl on the shallow bottom reflecting light. It is worth "
        "the stop and there is a pull-off."),
"haines-junction": dict(
    name="Haines Junction", slug="Haines_Junction", country="Canada",
    region="Yukon", type="village", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Kluane National Park", "Kluane_National_Park_and_Reserve"),
                ("Alaska Highway", "Alaska_Highway"),
                ("Kluane Lake", "Kluane_Lake"),
                ("Haines Highway", "Haines_Highway")],
    blurb="A village of 600 where the Haines Highway meets the Alaska "
          "Highway, directly under the front ranges of the St. Elias — the "
          "base for Kluane and the last real services before a long way in "
          "any direction.",
    fact="The village exists because of the Alaska Highway, thrown across "
         "2,700 km of wilderness by the US Army in eight months in 1942 "
         "after Pearl Harbor. Whole communities in the Yukon were founded "
         "by that construction camp chain.",
    tip="The bakery here is genuinely famous in a territory where that "
        "means something, and it is where the flightseeing pilots eat. Ask "
        "them about the weather over the icefield before you book."),
"kluane-lake": dict(
    name="Kluane Lake", slug="Kluane_Lake", country="Canada",
    region="Yukon", type="nature", tag="hidden",
    emoji="🏞️", sounds=["arctic-wind.mp3"],
    highlights=[("Kluane National Park", "Kluane_National_Park_and_Reserve"),
                ("Alaska Highway", "Alaska_Highway"),
                ("Destruction Bay", "Destruction_Bay"),
                ("Sheep Mountain", None)],
    blurb="The largest lake in the Yukon, 400 km², turquoise from glacial "
          "flour, with the Alaska Highway running along its shore for 60 km "
          "and mountains standing straight out of the far side.",
    fact="In 2016 the Slims River, which fed this lake, stopped — the "
         "Kaskawulsh Glacier retreated past a divide and its meltwater "
         "switched to a different ocean in a matter of days. It was the "
         "first observed case of modern river piracy.",
    tip="Sheep Mountain at the south end has Dall sheep on it, white "
        "against grey rock, visible from the highway pull-off with "
        "binoculars most of the year."),
"watson-lake": dict(
    name="Watson Lake", slug="Watson_Lake,_Yukon", country="Canada",
    region="Yukon", type="town", tag="hidden",
    emoji="🪧", sounds=["wilderness.mp3"],
    search_name="Watson Lake Yukon sign post forest",
    highlights=[("Sign Post Forest", "Sign_Post_Forest"),
                ("Alaska Highway", "Alaska_Highway"),
                ("Liard River", "Liard_River")],
    blurb="The first Yukon town on the Alaska Highway coming from the "
          "south, notable almost entirely for a forest of signposts — over "
          "100,000 stolen and donated place-name signs nailed to poles by "
          "passing travellers.",
    fact="It was started in 1942 by a homesick US Army GI named Carl "
         "Lindley, who put up a sign pointing to Danville, Illinois while "
         "recovering from an injury. People have been adding to it ever "
         "since.",
    tip="Bring your own sign if you want to add one, or make one at the "
        "visitor centre. Taking a road sign off a post to bring here is "
        "the tradition and is also theft."),
"top-of-the-world-highway": dict(
    name="Top of the World Highway", slug="Top_of_the_World_Highway",
    country="Canada", region="Yukon", type="landmark", tag="hidden",
    emoji="🛣️", sounds=["arctic-wind.mp3"],
    highlights=[("Dawson City", "Dawson_City"),
                ("Yukon River", "Yukon_River"),
                ("Poker Creek–Little Gold Creek Border Crossing",
                 "Poker_Creek–Little_Gold_Creek_Border_Crossing")],
    blurb="A gravel road running along the ridgelines west from Dawson "
          "City to Alaska, above the treeline nearly the whole way, so you "
          "drive with the country falling away on both sides for 100 km.",
    fact="Poker Creek at the far end is the northernmost land border "
         "crossing between Canada and the United States. It is open five "
         "months a year, closes at 8 p.m., and the officers live on site "
         "because there is nowhere else.",
    tip="You reach it by free ferry across the Yukon River at Dawson, which "
        "runs 24 hours in summer and stops entirely at freeze-up. Confirm "
        "border hours before you commit — the two time zones catch people "
        "out."),
"bonanza-creek": dict(
    name="Bonanza Creek", slug="Bonanza_Creek", country="Canada",
    region="Yukon", type="history", tag="hidden",
    emoji="⛏️", sounds=["wilderness.mp3"],
    highlights=[("Klondike", "Klondike,_Yukon"),
                ("Dawson City", "Dawson_City"),
                ("Dredge No. 4", "Dredge_No._4"),
                ("Klondike River", "Klondike_River")],
    blurb="The creek where gold was found in August 1896, starting the "
          "Klondike stampede. The valley floor is still covered in the "
          "gravel ridges left by dredges, kilometres of them, like a "
          "ploughed field the size of a town.",
    fact="Skookum Jim, Dawson Charlie and George Carmack made the "
         "discovery. It was almost certainly Skookum Jim who saw it first, "
         "but Carmack — the only white man of the three — filed the claim, "
         "because it was thought a Tagish claim would not be honoured.",
    tip="Dredge No. 4 is eight storeys of wooden gold dredge sitting in "
        "its own pond, the largest ever used in North America. You can go "
        "inside it, and free panning is allowed at Claim 6 downstream."),
"herschel-island": dict(
    name="Herschel Island", slug="Herschel_Island", country="Canada",
    region="Yukon", type="island", tag="hidden",
    emoji="🐻‍❄️", sounds=["arctic-wind.mp3"],
    highlights=[("Beaufort Sea", "Beaufort_Sea"),
                ("Ivvavik National Park", "Ivvavik_National_Park"),
                ("Yukon", "Yukon")],
    blurb="The Yukon's only island, in the Beaufort Sea, and its first "
          "territorial park — a whaling station of the 1890s where up to "
          "1,500 people wintered, now a handful of buildings on permafrost "
          "that is thawing under them.",
    fact="Qikiqtaruk, its Inuvialuit name, means simply the island. The "
         "settlement's mission house from 1893 is the oldest frame building "
         "in the Yukon, and the coast it stands on is retreating by "
         "metres a year.",
    tip="Access is charter flight or boat from Inuvik, weather permitting, "
        "which it often does not. Polar bears use the island; rangers "
        "accompany all visitors."),
"ivvavik": dict(
    name="Ivvavik National Park", slug="Ivvavik_National_Park",
    country="Canada", region="Yukon", type="wilderness", tag="hidden",
    emoji="🦌", sounds=["arctic-wind.mp3"],
    highlights=[("British Mountains", "British_Mountains"),
                ("Firth River", "Firth_River"),
                ("Beaufort Sea", "Beaufort_Sea"),
                ("Herschel Island", "Herschel_Island")],
    blurb="The first national park in Canada created through an "
          "Indigenous land claim, protecting the calving grounds of the "
          "Porcupine caribou herd on the Arctic coast — 10,000 km² with no "
          "facilities of any kind.",
    fact="Ivvavik means a place for giving birth in Inuvialuktun. The "
         "Porcupine herd numbers around 200,000 animals and makes the "
         "longest land migration of any mammal on Earth — up to 4,800 km a "
         "year.",
    tip="Parks Canada runs a small base camp on the Firth River for a few "
        "weeks each July, flown in from Inuvik. It is one of the few "
        "guided ways into the Arctic National Wildlife Refuge landscape."),
"old-crow": dict(
    name="Old Crow", slug="Old_Crow,_Yukon", country="Canada",
    region="Yukon", type="village", tag="hidden",
    emoji="✈️", sounds=["arctic-wind.mp3"],
    highlights=[("Porcupine River", "Porcupine_River"),
                ("Vuntut National Park", "Vuntut_National_Park"),
                ("Old Crow Flats", "Old_Crow_Flats")],
    blurb="The Yukon's only fly-in community and its northernmost, 250 "
          "people on the Porcupine River above the Arctic Circle. The "
          "Vuntut Gwitchin have lived on this river for thousands of years "
          "and still take caribou from the herd that passes it.",
    fact="The Old Crow Flats nearby held some of the oldest evidence of "
         "humans in North America — bone tools from Bluefish Caves nearby "
         "have been dated to 24,000 years ago, twice as old as most of the "
         "continent's accepted record.",
    tip="There is no road and never has been. The village solar farm, built "
        "in 2021, cut its diesel use by a quarter — the largest such "
        "project in the Canadian Arctic and it is community-owned."),

# ====================== NORTHWEST TERRITORIES ========================
"yellowknife": dict(
    name="Yellowknife", slug="Yellowknife", country="Canada",
    region="Northwest Territories", type="city", tag="hidden",
    emoji="🌌", sounds=["arctic-wind.mp3"],
    highlights=[("Great Slave Lake", "Great_Slave_Lake"),
                ("Old Town", None),
                ("Ingraham Trail", "Ingraham_Trail"),
                ("Prince of Wales Northern Heritage Centre",
                 "Prince_of_Wales_Northern_Heritage_Centre")],
    blurb="The territorial capital, 20,000 people on the north shore of "
          "Great Slave Lake, built on bare Precambrian rock around a gold "
          "mine and now living off diamonds, government and the northern "
          "lights.",
    fact="Yellowknife sits directly beneath the auroral oval and has a dry "
         "cold clear climate, which is why it is considered one of the best "
         "places on Earth to see the aurora. Visitors come from Japan in "
         "chartered planes for it.",
    tip="Old Town, out on the point, is houseboats, float planes and the "
        "Wildcat Café. Climb the Bush Pilots' Monument on the rock above it "
        "for the whole bay at once."),
"great-slave-lake": dict(
    name="Great Slave Lake", slug="Great_Slave_Lake", country="Canada",
    region="Northwest Territories", type="nature", tag="hidden",
    emoji="🧊", sounds=["arctic-wind.mp3"],
    highlights=[("Yellowknife", "Yellowknife"),
                ("Hay River", "Hay_River,_Northwest_Territories"),
                ("Mackenzie River", "Mackenzie_River"),
                ("East Arm", None)],
    blurb="The deepest lake in North America at 614 m, and the tenth "
          "largest in the world — big enough to hold its own weather, "
          "frozen solid for eight months, and the source of the Mackenzie "
          "River.",
    fact="The ice road across the lake to Dettah used to be a public "
         "winter highway and is still driven. On the arms of the lake, "
         "heavy trucks run ice roads north to the diamond mines for about "
         "nine weeks a year.",
    tip="The East Arm, now Thaidene Nëné, is a different lake entirely — "
        "cliffs, islands and clear water over rock, as opposed to the flat "
        "shallow south shore. Fly-in from Yellowknife."),
"nahanni": dict(
    name="Nahanni National Park", slug="Nahanni_National_Park_Reserve",
    country="Canada", region="Northwest Territories", type="nature",
    tag="hidden",
    emoji="💦", sounds=["waterfall.mp3"],
    highlights=[("Virginia Falls", "Virginia_Falls"),
                ("South Nahanni River", "South_Nahanni_River"),
                ("Fort Simpson", "Fort_Simpson"),
                ("Mackenzie Mountains", "Mackenzie_Mountains")],
    blurb="A river that is older than the mountains it runs through — the "
          "South Nahanni was there first and cut down as they rose around "
          "it, leaving four canyons over 1,000 m deep with the river still "
          "at the bottom.",
    fact="Nahanni was one of the first four sites inscribed on the UNESCO "
         "World Heritage List in 1978, alongside the Galápagos. There was "
         "no road to it then and there is none now.",
    tip="Virginia Falls is twice the height of Niagara with a rock spire "
        "splitting the flow. Most people see it on a float-plane day trip "
        "from Fort Simpson; the full river takes three weeks by canoe."),
"virginia-falls": dict(
    name="Virginia Falls", slug="Virginia_Falls_(Northwest_Territories)", country="Canada",
    region="Northwest Territories", type="nature", tag="hidden",
    emoji="💧", sounds=["waterfall.mp3"],
    highlights=[("South Nahanni River", "South_Nahanni_River"),
                ("Nahanni National Park", "Nahanni_National_Park_Reserve"),
                ("Mackenzie Mountains", "Mackenzie_Mountains")],
    blurb="Ninety-six metres of the South Nahanni going over a ledge in the "
          "middle of a roadless mountain range, split in two by a spire of "
          "rock called Mason's Rock. Twice the drop of Niagara and about a "
          "thousand times less visited.",
    fact="Its Dene name is Nailicho. The spire is named for Bill Mason, the "
         "canoeist and filmmaker whose work made this river famous to a "
         "generation of Canadians.",
    tip="The portage trail around it is 1.4 km and canoeists carry "
        "everything down it. The boardwalk to the lip is short, and standing "
        "at the brink you can feel the deck move."),
"great-bear-lake": dict(
    name="Great Bear Lake", slug="Great_Bear_Lake", country="Canada",
    region="Northwest Territories", type="nature", tag="hidden",
    emoji="🐟", sounds=["arctic-wind.mp3"],
    highlights=[("Déline", "Déline"),
                ("Mackenzie River", "Mackenzie_River"),
                ("Port Radium", "Port_Radium")],
    blurb="The largest lake entirely inside Canada and the eighth largest "
          "in the world, straddling the Arctic Circle. Ice covers it into "
          "July, the water is nearly sterile with cold, and about 500 "
          "people live on its shore.",
    fact="Port Radium on the east shore mined the uranium used in the "
         "Manhattan Project. Dene men carried the ore in sacks on their "
         "backs, and the community of Déline later sent a delegation to "
         "Hiroshima to apologise, not knowing what they had carried.",
    tip="The lake trout here grow enormous because the water is so cold "
        "they take decades to mature — the world record came out of this "
        "lake. Everything is catch and release now."),
"inuvik": dict(
    name="Inuvik", slug="Inuvik", country="Canada",
    region="Northwest Territories", type="town", tag="hidden",
    emoji="⛪", sounds=["arctic-wind.mp3"],
    highlights=[("Igloo Church", "Our_Lady_of_Victory_Church_(Inuvik)"),
                ("Mackenzie River", "Mackenzie_River"),
                ("Dempster Highway", "Dempster_Highway"),
                ("Tuktoyaktuk", "Tuktoyaktuk")],
    blurb="A planned town of 3,200 built in the 1950s on the Mackenzie "
          "Delta, 200 km above the Arctic Circle — the first community in "
          "the Canadian north designed as a town rather than grown from a "
          "trading post.",
    fact="Every building sits on pilings driven into permafrost, and all "
         "the water, sewage and heating runs above ground in insulated "
         "boxes called utilidors. Burying them would thaw the ground and "
         "the town would sink.",
    tip="The sun does not set for 56 days from late May. The Igloo Church, "
        "built dome-shaped by a priest with no architectural training, is "
        "the town's landmark and the interior is worth asking to see."),
"tuktoyaktuk": dict(
    name="Tuktoyaktuk", slug="Tuktoyaktuk", country="Canada",
    region="Northwest Territories", type="village", tag="hidden",
    emoji="🌊", sounds=["arctic-wind.mp3"],
    highlights=[("Beaufort Sea", "Beaufort_Sea"),
                ("Mackenzie River Delta", "Mackenzie_River_Delta"),
                ("Inuvik", "Inuvik"),
                ("Kugmallit Bay", None)],
    blurb="An Inuvialuit hamlet of 900 on the Arctic Ocean, and since 2017 "
          "the end of the only road in Canada that reaches the Arctic "
          "coast. Before that, the highway was a river of ice each winter.",
    fact="There are about 1,350 pingos around Tuk — ice-cored hills pushed "
         "up out of the flat delta, some 50 m high. It is a quarter of all "
         "the pingos on Earth, and eight of them are a national landmark.",
    tip="Dipping a hand in the Arctic Ocean at the end of the road is the "
        "local ritual and there is a sign for it. The community charges a "
        "small fee for visitors, which goes to the hamlet."),
"fort-smith": dict(
    name="Fort Smith", slug="Fort_Smith,_Northwest_Territories",
    country="Canada", region="Northwest Territories", type="town",
    tag="hidden",
    emoji="🦬", sounds=["wilderness.mp3"],
    search_name="Fort Smith Northwest Territories",
    highlights=[("Wood Buffalo National Park",
                 "Wood_Buffalo_National_Park"),
                ("Slave River", "Slave_River"),
                ("Rapids of the Drowned", None)],
    blurb="A town of 2,500 on the Slave River at the Alberta border, "
          "founded where four sets of rapids forced everything going north "
          "to be portaged. The headquarters for Wood Buffalo, the largest "
          "national park in Canada.",
    fact="White pelicans nest on rocks in the middle of the rapids here — "
         "the most northerly colony in the world, 1,200 km from any other. "
         "They fly upstream to fish and come back through whitewater.",
    tip="The Rapids of the Drowned are named for five men who died running "
        "them in 1786. There is a viewing platform in town, and the "
        "pelicans are visible from it with binoculars all summer."),
"hay-river": dict(
    name="Hay River", slug="Hay_River,_Northwest_Territories",
    country="Canada", region="Northwest Territories", type="town",
    tag="hidden",
    emoji="🚢", sounds=["arctic-wind.mp3"],
    search_name="Hay River Northwest Territories",
    highlights=[("Great Slave Lake", "Great_Slave_Lake"),
                ("Alexandra Falls", None),
                ("Twin Falls Gorge Territorial Park", None),
                ("Mackenzie River", "Mackenzie_River")],
    blurb="The hub of the north, on the south shore of Great Slave Lake — "
          "where the railway ends and the barges start, carrying everything "
          "that goes down the Mackenzie to the Arctic coast in the twelve "
          "weeks the river is open.",
    fact="The town has the longest ice-free season and the warmest summers "
         "in the territory, and grows a surprising amount of its own food. "
         "It also has the NWT's only commercial fishery.",
    tip="Alexandra Falls, half an hour south, drops 32 m into a limestone "
        "gorge you can walk down into. Twin Falls Gorge has two waterfalls "
        "and a trail between them, and almost nobody stops."),
"norman-wells": dict(
    name="Norman Wells", slug="Norman_Wells", country="Canada",
    region="Northwest Territories", type="town", tag="hidden",
    emoji="🛢️", sounds=["wilderness.mp3"],
    highlights=[("Mackenzie River", "Mackenzie_River"),
                ("Canol Road", "Canol_Road"),
                ("Mackenzie Mountains", "Mackenzie_Mountains")],
    blurb="An oil town of 700 on the Mackenzie River, where oil seeping "
          "out of the bank was known to the Dene long before a well was "
          "drilled in 1920 — the first oil field discovered in the "
          "Canadian north.",
    fact="The Canol Project of 1942 built a pipeline and road 1,000 km "
         "from here over the Mackenzie Mountains to Whitehorse, at "
         "enormous cost. It operated for eleven months, then was abandoned "
         "where it stood.",
    tip="The Canol Heritage Trail follows the abandoned road and is one of "
        "the hardest long-distance hikes in North America — 355 km, no "
        "bridges, and rusting trucks still sitting on it."),
"thaidene-nene": dict(
    name="Thaidene Nëné", slug="Thaidene_Nëné_National_Park_Reserve",
    country="Canada", region="Northwest Territories", type="wilderness",
    tag="hidden",
    emoji="🪨", sounds=["arctic-wind.mp3"],
    highlights=[("Great Slave Lake", "Great_Slave_Lake"),
                ("Łutselkʼe", "Łutselkʼe"),
                ("Canadian Shield", "Canadian_Shield")],
    blurb="Fourteen thousand square kilometres on the East Arm of Great "
          "Slave Lake — cliffs, deep clear water and the treeline running "
          "through the middle of it, where boreal forest gives out to "
          "tundra.",
    fact="The name means land of the ancestors in Dënesųłıné. The Łutsel "
         "K'e Dene fought a national park here for forty years, then "
         "negotiated one they co-govern as equals — a model since copied "
         "elsewhere in Canada.",
    tip="Pethei Peninsula's cliffs rise 200 m straight out of the lake, "
        "and the water beneath them is clear to 30 m. Access is boat or "
        "float plane from Yellowknife."),
"aulavik": dict(
    name="Aulavik National Park", slug="Aulavik_National_Park",
    country="Canada", region="Northwest Territories", type="wilderness",
    tag="hidden",
    emoji="🐂", sounds=["arctic-wind.mp3"],
    highlights=[("Banks Island", "Banks_Island"),
                ("Thomsen River", "Thomsen_River"),
                ("Sachs Harbour", "Sachs_Harbour"),
                ("M'Clure Strait", "M'Clure_Strait")],
    blurb="Twelve thousand square kilometres of Arctic desert on northern "
          "Banks Island, with the northernmost navigable river in the world "
          "running through it and more muskoxen than anywhere else on Earth.",
    fact="Banks Island holds roughly 68,000 muskoxen — about two thirds of "
         "the world population. In the park's river valley they are the "
         "commonest large animal you will see, in a landscape with no "
         "trees at all.",
    tip="Aulavik receives a handful of visitors a year, arriving by "
        "chartered Twin Otter from Inuvik. HMS Investigator, abandoned "
        "during the Franklin search, was found on the coast just outside "
        "the park in 2010."),
"tuktut-nogait": dict(
    name="Tuktut Nogait National Park", slug="Tuktut_Nogait_National_Park",
    country="Canada", region="Northwest Territories", type="wilderness",
    tag="hidden",
    emoji="🦌", sounds=["arctic-wind.mp3"],
    highlights=[("Paulatuk", "Paulatuk"),
                ("Hornaday River", "Hornaday_River"),
                ("Amundsen Gulf", "Amundsen_Gulf")],
    blurb="Arctic tundra above the Amundsen Gulf, canyons cut 100 m into "
          "the plateau, and the calving grounds of the Bluenose West "
          "caribou herd. Established in 1996 at the request of the people "
          "of Paulatuk.",
    fact="The name means young caribou in Inuvialuktun. The community "
         "insisted on protection here because the herd's calving ground was "
         "the one thing they could not afford to have disturbed — the park "
         "was their idea, not the government's.",
    tip="La Roncière Falls on the Hornaday drops into a red rock canyon "
        "and is the destination for most trips. Access is a charter from "
        "Paulatuk, 40 km away, and there are no facilities."),
"dettah": dict(
    name="Dettah", slug="Dettah", country="Canada",
    region="Northwest Territories", type="village", tag="hidden",
    emoji="🛷", sounds=["arctic-wind.mp3"],
    highlights=[("Yellowknife", "Yellowknife"),
                ("Great Slave Lake", "Great_Slave_Lake"),
                ("Ingraham Trail", "Ingraham_Trail")],
    blurb="A Yellowknives Dene community of 250 across the bay from "
          "Yellowknife — 27 km by road around the shore, or 6.5 km straight "
          "across the ice in winter, which is how most people go.",
    fact="The ice road to Dettah is one of the few public ice roads still "
         "maintained as a highway. It opens when the ice reaches about "
         "70 cm, and warming winters have shortened its season by weeks.",
    tip="The name means burnt point in Wıìlıìdeh Yatıì. Go for the spring "
        "carnival on the ice — hand games, dog sledding and tea boiling "
        "contests, and it is open to everyone."),
"mackenzie-river": dict(
    name="Mackenzie River", slug="Mackenzie_River", country="Canada",
    region="Northwest Territories", type="nature", tag="hidden",
    emoji="🛶", sounds=["wilderness.mp3"],
    highlights=[("Great Slave Lake", "Great_Slave_Lake"),
                ("Norman Wells", "Norman_Wells"),
                ("Inuvik", "Inuvik"),
                ("Fort Simpson", "Fort_Simpson")],
    blurb="The longest river in Canada, 1,738 km from Great Slave Lake to "
          "the Arctic Ocean, draining a fifth of the country. Its delta is "
          "the second largest Arctic delta in the world, a maze of 25,000 "
          "lakes.",
    fact="Alexander Mackenzie followed it to the sea in 1789 hoping it went "
         "to the Pacific. It did not, and he called it the River of "
         "Disappointment. The Dene name, Deh Cho, means big river, and is "
         "increasingly what it is called.",
    tip="The ferries at Tsiigehtchic and Fort Providence run only in open "
        "water, and the ice crossings only in deep winter. Freeze-up and "
        "break-up leave the north road-isolated for several weeks each way."),

# =============================== NUNAVUT ==============================
"iqaluit": dict(
    name="Iqaluit", slug="Iqaluit", country="Canada",
    region="Nunavut", type="city", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Frobisher Bay", "Frobisher_Bay"),
                ("Nunatta Sunakkutaangit Museum", None),
                ("Sylvia Grinnell Territorial Park", None),
                ("Baffin Island", "Baffin_Island")],
    blurb="The capital of Nunavut and the smallest capital in Canada — "
          "7,500 people at the head of Frobisher Bay on Baffin Island, with "
          "no road to anywhere else. Everything arrives by air or on the "
          "sealift in August.",
    fact="Nunavut was created in 1999, the first change to Canada's map "
         "since Newfoundland joined in 1949. It covers a fifth of the "
         "country, has about 40,000 people, and is 84% Inuit.",
    tip="Frobisher Bay has a tidal range of 11 m, among the largest in the "
        "world, which is why the boats sit on mud half the day. Inuktitut "
        "is the working language here — Iqaluit means place of many fish."),
"pangnirtung": dict(
    name="Pangnirtung", slug="Pangnirtung", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🎨", sounds=["arctic-wind.mp3"],
    highlights=[("Auyuittuq National Park", "Auyuittuq_National_Park"),
                ("Cumberland Sound", "Cumberland_Sound"),
                ("Pangnirtung Fjord", None),
                ("Mount Duval", None)],
    blurb="A hamlet of 1,500 in a fjord on Baffin Island, mountains rising "
          "on both sides of the single road, and the gateway to Auyuittuq. "
          "Known throughout the Arctic for its printmakers and its "
          "tapestry studio.",
    fact="Pangnirtung recorded a wind gust of 155 km/h in a valley that "
         "funnels the weather straight down onto the town. The local name "
         "for the phenomenon, and the general condition, is simply the "
         "Pang wind.",
    tip="The print shop has produced an annual collection since 1973 and "
        "the work is collected internationally. Prices at the co-op are a "
        "fraction of what the same print costs in a southern gallery."),
"auyuittuq": dict(
    name="Auyuittuq National Park", slug="Auyuittuq_National_Park",
    country="Canada", region="Nunavut", type="mountain", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Mount Thor", "Mount_Thor"),
                ("Mount Asgard", "Mount_Asgard"),
                ("Akshayuk Pass", "Akshayuk_Pass"),
                ("Pangnirtung", "Pangnirtung")],
    blurb="Granite walls and glaciers on Baffin Island, with a pass running "
          "97 km through the middle of it that Inuit have used as a travel "
          "route for generations and that is now the only way across on "
          "foot.",
    fact="Mount Thor has the greatest vertical drop on Earth — 1,250 m of "
         "granite overhanging at an average angle of 105 degrees. A dropped "
         "stone falls free the entire way.",
    tip="The name means the land that never melts. Crossing Akshayuk Pass "
        "takes eight to ten days, involves unbridged river fords that rise "
        "through the day, and requires a mandatory Parks Canada orientation."),
"pond-inlet": dict(
    name="Pond Inlet", slug="Pond_Inlet", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🐳", sounds=["arctic-wind.mp3"],
    highlights=[("Bylot Island", "Bylot_Island"),
                ("Sirmilik National Park", "Sirmilik_National_Park"),
                ("Baffin Island", "Baffin_Island"),
                ("Eclipse Sound", "Eclipse_Sound")],
    blurb="An Inuit hamlet of 1,600 on northern Baffin Island looking "
          "across Eclipse Sound at the glaciers and bird cliffs of Bylot "
          "Island. Among the most spectacular settings of any community in "
          "Canada.",
    fact="The floe edge — where landfast ice meets open water — forms "
         "offshore each spring and draws narwhal, beluga, bowhead, polar "
         "bears and seals to the same line. Guides take visitors out onto "
         "the ice to camp beside it.",
    tip="Mittimatalik is its Inuktitut name. Floe edge season is May and "
        "June and it is the single best wildlife experience in the "
        "Canadian Arctic — book with an outfitter from the community."),
"sirmilik": dict(
    name="Sirmilik National Park", slug="Sirmilik_National_Park",
    country="Canada", region="Nunavut", type="wilderness", tag="hidden",
    emoji="🦅", sounds=["arctic-wind.mp3"],
    highlights=[("Bylot Island", "Bylot_Island"),
                ("Pond Inlet", "Pond_Inlet"),
                ("Borden Peninsula", "Borden_Peninsula"),
                ("Oliver Sound", None)],
    blurb="Twenty-two thousand square kilometres across Bylot Island and "
          "the Borden Peninsula — glaciers, hoodoos, and seabird cliffs "
          "holding one of the largest colonies of thick-billed murres and "
          "black-legged kittiwakes in the world.",
    fact="The name means place of glaciers. Bylot Island's greater snow "
         "goose colony is among the largest anywhere, and the island has "
         "been a migratory bird sanctuary since 1965 — thirty years before "
         "the park existed.",
    tip="Oliver Sound is a 30 km fjord with no glacier at its head, so the "
        "water is calm and clear. It is a boat day trip from Pond Inlet in "
        "August and the least difficult way into the park."),
"kinngait": dict(
    name="Kinngait", slug="Kinngait", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🖨️", sounds=["arctic-wind.mp3"],
    search_name="Kinngait Cape Dorset Nunavut",
    highlights=[("Kinngait Studios", None),
                ("Foxe Peninsula", None),
                ("Mallikjuaq Territorial Park", None)],
    blurb="A hamlet of 1,400 on the south-west tip of Baffin Island, "
          "formerly Cape Dorset, and the centre of Inuit printmaking and "
          "carving — by some counts the highest proportion of working "
          "artists of any community on Earth.",
    fact="Kenojuak Ashevak's 1960 print The Enchanted Owl was made here and "
         "became the most recognised piece of Inuit art in the world. It "
         "has been on a Canadian stamp, and the annual print collection "
         "from these studios has been issued since 1959.",
    tip="Mallikjuaq, across a tidal flat you can walk at low tide, has "
        "Thule house rings and food caches a thousand years old sitting "
        "open on the tundra."),
"arctic-bay": dict(
    name="Arctic Bay", slug="Arctic_Bay", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="❄️", sounds=["arctic-wind.mp3"],
    highlights=[("Admiralty Inlet", "Admiralty_Inlet_(Nunavut)"),
                ("Baffin Island", "Baffin_Island"),
                ("Nanisivik", "Nanisivik")],
    blurb="A hamlet of 1,000 in a sheltered bay on Admiralty Inlet, the "
          "longest fjord in the world, with a flat-topped mountain called "
          "King George V behind it. Three months of continuous darkness "
          "each winter.",
    fact="Ikpiarjuk means the pocket, for the way the hills wrap the bay. "
          "The narwhal population in Admiralty Inlet is one of the largest "
          "anywhere and passes close to the community each summer.",
    tip="The sun returns in early February and the community marks it. The "
        "abandoned mine town at Nanisivik, 30 km away, is being cleared for "
        "a naval refuelling facility — the Arctic's strategic geography, "
        "in one place."),
"resolute": dict(
    name="Resolute", slug="Resolute,_Nunavut", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🧭", sounds=["arctic-wind.mp3"],
    search_name="Resolute Bay Nunavut",
    highlights=[("Cornwallis Island", "Cornwallis_Island_(Nunavut)"),
                ("Northwest Passage", "Northwest_Passage"),
                ("Barrow Strait", "Barrow_Strait")],
    blurb="One of the most northerly communities in Canada, 200 people on "
          "Cornwallis Island at 74°N, and the staging point for almost "
          "every expedition heading further north — poles, ice camps and "
          "the high Arctic parks.",
    fact="The community exists because of the High Arctic relocations of "
         "1953, when Inuit families from northern Quebec were moved here to "
         "assert Canadian sovereignty. They were promised they could return "
         "and were not allowed to. Canada apologised in 2010.",
    tip="Qausuittuq means the place with no dawn. The Canadian military's "
        "Arctic Training Centre is here, and so is the runway that "
        "everything going to the North Pole passes through."),
"grise-fiord": dict(
    name="Grise Fiord", slug="Grise_Fiord", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🐻‍❄️", sounds=["arctic-wind.mp3"],
    highlights=[("Ellesmere Island", "Ellesmere_Island"),
                ("Jones Sound", "Jones_Sound"),
                ("Craig Harbour", "Craig_Harbour")],
    blurb="Canada's northernmost civilian community, 130 people at 76°N on "
          "Ellesmere Island, under a mountain wall on Jones Sound. Four "
          "months without sunrise, and average February temperatures near "
          "−40°C.",
    fact="Its Inuktitut name, Aujuittuq, means the place that never thaws. "
         "It was founded by the same 1953 relocation as Resolute, in a spot "
         "the families were told resembled home. It did not.",
    tip="The community runs guided trips out to the floe edge and to the "
        "walrus haul-outs. Getting here means two flights from Iqaluit and "
        "the weather cancels a lot of them — build in days."),
"quttinirpaaq": dict(
    name="Quttinirpaaq National Park", slug="Quttinirpaaq_National_Park",
    country="Canada", region="Nunavut", type="wilderness", tag="hidden",
    emoji="🧊", sounds=["arctic-wind.mp3"],
    highlights=[("Ellesmere Island", "Ellesmere_Island"),
                ("Lake Hazen", "Lake_Hazen"),
                ("Barbeau Peak", "Barbeau_Peak"),
                ("Tanquary Fiord", None)],
    blurb="The most northerly national park in the world, on the top of "
          "Ellesmere Island — 37,000 km² of polar desert, ice caps and "
          "mountains, and the second largest park in Canada.",
    fact="Lake Hazen inside the park is a thermal oasis: mountains shelter "
         "it enough that summer temperatures reach 20°C, 800 km from the "
         "North Pole. Arctic hares, wolves and muskoxen live around it "
         "year-round.",
    tip="The name means top of the world. There are perhaps a few dozen "
        "visitors a year, all arriving by chartered Twin Otter from "
        "Resolute at very considerable expense."),
"alert": dict(
    name="Alert", slug="Alert,_Nunavut", country="Canada",
    region="Nunavut", type="landmark", tag="hidden",
    emoji="📡", sounds=["arctic-wind.mp3"],
    search_name="Alert Nunavut northernmost",
    highlights=[("Ellesmere Island", "Ellesmere_Island"),
                ("Lincoln Sea", "Lincoln_Sea"),
                ("Quttinirpaaq National Park",
                 "Quttinirpaaq_National_Park")],
    blurb="The northernmost permanently inhabited place on Earth — a "
          "military signals station and weather observatory at 82.5°N, "
          "817 km from the North Pole, staffed on rotation by about 60 "
          "people.",
    fact="The sun sets in mid-October and does not rise again until early "
         "March. Alert has recorded a July temperature of 21°C, the "
         "highest ever measured that far north, and the station's carbon "
         "dioxide record is one of the longest baseline series anywhere.",
    tip="There is no civilian access. It is on the map here because it is "
        "the end of the inhabited world, and because the greenhouse gas "
        "numbers measured at Alert are quoted in every climate report you "
        "have read."),
"rankin-inlet": dict(
    name="Rankin Inlet", slug="Rankin_Inlet", country="Canada",
    region="Nunavut", type="town", tag="hidden",
    emoji="🪨", sounds=["arctic-wind.mp3"],
    highlights=[("Hudson Bay", "Hudson_Bay"),
                ("Marble Island", "Marble_Island"),
                ("Meliadine River", None)],
    blurb="The hub of the Kivalliq region on the west coast of Hudson Bay, "
          "2,900 people, founded around a nickel mine in 1955 and now the "
          "transport and government centre for the whole mainland side of "
          "Nunavut.",
    fact="Rankin Inlet produced Jordin Tootoo, the first Inuk to play in "
         "the NHL. The community's ceramics studio, revived in the 1990s "
         "after closing in 1975, is the only Inuit ceramic operation of "
         "its kind.",
    tip="Marble Island, 50 km offshore, is white quartzite and considered "
        "sacred — tradition holds that you crawl ashore on first landing. "
        "James Knight's 1719 expedition died there to the last man."),
"baker-lake": dict(
    name="Baker Lake", slug="Baker_Lake,_Nunavut", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🧵", sounds=["arctic-wind.mp3"],
    search_name="Baker Lake Nunavut",
    highlights=[("Thelon River", "Thelon_River"),
                ("Baker Lake", "Baker_Lake_(Nunavut)"),
                ("Kazan River", "Kazan_River")],
    blurb="The only inland community in Nunavut and the geographic centre "
          "of Canada — 2,000 people on a lake at the head of Chesterfield "
          "Inlet, where the Thelon and Kazan rivers come down off the "
          "Barrenlands.",
    fact="Baker Lake's wall hangings, appliquéd in felt and duffel, are a "
         "distinct art form that developed here in the 1960s and exists "
         "essentially nowhere else. Jessie Oonark's work from this "
         "community hangs in the National Gallery.",
    tip="The Thelon River above the lake runs through a wooded oasis in the "
        "middle of the tundra, hundreds of kilometres past the treeline. "
        "It is one of the great canoe trips on Earth and takes a month."),
"cambridge-bay": dict(
    name="Cambridge Bay", slug="Cambridge_Bay", country="Canada",
    region="Nunavut", type="town", tag="hidden",
    emoji="🔬", sounds=["arctic-wind.mp3"],
    highlights=[("Victoria Island", "Victoria_Island_(Canada)"),
                ("Northwest Passage", "Northwest_Passage"),
                ("Canadian High Arctic Research Station", None),
                ("Ovayok Territorial Park", None)],
    blurb="The largest community on Victoria Island and the main stop on "
          "the Northwest Passage — 1,800 people, a deepwater anchorage, "
          "and the Canadian High Arctic Research Station, the country's "
          "flagship northern science facility.",
    fact="Roald Amundsen's ship Maud sank here in 1930 and lay on the "
         "bottom for 86 years. It was raised in 2016 and towed across the "
         "Atlantic on a barge back to Norway, arriving in 2018.",
    tip="Iqaluktuuttiaq means good fishing place, and the Arctic char here "
        "is regarded as the best in the north. Cruise ships transiting the "
        "Passage stop here, which is the one week a year it is busy."),
"gjoa-haven": dict(
    name="Gjoa Haven", slug="Gjoa_Haven", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="⚓", sounds=["arctic-wind.mp3"],
    highlights=[("King William Island", "King_William_Island"),
                ("Victoria Strait", "Victoria_Strait"),
                ("Rae Strait", "Rae_Strait"),
                ("Northwest Passage", "Northwest_Passage")],
    blurb="A hamlet of 1,300 on King William Island, in the harbour where "
          "Amundsen wintered for two years on the first successful "
          "navigation of the Northwest Passage — and where he learned from "
          "the Netsilik how to survive in the Arctic.",
    fact="Amundsen credited that apprenticeship — dogs, furs, snow houses "
         "— with getting him to the South Pole ahead of Scott. What he "
         "learned in this harbour won the race at the other end of the "
         "world.",
    tip="Inuit oral testimony about where Franklin's ships sank was "
        "recorded in the 1860s, disbelieved for 150 years, and turned out "
        "to be exactly right when Erebus was found in 2014. The community "
        "has never been quiet about this."),
"beechey-island": dict(
    name="Beechey Island", slug="Beechey_Island", country="Canada",
    region="Nunavut", type="history", tag="hidden",
    emoji="🪦", sounds=["arctic-wind.mp3"],
    highlights=[("Lancaster Sound", "Lancaster_Sound"),
                ("Devon Island", "Devon_Island"),
                ("Northwest Passage", "Northwest_Passage"),
                ("Resolute", "Resolute,_Nunavut")],
    blurb="A small island off Devon Island where Franklin's expedition "
          "spent the winter of 1845–46, and where three of his men are "
          "buried. The headboards stand on a gravel beach with nothing else "
          "on it.",
    fact="The three bodies were exhumed in the 1980s and found frozen and "
         "almost perfectly preserved after 140 years. Their tissues showed "
         "high lead levels, and the photographs of their faces are among "
         "the most unsettling images in polar history.",
    tip="Cruise ships transiting the Passage stop here and it is the only "
        "practical access. The graves are a National Historic Site and "
        "nothing may be touched or taken."),
"igloolik": dict(
    name="Igloolik", slug="Igloolik", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🎬", sounds=["arctic-wind.mp3"],
    highlights=[("Foxe Basin", "Foxe_Basin"),
                ("Melville Peninsula", "Melville_Peninsula"),
                ("Baffin Island", "Baffin_Island")],
    blurb="An island community of 2,000 in Foxe Basin, continuously "
          "occupied for around 4,000 years — one of the longest-inhabited "
          "places in the Arctic — and the home of Inuit filmmaking.",
    fact="Atanarjuat: The Fast Runner was made here in 2001, entirely in "
         "Inuktitut with an Inuit cast and crew, and won the Caméra d'Or at "
         "Cannes. It is regularly named the greatest Canadian film ever "
         "made.",
    tip="Artcirq, the community's circus troupe, was founded as a youth "
        "suicide prevention project and now tours internationally. If they "
        "are performing while you are here, go."),
"naujaat": dict(
    name="Naujaat", slug="Naujaat", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🧭", sounds=["arctic-wind.mp3"],
    search_name="Naujaat Repulse Bay Nunavut",
    highlights=[("Melville Peninsula", "Melville_Peninsula"),
                ("Hudson Bay", "Hudson_Bay"),
                ("Committee Bay", "Committee_Bay")],
    blurb="A hamlet of 1,200 sitting exactly on the Arctic Circle at the "
          "top of Hudson Bay, formerly Repulse Bay. A cairn in the "
          "community marks the line, and the sun does not quite set at "
          "solstice.",
    fact="Naujaat means nesting place of seagulls, for the cliffs beside "
         "the community. The former English name came from a bay that "
         "repulsed an eighteenth-century expedition looking for the "
         "Northwest Passage by refusing to have an outlet.",
    tip="Bowhead whales — which can live over 200 years, longer than any "
        "other mammal — are hunted here under quota, and the community's "
        "carvers work in whalebone as a result."),
"kugluktuk": dict(
    name="Kugluktuk", slug="Kugluktuk", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🌊", sounds=["arctic-wind.mp3"],
    highlights=[("Coppermine River", "Coppermine_River"),
                ("Coronation Gulf", "Coronation_Gulf"),
                ("Bloody Falls", "Bloody_Falls")],
    blurb="The westernmost community in Nunavut, 1,500 people at the mouth "
          "of the Coppermine River on Coronation Gulf — the warmest place "
          "in the territory, where trees actually reach the coast.",
    fact="Samuel Hearne walked overland to this river mouth in 1771, the "
         "first European to reach the Arctic Ocean by land in North "
         "America. His Dene companions killed a party of Inuit at the "
         "rapids upstream, which is why they are called Bloody Falls.",
    tip="Kugluktuk means place of moving water. The falls are 15 km "
        "upstream, reachable by boat or on foot, and the char run through "
        "them in numbers in August."),
"sanikiluaq": dict(
    name="Sanikiluaq", slug="Sanikiluaq", country="Canada",
    region="Nunavut", type="village", tag="hidden",
    emoji="🦆", sounds=["arctic-wind.mp3"],
    highlights=[("Belcher Islands", "Belcher_Islands"),
                ("Hudson Bay", "Hudson_Bay"),
                ("Flaherty Island", "Flaherty_Island")],
    blurb="The southernmost community in Nunavut, on the Belcher Islands in "
          "Hudson Bay — an archipelago of about 1,500 low islands of "
          "folded rock, 150 km from the Quebec coast and reachable only "
          "through Winnipeg.",
    fact="The people here depend on eider ducks in a way found nowhere "
         "else, using the skins with the down attached to make parkas. "
         "When the sea ice behaves strangely and the eiders die in "
         "numbers, it is noticed here first.",
    tip="The soapstone carvings from Sanikiluaq — especially the eiders — "
        "are distinctive, and the stone is quarried on the islands. The "
        "one flight a week routes through Montreal or Winnipeg, not "
        "Iqaluit."),
"devon-island": dict(
    name="Devon Island", slug="Devon_Island", country="Canada",
    region="Nunavut", type="island", tag="hidden",
    emoji="🚀", sounds=["arctic-wind.mp3"],
    highlights=[("Haughton impact crater", "Haughton_impact_crater"),
                ("Resolute", "Resolute,_Nunavut"),
                ("Baffin Bay", "Baffin_Bay")],
    blurb="The largest uninhabited island on Earth, 55,000 km² of polar "
          "desert in the high Arctic, with a 23 km meteorite crater near "
          "the middle of it and nobody living anywhere on it.",
    fact="NASA has run a Mars analogue research station in the Haughton "
         "crater since 1997. The cold, the dryness, the rock and the "
         "isolation make it the closest thing to Mars that can be reached "
         "without leaving the planet.",
    tip="There is no access without a research permit or an expedition "
        "charter. The island's south coast is passed by Northwest Passage "
        "cruises, which is how most people who have seen it, saw it."),
"ukkusiksalik": dict(
    name="Ukkusiksalik National Park", slug="Ukkusiksalik_National_Park",
    country="Canada", region="Nunavut", type="wilderness", tag="hidden",
    emoji="🐻‍❄️", sounds=["arctic-wind.mp3"],
    highlights=[("Wager Bay", "Wager_Bay"),
                ("Hudson Bay", "Hudson_Bay"),
                ("Repulse Bay", "Naujaat")],
    blurb="A park around Wager Bay, a 100 km inlet off Hudson Bay with a "
          "reversing tidal falls at its mouth — the water runs both ways "
          "through a narrows twice a day, and the bay behind is polar bear "
          "country.",
    fact="Ukkusiksalik means the place where there is stone for carving "
         "pots, for the soapstone taken here for generations. Over five "
         "hundred archaeological sites have been recorded in the park, "
         "including tent rings, food caches and fox traps.",
    tip="The bear density around Wager Bay is high enough that all visitors "
        "travel with armed Inuit guides from Naujaat or Chesterfield "
        "Inlet. There are no facilities and no marked routes."),
}


# ---------------------------------------------------------------------------
# FILL — what the 36 shipped records are missing.
#
# `rb.fill()` only writes a field that is currently empty, so nothing here can
# overwrite prose somebody already wrote. Two things are missing across the
# shipped roster:
#
#   search_name   nobody had it, because the field did not exist when this
#                 file was written. It is the only lever that reaches the
#                 media and monument searches BEFORE they run — a bare
#                 "Churchill" query returns Winston, and no title guard
#                 downstream can tell that the photo of a statesman is not a
#                 photo of a town on Hudson Bay.
#   hidden_gem_tip  five of the earliest records never got one.
# ---------------------------------------------------------------------------
FILL = {
    # --- the five records with no tip -------------------------------------
    "niagara-falls": dict(
        search_name="Niagara Falls Ontario Canada",
        tip="Cross to Table Rock at 2 a.m. The falls are lit, the coach "
            "parties are gone, and the viewing terrace directly over the "
            "Horseshoe crest is open around the clock and free."),
    "cn-tower": dict(
        tip="The glass floor is 342 m up and people queue for it. The "
            "outdoor SkyTerrace one level down has the same view through "
            "nothing at all, and is usually empty."),
    "old-quebec": dict(
        search_name="Old Quebec Vieux-Québec",
        tip="Walk the ramparts at first light. The full 4.6 km circuit is "
            "open, unstaffed and unticketed, and it is the only way to read "
            "how the upper and lower towns fit together."),
    "banff-lake-louise": dict(
        search_name="Lake Louise Banff Alberta",
        tip="Moraine Lake has been closed to private cars since 2023 — "
            "shuttle, bus or bicycle only. Book the first shuttle of the "
            "day; the colour is at its strongest before the sun is on it."),
    "stanley-park": dict(
        search_name="Stanley Park Vancouver",
        tip="The seawall is 9 km around the park and one-way for wheels, "
            "counter-clockwise. Start at Coal Harbour and you finish at "
            "Third Beach for the sunset, which is the way the locals ride "
            "it."),

    # --- search_name only: a namesake loud enough to hijack the search ----
    "churchill": dict(search_name="Churchill Manitoba Hudson Bay"),
    "lunenburg": dict(search_name="Lunenburg Nova Scotia"),
    "grand-river": dict(search_name="Grand River Ontario Canada"),
    "point-farms": dict(search_name="Point Farms Provincial Park Ontario"),
    "pinery": dict(search_name="Pinery Provincial Park Ontario"),
    "rondeau": dict(search_name="Rondeau Provincial Park Ontario"),
    "elora-gorge": dict(search_name="Elora Gorge Ontario"),
    "elora-quarry": dict(search_name="Elora Quarry Ontario"),
    "laurel-creek": dict(
        search_name="Laurel Creek Conservation Area Waterloo Ontario"),
    "starkey-hill": dict(search_name="Starkey Hill Guelph Ontario"),
    "hanlon-creek": dict(search_name="Hanlon Creek Guelph Ontario"),
    "pinehurst-lake": dict(
        search_name="Pinehurst Lake Conservation Area Ontario"),
    "shades-mills": dict(
        search_name="Shade's Mills Conservation Area Cambridge Ontario"),
    "dumfries-conservation-area": dict(
        search_name="Dumfries Conservation Area Cambridge Ontario"),
    "rockwood-conservation-area": dict(
        search_name="Rockwood Conservation Area Ontario"),
    "brant-conservation-area": dict(
        search_name="Brant Conservation Area Brantford Ontario"),
    "byng-island": dict(
        search_name="Byng Island Conservation Area Dunnville Ontario"),
    "apps-mill": dict(search_name="Apps' Mill Nature Centre Brant Ontario"),
    "taquanyah": dict(
        search_name="Taquanyah Conservation Area Cayuga Ontario"),
    "fwr-dickson": dict(
        search_name="F.W.R. Dickson Wilderness Area North Dumfries Ontario"),
    "luther-marsh": dict(search_name="Luther Marsh Wildlife Management Area"),
    "snyders-flats": dict(
        search_name="Snyder's Flats Bloomingdale Ontario"),
    "woolwich-reservoir": dict(
        search_name="Woolwich Reservoir Elmira Ontario"),
    "belwood-lake": dict(search_name="Belwood Lake Fergus Ontario"),
    "conestogo-lake": dict(search_name="Conestogo Lake Ontario"),
    "guelph-lake": dict(search_name="Guelph Lake Ontario"),
    "dawson-city": dict(search_name="Dawson City Yukon"),
    "tofino": dict(search_name="Tofino British Columbia"),
    "hopewell-rocks": dict(search_name="Hopewell Rocks New Brunswick"),
    "peggys-cove": dict(search_name="Peggy's Cove Nova Scotia"),
    "icefields-parkway": dict(search_name="Icefields Parkway Alberta"),
}


# ---------------------------------------------------------------------------
# REPAIR — highlights on shipped records that break the monument rule.
#
# `enrich_monuments.py` spends every highlight as a YouTube search term, so a
# highlight has to be a thing you can stand in front of: a structure, a town
# or a landform. Five shipped Canadian records break that, and two ways:
#
#   a people, an animal, an era or a phenomenon — "Polar Bears", "Northern
#   Lights", "Klondike Gold Rush". Each spends a slot on a search that can
#   only ever return stock nature footage or a documentary.
#
#   SELF — a highlight whose slug is the record's own article. "Tundra Buggy
#   Safari" pointing at Churchill, "The Seawall" pointing at Stanley Park,
#   "Midnight Dome" pointing at Dawson City. That is worse than a dead link:
#   the card promises a second place and delivers the one you are in.
#
# `rb.fill()` cannot do this — it only writes empty fields, by design. So the
# repairs run through `extra`, which sees the final list, and each one is a
# replacement rather than a deletion: the slot stays, pointed at something
# real and nearby.
# ---------------------------------------------------------------------------
REPAIR = {
    "churchill": [
        # was: Polar Bears -> Polar_bear (an animal),
        #      Northern Lights -> Aurora (a phenomenon),
        #      Tundra Buggy Safari -> Churchill,_Manitoba (SELF)
        ("Hudson Bay", "Hudson_Bay"),
        ("Wapusk National Park", "Wapusk_National_Park"),
        ("Prince of Wales Fort", "Prince_of_Wales_Fort"),
        ("Cape Merry", None),
        ("Churchill River", "Churchill_River_(Hudson_Bay)"),
    ],
    "dawson-city": [
        # was: Klondike Gold Rush (an era),
        #      Historic Boardwalk / Midnight Dome -> Dawson_City (SELF, twice)
        ("Bonanza Creek", "Bonanza_Creek"),
        ("Dredge No. 4", "Dredge_No._4"),
        ("Klondike River", "Klondike_River"),
        ("Top of the World Highway", "Top_of_the_World_Highway"),
    ],
    "cn-tower": [
        # was: CN Tower EdgeWalk -> CN_Tower (SELF)
        ("Rogers Centre", "Rogers_Centre"),
        ("Toronto Harbourfront", "Harbourfront,_Toronto"),
        ("Toronto Islands", "Toronto_Islands"),
        ("Ripley's Aquarium of Canada", "Ripley's_Aquarium_of_Canada"),
    ],
    "stanley-park": [
        # was: The Seawall -> Stanley_Park (SELF)
        ("Seawall", "Seawall_(Vancouver)"),
        ("Vancouver Aquarium", "Vancouver_Aquarium"),
        ("Lions Gate Bridge", "Lions_Gate_Bridge"),
        ("Brockton Point Lighthouse", "Brockton_Point_Lighthouse"),
        ("Siwash Rock", "Siwash_Rock"),
    ],
    "old-quebec": [
        # Petit_Champlain is a redirect; the rest are sound. Restated in full
        # so the stored titles are the canonical ones after this run.
        ("Château Frontenac", "Château_Frontenac"),
        ("Quartier Petit Champlain", "Petit_Champlain"),
        ("Plains of Abraham", "Plains_of_Abraham"),
        ("Ramparts of Quebec City", "Ramparts_of_Quebec_City"),
    ],
}


def repair(locs, got, notes):
    """Replace the highlight lists named in REPAIR, on records already shipped.

    Runs as `rb.run(extra=)`, over the final list, after NEW and FILL. Each
    slug still goes through `rb.link()`, so a repair cannot introduce the
    thing it is fixing: a slug that redirects is stored canonical, a slug with
    no article stays a text chip, and a slug that resolves back to the record
    itself is refused as SELF exactly as it would be in a new record.
    """
    by_id = {l["id"]: l for l in locs}
    for pid, pairs in REPAIR.items():
        loc = by_id.get(pid)
        if not loc:
            notes.add("MISSING", pid, "(repair target)",
                      "id is not in the file — REPAIR is stale")
            continue
        before = [h.get("wikipedia_slug") or h["name"]
                  for h in loc.get("highlights") or []]
        loc["highlights"] = rb.highlights({"highlights": pairs}, got, notes,
                                          pid, loc.get("wikipedia_slug"))
        after = [h.get("wikipedia_slug") or h["name"] for h in loc["highlights"]]
        dropped = [s for s in before if s not in after]
        if dropped:
            print(f"  repair {pid:<26} dropped {', '.join(dropped)}")
        rb.far_check(REGION, loc, loc["highlights"], got, notes, pid)


def migrate_province(locs, notes):
    """`province` -> `region`, in place, before anything else runs.

    See the header. This is a rename, not a reinterpretation: the value is
    carried across untouched. If a record somehow has both, the existing
    `region` wins and `province` is dropped — `region` is what every consumer
    prefers already.
    """
    n = 0
    for loc in locs:
        if "province" not in loc:
            continue
        val = loc.pop("province")
        if not loc.get("region"):
            loc["region"] = val
        n += 1
    if n:
        print(f"  migrate {n} record(s): province -> region")


def main():
    # A region with no box is a region the namesake guard silently skips, and
    # the whole reason this generator exists is that Canada's namesakes are
    # internal. Fail loudly at import rather than quietly at review time.
    unboxed = sorted({s["region"] for s in NEW.values()} - set(PROVINCE_BOX))
    if unboxed:
        raise SystemExit(f"NEW claims regions with no PROVINCE_BOX row: {unboxed}")

    extra_slugs = [s for pairs in REPAIR.values() for _, s in pairs if s]
    rb.run(REGION, NEW, FILL, extra=repair, migrate=migrate_province,
           extra_slugs=extra_slugs)


if __name__ == "__main__":
    main()
