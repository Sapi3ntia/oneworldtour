#!/usr/bin/env python3
"""
build_antarctica.py — the seventh continent, which the atlas did not have.

WHAT WAS MISSING
    1,728 places across 201 countries and not one of them south of 56°S.
    Antarctica appeared in the corpus exactly eight times: as a comparison
    ("the saltiest water outside Antarctica"), as a boast (Hobart is the
    closest resupply port to it), and once as a bug — Cordova's
    `Childs_Glacier` redirecting to `Foundation_Ice_Stream` at 83°S, which
    is how the Alaska batch learned that a redirect can cross a hemisphere.

    A continent that only ever shows up in other places' fun facts is a
    gap, not a decision. This is the roster that closes it.

ONE RULE DECIDES THE COUNTRY, AND IT IS NOT OURS
    Seven states claim wedges of Antarctica, two of them overlapping, and
    the rest of the world recognises none of it. Filing McMurdo under "New
    Zealand" (the Ross Dependency), Vostok under "Australia" (the
    Australian Antarctic Territory) or Dumont d'Urville under "France"
    would be taking a side in a dispute the Antarctic Treaty explicitly
    froze in 1961 — and would bury the continent inside three other ones.

    So the rule here is ISO 3166's, which is also the Treaty's:

        everything south of 60°S is AQ.

    That is `in_box`'s first line and it is the whole claim story. North of
    60°S the sub-Antarctic islands keep their own codes — GS, TF, HM, BV —
    exactly as the Oceania batch gave Pacific territories their own rows
    rather than filing Bora Bora under Europe.

P17 IS EXPECTED TO BE MISSING, AND THAT IS THE POINT
    `country_check` warns when an article has no P17. Sixty-six of these
    articles have none, because there is no sovereign to name: that is the
    fact the Treaty establishes, not an incomplete Wikidata record. Warning
    on each of them sixty-six times would bury the ones that matter, so
    `Region` gained `p17_optional` — a country whose articles are EXPECTED
    to answer nothing. It reports NOCLAIM once per record and keeps COUNTRY
    for the surprises. The four sub-Antarctic rows do not use it: they have
    sovereigns (UK, France, Australia, Norway) and they are checked against
    them by name through `expect_p17`.

THE THIRTEEN COUNTRY WARNINGS ARE ALL THE SAME WARNING, AND ALL FINE
    Thirteen articles DO answer P17, and every one of them answers with the
    country that runs the base rather than a country that owns the ground:
    McMurdo→US, Mawson→Australia, Kunlun→China, Villa Las Estrellas→Chile,
    Jang Bogo→South Korea, Bharati→India, Don Juan Pond→New Zealand,
    Mirny→the USSR (Q15180, a state that no longer exists), and four
    Argentine entries. Wikidata is recording the operator; we are recording
    the Treaty. The rule above wins and the field stays AQ.

    Grytviken is the one to actually read: its P17 says Argentina, because
    South Georgia is disputed on Wikidata the way the Falklands are. Ours
    says GS, which is the ISO code and the administering power both.

THE BOX IS A LATITUDE PLUS SIX ISLANDS
    South of 60°S there is nothing to disambiguate: no namesakes, no
    borders, nothing but the Treaty area. North of it a bare latitude test
    would let in Ushuaia (-54.8), Punta Arenas (-53.2), Stanley (-51.7) and
    the whole bottom of New Zealand — all of them real places in other
    region files. So the northern half of the box is six hand-drawn island
    rectangles and nothing else.

WHAT A HIGHLIGHT MAY BE HERE
    Same rule as everywhere: could a camera be pointed at it. Which cuts
    deeper on this continent than any other, because the obvious chips are
    all people (Shackleton, Scott, Amundsen, Mawson), expeditions (Nimrod,
    Terra Nova, Endurance), treaties and ice sheets the size of France.
    Huts, peaks, bays, stations and colonies stay; the rest live in the
    prose. `Endurance` is in five blurbs and no highlight — the wreck is
    3,008 m down in the Weddell Sea and the only camera that has ever seen
    it was on an ROV in 2022.

TRAPS THIS ROSTER HIT (every one caught by the resolver, not by reading)
    * `Alfred-Faure`, the French base on Crozet, redirects to **a French
      cyclist**. The base is `Alfred_Faure`, no hyphen. One character.
    * `Whalers_Bay`, `Hope_Bay`, `Observation_Hill`, `Lake_Bonney` and
      `Maitri` have NO P625 — so they cannot be records (make() refuses
      them) and they are highlights instead, which is exactly what the
      no-coordinate list is for. Maitri got a second chance because the
      base does have an article, under `Maitri_(research_station)`;
      Whalers Bay did not, and its two best details moved into Deception
      Island, which is the article that has the coordinate.
    * Bare `St_Andrews_Bay`, `Salisbury_Plain` and `Stromness` are all the
      British originals. The South Georgia records carry the disambiguated
      titles, `,_South_Georgia`.
    * `Ulvetanna` has no article at all; the peak is `Ulvetanna_Peak`.
    * Four highlight redirects land on a DIFFERENT SUBJECT and were demoted
      to text chips rather than linked to something they are not:
      Barne_Glacier→Mount_Erebus, Errera_Channel→Rongé_Island,
      Cape_Renard→Flandres_Bay, Enterprise_Island→Nansen_Island.
    * `King_George_Island` bare is a disambiguation page with no
      coordinate; the South Shetland one is
      `King_George_Island_(South_Shetland_Islands)`.
    * Seven canonical titles differ from the obvious slug and are stored
      canonical: Neumayer_Station_III, Syowa_Station_(Antarctica),
      Zhongshan_Station_(Antarctica), Great_Wall_Station_(Antarctica),
      Dome_F, Brown_Station, Paradise_Harbour.

NAMESAKES ARE THE NORM, SO `search_name` IS TOO
    Salisbury Plain is in Wiltshire. Stromness is in Orkney. St Andrews
    Bay is in Fife. Half Moon Island is in the Philippines and in Belize.
    Davis, Casey, Mawson, Palmer, Concordia and Troll are all somebody's
    surname or somebody's town. Every one of those records carries a
    `search_name`, because no downstream title guard can see a namesake.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regionbuild as rb

# The Treaty area, and then the six islands that ring it. `name` is the join
# key build_countries.py counts by — copy it, never retype it.
COUNTRY_CODE = {
    "Antarctica": "AQ",
    "South Georgia and the South Sandwich Islands": "GS",
    "French Southern and Antarctic Lands": "TF",
    "Heard Island and McDonald Islands": "HM",
    "Bouvet Island": "BV",
}

COUNTRY_SLUG = {
    "Antarctica": "Antarctica",
    "South Georgia and the South Sandwich Islands":
        "South_Georgia_and_the_South_Sandwich_Islands",
    "French Southern and Antarctic Lands": "French_Southern_and_Antarctic_Lands",
    "Heard Island and McDonald Islands": "Heard_Island_and_McDonald_Islands",
    "Bouvet Island": "Bouvet_Island",
}

# The sovereign each sub-Antarctic island's articles legitimately answer P17
# with. South of 60°S there is no such answer, which is what p17_optional says.
EXPECT_P17 = {
    "South Georgia and the South Sandwich Islands": "United_Kingdom",
    "French Southern and Antarctic Lands": "France",
    "Heard Island and McDonald Islands": "Australia",
    "Bouvet Island": "Norway",
}

# lat_min, lat_max, lng_min, lng_max — the only land this file accepts north
# of the Treaty line. Deliberately tight: a degree of slack here would admit
# Ushuaia, Punta Arenas, Stanley and Stewart Island, all of which already
# live in other region files.
SUB_ANTARCTIC = [
    (-55.5, -53.5, -38.5, -34.5),   # South Georgia
    (-60.0, -55.5, -30.0, -25.0),   # South Sandwich Islands
    (-55.0, -54.0,   2.5,   4.5),   # Bouvet Island
    (-50.5, -48.0,  68.0,  71.5),   # Kerguelen
    (-47.5, -45.5,  49.5,  53.0),   # Crozet
    (-54.0, -52.5,  72.0,  75.0),   # Heard Island and McDonald Islands
]


def in_box(lat, lng):
    """South of 60°S is the Treaty area — nothing else is down there to
    confuse it with. North of it, only the six islands above."""
    if lat <= -60.0:
        return True
    return any(a <= lat <= b and c <= lng <= d for a, b, c, d in SUB_ANTARCTIC)


# Warning-level namesake guard, one level down from the country — the same
# job province boxes do in build_canada.py. Two sectors get NO box on
# purpose: "Ross Sea" and "Polar Plateau" both wrap the antimeridian (the
# Ross Ice Shelf is at -175°, Beardmore at +171°, and every meridian meets
# at the Pole), so a rectangle over either is not a test, it is a coin flip.
SECTOR_BOX = {
    "Antarctic Peninsula":     (-70.5, -62.5, -70.0, -54.0),
    "South Shetland Islands":  (-63.5, -60.8, -63.0, -53.5),
    "South Orkney Islands":    (-61.5, -60.3, -47.0, -44.0),
    "Weddell Sea":             (-78.0, -70.0, -60.0, -15.0),
    "Queen Maud Land":         (-76.0, -69.5, -12.0,  30.0),
    "East Antarctica":         (-70.5, -65.5,  38.0, 145.0),
    "West Antarctica":         (-80.5, -66.0, -140.0, -70.0),
    "South Georgia":           (-55.5, -53.5, -38.5, -34.5),
    "South Sandwich Islands":  (-60.0, -55.5, -30.0, -25.0),
    "Kerguelen":               (-50.5, -48.0,  68.0,  71.5),
    "Crozet":                  (-47.5, -45.5,  49.5,  53.0),
    "Heard Island":            (-54.0, -52.5,  72.0,  75.0),
    "Bouvet Island":           (-55.0, -54.0,   2.5,   4.5),
}

REGION = rb.Region(target="antarctica.json", continent="Antarctica",
                   country_code=COUNTRY_CODE, in_box=in_box,
                   country_slug=COUNTRY_SLUG, expect_p17=EXPECT_P17,
                   subregion_box=SECTOR_BOX, p17_optional={"Antarctica"})

FILL = {}

NEW = {

# ===================== ANTARCTIC PENINSULA =====================
# The banana belt: the only part of the continent most visitors ever see,
# the only part with a summer above freezing, and the fastest-warming
# stretch of the southern hemisphere.

"port-lockroy": dict(
    name="Port Lockroy", slug="Port_Lockroy", country="Antarctica",
    region="Antarctic Peninsula", type="history", tag="famous",
    emoji="📮", sounds=["ocean-waves.mp3"],
    search_name="Port Lockroy Antarctica",
    highlights=[("Bransfield House", None),
                ("Goudier Island", "Goudier_Island"),
                ("Base A", None),
                ("Neumayer Channel", "Neumayer_Channel"),
                ("Jougla Point", None)],
    blurb="A black hut on a rock the size of a football pitch, staffed every "
          "summer by four people who run the world's southernmost post "
          "office and share the island with about 1,500 gentoo penguins. "
          "Built as a secret wartime base in 1944, it now stamps 70,000 "
          "postcards a season that take six months to reach anywhere.",
    fact="The post office is the most-applied-for seasonal job on Earth: "
         "roughly 6,000 people a year apply for four posts with no running "
         "water, no flushing toilet and a nightly bucket count of penguins.",
    tip="Half the island is fenced off as a control plot — the penguins on "
        "that side are studied precisely because nobody walks past them. "
        "Fifty years of data say the tourists make no difference, which is "
        "the rare case of a study everyone hoped would be boring."),

"paradise-harbour": dict(
    name="Paradise Harbour", slug="Paradise_Harbour", country="Antarctica",
    region="Antarctic Peninsula", type="coastal", tag="famous",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    search_name="Paradise Harbour Antarctica",
    highlights=[("Brown Station", "Brown_Station"),
                ("Skontorp Cove", None),
                ("Waterboat Point", "Waterboat_Point"),
                ("Bryde Island", None)],
    blurb="Whalers named it, and whalers were not sentimental people. A "
          "bowl of black cliffs and blue glacier fronts so still that the "
          "mountains arrive twice — once above the water and once in it — "
          "broken only when a serac the size of a house lets go and the "
          "sound reaches you a second after the splash.",
    fact="It is one of only two places on the whole peninsula where cruise "
         "passengers set foot on the Antarctic mainland rather than an "
         "offshore island — everywhere else that feels continental is "
         "technically an island in disguise.",
    tip="Ask for the zodiac cruise instead of the landing. The point of "
        "Paradise is the water level: leopard seals asleep on ice pans, "
        "and the glacier face read from below rather than from above."),

"lemaire-channel": dict(
    name="Lemaire Channel", slug="Lemaire_Channel", country="Antarctica",
    region="Antarctic Peninsula", type="coastal", tag="famous",
    emoji="🚢", sounds=["ocean-waves.mp3"],
    search_name="Lemaire Channel Antarctica",
    highlights=[("Booth Island", "Booth_Island"),
                ("Una Peaks", None),
                ("Cape Renard", None),
                ("Pléneau Bay", None)],
    blurb="Eleven kilometres long, 1,600 metres wide at the pinch, with "
          "cliffs going up 900 metres on both sides and icebergs jammed "
          "between them. Every ship that can fit tries to; the nickname "
          "'Kodak Gap' is older than digital cameras and has outlived them.",
    fact="The channel is regularly impassable — a single season's ice can "
         "cork it for weeks, and ships that entered from the north have had "
         "to reverse out the way they came rather than turn around.",
    tip="The transit is usually run at breakfast for the light. Skip "
        "breakfast."),

"neko-harbour": dict(
    name="Neko Harbour", slug="Neko_Harbour", country="Antarctica",
    region="Antarctic Peninsula", type="coastal", tag="hidden",
    emoji="🏔️", sounds=["ocean-waves.mp3"],
    search_name="Neko Harbour Antarctica",
    highlights=[("Andvord Bay", "Andvord_Bay"),
                ("Gentoo colony", None),
                ("Neko Glacier", None)],
    blurb="A cove off Andvord Bay where a glacier calves straight into the "
          "landing beach and a gentoo colony nests on the slope above it. "
          "Actual continental Antarctica, not an island — you can climb a "
          "hundred metres of snow and look back down at the ship.",
    fact="It is named after a factory ship. The *Neko* processed whales in "
         "this bay through the 1910s and 1920s; the harbour kept the name "
         "of the boat that emptied it.",
    tip="Stand back from the water. A calving here pushes a wave up the "
        "beach that has knocked people over, and the guides' shouted line "
        "about the shoreline is not a formality."),

"cuverville-island": dict(
    name="Cuverville Island", slug="Cuverville_Island", country="Antarctica",
    region="Antarctic Peninsula", type="island", tag="hidden",
    emoji="🐧", sounds=["ocean-waves.mp3"],
    search_name="Cuverville Island Antarctica",
    highlights=[("Errera Channel", None),
                ("Rongé Island", "Rongé_Island"),
                ("Gentoo rookery", None)],
    blurb="Two square kilometres of rock in the Errera Channel holding the "
          "largest gentoo penguin colony on the Antarctic Peninsula — "
          "roughly 6,500 breeding pairs, all of them commuting up the same "
          "worn highways of pink guano from the beach to the ridge.",
    fact="Penguin paths are called 'penguin highways' in the literature "
         "without irony: the birds follow the identical route uphill for "
         "decades, and satellite images pick out the stains from orbit — "
         "which is how several colonies were discovered in the first place.",
    tip="Get downwind before you decide how you feel about penguins."),

"danco-island": dict(
    name="Danco Island", slug="Danco_Island", country="Antarctica",
    region="Antarctic Peninsula", type="island", tag="hidden",
    emoji="⛷️", sounds=["ocean-waves.mp3"],
    search_name="Danco Island Antarctica",
    highlights=[("Errera Channel", None),
                ("Base O", None),
                ("Summit ridge", None)],
    blurb="A 180-metre snow dome in the middle of the Errera Channel with a "
          "gentoo colony at the bottom and a 360° view of the Peninsula "
          "from the top. The British ran a survey base here for three "
          "years in the fifties and took the buildings away again in 2004.",
    fact="Penguins nest all the way up this hill — gentoos will climb 150 "
         "vertical metres carrying stones, one at a time, to build a nest "
         "further from the meltwater than their neighbour's.",
    tip="The walk up is forty minutes in soft snow and the way down takes "
        "four, because everyone slides. Sit on something waterproof."),

"petermann-island": dict(
    name="Petermann Island", slug="Petermann_Island", country="Antarctica",
    region="Antarctic Peninsula", type="island", tag="hidden",
    emoji="🐧", sounds=["ocean-waves.mp3"],
    search_name="Petermann Island Antarctica",
    highlights=[("Port Circumcision", None),
                ("Charcot's cairn", None),
                ("Adélie colony", None)],
    blurb="A low granite island south of the Lemaire Channel holding the "
          "southernmost gentoo colony in the world — and, right beside it, "
          "an Adélie colony that has shrunk by more than 80% since the "
          "1980s while the gentoos moved in behind them.",
    fact="The two species are a thermometer you can watch. Adélies need "
         "sea ice and gentoos do not, so on this one island the birds have "
         "been swapping places for forty years as the ice went.",
    tip="Look for the cross above the landing: it remembers three British "
        "scientists who walked out over the sea ice from Faraday in 1982 "
        "and were never found."),

"vernadsky-station": dict(
    name="Vernadsky Research Base", slug="Vernadsky_Research_Base",
    country="Antarctica", region="Antarctic Peninsula", type="history",
    tag="quirky", emoji="🍸", sounds=["antarctic-wind.mp3"],
    search_name="Vernadsky Station Antarctica",
    highlights=[("Faraday Station", None),
                ("Galindez Island", "Galindez_Island"),
                ("The Faraday Bar", None),
                ("Argentine Islands", "Argentine_Islands")],
    blurb="Ukraine's year-round base on Galindez Island, bought from "
          "Britain in 1996 for one pound. The bar in the back was built by "
          "British carpenters out of timber shipped down for a new pier, "
          "and it is the southernmost bar on Earth.",
    fact="The ozone hole was discovered from this building. The Faraday "
         "team measured the same patch of sky every spring from 1957, and "
         "by 1985 the numbers had fallen so far that the paper's authors "
         "assumed their instrument was broken before they assumed it wasn't.",
    tip="The house rule at the bar: homemade vodka is free to any woman who "
        "leaves her bra behind. The ceiling has been redecorated this way "
        "for thirty years."),

"rothera-station": dict(
    name="Rothera Research Station", slug="Rothera_Research_Station",
    country="Antarctica", region="Antarctic Peninsula", type="history",
    tag="famous", emoji="✈️", sounds=["antarctic-wind.mp3"],
    search_name="Rothera Research Station Antarctica",
    highlights=[("Adelaide Island", "Adelaide_Island"),
                ("Ryder Bay", None),
                ("Bonner Laboratory", None),
                ("Reptile Ridge", None)],
    blurb="Britain's Antarctic capital: a gravel runway on Adelaide Island, "
          "a wharf, a dive lab, and up to 160 people in summer. Everything "
          "the UK does further south — deep-field camps, Sky-Blu, Halley — "
          "is flown out of here in red Twin Otters.",
    fact="The runway is 900 m of crushed rock with the sea at both ends and "
         "no go-around option worth the name, which is why BAS pilots train "
         "for it specifically and why the new wharf and its ice-strengthened "
         "ship, the *Sir David Attenborough*, matter so much.",
    tip="'Boatshed Point' and 'Reptile Ridge' are the two walks people who "
        "winter here name when you ask what they missed afterwards."),

"palmer-station": dict(
    name="Palmer Station", slug="Palmer_Station", country="Antarctica",
    region="Antarctic Peninsula", type="history", tag="famous",
    emoji="🔬", sounds=["ocean-waves.mp3"],
    search_name="Palmer Station Antarctica",
    highlights=[("Anvers Island", "Anvers_Island"),
                ("Arthur Harbor", None),
                ("Mount Français", "Mount_Français"),
                ("Torgersen Island", "Torgersen_Island")],
    blurb="The smallest of the three American stations — 46 people at peak, "
          "on the rocks of Anvers Island — and the only one you cannot fly "
          "to. Everyone and everything arrives by ship across the Drake "
          "Passage, four days from Punta Arenas.",
    fact="Palmer runs one of the longest-running ecosystem studies on the "
         "planet. The Adélie colony it was built to watch has fallen from "
         "about 15,000 breeding pairs in 1975 to a few hundred; the same "
         "researchers counted both numbers.",
    tip="The station's outdoor hot tub is real, is on the deck, and is the "
        "single most photographed object at any US Antarctic base."),

"brown-station": dict(
    name="Brown Station", slug="Brown_Station", country="Antarctica",
    region="Antarctic Peninsula", type="history", tag="quirky",
    emoji="🔥", sounds=["ocean-waves.mp3"],
    search_name="Almirante Brown Station Antarctica",
    highlights=[("Paradise Harbour", "Paradise_Harbour"),
                ("Skontorp Cove", None),
                ("Argentine Antarctica", None)],
    blurb="Argentina's summer base at the head of Paradise Harbour, orange "
          "huts on a rock shelf with a hill behind it that everyone climbs. "
          "It is the prettiest station on the Peninsula and the reason it "
          "is only a summer base is the best story in Antarctic medicine.",
    fact="In April 1984 the station doctor was told he would be wintering a "
         "second year. He burned the base down. Everyone survived, the US "
         "ship *Hero* took them all off, and Brown has never been rebuilt "
         "as a year-round station since.",
    tip="Climb the hill behind the huts. The view down into Skontorp Cove — "
        "ship, ice, and the whole bowl of Paradise — is the postcard the "
        "Peninsula sells itself with."),

"wilhelmina-bay": dict(
    name="Wilhelmina Bay", slug="Wilhelmina_Bay", country="Antarctica",
    region="Antarctic Peninsula", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    search_name="Wilhelmina Bay Antarctica whales",
    highlights=[("Enterprise Island", None),
                ("Guvernøren wreck", None),
                ("Gerlache Strait", "Gerlache_Strait")],
    blurb="Twenty-four kilometres of bay off the Gerlache Strait that "
          "krill swarm into every autumn, and humpbacks follow. Late in the "
          "season the water can hold hundreds of feeding whales at once, "
          "which is why everyone who has been calls it Whale-mina Bay.",
    fact="A 2009 survey counted 306 humpbacks in this one bay — a density "
         "of feeding whales that had not been recorded anywhere on Earth "
         "since industrial whaling stopped.",
    tip="The half-sunk whaling factory ship *Guvernøren* is beached at "
        "Enterprise Island in the same bay: she caught fire in 1915 and her "
        "captain ran her aground so the crew could save the oil."),

"anvers-island": dict(
    name="Anvers Island", slug="Anvers_Island", country="Antarctica",
    region="Antarctic Peninsula", type="island", tag="hidden",
    emoji="🗻", sounds=["antarctic-wind.mp3"],
    search_name="Anvers Island Antarctica",
    highlights=[("Mount Français", "Mount_Français"),
                ("Neumayer Channel", "Neumayer_Channel"),
                ("Palmer Station", "Palmer_Station"),
                ("Marr Ice Piedmont", None)],
    blurb="The biggest island in the Palmer Archipelago, 2,760 m high and "
          "almost entirely under ice, with the Neumayer Channel cut clean "
          "along its eastern side. Both Palmer Station and Port Lockroy sit "
          "in its shadow.",
    fact="Mount Français was not climbed until 1955, and the second ascent "
         "did not happen for another fifty years — closer to a big Alaskan "
         "peak than to anything on the tourist track below it.",
    tip="The Neumayer Channel between Anvers and Wiencke is the calmest "
        "water on the Peninsula on a still morning, and the standard "
        "approach to Port Lockroy."),

# ===================== TRINITY PENINSULA & THE WEDDELL SIDE =====================

"esperanza-base": dict(
    name="Esperanza Base", slug="Esperanza_Base", country="Antarctica",
    region="Antarctic Peninsula", type="village", tag="famous",
    emoji="👶", sounds=["antarctic-wind.mp3"],
    search_name="Esperanza Base Antarctica",
    highlights=[("Hope Bay", "Hope_Bay"),
                ("LRA36", "LRA36_Radio_Nacional_Arcángel_San_Gabriel"),
                ("Trinity Peninsula", "Trinity_Peninsula"),
                ("Adélie colony", None)],
    blurb="Argentina's year-round base at Hope Bay, and as close to a town "
          "as the continent gets: about 55 people over winter including "
          "whole families, a school, a chapel, a cemetery and a radio "
          "station. Forty-three orange buildings on a beach of volcanic rock.",
    fact="Emilio Palma was born here on 7 January 1978 — the first person "
         "ever born on the continent. Argentina flew his mother down at "
         "seven months pregnant, and eight more children followed. Sovereignty "
         "arguments have been made with stranger instruments.",
    tip="LRA36, the base's own shortwave station, has been broadcasting from "
        "this beach since 1979 and is the southernmost radio station on "
        "Earth. Amateur listeners worldwide still hunt its signal on 15476 kHz."),

"marambio-base": dict(
    name="Marambio Base", slug="Marambio_Base", country="Antarctica",
    region="Antarctic Peninsula", type="history", tag="hidden",
    emoji="🛬", sounds=["antarctic-wind.mp3"],
    search_name="Marambio Base Antarctica",
    highlights=[("Seymour Island", "Seymour_Island"),
                ("Weddell Sea", None),
                ("Antarctic fossil beds", None)],
    blurb="A flat-topped island of frozen gravel on the Weddell side, and "
          "the only place on the Antarctic Peninsula where a wheeled "
          "aircraft can land on bare ground all year. Argentina's air "
          "gateway to the continent, built in 1969 by men who levelled the "
          "runway by hand.",
    fact="Seymour Island is one of the richest fossil sites in Antarctica: "
          "giant penguins nearly two metres tall, marsupials, and the "
          "leaf litter of a temperate rainforest that grew here when the "
          "continent was still attached to South America.",
    tip="The base sits 200 m above the sea ice on a plateau that is scoured "
        "bare by wind — which is exactly why the runway works, and why "
        "there is nothing whatsoever to shelter behind."),

"snow-hill-island": dict(
    name="Snow Hill Island", slug="Snow_Hill_Island", country="Antarctica",
    region="Antarctic Peninsula", type="island", tag="famous",
    emoji="🥚", sounds=["antarctic-wind.mp3"],
    search_name="Snow Hill Island emperor penguins Antarctica",
    highlights=[("Nordenskjöld's hut", None),
                ("Emperor penguin colony", None),
                ("Swedish Antarctic Expedition",
                 "Swedish_Antarctic_Expedition")],
    blurb="An ice-domed island off the Weddell coast holding the most "
          "accessible emperor penguin colony in the world — about 4,000 "
          "pairs raising chicks on the fast ice — and, on a gravel spur, "
          "the wooden hut a Swedish expedition survived two unplanned "
          "winters in.",
    fact="The colony is normally reached by helicopter from an icebreaker "
         "because the fast ice is too broken to walk and too solid to sail: "
         "in many years the ice simply never sets right and nobody gets "
         "there at all.",
    tip="Otto Nordenskjöld's 1902 hut is still standing and still furnished. "
        "His ship was crushed, his relief party wintered in a stone shelter "
        "eating penguin, and all three groups met by chance on the same "
        "beach the following spring."),

"paulet-island": dict(
    name="Paulet Island", slug="Paulet_Island", country="Antarctica",
    region="Antarctic Peninsula", type="island", tag="hidden",
    emoji="🐧", sounds=["ocean-waves.mp3"],
    search_name="Paulet Island Antarctica",
    highlights=[("Stone hut of the Antarctic", None),
                ("Adélie colony", None),
                ("Antarctic Sound", "Antarctic_Sound")],
    blurb="A circular volcanic island a mile and a half across with roughly "
          "100,000 pairs of Adélie penguins on it — one of the largest "
          "colonies anywhere — and a low ring of stones at the north end "
          "that twenty shipwrecked Swedes built and lived in for a winter.",
    fact="When the *Antarctic* was crushed in the Weddell ice in 1903 her "
         "crew hauled to this island and survived on 1,100 penguins and "
         "seal blubber. Only one man died. The hut's walls are still there, "
         "and the penguins nest inside them.",
    tip="The island still has a warm crater lake behind the colony — Paulet "
        "is a young volcano, and the geothermal ground is part of why the "
        "penguins picked it."),

"brown-bluff": dict(
    name="Brown Bluff", slug="Brown_Bluff", country="Antarctica",
    region="Antarctic Peninsula", type="mountain", tag="hidden",
    emoji="🧱", sounds=["ocean-waves.mp3"],
    search_name="Brown Bluff Antarctica",
    highlights=[("Antarctic Sound", "Antarctic_Sound"),
                ("Tabarin Peninsula", "Tabarin_Peninsula"),
                ("Adélie colony", None)],
    blurb="A 745-metre wall of rust-red rock rising straight off a black "
          "cobble beach on the Antarctic Sound, with Adélies and gentoos "
          "nesting at the foot of it. One of the easiest landings on the "
          "actual continent, and the reddest thing for a thousand miles.",
    fact="Brown Bluff is a tuya — a volcano that erupted underneath a "
          "glacier about a million years ago and froze into a flat-topped "
          "island of its own meltwater cave. The colour is oxidised iron in "
          "the lava.",
    tip="The scree at the base is loose palagonite that crunches like burnt "
        "toast, and the whole cliff sheds it constantly — which is why the "
        "landing beach is one colour and everything above it another."),

"antarctic-sound": dict(
    name="Antarctic Sound", slug="Antarctic_Sound", country="Antarctica",
    region="Antarctic Peninsula", type="coastal", tag="hidden",
    emoji="🧊", sounds=["ocean-waves.mp3"],
    search_name="Antarctic Sound iceberg alley",
    highlights=[("Joinville Island", "Joinville_Island"),
                ("Hope Bay", "Hope_Bay"),
                ("Rosamel Island", None),
                ("Tabarin Peninsula", "Tabarin_Peninsula")],
    blurb="The 48-kilometre strait between the tip of the Peninsula and "
          "Joinville Island, and the drain the Weddell Sea empties its "
          "icebergs through. Tabular bergs the size of small towns queue up "
          "in it — flat-topped, sheer-sided, and grounded until they melt "
          "enough to move on.",
    fact="It is named for the ship it destroyed. The *Antarctic* was "
          "crushed here in 1903 and the sound has been called Iceberg Alley "
          "by everyone who has sailed it since.",
    tip="Tabular bergs come off the ice shelves hundreds of kilometres "
        "south, so the ice you are looking at fell as snow before the "
        "pyramids were built and has been travelling ever since."),
}

# ===================== SOUTH SHETLAND ISLANDS =====================
# Sixty miles off the Peninsula, the first land ever sighted south of the
# Convergence, and the most crowded real estate on the continent: nine
# countries keep bases on King George Island alone.

NEW.update({

"deception-island": dict(
    name="Deception Island", slug="Deception_Island", country="Antarctica",
    region="South Shetland Islands", type="island", tag="famous",
    emoji="🌋", sounds=["ocean-waves.mp3"],
    search_name="Deception Island Antarctica",
    highlights=[("Port Foster", "Port_Foster"),
                ("Neptunes Bellows", "Neptunes_Bellows"),
                ("Whalers Bay", None),
                ("Hektor Whaling Station", None),
                ("Telefon Bay", None),
                ("Baily Head", None)],
    blurb="An active volcano whose crater wall has collapsed on one side, "
          "so ships sail through a 230-metre gap called Neptune's Bellows "
          "into the flooded caldera and anchor inside the mountain. The "
          "beach steams. The sea, in places, is warm.",
    fact="The 1967 and 1969 eruptions destroyed the Chilean and British "
         "bases and buried the Norwegian whaling station in mud and ash. "
         "Two stations, Spanish and Argentine, operate here again anyway, "
         "with an evacuation plan and a seismometer.",
    tip="On the black sand at Whalers Bay, inside the caldera, the first "
        "powered flight in Antarctica took off in 1928 — and a hollow dug "
        "at the tideline still fills with water warm enough to sit in, a "
        "step away from a freezing sea."),

"half-moon-island": dict(
    name="Half Moon Island", slug="Half_Moon_Island", country="Antarctica",
    region="South Shetland Islands", type="island", tag="hidden",
    emoji="🌙", sounds=["ocean-waves.mp3"],
    search_name="Half Moon Island Antarctica",
    highlights=[("Cámara Base", "Cámara_Base"),
                ("Livingston Island", "Livingston_Island"),
                ("Chinstrap colony", None)],
    blurb="A two-kilometre crescent of rock curled into McFarlane Strait, "
          "with chinstrap penguins on the outcrops, Weddell seals in the "
          "bay, and the Tangra Mountains of Livingston Island filling the "
          "whole horizon behind it in glacier white.",
    fact="A wooden boat, upside down and half-buried, has sat on the "
         "isthmus for so long that nobody is sure whose it was; it appears "
         "in photographs from the 1950s already derelict.",
    tip="This is often the first landing of a whole voyage, which means it "
        "is where people learn how long the boot-washing, vacuuming and "
        "biosecurity routine actually takes. Budget an hour before you land."),

"king-george-island": dict(
    name="King George Island", slug="King_George_Island_(South_Shetland_Islands)",
    country="Antarctica", region="South Shetland Islands", type="island",
    tag="famous", emoji="🛩️", sounds=["antarctic-wind.mp3"],
    search_name="King George Island Antarctica",
    highlights=[("Maxwell Bay", None),
                ("Admiralty Bay", "Admiralty_Bay_(South_Shetland_Islands)"),
                ("Teniente R. Marsh Airport", None),
                ("Fildes Peninsula", "Fildes_Peninsula")],
    blurb="The busiest island in Antarctica: a gravel airstrip, a village "
          "with a school and a bank, and bases belonging to Chile, Russia, "
          "China, South Korea, Poland, Uruguay, Brazil, Argentina and Peru "
          "— several of them within walking distance of each other.",
    fact="Most 'fly-and-cruise' Antarctic trips start here, swapping the "
         "two-day Drake crossing for a two-hour flight from Punta Arenas. "
         "The runway is bare gravel and the weather turns it into a coin "
         "flip; being stuck for days is a normal outcome, not a disaster.",
    tip="Ninety-five percent of the island is under ice. Everything human "
        "is crammed onto the few ice-free peninsulas, which is also where "
        "every mosses-and-lichen ecologist wants to work — the collision "
        "is a permanent argument at Treaty meetings."),

"villa-las-estrellas": dict(
    name="Villa Las Estrellas", slug="Villa_Las_Estrellas", country="Antarctica",
    region="South Shetland Islands", type="village", tag="quirky",
    emoji="🏫", sounds=["antarctic-wind.mp3"],
    search_name="Villa Las Estrellas Antarctica",
    highlights=[("Frei Montalva Station", "Base_Presidente_Eduardo_Frei_Montalva"),
                ("Escuela F-50", None),
                ("Fildes Peninsula", "Fildes_Peninsula"),
                ("The post office", None)],
    blurb="A Chilean civilian settlement on King George Island: about "
          "eighty people in winter, a school, a post office, a bank branch, "
          "a gym, a chapel and a hostel, arranged along a gravel street "
          "with a satellite dish at the end of it.",
    fact="Everyone who overwinters must have their appendix removed first. "
         "There is no surgeon and no reliable way out in winter, so the "
         "appendix goes before you do — a rule several Antarctic programmes "
         "have used at one time or another.",
    tip="Escuela F-50 is one of only two schools on the continent (the "
        "other is at Esperanza). Class sizes run to single digits and the "
        "teacher is posted for a year with the families."),

"bellingshausen-station": dict(
    name="Bellingshausen Station", slug="Bellingshausen_Station",
    country="Antarctica", region="South Shetland Islands", type="history",
    tag="quirky", emoji="⛪", sounds=["antarctic-wind.mp3"],
    search_name="Bellingshausen Station Antarctica",
    highlights=[("Trinity Church", "Trinity_Church,_Antarctica"),
                ("Fildes Peninsula", "Fildes_Peninsula"),
                ("Ardley Island", "Ardley_Island")],
    blurb="Russia's base on the Fildes Peninsula, next door to Chile's, "
          "with a Russian Orthodox church on the hill above it — built of "
          "Siberian pine, assembled in Altai, taken apart, shipped south "
          "and put back together in 2004.",
    fact="Trinity Church is the southernmost Eastern Orthodox church on "
         "Earth and is permanently staffed by a priest who rotates yearly "
         "from a monastery near Moscow. At least one wedding has been held "
         "in it.",
    tip="The base is a fifteen-minute walk from the Chilean airstrip and "
        "roughly forty minutes from the Chinese and Uruguayan stations. "
        "Nowhere else in Antarctica can you walk between four countries."),

"king-sejong-station": dict(
    name="King Sejong Station", slug="King_Sejong_Station", country="Antarctica",
    region="South Shetland Islands", type="history", tag="hidden",
    emoji="🇰🇷", sounds=["antarctic-wind.mp3"],
    search_name="King Sejong Station Antarctica",
    highlights=[("Barton Peninsula", "Barton_Peninsula"),
                ("Marian Cove", None),
                ("Maxwell Bay", None)],
    blurb="South Korea's first Antarctic base, opened in 1988 on the Barton "
          "Peninsula of King George Island, with a chinstrap and gentoo "
          "colony a short walk away and a retreating glacier front across "
          "Marian Cove that has been measured every year since.",
    fact="Marian Cove's glacier has pulled back roughly 1.8 km since the "
         "station was built, opening water that did not exist in 1988. The "
         "seafloor exposed behind it is now one of the best natural "
         "laboratories anywhere for watching an ecosystem colonise from zero.",
    tip="Korea's second base, Jang Bogo, is on the far side of the "
        "continent in Terra Nova Bay — the two are 4,500 km apart and "
        "supplied by entirely different routes."),

"great-wall-station": dict(
    name="Great Wall Station", slug="Great_Wall_Station_(Antarctica)",
    country="Antarctica", region="South Shetland Islands", type="history",
    tag="hidden", emoji="🇨🇳", sounds=["antarctic-wind.mp3"],
    search_name="Great Wall Station Antarctica",
    highlights=[("Fildes Peninsula", "Fildes_Peninsula"),
                ("Great Wall Bay", None),
                ("Yanou Lake", None)],
    blurb="China's first Antarctic station, built on the Fildes Peninsula "
          "in a single summer in 1985 by a team that arrived with no prior "
          "polar construction experience and finished the main hut in 45 days.",
    fact="Building it got China upgraded from acceding party to full "
         "Consultative Party status under the Antarctic Treaty within nine "
         "months — a base is, in Treaty terms, a vote.",
    tip="China now runs five Antarctic stations. Great Wall is the only one "
        "you can reach without an icebreaker, which is why it doubles as "
        "the training base for everyone heading further south."),

"arctowski-station": dict(
    name="Henryk Arctowski Polish Antarctic Station",
    slug="Henryk_Arctowski_Polish_Antarctic_Station", country="Antarctica",
    region="South Shetland Islands", type="history", tag="hidden",
    emoji="🇵🇱", sounds=["ocean-waves.mp3"],
    search_name="Arctowski Station Antarctica",
    highlights=[("Admiralty Bay", "Admiralty_Bay_(South_Shetland_Islands)"),
                ("Point Thomas", None),
                ("Elephant seal wallow", None)],
    blurb="Poland's year-round station on Admiralty Bay, running "
          "continuously since 1977 and holding one of the longest unbroken "
          "ecological datasets in Antarctica: the same penguin colonies, "
          "counted the same way, for nearly fifty years.",
    fact="It is named for Henryk Arctowski, who sailed on the *Belgica* in "
         "1897 — the first expedition ever to winter in the Antarctic, "
         "trapped in the ice for thirteen months with a young Roald "
         "Amundsen as second mate.",
    tip="Admiralty Bay is an Antarctic Specially Managed Area — one of the "
        "few places where Poland, Brazil, Peru, Ecuador and the US all "
        "agreed to jointly manage a single bay rather than carve it up."),

"elephant-island": dict(
    name="Elephant Island", slug="Elephant_Island", country="Antarctica",
    region="South Shetland Islands", type="island", tag="famous",
    emoji="⛺", sounds=["ocean-waves.mp3"],
    search_name="Elephant Island Antarctica",
    highlights=[("Point Wild", "Point_Wild"),
                ("Cape Valentine", None),
                ("Pardo bust", None),
                ("Chinstrap colony", None)],
    blurb="A bleak, unvisitable lump of rock and glacier at the outer edge "
          "of the South Shetlands, notable for one spit of shingle where "
          "twenty-two men lived under two upturned boats for four and a "
          "half months in 1916 and every single one of them came home.",
    fact="Shackleton left them there on 24 April 1916 and reached them "
         "again on 30 August after four failed relief attempts, aboard the "
         "Chilean tug *Yelcho* under Luis Pardo. He counted them from the "
         "boat before he landed. Twenty-two.",
    tip="Landing at Point Wild is nearly impossible — the beach is a few "
        "metres wide, the swell is constant, and most ships can only stand "
        "off and look at Pardo's bust through binoculars."),

# ===================== SOUTH ORKNEY ISLANDS =====================

"orcadas-base": dict(
    name="Orcadas Base", slug="Orcadas_Base", country="Antarctica",
    region="South Orkney Islands", type="history", tag="famous",
    emoji="📅", sounds=["antarctic-wind.mp3"],
    search_name="Orcadas Base Antarctica",
    highlights=[("Laurie Island", "Laurie_Island"),
                ("Scotia Bay", None),
                ("Uruguay Cove", None),
                ("The 1903 magnetic hut", None)],
    blurb="The oldest permanently occupied station in Antarctica, on "
          "Laurie Island in the South Orkneys, staffed without a single "
          "break since 1904 — longer than any other human settlement south "
          "of the Convergence, by seventy years.",
    fact="The weather record from Orcadas is the longest continuous "
         "instrumental series in Antarctica: the same observations, from "
         "the same spot, every day since William Speirs Bruce's Scottish "
         "expedition handed the hut to Argentina in 1904.",
    tip="Bruce sold the base to Argentina for a nominal sum after Britain "
        "declined to fund it. The consequences for the region's sovereignty "
        "arguments have run for a century and are not finished."),

"signy-island": dict(
    name="Signy Island", slug="Signy_Island", country="Antarctica",
    region="South Orkney Islands", type="island", tag="hidden",
    emoji="🦠", sounds=["antarctic-wind.mp3"],
    search_name="Signy Island Antarctica",
    highlights=[("Signy Research Station", None),
                ("Borge Bay", None),
                ("Moss banks", None),
                ("Fur seal beaches", None)],
    blurb="A six-by-five-kilometre island in the South Orkneys that Britain "
          "has used as a biological laboratory since 1947 — small enough to "
          "walk across, varied enough to hold lakes, moss banks, penguins "
          "and one of the fastest-growing fur seal populations on record.",
    fact="Signy's fur seals went from a few dozen animals in the 1950s to "
         "more than 20,000 in summer by the 1990s, and they have trampled "
         "moss banks that took a thousand years to grow. Recovery from "
         "sealing turned out to have a bill attached.",
    tip="The island's moss banks are up to three metres deep and are dated "
        "like peat cores. The bottom of one bank at Signy started growing "
        "before the Norman Conquest."),
})

# ===================== ROSS SEA & VICTORIA LAND =====================
# The other doorway. Everything that went to the Pole before 1958 left
# from this coast, and the huts they left behind are still furnished.

NEW.update({

"mcmurdo-station": dict(
    name="McMurdo Station", slug="McMurdo_Station", country="Antarctica",
    region="Ross Sea", type="village", tag="famous",
    emoji="🏗️", sounds=["antarctic-wind.mp3"],
    search_name="McMurdo Station Antarctica",
    highlights=[("Ross Island", "Ross_Island"),
                ("Hut Point", "Hut_Point_Peninsula"),
                ("Observation Hill", None),
                ("Ice Pier", None),
                ("Crary Lab", None)],
    blurb="The largest settlement on the continent: up to 1,000 people in "
          "summer, on the bare volcanic dirt of Ross Island. It looks like "
          "an Alaskan mining town — steel sheds, fuel tanks, gravel roads, "
          "shipping containers — because that is essentially what it is.",
    fact="Everything the US does in Antarctica moves through here, "
         "including the fuel for the South Pole. From 1962 to 1972 the "
         "station ran on a portable nuclear reactor, PM-3A, nicknamed "
         "'Nukey Poo'; it leaked, was shut down, and 101 drums of "
         "contaminated rock were shipped back to California.",
    tip="Three bars, a coffee house, a chapel, a bowling alley for decades, "
        "and an annual outdoor music festival called IceStock. The "
        "community is real, and so is the shortage of anywhere to be alone."),

"scott-base": dict(
    name="Scott Base", slug="Scott_Base", country="Antarctica",
    region="Ross Sea", type="history", tag="hidden",
    emoji="💚", sounds=["antarctic-wind.mp3"],
    search_name="Scott Base Antarctica",
    highlights=[("Pram Point", None),
                ("Hillary's TAE hut", None),
                ("Ross Ice Shelf", "Ross_Ice_Shelf"),
                ("Pressure ridges", None)],
    blurb="New Zealand's base, three kilometres over the hill from McMurdo, "
          "painted a single shade of green — 'Chelsea cucumber' — since the "
          "1980s. Built by Edmund Hillary in 1957 as the launch point for "
          "his tractor run to the Pole.",
    fact="Hillary was supposed to lay depots and stop. He kept going and "
         "reached the South Pole on 4 January 1958 on three Massey Ferguson "
         "farm tractors, beating the expedition he was supporting there and "
         "causing a diplomatic incident that lasted longer than the trip.",
    tip="The pressure ridges below the base — where the Ross Ice Shelf "
        "grinds against Ross Island and buckles into blue walls — are "
        "walkable on a guided route, and Weddell seals haul out in them."),

"mount-erebus": dict(
    name="Mount Erebus", slug="Mount_Erebus", country="Antarctica",
    region="Ross Sea", type="mountain", tag="famous",
    emoji="🌋", sounds=["antarctic-wind.mp3"],
    search_name="Mount Erebus Antarctica",
    highlights=[("Ross Island", "Ross_Island"),
                ("The lava lake", None),
                ("Ice fumaroles", None),
                ("Erebus Glacier Tongue", "Erebus_Glacier_Tongue")],
    blurb="A 3,794-metre volcano with a permanent lava lake in its summit "
          "crater — one of very few on Earth — sitting on an island of ice, "
          "throwing bombs of molten rock onto snow. It has been erupting "
          "continuously since at least 1972.",
    fact="Escaping steam freezes as it hits the air and builds hollow ice "
         "chimneys up to ten metres tall on the volcano's flanks. Inside "
         "them, warm and dark and cut off from everything, live microbial "
         "communities found nowhere else.",
    tip="The name came off the ships: James Clark Ross sailed *Erebus* and "
        "*Terror* into this sea in 1841 and gave both peaks their names. "
        "Both ships later vanished with Franklin in the Arctic."),

"discovery-hut": dict(
    name="Discovery Hut", slug="Discovery_Hut", country="Antarctica",
    region="Ross Sea", type="history", tag="famous",
    emoji="🪵", sounds=["antarctic-wind.mp3"],
    search_name="Discovery Hut Hut Point Antarctica",
    highlights=[("Hut Point", "Hut_Point_Peninsula"),
                ("Seal blubber stove", None),
                ("Discovery Expedition", "Discovery_Expedition")],
    blurb="Scott's first hut, prefabricated in Australia and put up at Hut "
          "Point in 1902 — an outback design with a verandah, hopeless in "
          "the cold, which is why his men mostly slept on the ship and used "
          "it as a store.",
    fact="It stands 300 metres from McMurdo's edge, so the busiest place in "
         "Antarctica and its oldest building share a shoreline. The hut "
         "still smells of seal blubber smoke from Shackleton's Ross Sea "
         "party, who sheltered here in 1915 and blackened the ceiling.",
    tip="Entry is by permit with a guide, and numbers inside are capped at "
        "a handful of people at a time. The New Zealand Antarctic Heritage "
        "Trust conserves it object by object, down to the biscuit crumbs."),

"cape-evans": dict(
    name="Cape Evans", slug="Cape_Evans", country="Antarctica",
    region="Ross Sea", type="history", tag="famous",
    emoji="🕯️", sounds=["antarctic-wind.mp3"],
    search_name="Cape Evans hut Antarctica",
    highlights=[("Terra Nova Hut", None),
                ("Ponting's darkroom", None),
                ("Wind Vane Hill", None),
                ("Barne Glacier", None)],
    blurb="Scott's *Terra Nova* hut, built in 1911 and still standing with "
          "everything in it: bunks, boots, a bicycle, Ponting's darkroom, "
          "seal blubber in the galley, and 8,000 objects catalogued where "
          "the men left them when they walked out.",
    fact="Three crates of whisky were found under the floorboards in 2010 — "
         "Mackinlay's, bottled 1898, still liquid at −30 °C. A distillery "
         "flew samples to Scotland, reverse-engineered the recipe, and put "
         "the blend back on sale.",
    tip="The stables at the end are the coldest part of the building "
        "because the ponies' heat is gone; the men's quarters, packed with "
        "reindeer-skin bags, still feel measurably different to walk into."),

"cape-royds": dict(
    name="Cape Royds", slug="Cape_Royds", country="Antarctica",
    region="Ross Sea", type="history", tag="hidden",
    emoji="🥫", sounds=["antarctic-wind.mp3"],
    search_name="Cape Royds Shackleton hut Antarctica",
    highlights=[("Nimrod Hut", None),
                ("Adélie colony", None),
                ("Pony stables", None),
                ("Backdoor Bay", None)],
    blurb="Shackleton's 1908 *Nimrod* hut, smaller and tidier than Scott's, "
          "with the southernmost Adélie penguin colony in the world nesting "
          "a few hundred metres away — about 2,000 pairs at the very edge "
          "of where the species can breed at all.",
    fact="Fifteen men lived in a single room 10 by 5.8 metres for a year, "
         "partitioned with packing crates. From here Shackleton walked to "
         "within 180 km of the Pole and turned back, which is why his men "
         "came home and Scott's did not.",
    tip="The colony is monitored every season and has swung between 1,000 "
        "and 4,000 pairs depending on how far the fast ice pushes the "
        "adults' walk to open water. Some years it is a short commute; "
        "some years it is fifty kilometres each way."),

"cape-crozier": dict(
    name="Cape Crozier", slug="Cape_Crozier", country="Antarctica",
    region="Ross Sea", type="nature", tag="hidden",
    emoji="🥚", sounds=["antarctic-wind.mp3"],
    search_name="Cape Crozier Antarctica emperor penguins",
    highlights=[("Emperor penguin colony", None),
                ("The stone igloo", None),
                ("Ross Ice Shelf edge", "Ross_Ice_Shelf"),
                ("Adélie colony", None)],
    blurb="The eastern end of Ross Island, where the Ross Ice Shelf runs "
          "into the land, holding both an emperor colony on the sea ice "
          "below and a quarter of a million Adélies above — and the ruined "
          "stone hut of the worst journey in the world.",
    fact="In midwinter 1911 three of Scott's men sledged here in the dark "
         "at −60 °C for five weeks to collect three emperor eggs, believing "
         "the embryos would prove birds descended from reptiles. The theory "
         "was wrong. The eggs are in the Natural History Museum.",
    tip="Apsley Cherry-Garrard wrote the account afterwards and gave it the "
        "title everyone remembers. His teeth shattered from chattering; his "
        "sleeping bag froze solid enough to take twenty minutes to enter."),

"ross-ice-shelf": dict(
    name="Ross Ice Shelf", slug="Ross_Ice_Shelf", country="Antarctica",
    region="Ross Sea", type="nature", tag="famous",
    emoji="🧊", sounds=["antarctic-wind.mp3"],
    search_name="Ross Ice Shelf Antarctica",
    highlights=[("The Barrier", None),
                ("Bay of Whales", "Bay_of_Whales"),
                ("Roosevelt Island", "Roosevelt_Island,_Antarctica"),
                ("Ice front", None)],
    blurb="A floating slab of ice the size of France, several hundred "
          "metres thick, ending in a cliff up to 50 m high and 600 km long. "
          "Ross found it in 1841, called it the Barrier because that is "
          "what it was, and sailed 400 km along it without finding a way in.",
    fact="Everything that walked to the Pole crossed this shelf, and it is "
         "moving underneath them the whole way — about 1.5 to 3 metres a "
         "day toward the sea. It is also floating, so all of it is already "
         "displacing its own water and its melting adds no sea level at all.",
    tip="Beneath the shelf, 800 m down and hundreds of kilometres from open "
        "water, drills have found fish and amphipods living in total "
        "darkness on whatever drifts in from the edge."),

"mcmurdo-dry-valleys": dict(
    name="McMurdo Dry Valleys", slug="McMurdo_Dry_Valleys", country="Antarctica",
    region="Ross Sea", type="nature", tag="famous",
    emoji="🏜️", sounds=["antarctic-wind.mp3"],
    search_name="McMurdo Dry Valleys Antarctica",
    highlights=[("Taylor Valley", "Taylor_Valley"),
                ("Wright Valley", "Wright_Valley"),
                ("Lake Vanda", "Lake_Vanda"),
                ("Lake Bonney", None),
                ("Onyx River", "Onyx_River")],
    blurb="4,800 square kilometres of bare gravel where it has not rained "
          "meaningfully in two million years. Katabatic winds pour off the "
          "plateau at up to 320 km/h and evaporate the ice before it can "
          "settle, leaving the largest ice-free area on the continent.",
    fact="NASA tested Viking's Mars instruments here because it is the "
         "closest analogue on Earth. Mummified seal carcasses lie in the "
         "valleys hundreds of years old and dozens of kilometres from the "
         "sea, freeze-dried rather than rotted.",
    tip="Nothing organic may be left behind — everything, human waste "
        "included, flies out. It is the strictest waste regime anywhere in "
        "Antarctica, because there is no process here that would break it down."),

"blood-falls": dict(
    name="Blood Falls", slug="Blood_Falls", country="Antarctica",
    region="Ross Sea", type="nature", tag="famous",
    emoji="🩸", sounds=["antarctic-wind.mp3"],
    search_name="Blood Falls Antarctica",
    highlights=[("Taylor Glacier", "Taylor_Glacier"),
                ("Lake Bonney", None),
                ("Subglacial brine", None)],
    blurb="A rust-red waterfall bleeding out of the snout of Taylor Glacier "
          "onto the ice of Lake Bonney. For a century nobody knew why; the "
          "first guess was red algae. It is iron, oxidising the instant it "
          "meets air after two million years without any.",
    fact="The source is a lake of brine sealed under 400 m of ice, three "
         "times saltier than seawater and therefore liquid at −5 °C. It "
         "holds a microbial community that has been cut off from sunlight "
         "and oxygen for something like 1.5 million years and lives on iron "
         "and sulphur.",
    tip="It is one of the most-cited arguments that life could survive "
        "under the ice of Europa or Enceladus — a closed, cold, dark, salty "
        "system that has demonstrably not gone sterile."),

"don-juan-pond": dict(
    name="Don Juan Pond", slug="Don_Juan_Pond", country="Antarctica",
    region="Ross Sea", type="nature", tag="quirky",
    emoji="🧂", sounds=["antarctic-wind.mp3"],
    search_name="Don Juan Pond Antarctica",
    highlights=[("Wright Valley", "Wright_Valley"),
                ("Antarcticite", None),
                ("Dais", None)],
    blurb="A puddle ten centimetres deep in the Wright Valley that is the "
          "saltiest body of water on Earth — over 40% calcium chloride, "
          "roughly eighteen times seawater — and therefore stays liquid "
          "down to about −50 °C.",
    fact="It is the only place on the planet where the mineral "
         "antarcticite forms naturally. The pond is so hostile that even "
         "here, in a continent full of extremophiles, it is argued over "
         "whether anything actually lives in it.",
    tip="It was named in 1961 after the two helicopter pilots who first "
        "reached it, Lieutenants Don Roe and John Hickey — Don and Juan, "
        "which is a better story than the Spanish one everyone assumes."),

"onyx-river": dict(
    name="Onyx River", slug="Onyx_River", country="Antarctica",
    region="Ross Sea", type="nature", tag="quirky",
    emoji="🏞️", sounds=["antarctic-wind.mp3"],
    search_name="Onyx River Antarctica",
    highlights=[("Wright Valley", "Wright_Valley"),
                ("Lake Vanda", "Lake_Vanda"),
                ("Wright Lower Glacier", None)],
    blurb="The longest river in Antarctica: 32 kilometres of meltwater "
          "running through the Wright Valley for a few weeks each summer — "
          "and running inland, away from the sea, to end in Lake Vanda "
          "with no outlet at all.",
    fact="It has been gauged every summer since 1969, one of the longest "
         "hydrological records in the polar regions. Some years it does not "
         "flow. In 2001–02 it ran hard enough to raise Lake Vanda by more "
         "than a metre.",
    tip="There are no fish in it. There is nothing in it but algal mats and "
        "microscopic invertebrates — and the mats, dried and blown around "
        "the valley, are most of the region's soil carbon."),

"cape-adare": dict(
    name="Cape Adare", slug="Cape_Adare", country="Antarctica",
    region="Ross Sea", type="history", tag="hidden",
    emoji="🚩", sounds=["ocean-waves.mp3"],
    search_name="Cape Adare Antarctica",
    highlights=[("Borchgrevink's huts", None),
                ("Ridley Beach", None),
                ("Adélie colony", None),
                ("Hanson's grave", None)],
    blurb="A triangular beach at the northern tip of Victoria Land holding "
          "the first buildings ever erected on the Antarctic continent — "
          "Carsten Borchgrevink's two huts of 1899 — and about half a "
          "million Adélie penguins.",
    fact="Ten men wintered here in 1899, the first people ever to spend a "
         "winter on the continent. One of them, the zoologist Nicolai "
         "Hanson, died in October and is buried on the ridge above: the "
         "first grave in Antarctica.",
    tip="The huts are half-buried in guano and were nearly lost; a "
        "conservation team dug them out and rebuilt the roofs in 2016–22. "
        "The swell at Ridley Beach still turns most attempted landings back."),

"zucchelli-station": dict(
    name="Zucchelli Station", slug="Zucchelli_Station", country="Antarctica",
    region="Ross Sea", type="history", tag="hidden",
    emoji="🇮🇹", sounds=["antarctic-wind.mp3"],
    search_name="Mario Zucchelli Station Antarctica",
    highlights=[("Terra Nova Bay", "Terra_Nova_Bay"),
                ("Northern Foothills", None),
                ("Ice runway", None)],
    blurb="Italy's summer station on Terra Nova Bay in Victoria Land, a "
          "cluster of steel modules on bare rock beside a polynya that "
          "stays open all winter and is one of the main places Antarctic "
          "Bottom Water is made.",
    fact="A polynya is a patch of sea that refuses to freeze because "
         "katabatic wind keeps shoving the new ice away. As it freezes and "
         "is blown off, it dumps salt into the water below, which becomes "
         "the densest water in the world ocean and sinks to the seafloor.",
    tip="Italy and France jointly run Concordia, 1,200 km inland on the "
        "plateau, and most of its traverse convoys start from this bay."),

"jang-bogo-station": dict(
    name="Jang Bogo Station", slug="Jang_Bogo_Station", country="Antarctica",
    region="Ross Sea", type="history", tag="hidden",
    emoji="🇰🇷", sounds=["antarctic-wind.mp3"],
    search_name="Jang Bogo Station Antarctica",
    highlights=[("Terra Nova Bay", "Terra_Nova_Bay"),
                ("Campbell Glacier", None),
                ("Ross Sea", "Ross_Sea")],
    blurb="South Korea's year-round station on Terra Nova Bay, opened in "
          "2014 — a three-armed building raised on stilts so the drift "
          "blows underneath it instead of burying it, and designed to "
          "survive the katabatic wind that comes off the plateau here.",
    fact="The three wings point outward at 120° so that whichever way the "
         "wind arrives, the building presents an edge rather than a wall. "
         "It is a shape borrowed from Halley and Princess Elisabeth and now "
         "close to standard for anything new on this coast.",
    tip="Korea's icebreaker *Araon* supplies both Korean bases and has "
        "spent as much time rescuing other countries' ships in the Ross Sea "
        "as delivering its own cargo."),

"framheim": dict(
    name="Framheim", slug="Framheim", country="Antarctica",
    region="Ross Sea", type="history", tag="hidden",
    emoji="🛷", sounds=["antarctic-wind.mp3"],
    search_name="Framheim Amundsen Bay of Whales",
    highlights=[("Bay of Whales", "Bay_of_Whales"),
                ("Ross Ice Shelf", "Ross_Ice_Shelf"),
                ("Amundsen's South Pole expedition",
                 "Amundsen's_South_Pole_expedition")],
    blurb="Amundsen's base camp, built on the floating ice of the Bay of "
          "Whales in 1911 — a hut buried under snow with tunnels dug out to "
          "workshops, kennels and a sauna, and 97 dogs living in the drifts "
          "around it.",
    fact="Camping on a floating shelf was thought reckless. It also put him "
         "60 miles closer to the Pole than Scott and let him start earlier "
         "in the season. He reached the Pole on 14 December 1911, five "
         "weeks ahead, and lost nobody.",
    tip="The site itself is gone. The Bay of Whales was an indentation in "
        "the moving ice front, and the whole section calved off decades "
        "ago — the hut, the tunnels and the ground they stood on are at sea."),

"beardmore-glacier": dict(
    name="Beardmore Glacier", slug="Beardmore_Glacier", country="Antarctica",
    region="Ross Sea", type="nature", tag="hidden",
    emoji="🧗", sounds=["antarctic-wind.mp3"],
    search_name="Beardmore Glacier Antarctica",
    highlights=[("Transantarctic Mountains", "Transantarctic_Mountains"),
                ("Mount Hope", None),
                ("Gateway", None),
                ("Glossopteris fossils", None)],
    blurb="One of the largest valley glaciers in the world — 200 km long, "
          "40 km wide — and the staircase both Shackleton and Scott climbed "
          "from the Ross Ice Shelf up onto the polar plateau, gaining 3,000 "
          "metres through crevasse fields.",
    fact="Scott's party collected 16 kg of rock on the way back down, "
         "including fossil *Glossopteris* leaves proving Antarctica once "
         "had forests. They hauled the samples to the end and the stones "
         "were found with their bodies.",
    tip="Shackleton found the route in 1908 by climbing Mount Hope and "
        "looking. Every plateau traverse for the next fifty years used the "
        "line he saw from the top."),

"drygalski-ice-tongue": dict(
    name="Drygalski Ice Tongue", slug="Drygalski_Ice_Tongue",
    country="Antarctica", region="Ross Sea", type="nature", tag="hidden",
    emoji="👅", sounds=["antarctic-wind.mp3"],
    search_name="Drygalski Ice Tongue Antarctica",
    highlights=[("David Glacier", "David_Glacier"),
                ("Terra Nova Bay", "Terra_Nova_Bay"),
                ("Victoria Land", "Victoria_Land")],
    blurb="A finger of floating glacier ice sticking 70 km straight out "
          "into the Ross Sea, 24 km wide, fed by the David Glacier pouring "
          "off Victoria Land. It has been there for at least four thousand "
          "years and it does not care what is in the way.",
    fact="In 2005 the iceberg B-15A — itself a fragment of the largest "
         "berg ever recorded — drifted into the end of the tongue and "
         "snapped five kilometres off it. Both objects were visible from "
         "orbit; the collision was watched live by satellite.",
    tip="Ice tongues are what glaciers do when they reach the sea somewhere "
        "too sheltered to break them up. Everywhere else they calve at the "
        "coast; here the ice just keeps going."),

"cape-washington": dict(
    name="Cape Washington", slug="Cape_Washington", country="Antarctica",
    region="Ross Sea", type="nature", tag="hidden",
    emoji="🐧", sounds=["antarctic-wind.mp3"],
    search_name="Cape Washington emperor penguins Antarctica",
    highlights=[("Emperor penguin colony", None),
                ("Terra Nova Bay", "Terra_Nova_Bay"),
                ("Mount Melbourne", "Mount_Melbourne")],
    blurb="A basalt headland on the north side of Terra Nova Bay with one "
          "of the largest emperor penguin colonies in the world on the fast "
          "ice below it — around 20,000 birds, protected from the swell by "
          "the cape itself.",
    fact="Emperors are the only animal that breeds through an Antarctic "
         "winter. The male holds the egg on his feet for 65 days in the "
         "dark at −40 °C without eating, loses nearly half his body weight, "
         "and is still there when the female comes back with food.",
    tip="Most of the classic emperor footage in wildlife documentaries was "
        "shot at this colony or at Atka Bay, because both are reachable "
        "from a base and hold still enough ice for a camera team to camp."),
})

# ===================== QUEEN MAUD LAND & THE WEDDELL COAST =====================
# The Atlantic-facing quarter: Norway's claim on paper, an international
# terrace of bases in practice, and the most improbable granite on Earth
# sticking out of the ice behind them.

NEW.update({

"troll-station": dict(
    name="Troll Station", slug="Troll_(research_station)", country="Antarctica",
    region="Queen Maud Land", type="history", tag="hidden",
    emoji="🇳🇴", sounds=["antarctic-wind.mp3"],
    search_name="Troll Research Station Antarctica",
    highlights=[("Jutulsessen", "Jutulsessen"),
                ("Troll Airfield", "Troll_Airfield"),
                ("Princess Martha Coast", None)],
    blurb="Norway's year-round station in Queen Maud Land, 235 km inland on "
          "a bare rock ridge at 1,275 m, with a blue-ice runway beside it "
          "long enough to take a full-size intercontinental jet straight "
          "from Cape Town.",
    fact="Troll Airfield is one of the few places on the continent where a "
         "wide-body aircraft can land on natural ice. The Dronning Maud "
         "Land Air Network — eleven countries pooling flights — runs "
         "through it, which is why bases from six nations share one runway.",
    tip="Norway upgraded Troll from a summer hut to a year-round base in "
        "2005 and the King and Queen flew down to open it, making it one "
        "of very few Antarctic buildings with a royal ribbon-cutting."),

"neumayer-station": dict(
    name="Neumayer-Station III", slug="Neumayer_Station_III",
    country="Antarctica", region="Queen Maud Land", type="history",
    tag="hidden", emoji="🇩🇪", sounds=["antarctic-wind.mp3"],
    search_name="Neumayer Station III Antarctica",
    highlights=[("Ekström Ice Shelf", "Ekström_Ice_Shelf"),
                ("Atka Bay", "Atka_Iceport"),
                ("Hydraulic legs", None),
                ("Emperor colony", None)],
    blurb="Germany's base on the floating Ekström Ice Shelf, standing on "
          "sixteen hydraulic legs. Snow buries about 80 cm a year, so once "
          "a season the whole 2,300-tonne building is jacked back up above "
          "the drift.",
    fact="Its two predecessors were not raised and were simply crushed. "
         "Neumayer I and II were buried under the accumulating snow and "
         "abandoned; the ice they stood on has since calved into the sea.",
    tip="The emperor penguin colony at Atka Bay is a few kilometres away "
        "and is watched all winter by a remote camera array — some of the "
        "only imagery anywhere of emperors during the polar night."),

"sanae-iv": dict(
    name="SANAE IV", slug="SANAE_IV", country="Antarctica",
    region="Queen Maud Land", type="history", tag="hidden",
    emoji="🇿🇦", sounds=["antarctic-wind.mp3"],
    search_name="SANAE IV Antarctica",
    highlights=[("Vesleskarvet", "Vesleskarvet"),
                ("Ahlmann Ridge", None),
                ("Queen Maud Land", None)],
    blurb="South Africa's station, three linked modules on stilts along the "
          "top of a nunatak called Vesleskarvet, 170 km inland. Nine people "
          "winter here and see nobody else for roughly nine months.",
    fact="Putting it on exposed rock rather than the ice shelf means it "
         "will never need moving, unlike almost every other base on this "
         "coast — a decision taken after three previous SANAE stations were "
         "swallowed by snow.",
    tip="The overwintering team is nine: a doctor, engineers, a couple of "
        "physicists. South Africa's psychological screening for these posts "
        "has been running long enough to be its own body of research."),

"novolazarevskaya-station": dict(
    name="Novolazarevskaya Station", slug="Novolazarevskaya_Station",
    country="Antarctica", region="Queen Maud Land", type="history",
    tag="quirky", emoji="🪒", sounds=["antarctic-wind.mp3"],
    search_name="Novolazarevskaya Station Antarctica",
    highlights=[("Schirmacher Oasis", "Schirmacher_Oasis"),
                ("Novo Airbase", None),
                ("Lake Untersee", "Lake_Untersee")],
    blurb="Russia's base in the Schirmacher Oasis, an ice-free strip of "
          "rock and meltwater lakes behind the Queen Maud coast, and the "
          "hub of the blue-ice Novo Airbase that most non-Russian "
          "expeditions to this sector fly through.",
    fact="In 1961 the station doctor, Leonid Rogozov, developed "
         "appendicitis with no way out and no other surgeon. He operated on "
         "himself with local anaesthetic, a mirror and two untrained "
         "assistants, and was back at work in two weeks.",
    tip="Lake Untersee, 90 km away, is a permanently ice-covered lake with "
        "some of the most alkaline water on Earth and modern microbial "
        "structures that look like fossils from three billion years ago."),

"maitri-station": dict(
    name="Maitri", slug="Maitri_(research_station)", country="Antarctica",
    region="Queen Maud Land", type="history", tag="hidden",
    emoji="🇮🇳", sounds=["antarctic-wind.mp3"],
    search_name="Maitri Station Antarctica",
    highlights=[("Schirmacher Oasis", "Schirmacher_Oasis"),
                ("Lake Priyadarshini", None),
                ("Dakshin Gangotri", "Dakshin_Gangotri")],
    blurb="India's second Antarctic station, built in 1989 on the rock of "
          "the Schirmacher Oasis beside a freshwater lake that the station "
          "draws from directly — a rarity anywhere on the continent, where "
          "water usually means melting snow with diesel.",
    fact="India's first base, Dakshin Gangotri, was built on the ice shelf "
         "and was buried by 1990. Maitri was sited on rock specifically so "
         "the same thing could not happen twice; it means 'friendship'.",
    tip="India now runs Maitri and Bharati, 3,000 km apart on opposite "
        "sides of the East Antarctic coast, plus a Himalayan analogue "
        "station used to train the teams before they fly south."),

"princess-elisabeth-station": dict(
    name="Princess Elisabeth Antarctica",
    slug="Princess_Elisabeth_Antarctica", country="Antarctica",
    region="Queen Maud Land", type="history", tag="quirky",
    emoji="🔋", sounds=["antarctic-wind.mp3"],
    search_name="Princess Elisabeth Antarctica station",
    highlights=[("Utsteinen Nunatak", None),
                ("Sør Rondane Mountains", "Sør_Rondane_Mountains"),
                ("Wind turbines", None)],
    blurb="Belgium's station on a granite ridge below the Sør Rondane "
          "Mountains, and the only zero-emission research station in "
          "Antarctica: nine wind turbines, 380 m² of solar panels, and a "
          "microgrid that shuts down non-essential loads by itself when "
          "the wind drops.",
    fact="A stainless-steel shell over a nine-layer wall means the building "
         "needs no heating system at all — body heat, electronics and sun "
         "hold it above freezing inside while it is −50 °C outside.",
    tip="It runs on renewables for the great majority of its power, with a "
        "generator kept purely as backup — which on a continent that "
        "measures everything in litres of flown-in diesel is the real "
        "achievement."),

"ulvetanna": dict(
    name="Ulvetanna", slug="Ulvetanna_Peak", country="Antarctica",
    region="Queen Maud Land", type="mountain", tag="hidden",
    emoji="🐺", sounds=["antarctic-wind.mp3"],
    search_name="Ulvetanna Peak Antarctica",
    highlights=[("Fenriskjeften", "Fenriskjeften"),
                ("Drygalski Mountains", "Drygalski_Mountains"),
                ("North East Ridge", None)],
    blurb="'The Wolf's Fang': a 2,931-metre blade of granite standing out "
          "of the ice in Queen Maud Land, part of a ridge called "
          "Fenriskjeften — the Jaws of Fenrir — because the whole line of "
          "peaks looks like a set of teeth.",
    fact="It was first climbed in 1994 and its hardest line, the north-east "
         "ridge, not until 2013 — a big-wall route at −30 °C where the "
         "approach involves flying a ski-plane onto blue ice and driving a "
         "skidoo to the base.",
    tip="These peaks are nunataks: only the tips of a buried mountain "
        "range. There is more Ulvetanna under the ice than above it, and "
        "the ice sheet around it is two kilometres deep."),

"halley-station": dict(
    name="Halley Research Station", slug="Halley_Research_Station",
    country="Antarctica", region="Weddell Sea", type="history",
    tag="famous", emoji="🦿", sounds=["antarctic-wind.mp3"],
    search_name="Halley Research Station Antarctica",
    highlights=[("Brunt Ice Shelf", "Brunt_Ice_Shelf"),
                ("Halley VI modules", None),
                ("Chasm 1", None),
                ("Ozone monitoring", None)],
    blurb="Britain's base on the floating Brunt Ice Shelf: eight blue and "
          "red modules on hydraulic legs and giant skis, so the whole "
          "station can be towed to new ground when the ice it sits on "
          "starts to break up. Which it did.",
    fact="The Antarctic ozone hole was discovered from Halley's data in "
         "1985 — measurements begun in 1956, showing spring ozone falling "
         "by a third. It led to the Montreal Protocol, the most successful "
         "environmental treaty ever signed.",
    tip="A crack called Chasm 1 forced the entire station to be towed 23 km "
        "upstream in 2016–17, and it has been unstaffed each winter since "
        "2017 — run remotely, in the dark, by instruments alone."),
})

# ===================== EAST ANTARCTICA =====================
# The old, cold, high side: two-thirds of the continent, the Australian
# and French and Japanese and Chinese and Russian coast, and the windiest
# place on the planet.

NEW.update({

"mawson-station": dict(
    name="Mawson Station", slug="Mawson_Station", country="Antarctica",
    region="East Antarctica", type="history", tag="hidden",
    emoji="🇦🇺", sounds=["antarctic-wind.mp3"],
    search_name="Mawson Station Antarctica",
    highlights=[("Horseshoe Harbour", None),
                ("Framnes Mountains", "Framnes_Mountains"),
                ("Auster emperor rookery", None),
                ("Wind turbines", None)],
    blurb="The oldest continuously operating station south of the Antarctic "
          "Circle, opened by Australia in 1954 on a rock harbour in Mac. "
          "Robertson Land, with the Framnes Mountains behind it and "
          "katabatic wind coming off the plateau most days of the year.",
    fact="Mawson was the last Antarctic station to use dogs. The huskies "
         "were shipped out in 1993 when the Environmental Protocol banned "
         "non-native species — and a working tradition that had been "
         "running since Amundsen ended, on this beach, that year.",
    tip="Two wind turbines on the ridge supplied a large share of the "
        "station's power for two decades, making Mawson the first "
        "Antarctic base to run seriously on wind."),

"davis-station": dict(
    name="Davis Station", slug="Davis_Station", country="Antarctica",
    region="East Antarctica", type="history", tag="hidden",
    emoji="🏖️", sounds=["antarctic-wind.mp3"],
    search_name="Davis Station Antarctica",
    highlights=[("Vestfold Hills", "Vestfold_Hills"),
                ("Deep Lake", "Deep_Lake_(Antarctica)"),
                ("Prydz Bay", "Prydz_Bay")],
    blurb="Australia's busiest station, on the ice-free Vestfold Hills — "
          "brown rock, meltwater lakes, no glacier in sight — which is why "
          "people who work here call it the Riviera of the South, with the "
          "irony fully intended.",
    fact="Deep Lake, a few kilometres away, sits 50 m below sea level, is "
         "ten times saltier than the ocean and stays liquid to −20 °C. The "
         "microbes in it swap DNA so promiscuously that they blur the line "
         "between species.",
    tip="The Vestfold Hills hold hundreds of lakes, some fresh, some "
        "hypersaline, some layered with both — every one of them cut off "
        "from the others long enough to have gone its own evolutionary way."),

"casey-station": dict(
    name="Casey Station", slug="Casey_Station", country="Antarctica",
    region="East Antarctica", type="history", tag="hidden",
    emoji="🎨", sounds=["antarctic-wind.mp3"],
    search_name="Casey Station Antarctica",
    highlights=[("Bailey Peninsula", None),
                ("Wilkes Station", "Wilkes_Station"),
                ("Shirley Island", None),
                ("Wilkins Runway", "Wilkins_Runway")],
    blurb="Australia's station on the Budd Coast, a row of brightly "
          "coloured boxy buildings joined by covered walkways — 'the Red "
          "Shed' is the living quarters and everyone calls it that — with "
          "an Adélie colony on the island across the bay.",
    fact="Its predecessor, the American-built Wilkes Station, was handed "
         "to Australia in 1959 and eventually abandoned to the drift. It is "
         "still there under the snow, a fully furnished 1950s base slowly "
         "being crushed.",
    tip="The Wilkins blue-ice runway, 70 km inland, took Australia's first "
        "intercontinental A319 flights from Hobart — four and a half hours "
        "instead of two weeks by ship."),

"mirny-station": dict(
    name="Mirny Station", slug="Mirny_Station", country="Antarctica",
    region="East Antarctica", type="history", tag="hidden",
    emoji="⚓", sounds=["antarctic-wind.mp3"],
    search_name="Mirny Station Antarctica",
    highlights=[("Davis Sea", "Davis_Sea"),
                ("Queen Mary Land", "Queen_Mary_Land"),
                ("Vostok traverse", None)],
    blurb="The Soviet Union's first Antarctic station, opened in 1956 on "
          "the Queen Mary Land coast and named after one of Bellingshausen's "
          "ships. For decades it was the headquarters of the entire Soviet "
          "Antarctic programme and the start of the tractor road to Vostok.",
    fact="The Vostok traverse from here is 1,400 km of plateau, climbing to "
         "3,500 m, and used to take heavy tractor trains over a month each "
         "way — the longest routine overland supply run ever operated "
         "anywhere on Earth.",
    tip="Buildings at Mirny sink into the ice as the snow accumulates over "
        "them; some of the original 1956 structures are now well below the "
        "surface and reached by stairs."),

"cape-denison": dict(
    name="Cape Denison", slug="Cape_Denison", country="Antarctica",
    region="East Antarctica", type="history", tag="famous",
    emoji="💨", sounds=["antarctic-wind.mp3"],
    search_name="Cape Denison Antarctica Mawson's Huts",
    highlights=[("Mawson's Huts", "Mawson's_Huts"),
                ("Commonwealth Bay", "Commonwealth_Bay"),
                ("Boat Harbour", None),
                ("Memorial Cross", None)],
    blurb="The windiest place at sea level on Earth. Douglas Mawson built "
          "his hut here in 1912 and measured an average wind speed of about "
          "50 mph for a whole year, with gusts to 200 — his men learned to "
          "walk by leaning at forty-five degrees, on crampons, indoors-out.",
    fact="Mawson called his book *The Home of the Blizzard*. He also "
         "survived the worst sledging journey in Antarctic history: both "
         "companions dead, his dogs eaten, his soles peeling off, alone for "
         "the last hundred miles — and reached the hut hours after his ship "
         "sailed, condemning him to another winter.",
    tip="The huts are still standing, packed with ice, and are conserved by "
        "an Australian foundation. Commonwealth Bay is often unreachable: a "
        "grounded iceberg blocked it for years and hardly anyone got in."),

"dumont-durville-station": dict(
    name="Dumont d'Urville Station", slug="Dumont_d'Urville_Station",
    country="Antarctica", region="East Antarctica", type="history",
    tag="famous", emoji="🎬", sounds=["antarctic-wind.mp3"],
    search_name="Dumont d'Urville Station Antarctica",
    highlights=[("Île des Pétrels", None),
                ("Adélie Land", "Adélie_Land"),
                ("Emperor colony", None),
                ("Astrolabe Glacier", "Astrolabe_Glacier")],
    blurb="France's station on a small island off Adélie Land, sharing the "
          "rock with an emperor penguin colony and about the same number of "
          "Adélies. The whole species is named after this coast, and this "
          "coast after the wife of the man who found it.",
    fact="*March of the Penguins* was filmed here across a full year, "
         "including the winter, by a crew of two. It went on to make more "
         "money than any documentary before it, off a colony that walks "
         "past the station's front door.",
    tip="An attempt in the 1980s to blast an airstrip out of the "
        "neighbouring islets destroyed penguin habitat, was never finished, "
        "and became one of the reasons the Environmental Protocol has teeth."),

"syowa-station": dict(
    name="Syowa Station", slug="Syowa_Station_(Antarctica)",
    country="Antarctica", region="East Antarctica", type="history",
    tag="quirky", emoji="🐕", sounds=["antarctic-wind.mp3"],
    search_name="Showa Station Antarctica",
    highlights=[("East Ongul Island", "East_Ongul_Island"),
                ("Lützow-Holm Bay", "Lützow-Holm_Bay"),
                ("Taro and Jiro", "Taro_and_Jiro")],
    blurb="Japan's main Antarctic base, on East Ongul Island in "
          "Lützow-Holm Bay since 1957, and the reason two sled dogs are "
          "among the most famous animals in Japan.",
    fact="When the 1958 relief failed, fifteen chained huskies were left "
         "behind with a week of food. A year later a team returned and "
         "found two brothers, Taro and Jiro, alive and healthy. Nobody has "
         "ever fully explained how; the story has been filmed twice.",
    tip="Japan's icebreaker *Shirase* still fights through the fast ice of "
        "Lützow-Holm Bay every summer, and in bad years rams the same "
        "hundred kilometres for weeks without getting through."),

"zhongshan-station": dict(
    name="Zhongshan Station", slug="Zhongshan_Station_(Antarctica)",
    country="Antarctica", region="East Antarctica", type="history",
    tag="hidden", emoji="🇨🇳", sounds=["antarctic-wind.mp3"],
    search_name="Zhongshan Station Antarctica",
    highlights=[("Larsemann Hills", "Larsemann_Hills"),
                ("Prydz Bay", "Prydz_Bay"),
                ("Dome A traverse", None)],
    blurb="China's second Antarctic station, on the Larsemann Hills beside "
          "Prydz Bay, opened in 1989 and now the coastal end of the "
          "1,200-km inland traverse that supplies Kunlun on the highest "
          "point of the ice sheet.",
    fact="The Larsemann Hills are one of only two ice-free coastal oases in "
         "all of East Antarctica with more than one nation's station on "
         "them — China, Russia, India and Australia all have or had "
         "buildings within a few kilometres.",
    tip="Zhongshan sits close enough to the magnetic pole for aurora "
        "australis observation to be one of its main programmes; the "
        "displays here rival anything seen from the Arctic."),

"bharati-station": dict(
    name="Bharati", slug="Bharati_(research_station)", country="Antarctica",
    region="East Antarctica", type="history", tag="quirky",
    emoji="📦", sounds=["antarctic-wind.mp3"],
    search_name="Bharati Station Antarctica",
    highlights=[("Larsemann Hills", "Larsemann_Hills"),
                ("Prydz Bay", "Prydz_Bay"),
                ("Shipping containers", None)],
    blurb="India's third station, on the Larsemann Hills, built out of 134 "
          "shipping containers welded together and clad in a smooth "
          "aluminium shell — assembled in Germany, tested, taken apart, "
          "shipped south and rebuilt in one summer.",
    fact="The container idea was not a shortcut: each unit is fitted out "
         "before it leaves, so the whole interior arrives finished and the "
         "on-ice build becomes assembly rather than construction. It is "
         "now a template several programmes have copied.",
    tip="The shell is shaped to shed katabatic wind and drift. Buildings "
        "on this coast are increasingly designed like aircraft parts, "
        "because the wind is the thing that destroys them."),

"amery-ice-shelf": dict(
    name="Amery Ice Shelf", slug="Amery_Ice_Shelf", country="Antarctica",
    region="East Antarctica", type="nature", tag="hidden",
    emoji="🧊", sounds=["antarctic-wind.mp3"],
    search_name="Amery Ice Shelf Antarctica",
    highlights=[("Lambert Glacier", "Lambert_Glacier"),
                ("Prydz Bay", "Prydz_Bay"),
                ("Loose Tooth", None)],
    blurb="The outlet for the Lambert Glacier, the largest glacier in the "
          "world: a 60,000 km² floating shelf draining roughly a sixth of "
          "the entire East Antarctic ice sheet through one 100-km-wide gate.",
    fact="A rift system nicknamed the Loose Tooth was watched by satellite "
         "for two decades before it finally let go in 2019, releasing an "
         "iceberg bigger than Greater London — one of the most anticipated "
         "calvings in glaciology.",
    tip="Under the shelf, seawater refreezes onto the base as 'marine ice' "
        "hundreds of metres thick, so parts of it are made of frozen ocean "
        "rather than compressed snow."),
})

# ===================== THE POLAR PLATEAU =====================
# Three kilometres up, no horizon, and the coldest air ever measured on
# the surface of this planet.

NEW.update({

"south-pole": dict(
    name="Amundsen–Scott South Pole Station",
    slug="Amundsen–Scott_South_Pole_Station", country="Antarctica",
    region="Polar Plateau", type="history", tag="famous",
    emoji="🎯", sounds=["antarctic-wind.mp3"],
    search_name="Amundsen-Scott South Pole Station",
    highlights=[("Geographic South Pole", None),
                ("Ceremonial South Pole", None),
                ("South Pole Telescope", "South_Pole_Telescope"),
                ("IceCube Neutrino Observatory",
                 "IceCube_Neutrino_Observatory"),
                ("The Dark Sector", None)],
    blurb="Ninety degrees south: a raised aluminium building on 2,700 "
          "metres of ice at the bottom of the world, where every direction "
          "is north, the sun rises once a year, and about 45 people spend "
          "the winter completely unreachable from February to October.",
    fact="The marker for the geographic pole is moved every New Year's Day, "
         "because the ice sheet it stands on flows about ten metres a year. "
         "Each year's marker is designed and machined by the winter crew, "
         "and the old ones are lined up in the station.",
    tip="There is a 300 Club: sauna at 200 °F, then run outside naked to "
        "the Pole and back when the air hits −100 °F. It is real, it is "
        "unofficial, and it happens most winters."),

"vostok-station": dict(
    name="Vostok Station", slug="Vostok_Station", country="Antarctica",
    region="Polar Plateau", type="history", tag="famous",
    emoji="🥶", sounds=["antarctic-wind.mp3"],
    search_name="Vostok Station Antarctica",
    highlights=[("Lake Vostok", "Lake_Vostok"),
                ("Ice core drilling", None),
                ("Southern Pole of Cold", None)],
    blurb="The coldest inhabited place on Earth: −89.2 °C measured here on "
          "21 July 1983, on a featureless plateau 3,488 m above sea level "
          "and 1,300 km from the nearest coast, held by Russia since 1957.",
    fact="Vostok's ice cores went back 420,000 years and produced the graph "
         "that made the case for greenhouse warming visible to "
         "non-scientists: CO₂ and temperature moving together through four "
         "glacial cycles, drawn from bubbles of ancient air.",
    tip="The air is so thin and so dry that new arrivals need a week to "
        "acclimatise; the effective altitude is closer to 5,000 m than "
        "3,500, because the atmosphere itself is thinner over the poles."),

"lake-vostok": dict(
    name="Lake Vostok", slug="Lake_Vostok", country="Antarctica",
    region="Polar Plateau", type="nature", tag="famous",
    emoji="💧", sounds=["antarctic-wind.mp3"],
    search_name="Lake Vostok Antarctica",
    highlights=[("Vostok Station", "Vostok_Station"),
                ("Subglacial lake", "Subglacial_lake"),
                ("Borehole 5G", None)],
    blurb="A freshwater lake the size of Lake Ontario, sealed under four "
          "kilometres of ice and cut off from the atmosphere for something "
          "like fifteen million years. It was found by radar in the 1970s "
          "and nobody has ever seen it.",
    fact="Russian drillers reached the water in February 2012 after more "
         "than twenty years, stopping just short each season while the "
         "world argued about contamination. Water rose up the borehole and "
         "froze; that ice is what has been sampled.",
    tip="There are now more than 400 known subglacial lakes under "
        "Antarctica, some connected by rivers that fill and drain on "
        "decade timescales — an entire hydrological system nobody knew "
        "existed fifty years ago."),

"concordia-station": dict(
    name="Concordia Station", slug="Concordia_Station", country="Antarctica",
    region="Polar Plateau", type="history", tag="famous",
    emoji="🚀", sounds=["antarctic-wind.mp3"],
    search_name="Concordia Station Antarctica",
    highlights=[("Dome C", "Dome_C"),
                ("EPICA ice core", "European_Project_for_Ice_Coring_in_Antarctica"),
                ("White Mars", None)],
    blurb="Two cylindrical towers on Dome C, 3,233 m up and 1,100 km from "
          "the coast, run jointly by France and Italy. Thirteen people "
          "winter here in temperatures down to −80 °C with no possibility "
          "of rescue for nine months.",
    fact="ESA uses it as a Mars analogue and calls it White Mars: isolation, "
         "confinement, a small fixed crew, hypoxia, and no way out — the "
         "closest thing on Earth to a long-duration crewed mission, with a "
         "permanent human-physiology programme attached.",
    tip="Dome C has the best astronomical seeing on the planet — colder, "
        "drier, stiller air than any mountaintop — which is why telescopes "
        "keep being proposed for a place this hard to reach."),

"dome-fuji": dict(
    name="Dome Fuji Station", slug="Dome_F", country="Antarctica",
    region="Polar Plateau", type="history", tag="hidden",
    emoji="🗻", sounds=["antarctic-wind.mp3"],
    search_name="Dome Fuji Station Antarctica",
    highlights=[("Queen Maud Land", None),
                ("Deep ice core", None),
                ("Syowa traverse", None)],
    blurb="Japan's inland station at 3,810 m on the second-highest dome of "
          "the East Antarctic ice sheet, opened in 1995 and reached by a "
          "1,000-km tractor traverse from the coast. Temperatures here have "
          "hit −79.7 °C.",
    fact="The Dome Fuji core reached 3,035 m and 720,000 years of climate "
         "record. Japan is now drilling nearby for ice more than a million "
         "years old, hunting the point where Earth's ice ages changed "
         "rhythm from 41,000-year cycles to 100,000-year ones.",
    tip="Three separate projects — Japanese, European and Chinese — are "
        "all currently drilling for 'oldest ice' on this plateau within a "
        "few hundred kilometres of each other."),

"kunlun-station": dict(
    name="Kunlun Station", slug="Kunlun_Station", country="Antarctica",
    region="Polar Plateau", type="history", tag="hidden",
    emoji="🔭", sounds=["antarctic-wind.mp3"],
    search_name="Kunlun Station Dome A Antarctica",
    highlights=[("Dome A", "Dome_A"),
                ("Zhongshan traverse", None),
                ("Antarctic astronomy", None)],
    blurb="China's summer station on Dome A, at 4,093 m the highest point "
          "on the Antarctic ice sheet and the coldest place on the surface "
          "of the Earth — satellite readings from the ridge nearby have "
          "gone below −93 °C.",
    fact="Dome A has almost no wind, almost no water vapour and a "
         "boundary layer only a few metres thick, which makes it arguably "
         "the best site on the planet for optical and terahertz astronomy. "
         "China has been putting small survey telescopes there since 2008.",
    tip="Getting there is a 1,200-km traverse from Zhongshan taking about "
        "three weeks each way, climbing four kilometres. Nobody has "
        "wintered at Kunlun yet."),
})

# ===================== WEST ANTARCTICA =====================
# The unstable third: an ice sheet sitting on bedrock below sea level,
# which is why the glaciers on this side have their own news cycle.

NEW.update({

"mount-vinson": dict(
    name="Vinson Massif", slug="Vinson_Massif", country="Antarctica",
    region="West Antarctica", type="mountain", tag="famous",
    emoji="🏔️", sounds=["antarctic-wind.mp3"],
    search_name="Vinson Massif Antarctica",
    highlights=[("Sentinel Range", "Sentinel_Range"),
                ("Ellsworth Mountains", "Ellsworth_Mountains"),
                ("Branscomb Glacier", None),
                ("Low Camp", None)],
    blurb="At 4,892 m the highest mountain in Antarctica and one of the "
          "Seven Summits — technically straightforward, logistically "
          "absurd, and cold enough that the standard climbing failure here "
          "is frostbite rather than altitude.",
    fact="Nobody even knew it existed until a US Navy flight spotted it in "
         "1958. The first ascent was 1966. It is the most recently "
         "discovered of the Seven Summits by a margin of centuries.",
    tip="Everyone flies in via Union Glacier and then a ski-plane to base "
        "camp at 2,100 m. The whole trip runs three weeks, most of it "
        "waiting for weather, and costs more than the other six summits "
        "combined."),

"union-glacier-camp": dict(
    name="Union Glacier Camp", slug="Union_Glacier_Camp", country="Antarctica",
    region="West Antarctica", type="village", tag="hidden",
    emoji="⛺", sounds=["antarctic-wind.mp3"],
    search_name="Union Glacier Camp Antarctica",
    highlights=[("Union Glacier", "Union_Glacier"),
                ("Blue-ice runway", None),
                ("Ellsworth Mountains", "Ellsworth_Mountains"),
                ("Mount Rossman", None)],
    blurb="A private camp on a blue-ice runway in the Ellsworth Mountains, "
          "and the gateway for almost everything non-governmental in deep "
          "Antarctica: Vinson climbers, South Pole skiers, marathon "
          "runners, and the occasional wedding.",
    fact="The runway is natural blue ice — wind-scoured glacier hard enough "
         "to land an Ilyushin Il-76 jet on wheels, straight from Punta "
         "Arenas. There is no tarmac and no snow to clear; there is just ice.",
    tip="The Antarctic Ice Marathon is run from here, in wind chill down to "
        "−20 °C at 700 m altitude on soft snow. Finishing times are roughly "
        "double what the same runners do at home."),

"thwaites-glacier": dict(
    name="Thwaites Glacier", slug="Thwaites_Glacier", country="Antarctica",
    region="West Antarctica", type="nature", tag="famous",
    emoji="⚠️", sounds=["antarctic-wind.mp3"],
    search_name="Thwaites Glacier Antarctica",
    highlights=[("Amundsen Sea", "Amundsen_Sea"),
                ("Grounding line", None),
                ("Ice shelf buttress", None),
                ("West Antarctic Ice Sheet",
                 "West_Antarctic_Ice_Sheet")],
    blurb="The Doomsday Glacier: 120 km wide where it meets the sea, "
          "draining an area the size of Britain, and sitting on bedrock "
          "that slopes *downward* inland — so once it starts retreating, "
          "the geometry makes it retreat faster.",
    fact="Thwaites on its own holds enough ice for about 65 cm of global "
         "sea-level rise, and it plugs a basin holding several metres more. "
         "It is the single largest uncertainty in every sea-level "
         "projection published.",
    tip="In 2019–2020 a hot-water drill put a robot through 600 m of ice to "
        "the grounding line and found warm water arriving from below — the "
        "melt is coming from the ocean underneath, not the air above."),

"pine-island-glacier": dict(
    name="Pine Island Glacier", slug="Pine_Island_Glacier",
    country="Antarctica", region="West Antarctica", type="nature",
    tag="hidden", emoji="📉", sounds=["antarctic-wind.mp3"],
    search_name="Pine Island Glacier Antarctica",
    highlights=[("Amundsen Sea", "Amundsen_Sea"),
                ("Ice shelf calving", None),
                ("Iceberg B-46", None)],
    blurb="Antarctica's fastest-thinning major glacier, moving about four "
          "kilometres a year and responsible on its own for roughly a "
          "quarter of all Antarctic ice loss. Its front has retreated more "
          "than 30 km since the 1970s.",
    fact="It used to calve a big iceberg roughly every six years. Since "
         "2013 it has been doing it every year or two, and the ice shelf "
         "that holds the glacier back is now shorter than at any point in "
         "the satellite record.",
    tip="It is 2,500 km from the nearest permanent station, which is why "
        "almost everything known about it comes from satellites, "
        "airborne radar and a handful of very expensive field seasons."),

"mount-sidley": dict(
    name="Mount Sidley", slug="Mount_Sidley", country="Antarctica",
    region="West Antarctica", type="mountain", tag="hidden",
    emoji="🌋", sounds=["antarctic-wind.mp3"],
    search_name="Mount Sidley Antarctica",
    highlights=[("Executive Committee Range",
                 "Executive_Committee_Range"),
                ("Marie Byrd Land", "Marie_Byrd_Land"),
                ("Summit caldera", None)],
    blurb="The highest volcano in Antarctica at 4,285 m, in Marie Byrd "
          "Land — a dormant shield with a caldera five kilometres across "
          "cut into its southern side, sitting in the least-visited "
          "quarter of the least-visited continent.",
    fact="Marie Byrd Land is the largest piece of land on Earth claimed by "
         "nobody at all. Every other sector of Antarctica has at least one "
         "claimant; this one has none, and never has.",
    tip="It is one of the Volcanic Seven Summits, which is why the handful "
        "of ascents it gets each decade are almost all by people ticking "
        "that list."),

"peter-i-island": dict(
    name="Peter I Island", slug="Peter_I_Island", country="Antarctica",
    region="West Antarctica", type="island", tag="quirky",
    emoji="📻", sounds=["ocean-waves.mp3"],
    search_name="Peter I Island Antarctica",
    highlights=[("Lars Christensen Peak", None),
                ("Bellingshausen Sea", "Bellingshausen_Sea"),
                ("Norwegian dependency", None)],
    blurb="A volcanic island in the Bellingshausen Sea, 450 km from any "
          "other land, ringed by ice cliffs on almost every side and "
          "claimed by Norway. Fewer people have set foot on it than have "
          "stood on the summit of Everest.",
    fact="It is one of the most wanted entities in amateur radio: a "
         "DXpedition here costs a fortune, needs a helicopter and an "
         "icebreaker, and happens roughly once a decade. Operators "
         "worldwide sit up at night waiting for the callsign.",
    tip="Bellingshausen sighted it in 1821 and nobody managed to land until "
        "1929. The ice cliffs mean there is essentially no beach — you "
        "arrive by helicopter or you do not arrive."),
})

# ===================== SOUTH GEORGIA & THE SOUTH SANDWICH ISLANDS =====================
# North of 60°S, so not Antarctica under the Treaty — but south of the
# Antarctic Convergence, which is the line the wildlife actually obeys.

NEW.update({

"grytviken": dict(
    name="Grytviken", slug="Grytviken",
    country="South Georgia and the South Sandwich Islands",
    region="South Georgia", type="history", tag="famous",
    emoji="⚱️", sounds=["ocean-waves.mp3"],
    search_name="Grytviken South Georgia",
    highlights=[("Shackleton's grave", None),
                ("South Georgia Museum", "South_Georgia_Museum"),
                ("Whalers' church", None),
                ("King Edward Cove", None)],
    blurb="A rusting whaling station in a green cove ringed by mountains, "
          "abandoned in 1965 and now half museum, half fur-seal colony. "
          "Between 1904 and 1965 this one bay processed more than 175,000 "
          "whales.",
    fact="Shackleton is buried in the whalers' cemetery here, facing south, "
         "at his widow's request. He died of a heart attack aboard ship in "
         "King Edward Cove in 1922, on his way back to the ice. His right "
         "hand man Frank Wild's ashes were laid beside him in 2011.",
    tip="Everyone who lands does the same thing: walks up to the grave with "
        "a tot of whisky, pours one for him and drinks the rest. The "
        "museum sells the whisky for exactly this reason."),

"king-edward-point": dict(
    name="King Edward Point", slug="King_Edward_Point",
    country="South Georgia and the South Sandwich Islands",
    region="South Georgia", type="village", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    search_name="King Edward Point South Georgia",
    highlights=[("King Edward Cove", None),
                ("Grytviken", "Grytviken"),
                ("Discovery House", None),
                ("Mount Duse", None)],
    blurb="The capital of South Georgia, such as it is: a research station "
          "and the government offices, with a permanent population in the "
          "low double digits. It is the administrative centre of a "
          "territory with no permanent residents at all.",
    fact="South Georgia's toothfish and krill fishery is one of the "
         "best-managed in the world and its licence fees pay for the entire "
         "territory — the government of a place with no taxpayers funds "
         "itself by selling fishing rights.",
    tip="The station also ran the rat eradication that finished in 2018: "
        "the largest rodent removal ever attempted anywhere, across 1,000 "
        "km² by helicopter, and the pipits and pintails came back."),

"salisbury-plain": dict(
    name="Salisbury Plain", slug="Salisbury_Plain,_South_Georgia",
    country="South Georgia and the South Sandwich Islands",
    region="South Georgia", type="nature", tag="famous",
    emoji="👑", sounds=["ocean-waves.mp3"],
    search_name="Salisbury Plain South Georgia king penguins",
    highlights=[("Bay of Isles", "Bay_of_Isles"),
                ("Grace Glacier", None),
                ("King penguin colony", None),
                ("Elephant seals", None)],
    blurb="A glacial outwash plain in the Bay of Isles holding around "
          "60,000 pairs of king penguins — an unbroken carpet of orange and "
          "grey stretching from the beach to the moraine, with elephant "
          "seals asleep in the middle of it.",
    fact="King penguins take fourteen months to raise a chick, so the "
         "colony never empties and never synchronises. Every visit has "
         "eggs, brown woolly chicks and adults moulting all at once, which "
         "is why early sealers thought the chicks were a separate species.",
    tip="The 'oakum boys' — the brown fluffy chicks — were named by whalers "
        "after the tarred rope fibres they picked as punishment. The name "
        "stuck and is still used."),

"st-andrews-bay": dict(
    name="St Andrews Bay", slug="St_Andrews_Bay,_South_Georgia",
    country="South Georgia and the South Sandwich Islands",
    region="South Georgia", type="nature", tag="famous",
    emoji="🐧", sounds=["ocean-waves.mp3"],
    search_name="St Andrews Bay South Georgia",
    highlights=[("Cook Glacier", "Cook_Glacier_(South_Georgia)"),
                ("King penguin colony", None),
                ("Elephant seal beach", None),
                ("Mount Skittle", None)],
    blurb="The largest king penguin colony on South Georgia and one of the "
          "largest on Earth: roughly 150,000 pairs on a three-kilometre "
          "beach below three glaciers, with several thousand elephant seals "
          "hauled out among them.",
    fact="The Cook, Heaney and Buxton glaciers used to reach the beach and "
         "have retreated far enough to expose new ground — which the "
         "penguins immediately colonised. The colony has grown as the ice "
         "has gone.",
    tip="The surf on this beach turns landings back more often than not. "
        "People who have sailed South Georgia three times have been "
        "refused St Andrews all three."),

"stromness": dict(
    name="Stromness", slug="Stromness,_South_Georgia",
    country="South Georgia and the South Sandwich Islands",
    region="South Georgia", type="history", tag="famous",
    emoji="🚪", sounds=["ocean-waves.mp3"],
    search_name="Stromness South Georgia",
    highlights=[("Shackleton Waterfall", None),
                ("Manager's Villa", None),
                ("Fortuna Bay", "Fortuna_Bay"),
                ("Whaling station ruins", None)],
    blurb="The whaling station where Shackleton's crossing ended. Three men "
          "walked out of the mountains on 20 May 1916, unrecognisable, and "
          "knocked on the station manager's door. The first people they met "
          "were two boys, who ran away.",
    fact="They had crossed 32 km of unmapped glaciated mountains in 36 "
         "hours with no map, no tent, no sleeping bags, fifty feet of rope "
         "and screws from the boat hammered into their boots for crampons. "
         "The route was not repeated until 1955.",
    tip="The last stage of the Shackleton Walk from Fortuna Bay finishes "
        "at the waterfall above the station — the same one they abseiled "
        "down on their rope, soaking wet, hours from the door."),

"gold-harbour": dict(
    name="Gold Harbour", slug="Gold_Harbour",
    country="South Georgia and the South Sandwich Islands",
    region="South Georgia", type="nature", tag="hidden",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    search_name="Gold Harbour South Georgia",
    highlights=[("Bertrab Glacier", None),
                ("King penguin colony", None),
                ("Elephant seal harems", None),
                ("Light-mantled albatross", None)],
    blurb="A short beach on South Georgia's south-east coast under the "
          "hanging Bertrab Glacier, with 25,000 pairs of king penguins, a "
          "wall of elephant seals, and light-mantled sooty albatrosses "
          "doing synchronised display flights along the cliff behind.",
    fact="It is named for the way the early morning sun hits the tussac "
         "grass and the glacier above the beach — the light lasts about "
         "twenty minutes and is the reason ships anchor here overnight.",
    tip="Elephant seal bulls weigh up to four tonnes and fight through "
        "October. The rule is 15 metres, and the reason for the rule is "
        "that they can move much faster than they look like they can."),

"zavodovski-island": dict(
    name="Zavodovski Island", slug="Zavodovski_Island",
    country="South Georgia and the South Sandwich Islands",
    region="South Sandwich Islands", type="island", tag="quirky",
    emoji="🤢", sounds=["ocean-waves.mp3"],
    search_name="Zavodovski Island South Sandwich",
    highlights=[("Mount Curry", None),
                ("Chinstrap colony", None),
                ("Stench Point", None),
                ("Noxious Bluff", None)],
    blurb="An active volcano in the South Sandwich Islands carrying the "
          "largest penguin colony on the planet: something like a million "
          "pairs of chinstraps nesting on the warm ash slopes of a mountain "
          "that erupts on them periodically.",
    fact="Its capes are named Stench Point, Noxious Bluff, Reek Point and "
         "Acrid Point. Captain Cook's crew and everyone since has been "
         "unable to describe the island without reference to the smell of a "
         "million penguins on a volcano.",
    tip="The whole South Sandwich chain is uninhabited, has no harbours "
        "and is barely visited — a couple of ships a year get close enough "
        "to look, and far fewer manage to land."),
})

# ===================== FRENCH SOUTHERN TERRITORIES =====================

NEW.update({

"port-aux-francais": dict(
    name="Port-aux-Français", slug="Port-aux-Français",
    country="French Southern and Antarctic Lands",
    region="Kerguelen", type="village", tag="hidden",
    emoji="🇫🇷", sounds=["antarctic-wind.mp3"],
    search_name="Port-aux-Francais Kerguelen",
    highlights=[("Kerguelen Islands", "Kerguelen_Islands"),
                ("Golfe du Morbihan", None),
                ("Kerguelen cabbage", "Kerguelen_cabbage"),
                ("Feral cats and reindeer", None)],
    blurb="The only settlement on Kerguelen: 45 to 100 people depending on "
          "the season, on an archipelago 3,300 km from anywhere, supplied "
          "four times a year by one ship out of Réunion. There is no "
          "airstrip. There is no other option.",
    fact="Kerguelen is nicknamed the Desolation Islands, by its own "
         "discoverer, who had sold it to Louis XV as a rich southern "
         "continent and had to go back and admit what it actually was.",
    tip="The islands are overrun by species people introduced and then "
        "left: reindeer, rabbits, feral cats, mouflon sheep and trout, all "
        "eating an ecosystem that evolved without any of them."),

"kerguelen-islands": dict(
    name="Kerguelen Islands", slug="Kerguelen_Islands",
    country="French Southern and Antarctic Lands",
    region="Kerguelen", type="island", tag="hidden",
    emoji="🥬", sounds=["antarctic-wind.mp3"],
    search_name="Kerguelen Islands",
    highlights=[("Mount Ross", None),
                ("Cook Ice Cap", None),
                ("Kerguelen cabbage", "Kerguelen_cabbage"),
                ("Golfe du Morbihan", None)],
    blurb="Three hundred islands and 7,215 km² of black rock, glacier and "
          "tussock in the middle of the Southern Ocean, with a coastline so "
          "fjorded that no point on the main island is more than 21 km from "
          "the sea. The wind blows over 100 km/h roughly a hundred days a year.",
    fact="Kerguelen cabbage saved lives: full of vitamin C, edible raw, and "
         "the reason Cook's crews and generations of sealers here did not "
         "get scurvy. It evolved with no insect pollinators and is "
         "pollinated by the wind.",
    tip="The archipelago sits on the Kerguelen Plateau, a submerged "
        "continent three times the size of Japan that was above water 20 "
        "million years ago and had forests on it."),

"alfred-faure": dict(
    name="Alfred Faure", slug="Alfred_Faure",
    country="French Southern and Antarctic Lands",
    region="Crozet", type="history", tag="hidden",
    emoji="👑", sounds=["ocean-waves.mp3"],
    search_name="Alfred Faure Crozet Islands",
    highlights=[("Île de la Possession", "Île_de_la_Possession"),
                ("Baie du Marin", None),
                ("King penguin colony", None),
                ("Crozet Islands", "Crozet_Islands")],
    blurb="France's base on Île de la Possession in the Crozet archipelago, "
          "perched above the Baie du Marin and its king penguin colony — "
          "a couple of dozen people, one supply ship every few months, and "
          "some of the roughest sea in the world all around.",
    fact="The Crozets hold about half the world's king penguins. The colony "
         "at Baie du Marin alone has been counted continuously since the "
         "1960s, one of the longest seabird series in the southern "
         "hemisphere.",
    tip="Wandering albatrosses breed on these islands and are tracked from "
        "here with satellite tags. Individual birds have been recorded "
        "circling Antarctica in 46 days and covering 120,000 km a year."),

"ile-aux-cochons": dict(
    name="Île aux Cochons", slug="Île_aux_Cochons",
    country="French Southern and Antarctic Lands",
    region="Crozet", type="island", tag="quirky",
    emoji="📉", sounds=["ocean-waves.mp3"],
    search_name="Ile aux Cochons Crozet",
    highlights=[("Crozet Islands", "Crozet_Islands"),
                ("King penguin colony", None),
                ("Mont Richard-Foy", None)],
    blurb="A small island in the Crozets that in 1982 held the largest king "
          "penguin colony ever recorded — about two million birds. When "
          "satellites looked again in 2017, nearly 90% of them were gone.",
    fact="The collapse was spotted from space, because nobody had physically "
         "landed on the island in 35 years. The cause is still argued: "
         "disease, an El Niño shifting the fish, cats and mice, or all "
         "three at once.",
    tip="It is one of the clearest demonstrations of how thin Southern "
        "Ocean monitoring really is — the biggest penguin colony on Earth "
        "lost a million and a half birds and nobody noticed for decades."),
})

# ===================== HEARD ISLAND & BOUVET =====================

NEW.update({

"heard-island": dict(
    name="Heard Island", slug="Heard_Island",
    country="Heard Island and McDonald Islands",
    region="Heard Island", type="island", tag="quirky",
    emoji="🌋", sounds=["antarctic-wind.mp3"],
    search_name="Heard Island Australia",
    highlights=[("Big Ben", "Big_Ben_(Heard_Island)"),
                ("Mawson Peak", None),
                ("Atlas Cove", None),
                ("McDonald Islands", None)],
    blurb="An Australian island 4,000 km south-west of Perth carrying Big "
          "Ben, an active volcano 2,745 m high and covered in glaciers — "
          "the highest Australian territory anywhere, higher than anything "
          "on the Australian mainland.",
    fact="It is one of only two active volcanoes in Australian territory "
          "and among the most remote places on the planet: no permanent "
          "population, no airstrip, and a two-week sail from Fremantle. "
          "Mawson Peak has been summited fewer than a handful of times.",
    tip="Neighbouring McDonald Island doubled in size between 1980 and 2000 "
        "by erupting, after 75,000 years of doing nothing. The island grew "
        "while nobody was watching it."),

"bouvet-island": dict(
    name="Bouvet Island", slug="Bouvet_Island",
    country="Bouvet Island", region="Bouvet Island", type="island",
    tag="quirky", emoji="🏝️", sounds=["ocean-waves.mp3"],
    search_name="Bouvet Island Norway",
    highlights=[("Olav Peak", None),
                ("Nyrøysa", None),
                ("Bouvetøya glacier", None)],
    blurb="The most remote island on Earth: 49 km² of ice-covered volcano "
          "in the South Atlantic, 1,600 km from the nearest land, which is "
          "the uninhabited Queen Maud Land coast. The nearest people are "
          "usually on the ISS.",
    fact="In 1964 a lifeboat was found on the island with oars and supplies "
         "and no people, and nobody has ever established whose it was or "
         "what happened. The beach it sat on did not exist before a "
         "landslide in the late 1950s created it.",
    tip="Norway keeps an automated weather station here, which has twice "
        "been swept away. Landing means a helicopter and a very good day; "
        "the whole island is ringed by ice cliffs."),
})


if __name__ == "__main__":
    rb.run(REGION, NEW, FILL)
