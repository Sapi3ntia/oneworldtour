#!/usr/bin/env python3
"""
build_alaska.py — Alaska, which the atlas had one record for.

WHAT WAS WRONG
    `data/usa.json` carried 74 places and exactly one of them was in Alaska:
    `denali`, whose blurb and fun_fact were empty strings and whose third
    highlight ("Park Road") pointed at the record's own article. A state
    larger than Texas, California and Montana together, with more coastline
    than the other forty-nine combined, was one park with no text.

    So this is the same job the Canada batch did one file over: a roster, a
    box, and every slug resolved live. The frame is `regionbuild.py`.

THE BOX HAS TWO HALVES
    Alaska is the only state that crosses the antimeridian. The Aleutians run
    west past 180° and come back as +172°, so a single longitude range either
    excludes Attu or, if you widen it to -180..180, stops being a test at all.
    `in_box()` below is two ranges OR-ed together — the same shape the Oceania
    batch needed for Fiji and Kiribati.

    No place in this roster actually sits west of the dateline (Adak, the
    furthest, is -176.6), but the box is written for the state rather than
    for the roster, because the next person to add Attu should not have to
    rediscover this.

STATE_BOX EARNS ITS KEEP HERE TOO
    `usa.json` holds 29 states, and Alaska's town names are not distinctive:
    Petersburg (Virginia), Wrangell, Palmer, Homer, Kenai, Eagle, Bethel,
    Cordova, Valdez, Whittier, Juneau. P17 answers "United States" for every
    namesake, and a nationwide box contains them all. The state rectangle is
    the only guard that separates them, and like the province boxes in
    build_canada.py it is a WARNING — a hand-drawn rectangle over a state
    with a panhandle is not evidence, it is a prompt to look.

HIGHLIGHTS
    Structures, towns and landforms only. `enrich_monuments.py` spends every
    highlight as a YouTube search term, so a person, an era, a ship or a
    federal agency is a wasted query. Five traps this roster hit and you will
    hit again:
      * `Childs_Glacier` redirects to `Foundation_Ice_Stream`, in Antarctica.
      * `Brooks_River` is in Quebec. The one at Brooks Falls has no article.
      * `Holy_Resurrection_Cathedral`, bare, is in Tokyo. Kodiak's is
        `Holy_Resurrection_Church_(Kodiak,_Alaska)`, and `Church_of_the_Holy_
        Ascension` — which reads like the same building — is 982 km away in
        Unalaska. Two Russian churches, two towns, one careless slug.
      * `Serpentine_Hot_Springs` redirects to Bering Land Bridge itself, so on
        that record it would have been a SELF. It stays a text chip.
      * `Romanzof_Mountains` redirects to `Brooks_Range`, which was already on
        the same record. A redirect can quietly duplicate a highlight.
    A `None` slug is deliberate — the UI renders highlights as text chips, so
    a name with no link costs nothing and a dead link is rot.

    Whole seas are legal under the rule and still bad. Chukchi, Beaufort and
    Bering between them held ten slots on the first pass, every one of them
    hundreds of kilometres of FAR and every one of them a search term that
    returns crab boats. They are down to two — the sea a place actually
    stands on — and the slots went to the spit, the island, the river and the
    pass that the place is made of.

TWO COUNTRY WARNINGS THAT ARE CORRECT
    `Mount_Saint_Elias` and `Hubbard_Glacier` both answer P17 = Q16, Canada.
    Both are right to: the summit is a boundary point and the glacier's
    accumulation basin sits on the border crest between Mount Vancouver and
    Mount Hubbard. They are Alaskan by every other measure — the glacier
    calves into Disenchantment Bay near Yakutat — so the warning is left
    standing rather than suppressed, and this paragraph is the answer to it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regionbuild as rb

COUNTRY_CODE = {"United States": "US"}

# Alaska, in two pieces, because the Aleutians cross 180°.
AK_LAT = (51.0, 71.6)
AK_LNG_E = (-180.0, -129.0)     # the mainland, the panhandle, most islands
AK_LNG_W = (172.0, 180.0)       # Attu, Agattu, the western Near Islands


def in_box(lat, lng):
    if not (AK_LAT[0] <= lat <= AK_LAT[1]):
        return False
    return (AK_LNG_E[0] <= lng <= AK_LNG_E[1]) or (AK_LNG_W[0] <= lng <= AK_LNG_W[1])


# Warning-level namesake guard: the coordinate against the state claimed.
# Only the eastern half — a record west of the dateline will warn, and should,
# because it is rare enough to deserve a human reading the line.
STATE_BOX = {"Alaska": (51.0, 71.6, -180.0, -129.0)}

REGION = rb.Region(target="usa.json", continent="North America",
                   country_code=COUNTRY_CODE, in_box=in_box,
                   subregion_box=STATE_BOX)

# `search_name` sharpens the media/monument query before it is asked. Alaska
# needs it constantly: Juneau is fine, but Petersburg, Wrangell, Palmer, Homer,
# Eagle, Bethel, Cordova, Valdez, Kenai and Whittier all lose their own search
# to a namesake in the lower 48 or in Europe. No downstream title guard can
# see a namesake, so it has to be said here.
NEW = {

# ========================= SOUTHCENTRAL =========================
"anchorage": dict(
    name="Anchorage", slug="Anchorage,_Alaska", country="United States",
    region="Alaska", type="city", tag="famous",
    emoji="🏙️", sounds=["city-hum.mp3"],
    search_name="Anchorage Alaska",
    highlights=[("Tony Knowles Coastal Trail", "Tony_Knowles_Coastal_Trail"),
                ("Anchorage Museum", "Anchorage_Museum"),
                ("Chugach State Park", "Chugach_State_Park"),
                ("Ship Creek", "Ship_Creek_(Alaska)"),
                ("Flattop Mountain", "Flattop_Mountain_(Anchorage,_Alaska)")],
    blurb="Home to nearly half of everybody in Alaska, wedged between an "
          "inlet that drains and refills twice a day and a mountain range "
          "that starts at the edge of the suburbs. Moose walk the bike "
          "paths. So do the people, at eleven at night in June.",
    fact="The 1964 Good Friday earthquake, magnitude 9.2 and the largest ever "
         "recorded in North America, dropped one Anchorage neighbourhood "
         "nine metres. The ground it slid across is a public park now.",
    tip="Ride the Coastal Trail out to Kincaid at low tide and look back: "
        "the whole city sits on a bluff you cannot see from inside it. "
        "Beluga whales come up Turnagain Arm on the incoming tide."),

"girdwood": dict(
    name="Girdwood", slug="Girdwood,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🎿", sounds=["mountain-wind.mp3"],
    search_name="Girdwood Alaska",
    highlights=[("Alyeska Resort", "Alyeska_Resort"),
                ("Crow Creek", "Crow_Creek_(Alaska)"),
                ("Turnagain Arm", "Turnagain_Arm"),
                ("Portage Glacier", "Portage_Glacier")],
    blurb="A ski town in a rainforest valley forty minutes from Anchorage, "
          "with seven glaciers visible from the tram and a permanent smell "
          "of wet spruce. The original townsite is under the mud flats.",
    fact="Girdwood moved. The 1964 earthquake dropped the valley floor by "
         "two and a half metres, the tide came in over the old town, and "
         "the whole place was rebuilt four kilometres up the valley.",
    tip="The drowned forest along the Seward Highway below town is the old "
        "Girdwood: dead spruce still standing in salt water sixty years on. "
        "Best light on it is the hour before sunset."),

"whittier": dict(
    name="Whittier", slug="Whittier,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🚇", sounds=["ocean-waves.mp3"],
    search_name="Whittier Alaska",
    highlights=[("Begich Towers", "Begich_Towers"),
                ("Anton Anderson Memorial Tunnel", "Portage_Glacier_Highway"),
                ("Prince William Sound", "Prince_William_Sound"),
                ("Portage Glacier", "Portage_Glacier")],
    blurb="A port on Prince William Sound where almost the entire town — "
          "homes, school, police station, shop, church — lives in one "
          "fourteen-storey building the army put up in 1957.",
    fact="The only road in is a single-lane tunnel shared with the railway, "
         "four kilometres through a mountain, running one direction at a "
         "time on a published timetable. Miss the last one and you stay.",
    tip="Check the tunnel schedule before you commit to the drive, both "
        "ways. Whittier averages over five metres of precipitation a year, "
        "so the sunny photographs you have seen are the exception."),

"seward": dict(
    name="Seward", slug="Seward,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    search_name="Seward Alaska",
    highlights=[("Kenai Fjords National Park", "Kenai_Fjords_National_Park"),
                ("Exit Glacier", "Exit_Glacier"),
                ("Alaska SeaLife Center", "Alaska_SeaLife_Center"),
                ("Resurrection Bay", "Resurrection_Bay")],
    blurb="A fishing and cruise port at the head of Resurrection Bay, with "
          "the only road-accessible glacier in Kenai Fjords eleven "
          "kilometres out of town and an icefield above it.",
    fact="Every Fourth of July the town races up Mount Marathon and back — "
         "921 metres of gain, a scree descent people take on the seat of "
         "their shorts, and a course record that has stood since 2016.",
    tip="Walk to Exit Glacier past the year markers on the road: 1917, "
        "1951, 1998, 2010. Each one is where the ice ended. The walk "
        "between the last two takes about a minute."),

"homer": dict(
    name="Homer", slug="Homer,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🎣", sounds=["ocean-waves.mp3"],
    search_name="Homer Alaska",
    highlights=[("Homer Spit", "Homer_Spit"),
                ("Kachemak Bay", "Kachemak_Bay"),
                ("Kachemak Bay State Park", "Kachemak_Bay_State_Park"),
                ("Halibut Cove", "Halibut_Cove,_Alaska")],
    blurb="The end of the road on the Kenai Peninsula, where a gravel spit "
          "runs seven kilometres straight out into Kachemak Bay and ends in "
          "a harbour, a boardwalk and a bar with dollar bills on the wall.",
    fact="The Spit is a glacial moraine, and the 1964 earthquake dropped it "
         "about one and a half metres. Everything on it now stands on fill "
         "trucked out to replace what the sea took.",
    tip="Cross the bay to Halibut Cove or Seldovia on the morning water "
        "taxi — no roads, boardwalk streets, and you will have the "
        "afternoon there. Otters work the harbour year-round."),

"kenai": dict(
    name="Kenai", slug="Kenai,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    search_name="Kenai Alaska",
    highlights=[("Kenai River", "Kenai_River"),
                ("Cook Inlet", "Cook_Inlet"),
                ("Soldotna", "Soldotna,_Alaska"),
                ("Old Town Kenai", None)],
    blurb="A Russian trading post from 1791 at the mouth of the river that "
          "produces the largest king salmon in the world, looking across "
          "Cook Inlet at four volcanoes.",
    fact="The world-record king salmon, 44 kg, came out of the Kenai River "
         "in 1985 and has not been approached since. The run it belonged to "
         "is now a fraction of what it was.",
    tip="Stand on the bluff at Old Town in July and watch dipnetting: "
        "residents wade in chest-deep with hoops on poles, legal only here "
        "and only for Alaskans. It looks like chaos and it is organised."),

"palmer": dict(
    name="Palmer", slug="Palmer,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🥬", sounds=["mountain-wind.mp3"],
    search_name="Palmer Alaska Matanuska",
    highlights=[("Hatcher Pass", "Hatcher_Pass"),
                ("Independence Mine", "Independence_Mines,_Alaska"),
                ("Matanuska Glacier", "Matanuska_Glacier"),
                ("Matanuska River", "Matanuska_River")],
    blurb="A farm town in the Matanuska Valley, ringed by peaks, founded in "
          "1935 when the federal government moved two hundred families here "
          "from the Depression-flattened upper Midwest.",
    fact="Twenty hours of summer daylight grow vegetables to absurd sizes. "
         "The state fair record cabbage weighed 62.7 kg. The pumpkin record "
         "is over 900.",
    tip="Drive Hatcher Pass to the Independence Mine buildings above the "
        "treeline — bunkhouses and mills left standing in the tundra. The "
        "road over the top is gravel and only open in late summer."),

"valdez": dict(
    name="Valdez", slug="Valdez,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🛢️", sounds=["ocean-waves.mp3"],
    search_name="Valdez Alaska",
    highlights=[("Thompson Pass", "Thompson_Pass"),
                ("Keystone Canyon", "Keystone_Canyon"),
                ("Trans-Alaska Pipeline", "Trans-Alaska_Pipeline_System"),
                ("Columbia Glacier", "Columbia_Glacier_(Alaska)")],
    blurb="The southern end of the pipeline, at the head of a fjord walled "
          "by mountains that catch more snow than almost anywhere in North "
          "America. Waterfalls come off the canyon walls all summer.",
    fact="Thompson Pass, just inland, holds the state snowfall records: "
         "24.9 m in the winter of 1952-53, and 1.6 m in a single day. The "
         "highway over it is kept open anyway.",
    tip="Old Valdez is four kilometres away and empty — the town moved "
        "after 1964 and left the street grid. Walk it. The signs tell you "
        "which building stood where."),

"cordova": dict(
    name="Cordova", slug="Cordova,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🦅", sounds=["ocean-waves.mp3"],
    search_name="Cordova Alaska",
    highlights=[("Copper River", "Copper_River_(Alaska)"),
                ("Million Dollar Bridge", "Miles_Glacier_Bridge"),
                ("Prince William Sound", "Prince_William_Sound"),
                ("Childs Glacier", None)],
    blurb="A fishing town on Prince William Sound with no road to anywhere "
          "— you arrive by ferry or by plane — living off the Copper River "
          "salmon run and the delta the river built.",
    fact="The Copper River Delta is the largest contiguous wetland on the "
         "Pacific coast of North America, and effectively the entire world "
         "population of western sandpipers stops here each May.",
    tip="Drive the Copper River Highway as far as it still goes and stand "
        "at the Million Dollar Bridge. It was half-destroyed in 1964, "
        "patched decades later, and the glacier opposite calves into the "
        "river loudly enough to hear from the deck."),

"talkeetna": dict(
    name="Talkeetna", slug="Talkeetna,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🛩️", sounds=["wilderness.mp3"],
    search_name="Talkeetna Alaska",
    highlights=[("Denali", "Denali"),
                ("Alaska Range", "Alaska_Range"),
                ("Talkeetna River", "Talkeetna_River"),
                ("Susitna River", "Susitna_River")],
    blurb="Three rivers meet at a gravel bar and a one-street town of log "
          "buildings sits above them, from which every climber attempting "
          "Denali flies out to the glacier.",
    fact="A cat called Stubbs was the honorary mayor for twenty years. The "
         "town has no elected mayor, so the joke was only half a joke.",
    tip="The view of Denali from the river bar at the end of Main Street is "
        "the best road-accessible one there is, and the mountain is out "
        "roughly one day in three. Go early — clouds build by noon."),

"turnagain-arm": dict(
    name="Turnagain Arm", slug="Turnagain_Arm", country="United States",
    region="Alaska", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Beluga Point", "Beluga_Point_Site"),
                ("Seward Highway", "Seward_Highway"),
                ("Portage Glacier", "Portage_Glacier"),
                ("Cook Inlet", "Cook_Inlet")],
    blurb="A narrow arm of Cook Inlet with a highway pinned between the "
          "water and the cliffs, named by Cook's crew for having to turn "
          "back at the end of it.",
    fact="It has the second-largest tidal range in North America — around "
         "twelve metres — and a bore tide that runs up the arm as a single "
         "wave up to two metres high, at about fifteen knots.",
    tip="Bore tide times are published; the good ones follow a very low "
        "tide by roughly two hours. Watch from Bird Point. Do not walk on "
        "the mud flats — the silt sets around your legs and the tide "
        "returns faster than anyone can dig."),

"chugach-state-park": dict(
    name="Chugach State Park", slug="Chugach_State_Park",
    country="United States", region="Alaska", type="nature", tag="hidden",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Flattop Mountain", "Flattop_Mountain_(Anchorage,_Alaska)"),
                ("Chugach Mountains", "Chugach_Mountains"),
                ("Anchorage", "Anchorage,_Alaska"),
                ("Eagle River", None)],
    blurb="Two thousand square kilometres of mountains, glaciers and "
          "hanging valleys with a trailhead twenty minutes from downtown "
          "Anchorage — one of the largest state parks in the country.",
    fact="Flattop is the most climbed mountain in Alaska, largely because "
         "you can be on its summit within an hour of leaving a city of "
         "290,000 people, with Denali visible on a clear day.",
    tip="Take the Powerline Pass trail instead of Flattop if you want the "
        "valley to yourself. Dall sheep are on the slopes above it most "
        "mornings, and the trail stays gentle for the first six kilometres."),

"matanuska-glacier": dict(
    name="Matanuska Glacier", slug="Matanuska_Glacier",
    country="United States", region="Alaska", type="nature", tag="hidden",
    emoji="🧊", sounds=["mountain-wind.mp3"],
    highlights=[("Glenn Highway", "Glenn_Highway"),
                ("Chugach Mountains", "Chugach_Mountains"),
                ("Matanuska River", "Matanuska_River"),
                ("Palmer", "Palmer,_Alaska")],
    blurb="Forty kilometres of ice ending four kilometres wide beside the "
          "Glenn Highway, the largest glacier in the United States you can "
          "drive to and then walk onto.",
    fact="It has barely retreated in the last century while almost every "
         "other Alaskan glacier has collapsed — the valley behind it feeds "
         "enough snow to keep pace, for now.",
    tip="The ice is on private land and access is ticketed; guided walks "
        "are the only legal way past the moraine and the crevasses are the "
        "reason. Go in the morning before the meltwater channels open up."),

"portage-glacier": dict(
    name="Portage Glacier", slug="Portage_Glacier", country="United States",
    region="Alaska", type="nature", tag="hidden",
    emoji="🧊", sounds=["mountain-wind.mp3"],
    highlights=[("Portage Lake", "Portage_Lake_(Alaska)"),
                ("Whittier", "Whittier,_Alaska"),
                ("Turnagain Arm", "Turnagain_Arm"),
                ("Byron Glacier", None)],
    blurb="A glacier that used to sit at the end of the road and now sits "
          "around a corner of its own lake, out of sight of the visitor "
          "centre built in 1986 specifically to look at it.",
    fact="In 1914 the ice filled the entire valley the lake now occupies. "
         "The lake is the glacier's own retreat, five kilometres of it, "
         "measured in water.",
    tip="Take the boat or walk the Byron Glacier trail next door — twenty "
        "minutes to standing under blue ice, and one of the few places in "
        "Alaska where ice worms are easy to find in the snowfield."),

"worthington-glacier": dict(
    name="Worthington Glacier", slug="Worthington_Glacier",
    country="United States", region="Alaska", type="nature", tag="hidden",
    emoji="🧊", sounds=["mountain-wind.mp3"],
    highlights=[("Thompson Pass", "Thompson_Pass"),
                ("Richardson Highway", "Richardson_Highway"),
                ("Valdez", "Valdez,_Alaska"),
                ("Keystone Canyon", "Keystone_Canyon")],
    blurb="A glacier that comes down almost to the Richardson Highway just "
          "below Thompson Pass, with a paved path to a viewpoint a few "
          "hundred metres from the ice.",
    fact="This is one of the most accessible glaciers in the state and one "
         "of the snowiest places in it — the pass above records winter "
         "totals measured in tens of metres.",
    tip="The moraine trail up the left side gets you level with the "
        "icefall in about forty minutes. Don't go onto the ice: it is "
        "crevassed under the snow and there is no guide service here."),

"prince-william-sound": dict(
    name="Prince William Sound", slug="Prince_William_Sound",
    country="United States", region="Alaska", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Columbia Glacier", "Columbia_Glacier_(Alaska)"),
                ("Valdez", "Valdez,_Alaska"),
                ("Whittier", "Whittier,_Alaska"),
                ("Cordova", "Cordova,_Alaska")],
    blurb="A sound the size of a small country, ringed by the Chugach "
          "Mountains and filled with fjords, tidewater glaciers and islands "
          "that have never had a road on them.",
    fact="The Columbia Glacier has retreated more than twenty kilometres "
         "since 1980 and thinned by half a kilometre in places — one of the "
         "fastest-moving glaciers on earth and one of the fastest shrinking.",
    tip="The state ferry between Whittier and Valdez costs a fraction of a "
        "tour and crosses the same water. Sit outside; the whales don't "
        "announce themselves."),

"kachemak-bay": dict(
    name="Kachemak Bay", slug="Kachemak_Bay", country="United States",
    region="Alaska", type="coastal", tag="hidden",
    emoji="🦦", sounds=["ocean-waves.mp3"],
    highlights=[("Homer", "Homer,_Alaska"),
                ("Homer Spit", "Homer_Spit"),
                ("Halibut Cove", "Halibut_Cove,_Alaska"),
                ("Grewingk Glacier", "Grewingk_Glacier")],
    blurb="A bay off Cook Inlet with a town on one shore and, on the other, "
          "a wall of glaciated mountains with no roads at all — only "
          "boardwalk villages and trailheads reached by skiff.",
    fact="It was Alaska's first state park and remains one of the most "
         "productive cold-water estuaries anywhere, with tides that expose "
         "kilometres of intertidal zone twice a day.",
    tip="The Grewingk Glacier Lake trail from Glacier Spit is flat, about "
        "five kilometres, and ends at a lake with icebergs in it. The water "
        "taxi drops you and returns at an agreed hour — agree carefully."),

"seward-highway": dict(
    name="Seward Highway", slug="Seward_Highway", country="United States",
    region="Alaska", type="nature", tag="hidden",
    emoji="🛣️", sounds=["mountain-wind.mp3"],
    highlights=[("Turnagain Arm", "Turnagain_Arm"),
                ("Beluga Point", "Beluga_Point_Site"),
                ("Anchorage", "Anchorage,_Alaska"),
                ("Seward", "Seward,_Alaska")],
    blurb="Two hundred kilometres from Anchorage to Seward, most of it "
          "carved into the cliff above Turnagain Arm and the rest climbing "
          "through the Kenai Mountains past hanging glaciers.",
    fact="It is a National Scenic Byway, an All-American Road and a Forest "
          "Service Scenic Byway simultaneously — one of very few roads in "
          "the country to hold all three designations.",
    tip="Pull off at every marked viewpoint on the Arm; the tide changes "
        "the view completely in six hours. Dall sheep stand on the rock "
        "directly above the road near Windy Corner and cause the traffic."),

# ============================ INTERIOR ============================
"fairbanks": dict(
    name="Fairbanks", slug="Fairbanks,_Alaska", country="United States",
    region="Alaska", type="city", tag="famous",
    emoji="🌌", sounds=["city-hum.mp3"],
    search_name="Fairbanks Alaska",
    highlights=[("Chena River", "Chena_River"),
                ("University of Alaska Fairbanks", "University_of_Alaska_Fairbanks"),
                ("Pioneer Park", "Pioneer_Park_(Fairbanks,_Alaska)"),
                ("Trans-Alaska Pipeline", "Trans-Alaska_Pipeline_System")],
    blurb="The last real city before the Arctic, a gold camp that stayed, "
          "sitting in a river basin that traps cold air at forty below and "
          "sits directly under the auroral oval.",
    fact="The recorded extremes here span 99 degrees Celsius: −52 °C in "
         "winter and +38 °C in summer. Both were measured at the same "
         "airport.",
    tip="Aurora season is roughly late August to April and the best hours "
        "are the ugly ones, from about eleven to three. Get out of the "
        "river valley — Cleary Summit or Murphy Dome — and let your eyes "
        "adjust for twenty full minutes before you decide nothing is there."),

"north-pole-alaska": dict(
    name="North Pole", slug="North_Pole,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🎅", sounds=["city-hum.mp3"],
    search_name="North Pole Alaska town",
    highlights=[("Santa Claus House", "Santa_Claus_House"),
                ("Fairbanks", "Fairbanks,_Alaska"),
                ("Chena River", "Chena_River"),
                ("Candy Cane Lane", None)],
    blurb="A small town outside Fairbanks, 2,700 km from the actual North "
          "Pole, that renamed itself in 1952 to attract a toy factory. The "
          "factory never came. Everything else did.",
    fact="The streets are called Santa Claus Lane, Kris Kringle Drive and "
         "Snowman Lane, the street lights are candy canes, and the post "
         "office answers hundreds of thousands of letters a year.",
    tip="It is genuinely strange in July, which is the right time to see "
        "it: candy-cane lamp posts in full daylight at midnight, and "
        "nobody around."),

"chena-hot-springs": dict(
    name="Chena Hot Springs", slug="Chena_Hot_Springs,_Alaska",
    country="United States", region="Alaska", type="village", tag="hidden",
    emoji="♨️", sounds=["wilderness.mp3"],
    search_name="Chena Hot Springs Alaska",
    highlights=[("Chena River", "Chena_River"),
                ("Chena River State Recreation Area", "Chena_River_State_Recreation_Area"),
                ("Fairbanks", "Fairbanks,_Alaska"),
                ("Aurora Ice Museum", None)],
    blurb="A hot spring at the end of a hundred-kilometre road out of "
          "Fairbanks, found by gold miners in 1905 and running ever since, "
          "with a rock lake outdoors at 41 °C in the middle of the taiga.",
    fact="The resort runs almost entirely on its own geothermal water, "
          "including the electricity — it holds the record for the lowest "
          "temperature geothermal resource used for commercial power.",
    tip="Sit in the outdoor rock lake in January with the aurora "
        "overhead: that is the whole reason the road exists. Long hair "
        "freezes solid within minutes, which is the local photograph."),

"denali-highway": dict(
    name="Denali Highway", slug="Denali_Highway", country="United States",
    region="Alaska", type="nature", tag="hidden",
    emoji="🚙", sounds=["mountain-wind.mp3"],
    highlights=[("Alaska Range", "Alaska_Range"),
                ("Cantwell", "Cantwell,_Alaska"),
                ("Paxson", "Paxson,_Alaska"),
                ("Susitna River", "Susitna_River")],
    blurb="Two hundred and twenty kilometres of mostly gravel across the "
          "tundra south of the Alaska Range, with no towns, no services for "
          "long stretches and the mountains on the horizon the whole way.",
    fact="Until the Parks Highway opened in 1971 this was the only road to "
         "Denali National Park. Traffic dropped to almost nothing overnight "
         "and it has stayed that way.",
    tip="It closes with the first serious snow and reopens in May. Carry a "
        "full-size spare, and stop at the Maclaren Summit pull-off — the "
        "second-highest highway pass in Alaska and glaciers in view from "
        "the car."),

"dalton-highway": dict(
    name="Dalton Highway", slug="Dalton_Highway", country="United States",
    region="Alaska", type="nature", tag="famous",
    emoji="🛻", sounds=["arctic-wind.mp3"],
    highlights=[("Atigun Pass", "Atigun_Pass"),
                ("Brooks Range", "Brooks_Range"),
                ("Coldfoot", "Coldfoot,_Alaska"),
                ("Yukon River", "Yukon_River"),
                ("Prudhoe Bay", "Prudhoe_Bay,_Alaska")],
    blurb="Six hundred and sixty kilometres of haul road from the Yukon "
          "River to the Arctic Ocean, built in five months in 1974 to "
          "supply the pipeline, and still mostly gravel.",
    fact="There are three fuel stops on the entire route and one of the "
         "gaps between them is 390 km — the longest stretch without "
         "services on any public road in North America.",
    tip="Atigun Pass at 1,444 m is the only road crossing of the Brooks "
        "Range and the treeline is below it: the last spruce on the "
        "highway is marked with a sign, and there is nothing taller than "
        "your knee for the next three hundred kilometres."),

"coldfoot": dict(
    name="Coldfoot", slug="Coldfoot,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🥶", sounds=["arctic-wind.mp3"],
    search_name="Coldfoot Alaska Dalton Highway",
    highlights=[("Atigun Pass", "Atigun_Pass"),
                ("Wiseman", "Wiseman,_Alaska"),
                ("Dalton Highway", "Dalton_Highway"),
                ("Gates of the Arctic National Park",
                 "Gates_of_the_Arctic_National_Park_and_Preserve")],
    blurb="A truck stop at the foot of the Brooks Range with a population "
          "in single figures, a café that never closes and the last fuel "
          "for 390 kilometres in either direction.",
    fact="It recorded −62 °C in January 1989, the coldest temperature ever "
         "measured in the United States outside a research station. The "
         "name comes from gold stampeders who got this far and turned back.",
    tip="Wiseman, twenty kilometres north, is the better stop: a dozen "
        "residents in log cabins from 1908, still on a dirt road, and "
        "people will talk to you if you are not in a hurry."),

"chicken": dict(
    name="Chicken", slug="Chicken,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🐔", sounds=["wilderness.mp3"],
    search_name="Chicken Alaska",
    highlights=[("Taylor Highway", "Taylor_Highway"),
                ("Fortymile River", "Fortymile_River"),
                ("Eagle", "Eagle,_Alaska"),
                ("Top of the World Highway", "Top_of_the_World_Highway")],
    blurb="A gold camp on the Taylor Highway with a summer population of "
          "about a dozen, no running water, no phones, and three "
          "competing businesses in a row.",
    fact="They wanted to name it Ptarmigan, after the bird all around them, "
         "and could not agree on how to spell it. Chicken was close enough "
         "and nobody could get it wrong.",
    tip="The road is closed by snow from roughly October to April, and the "
        "dredge at the edge of town can be toured. Bring cash — there is "
        "no bank and the connection is not reliable."),

"eagle-alaska": dict(
    name="Eagle", slug="Eagle,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🏛️", sounds=["wilderness.mp3"],
    search_name="Eagle Alaska Yukon River",
    highlights=[("Yukon River", "Yukon_River"),
                ("Fort Egbert", "Fort_Egbert"),
                ("Taylor Highway", "Taylor_Highway"),
                ("Yukon–Charley Rivers", "Yukon–Charley_Rivers_National_Preserve")],
    blurb="A Yukon River town of about eighty people at the end of a "
          "seasonal road, with an army post from 1899 still standing and a "
          "courthouse that once served a district the size of Texas.",
    fact="Roald Amundsen walked and sledged 800 km here in 1905 from the "
         "iced-in Gjøa to reach the telegraph line and tell the world he "
         "had made the Northwest Passage — then went back and waited out "
         "the winter.",
    tip="The town runs its own walking tour of the fort buildings, and the "
        "custodians are residents. Ice break-up on the river in early May "
        "is the event of the year and can pile floes three storeys high."),

"yukon-charley": dict(
    name="Yukon–Charley Rivers", slug="Yukon–Charley_Rivers_National_Preserve",
    country="United States", region="Alaska", type="wilderness", tag="hidden",
    emoji="🛶", sounds=["wilderness.mp3"],
    highlights=[("Yukon River", "Yukon_River"),
                ("Charley River", "Charley_River"),
                ("Eagle", "Eagle,_Alaska"),
                ("Circle", "Circle,_Alaska")],
    blurb="Ten thousand square kilometres of the Yukon valley with no road "
          "in it, preserved around a river — the Charley — that runs clear "
          "into a Yukon the colour of milky tea.",
    fact="The Charley's entire watershed lies inside the preserve and was "
         "never glaciated, so plants survive here that were wiped out "
         "everywhere around them during the ice ages.",
    tip="The classic trip is Eagle to Circle by canoe: about 250 km, a "
        "week on the current, with old trapper cabins on the bank. There "
        "is no permit and no ranger — file your plan with somebody."),

# ============================= ARCTIC =============================
"utqiagvik": dict(
    name="Utqiaġvik", slug="Utqiaġvik,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🐻‍❄️", sounds=["arctic-wind.mp3"],
    search_name="Utqiagvik Barrow Alaska",
    highlights=[("Point Barrow", "Point_Barrow"),
                ("Chukchi Sea", "Chukchi_Sea"),
                ("Birnirk site", "Birnirk_site"),
                ("Iñupiat Heritage Center", "Iñupiat_Heritage_Center")],
    blurb="The northernmost town in the United States, on a gravel spit "
          "between two frozen seas, where people have lived continuously "
          "for more than a thousand years and still hunt bowhead whales "
          "from skin boats.",
    fact="The sun sets in mid-November and does not rise again until late "
         "January — around 65 days of night, answered by 80 days in summer "
         "when it never goes down.",
    tip="The whale bone arch on the beach is the photograph everyone "
        "takes; the Heritage Center is the reason to stay a day. Polar "
        "bears come along that beach. Ask locally before walking it."),

"prudhoe-bay": dict(
    name="Prudhoe Bay", slug="Deadhorse,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🛢️", sounds=["arctic-wind.mp3"],
    search_name="Prudhoe Bay Deadhorse Alaska",
    highlights=[("Dalton Highway", "Dalton_Highway"),
                ("Trans-Alaska Pipeline", "Trans-Alaska_Pipeline_System"),
                ("Sagavanirktok River", "Sagavanirktok_River"),
                ("Deadhorse Airport", "Deadhorse_Airport")],
    blurb="The top of the Dalton Highway and the north end of the pipeline: "
          "a settlement called Deadhorse serving the largest oil field in "
          "North America, on flat tundra beside the Arctic Ocean.",
    fact="Almost nobody lives here. The population is thousands of workers "
         "on two-week rotations flying in and out, and a permanent "
         "population you can count on two hands.",
    tip="The last few kilometres to the water cross oil-field property and "
        "you cannot drive them yourself — a security-cleared shuttle is the "
        "only way to touch the Arctic Ocean, and it must be booked ahead."),

"kotzebue": dict(
    name="Kotzebue", slug="Kotzebue,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🌅", sounds=["arctic-wind.mp3"],
    search_name="Kotzebue Alaska",
    highlights=[("Kotzebue Sound", "Kotzebue_Sound"),
                ("Baldwin Peninsula", "Baldwin_Peninsula"),
                ("Noatak River", "Noatak_River"),
                ("Cape Krusenstern National Monument",
                 "Cape_Krusenstern_National_Monument")],
    blurb="An Iñupiaq town of about three thousand on a spit above the "
          "Arctic Circle, the hub for a region the size of Indiana that has "
          "no roads connecting any of it.",
    fact="It has been occupied for at least six hundred years as the "
         "trading crossroads of northwest Alaska, where the coast, three "
         "rivers and the Siberian trade all met.",
    tip="The sun stays up from early June to early August and the whole "
        "town is outdoors at two in the morning. The beach ridges at Cape "
        "Krusenstern record five thousand years of settlement, one ridge "
        "at a time."),

"nome": dict(
    name="Nome", slug="Nome,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🐕", sounds=["arctic-wind.mp3"],
    search_name="Nome Alaska",
    highlights=[("Seward Peninsula", "Seward_Peninsula"),
                ("Norton Sound", "Norton_Sound"),
                ("Council", "Council,_Alaska"),
                ("Iditarod Trail", "Iditarod_Trail")],
    blurb="A gold-rush town on the Bering Sea coast with no road to the "
          "rest of Alaska, three hundred kilometres of road going nowhere "
          "in particular, and a burled arch on Front Street.",
    fact="In 1900 twenty thousand people were camped on this beach panning "
         "gold out of the sand, because the beach itself was the claim and "
         "nobody could stake it.",
    tip="Drive the Council road to the Last Train to Nowhere: three steam "
        "locomotives from 1881 abandoned in the tundra where the railway "
        "stopped. Musk ox are common along all three roads out of town."),

"anaktuvuk-pass": dict(
    name="Anaktuvuk Pass", slug="Anaktuvuk_Pass,_Alaska",
    country="United States", region="Alaska", type="village", tag="hidden",
    emoji="🦌", sounds=["arctic-wind.mp3"],
    highlights=[("Endicott Mountains", "Endicott_Mountains"),
                ("Gates of the Arctic National Park",
                 "Gates_of_the_Arctic_National_Park_and_Preserve"),
                ("John River", "John_River_(Alaska)"),
                ("Nunamiut Museum", None)],
    blurb="The only settlement inside Gates of the Arctic, three hundred "
          "people in a pass through the Brooks Range that the caribou have "
          "used for as long as anyone has counted.",
    fact="The Nunamiut who live here were the last nomadic band in North "
         "America to settle, in the late 1940s. The name means 'place of "
         "caribou droppings', which is a description of the pass.",
    tip="Flights come from Fairbanks and the weather cancels them without "
        "warning. Bring a day more food than your plan needs, and do not "
        "photograph people without asking first."),

"gates-of-the-arctic": dict(
    name="Gates of the Arctic", slug="Gates_of_the_Arctic_National_Park_and_Preserve",
    country="United States", region="Alaska", type="wilderness", tag="hidden",
    emoji="🏔️", sounds=["arctic-wind.mp3"],
    highlights=[("Brooks Range", "Brooks_Range"),
                ("Arrigetch Peaks", "Arrigetch_Peaks"),
                ("Noatak River", "Noatak_River"),
                ("Anaktuvuk Pass", "Anaktuvuk_Pass,_Alaska")],
    blurb="Thirty-four thousand square kilometres of the Brooks Range "
          "entirely above the Arctic Circle, with no roads, no trails, no "
          "campgrounds and no signs anywhere inside it.",
    fact="It is the least visited national park in the United States — "
         "roughly ten thousand people a year, most of whom fly over. "
         "Yosemite gets that many before lunch.",
    tip="The Arrigetch Peaks are the classic destination and the granite "
        "is the reason, but there is no trail to them and the bush flight "
        "lands on a lake. Everything you carry in comes back out with you."),

"arctic-nwr": dict(
    name="Arctic National Wildlife Refuge",
    slug="Arctic_National_Wildlife_Refuge", country="United States",
    region="Alaska", type="wilderness", tag="hidden",
    emoji="🦌", sounds=["arctic-wind.mp3"],
    highlights=[("Brooks Range", "Brooks_Range"),
                ("Kaktovik", "Kaktovik,_Alaska"),
                ("Sheenjek River", "Sheenjek_River"),
                ("Porcupine River", "Porcupine_River")],
    blurb="Eighty thousand square kilometres from the boreal forest over "
          "the Brooks Range to the Arctic Ocean — the only conservation "
          "area in the country that protects a complete arctic-to-subarctic "
          "range of habitat in one piece.",
    fact="The Porcupine caribou herd, close to 200,000 animals, calves on "
         "the coastal plain every June after one of the longest land "
         "migrations of any mammal on earth.",
    tip="Kaktovik, on the coast inside the refuge, is where polar bears "
        "gather in September after the whaling season. Go with a guide; "
        "the bears are on the edge of the village and are not tame."),

"kobuk-valley": dict(
    name="Kobuk Valley", slug="Kobuk_Valley_National_Park",
    country="United States", region="Alaska", type="desert", tag="hidden",
    emoji="🏜️", sounds=["arctic-wind.mp3"],
    highlights=[("Kobuk River", "Kobuk_River"),
                ("Great Kobuk Sand Dunes", None),
                ("Kotzebue", "Kotzebue,_Alaska"),
                ("Noatak River", "Noatak_River")],
    blurb="Sand dunes above the Arctic Circle. Sixty-five square kilometres "
          "of them, drifting up to thirty metres high, in a national park "
          "with no roads, no trails and no facilities of any kind.",
    fact="The dunes are ground rock left by glaciers and blown into place, "
         "and summer sand temperatures reach 38 °C — in a valley where "
         "winter goes to −50 °C.",
    tip="Half a million caribou cross the Kobuk River here twice a year at "
        "Onion Portage, on the same fords they have used for nine thousand "
        "years. Everyone arrives by bush plane from Kotzebue."),

"bering-land-bridge": dict(
    name="Bering Land Bridge", slug="Bering_Land_Bridge_National_Preserve",
    country="United States", region="Alaska", type="wilderness", tag="hidden",
    emoji="🌋", sounds=["arctic-wind.mp3"],
    highlights=[("Seward Peninsula", "Seward_Peninsula"),
                ("Serpentine Hot Springs", None),
                ("Nome", "Nome,_Alaska"),
                ("Imuruk Lake", "Imuruk_Lake")],
    blurb="What is left above water of Beringia, the plain that joined "
          "Alaska to Siberia when the sea was 100 m lower — now a "
          "roadless preserve of tundra, lava flows and hot springs on the "
          "Seward Peninsula.",
    fact="It holds the largest maar lakes on earth: craters blown out where "
         "rising magma hit permafrost, one of them eight kilometres across "
         "and filled with water.",
    tip="Serpentine Hot Springs has a bunkhouse and a soaking tub in the "
        "middle of granite tors, reachable only by bush plane or "
        "snowmachine. It is a healing place for Iñupiaq people — treat it "
        "as one."),

"shishmaref": dict(
    name="Shishmaref", slug="Shishmaref,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🌊", sounds=["arctic-wind.mp3"],
    highlights=[("Sarichef Island", "Sarichef_Island"),
                ("Seward Peninsula", "Seward_Peninsula"),
                ("Bering Land Bridge", "Bering_Land_Bridge_National_Preserve"),
                ("Wales", "Wales,_Alaska")],
    blurb="An Iñupiaq village of about six hundred on a barrier island four "
          "hundred metres wide in the Chukchi Sea, occupied for four "
          "thousand years and now visibly running out of island.",
    fact="The sea ice that used to shield the shore through autumn storms "
         "now forms weeks late. The island has lost tens of metres of "
         "coast, houses have been moved inland, and the village has voted "
         "more than once to relocate entirely.",
    tip="This is not a sightseeing stop; it is a community that has been "
        "photographed a great deal and consulted very little. If you go, "
        "go because you were invited, and buy the carving."),

# ==================== SOUTHEAST / INSIDE PASSAGE ====================
"juneau": dict(
    name="Juneau", slug="Juneau,_Alaska", country="United States",
    region="Alaska", type="city", tag="famous",
    emoji="🏛️", sounds=["city-hum.mp3"],
    search_name="Juneau Alaska",
    highlights=[("Mendenhall Glacier", "Mendenhall_Glacier"),
                ("Mount Roberts", "Mount_Roberts_(Juneau,_Alaska)"),
                ("Alaska State Capitol", "Alaska_State_Capitol"),
                ("Gastineau Channel", "Gastineau_Channel")],
    blurb="A state capital with no road to it, squeezed onto a strip of "
          "shore between a channel and a mountain, with an icefield "
          "starting a few kilometres behind the legislature.",
    fact="It is the only US state capital that borders another country, "
         "and one of only two — with Honolulu — that cannot be driven to. "
         "Legislators fly in for the session.",
    tip="The tram up Mount Roberts is the easy view; the Perseverance "
        "Trail out of downtown is the better one, following a mining road "
        "up a valley to waterfalls with the city out of sight behind you."),

"sitka": dict(
    name="Sitka", slug="Sitka,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🕍", sounds=["ocean-waves.mp3"],
    search_name="Sitka Alaska",
    highlights=[("Sitka National Historical Park", "Sitka_National_Historical_Park"),
                ("St. Michael's Cathedral", "St._Michael's_Cathedral_(Sitka,_Alaska)"),
                ("Mount Edgecumbe", "Mount_Edgecumbe_(Alaska)"),
                ("Castle Hill", "Castle_Hill_(Sitka,_Alaska)")],
    blurb="The capital of Russian America until 1867, on the outer coast "
          "facing the open Pacific, with a dormant volcano across the sound "
          "and totem poles in the rainforest at the edge of town.",
    fact="Alaska was formally handed from Russia to the United States on "
         "Castle Hill here in October 1867. The Tlingit, who had fought the "
         "Russians to a standstill in 1804, were not consulted about either.",
    tip="Walk the totem trail in the National Historical Park at opening "
        "time, in rain, with nobody else on it. That is the version of "
        "Sitka worth having, and it rains about 230 days a year."),

"ketchikan": dict(
    name="Ketchikan", slug="Ketchikan,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    search_name="Ketchikan Alaska",
    highlights=[("Creek Street", None),
                ("Totem Bight State Historical Park", "Totem_Bight_State_Historical_Park"),
                ("Misty Fjords National Monument", "Misty_Fjords_National_Monument"),
                ("Saxman", "Saxman,_Alaska")],
    blurb="A town built on pilings up a hillside above Tongass Narrows, "
          "with a boardwalk street over a salmon creek and the largest "
          "collection of standing totem poles anywhere.",
    fact="It gets around 3.8 m of rain a year and the sign at the dock "
          "measures it in a gauge for arriving passengers. Locals call the "
          "drizzle liquid sunshine and mean it slightly.",
    tip="Creek Street was the red-light district until 1954 and the "
        "buildings are unchanged. Stand on the boardwalk in August and "
        "watch salmon fight up the creek directly underneath you."),

"skagway": dict(
    name="Skagway", slug="Skagway,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🚂", sounds=["mountain-wind.mp3"],
    search_name="Skagway Alaska",
    highlights=[("White Pass", "White_Pass"),
                ("Chilkoot Trail", "Chilkoot_Trail"),
                ("White Pass and Yukon Route", "White_Pass_and_Yukon_Route"),
                ("Dyea", "Dyea,_Alaska")],
    blurb="The gateway to the Klondike: a false-fronted gold-rush town at "
          "the head of a fjord, where a hundred thousand people came ashore "
          "in 1897 to walk over the mountains into Canada.",
    fact="The Mounties turned back anyone at the summit without a ton of "
         "supplies, so stampeders relayed their outfit up the Chilkoot in "
         "thirty or forty trips. The trail is a linear museum of what they "
         "gave up and dropped.",
    tip="Take the railway to the White Pass summit — 900 m of climb in "
        "32 km, built in 1898 — and look down on the old trail. Dyea, the "
        "rival town at the Chilkoot trailhead, is now an empty flat with a "
        "cemetery."),

"haines": dict(
    name="Haines", slug="Haines,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🦅", sounds=["mountain-wind.mp3"],
    search_name="Haines Alaska",
    highlights=[("Chilkat River", "Chilkat_River"),
                ("Alaska Chilkat Bald Eagle Preserve", "Alaska_Chilkat_Bald_Eagle_Preserve"),
                ("Fort William H. Seward", "Fort_William_H._Seward"),
                ("Haines Highway", "Haines_Highway")],
    blurb="Skagway's quieter neighbour twenty-five kilometres down the "
          "fjord, with a parade-ground fort from 1904, a road out to Canada "
          "and a river valley that fills with eagles every autumn.",
    fact="Warm water welling up through the Chilkat gravel keeps a stretch "
         "of river open after everything else freezes, and three to four "
         "thousand bald eagles gather there in November — the largest "
         "concentration on earth.",
    tip="Late October to early December is the eagle window and the pull-"
        "offs on the highway between mileposts 18 and 24 are the whole "
        "show. Bring the longest lens you own and stay in the car."),

"petersburg": dict(
    name="Petersburg", slug="Petersburg,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🇳🇴", sounds=["ocean-waves.mp3"],
    search_name="Petersburg Alaska",
    highlights=[("Frederick Sound", "Frederick_Sound"),
                ("LeConte Glacier", "LeConte_Glacier"),
                ("Wrangell Narrows", "Wrangell_Narrows"),
                ("Kupreanof Island", "Kupreanof_Island")],
    blurb="A Norwegian fishing town at the north end of the Wrangell "
          "Narrows, with rosemaling painted on the buildings, no cruise "
          "dock big enough for the large ships, and a working harbour.",
    fact="LeConte Glacier, just south, is the southernmost tidewater "
         "glacier in the northern hemisphere, and it calves from "
         "underwater — icebergs surface suddenly, which is why boats keep "
         "their distance.",
    tip="The Wrangell Narrows is 34 km of channel with more than sixty "
        "navigation markers; taking the state ferry through it at night is "
        "one of the great small journeys in Alaska."),

"wrangell": dict(
    name="Wrangell", slug="Wrangell,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    search_name="Wrangell Alaska",
    highlights=[("Stikine River", "Stikine_River"),
                ("Petroglyph Beach", None),
                ("Wrangell Island", "Wrangell_Island"),
                ("Anan Creek", None)],
    blurb="A town at the mouth of the Stikine that has been governed by "
          "Tlingit, Russia, Britain and the United States, with prehistoric "
          "carvings on the beach nobody can date.",
    fact="Petroglyph Beach has around forty carvings on the rocks in the "
         "intertidal zone. Nobody knows who made them or when — estimates "
         "run from a few centuries to several thousand years.",
    tip="Go to the beach at low tide, in the morning, with the sun at an "
        "angle: the carvings are almost invisible in flat light and "
        "obvious in raking light."),

"gustavus": dict(
    name="Gustavus", slug="Gustavus,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    search_name="Gustavus Alaska Glacier Bay",
    highlights=[("Glacier Bay National Park", "Glacier_Bay_National_Park_and_Preserve"),
                ("Icy Strait", "Icy_Strait"),
                ("Bartlett Cove", None),
                ("Juneau", "Juneau,_Alaska")],
    blurb="The doorstep of Glacier Bay: five hundred people on a flat "
          "outwash plain with a disproportionately large runway, gravel "
          "roads and no traffic lights.",
    fact="The land here is still rising — freed of the weight of the ice, "
         "the ground lifts several centimetres a year, which is fast enough "
         "that the shoreline moves within a lifetime and docks need "
         "rebuilding.",
    tip="Everyone flies through on the way to the bay. Stay a night: the "
        "beach at Point Gustavus at dusk in July has humpbacks feeding "
        "close in, and no boat between you and them."),

"hyder": dict(
    name="Hyder", slug="Hyder,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🐻", sounds=["wilderness.mp3"],
    search_name="Hyder Alaska",
    highlights=[("Stewart, British Columbia", "Stewart,_British_Columbia"),
                ("Salmon Glacier", None),
                ("Fish Creek", None),
                ("Misty Fjords National Monument", "Misty_Fjords_National_Monument")],
    blurb="The friendliest ghost town in Alaska: about fifty people at the "
          "head of the Portland Canal, reached only by driving through "
          "Canada, with no US customs post on the way in.",
    fact="Hyder runs on Pacific time to match Stewart next door, uses "
         "Canadian currency in most of its businesses, and sends its "
         "children to school across the border.",
    tip="The Fish Creek boardwalk in late summer is one of the most "
        "reliable brown bear viewing sites anywhere, and the road above it "
        "climbs to an overlook of the Salmon Glacier — the largest road-"
        "accessible glacier in the world."),

"glacier-bay": dict(
    name="Glacier Bay", slug="Glacier_Bay_National_Park_and_Preserve",
    country="United States", region="Alaska", type="nature", tag="famous",
    emoji="🧊", sounds=["ocean-waves.mp3"],
    highlights=[("Margerie Glacier", "Margerie_Glacier"),
                ("Mount Fairweather", "Mount_Fairweather"),
                ("Gustavus", "Gustavus,_Alaska"),
                ("Icy Strait", "Icy_Strait")],
    blurb="A hundred-kilometre fjord system where there was solid ice two "
          "hundred and fifty years ago — the fastest documented glacial "
          "retreat anywhere, and a laboratory for what grows back.",
    fact="When Vancouver's expedition passed in 1794 the bay did not "
         "exist: the ice front was at the mouth. By 1879 John Muir found it "
         "had pulled back 65 km. It is now more than 100.",
    tip="You can walk from bare rock to mature rainforest in a few "
        "kilometres and read the retreat as vegetation. Bartlett Cove has "
        "the only road, the only lodge and a full humpback skeleton."),

"mendenhall-glacier": dict(
    name="Mendenhall Glacier", slug="Mendenhall_Glacier",
    country="United States", region="Alaska", type="nature", tag="famous",
    emoji="🧊", sounds=["waterfall.mp3"],
    highlights=[("Nugget Falls", "Nugget_Falls"),
                ("Mendenhall Lake", "Mendenhall_Lake"),
                ("Juneau Icefield", "Juneau_Icefield"),
                ("Juneau", "Juneau,_Alaska")],
    blurb="Twenty kilometres of ice off the Juneau Icefield ending in a "
          "lake nineteen kilometres from the state capital, with a visitor "
          "centre, a bus route and a waterfall beside the face.",
    fact="The glacier has retreated about three kilometres since 1929 and "
         "the lake it left did not exist before then. Forest that was under "
         "the ice for centuries is emerging as bare stumps.",
    tip="Walk the flat trail to the base of Nugget Falls — most visitors "
        "stop at the centre and the last kilometre thins out fast. The ice "
        "caves people photograph are unstable and have killed people."),

"misty-fiords": dict(
    name="Misty Fjords", slug="Misty_Fjords_National_Monument",
    country="United States", region="Alaska", type="nature", tag="hidden",
    emoji="🌫️", sounds=["waterfall.mp3"],
    highlights=[("Behm Canal", "Behm_Canal"),
                ("Ketchikan", "Ketchikan,_Alaska"),
                ("Rudyerd Bay", None),
                ("Tongass National Forest", "Tongass_National_Forest")],
    blurb="Nine thousand square kilometres of granite walls rising nine "
          "hundred metres straight out of saltwater, with waterfalls down "
          "every face and cloud in the tops most days of the year.",
    fact="New Eddystone Rock, a 70 m basalt pillar standing alone in the "
         "middle of Behm Canal, is the neck of a volcano the glaciers "
         "scraped everything else away from.",
    tip="The floatplane from Ketchikan lands on a fjord and shuts the "
        "engine off. Ten minutes of that silence is the point of the trip; "
        "book the flight that includes a water landing, not the flyover."),

"tracy-arm": dict(
    name="Tracy Arm", slug="Tracy_Arm", country="United States",
    region="Alaska", type="coastal", tag="hidden",
    emoji="🧊", sounds=["ocean-waves.mp3"],
    highlights=[("Juneau", "Juneau,_Alaska"),
                ("Endicott Arm", None),
                ("Sawyer Glacier", None),
                ("Tongass National Forest", "Tongass_National_Forest")],
    blurb="A fjord fifty kilometres long and sometimes only a few hundred "
          "metres wide, walls a kilometre high, ending at two tidewater "
          "glaciers with icebergs the whole length of it.",
    fact="The bergs at the mouth are blue because the ice is old and "
         "compressed enough to have squeezed out the air bubbles that make "
         "younger ice look white.",
    tip="Harbour seals haul out on the floes near the glacier face to pup, "
        "and boats are required to keep away from them. The small vessels "
        "get further up the arm than the cruise ships can."),

"tongass": dict(
    name="Tongass National Forest", slug="Tongass_National_Forest",
    country="United States", region="Alaska", type="wilderness", tag="hidden",
    emoji="🌲", sounds=["wilderness.mp3"],
    highlights=[("Admiralty Island", "Admiralty_Island"),
                ("Misty Fjords National Monument", "Misty_Fjords_National_Monument"),
                ("Ketchikan", "Ketchikan,_Alaska"),
                ("Sitka", "Sitka,_Alaska")],
    blurb="Sixty-eight thousand square kilometres of coastal temperate "
          "rainforest across the whole Alaskan panhandle — the largest "
          "national forest in the United States, and most of it islands.",
    fact="Admiralty Island inside it holds around 1,600 brown bears, "
         "roughly one per square mile and more than the whole of the lower "
         "48 states put together. The Tlingit name for it means Fortress "
         "of the Bears.",
    tip="The Forest Service rents about 150 cabins across the forest for "
        "very little, most reached by floatplane or boat. They book out "
        "six months ahead and are the cheapest wilderness in Alaska."),

# ================= SOUTHWEST / ALASKA PENINSULA / ALEUTIANS =================
"kodiak": dict(
    name="Kodiak", slug="Kodiak,_Alaska", country="United States",
    region="Alaska", type="town", tag="famous",
    emoji="🐻", sounds=["ocean-waves.mp3"],
    search_name="Kodiak Alaska",
    highlights=[("Kodiak Island", "Kodiak_Island"),
                ("Kodiak National Wildlife Refuge", "Kodiak_National_Wildlife_Refuge"),
                ("Fort Abercrombie", "Fort_Abercrombie_State_Historical_Park"),
                ("Holy Resurrection Church", "Holy_Resurrection_Church_(Kodiak,_Alaska)")],
    blurb="A fishing port on an island of green treeless hills, founded by "
          "Russian fur traders in 1792 and home to the largest brown bears "
          "on earth.",
    fact="The 1912 Novarupta eruption 160 km away buried the town in half "
         "a metre of ash and turned day to night for sixty hours. The 1964 "
         "tsunami then destroyed the waterfront.",
    tip="Only about 160 km of road exists on an island 160 km long. Drive "
        "to the end of Chiniak Road and the pavement simply stops at a "
        "beach with WWII bunkers in the grass behind it."),

"unalaska": dict(
    name="Unalaska", slug="Unalaska,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    search_name="Unalaska Dutch Harbor Alaska",
    highlights=[("Dutch Harbor", "Dutch_Harbor"),
                ("Church of the Holy Ascension", "Church_of_the_Holy_Ascension"),
                ("Mount Ballyhoo", "Mount_Ballyhoo"),
                ("Aleutian Islands", "Aleutian_Islands")],
    blurb="The busiest fishing port in the United States by volume, on a "
          "treeless volcanic island 1,300 km out along the Aleutian chain, "
          "with a Russian Orthodox cathedral from 1896 above the harbour.",
    fact="It was bombed by Japanese carrier aircraft in June 1942 — one of "
         "the very few places on US soil attacked in the war — and the "
         "hills are still full of concrete bunkers and gun mounts.",
    tip="Walk the switchback road up Mount Ballyhoo through the ruins of "
        "Fort Schwatka, the highest coastal battery ever built by the US "
        "Army. The weather turns every twenty minutes; go anyway."),

"adak": dict(
    name="Adak", slug="Adak,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🌫️", sounds=["mountain-wind.mp3"],
    search_name="Adak Island Alaska",
    highlights=[("Adak Island", "Adak_Island"),
                ("Mount Moffett", "Mount_Moffett"),
                ("Naval Air Facility Adak", "Naval_Air_Facility_Adak"),
                ("Aleutian Islands", "Aleutian_Islands")],
    blurb="The westernmost town in the United States: a decommissioned "
          "naval base for six thousand people now inhabited by fewer than "
          "a hundred, with empty streets, a McDonald's sign and no trees.",
    fact="The handful of conifers planted by servicemen carry a sign "
         "reading 'You are now entering and leaving the Adak National "
         "Forest'. Nothing else taller than a shrub grows on the island.",
    tip="It is one of the hardest places in America to reach — a couple of "
        "flights a week, frequently cancelled for weather. Birders come "
        "anyway, for Asian vagrants that appear nowhere else in the US."),

"king-salmon": dict(
    name="King Salmon", slug="King_Salmon,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🐟", sounds=["wilderness.mp3"],
    search_name="King Salmon Alaska",
    highlights=[("Katmai National Park", "Katmai_National_Park_and_Preserve"),
                ("Naknek River", "Naknek_River"),
                ("Bristol Bay", "Bristol_Bay"),
                ("Naknek", "Naknek,_Alaska")],
    blurb="An old air force station on the Naknek River that is now the "
          "front door to Katmai, with a runway far larger than the "
          "settlement it serves.",
    fact="Bristol Bay next door produces the largest sockeye salmon run in "
         "the world — often more than fifty million fish returning in a few "
         "weeks, which is why the population multiplies every June.",
    tip="Everything to Brooks Camp goes by floatplane from here. Book the "
        "flight before the accommodation; the planes fill first and the "
        "weather cancels a third of them."),

"bethel": dict(
    name="Bethel", slug="Bethel,_Alaska", country="United States",
    region="Alaska", type="town", tag="hidden",
    emoji="🛶", sounds=["wind.mp3"],
    search_name="Bethel Alaska",
    highlights=[("Kuskokwim River", "Kuskokwim_River"),
                ("Yukon–Kuskokwim Delta", "Yukon–Kuskokwim_Delta"),
                ("Yukon Delta National Wildlife Refuge", "Yukon_Delta_National_Wildlife_Refuge"),
                ("Kuskokwim Bay", "Kuskokwim_Bay")],
    blurb="The hub of the Yukon–Kuskokwim Delta, a flat treeless expanse of "
          "tundra and water the size of a small country, with no road to "
          "anywhere else.",
    fact="In winter the frozen Kuskokwim becomes a marked ice road hundreds "
         "of kilometres long, with speed limits and route signs, linking "
         "villages that are otherwise unreachable by land.",
    tip="More than eighty percent of the delta's people are Yup'ik and the "
        "language is spoken daily. Ask before photographing anyone; it is "
        "a working community, not a destination."),

"katmai": dict(
    name="Katmai", slug="Katmai_National_Park_and_Preserve",
    country="United States", region="Alaska", type="nature", tag="famous",
    emoji="🐻", sounds=["waterfall.mp3"],
    highlights=[("Brooks Falls", "Brooks_Falls"),
                ("Valley of Ten Thousand Smokes", "Valley_of_Ten_Thousand_Smokes"),
                ("Mount Katmai", "Mount_Katmai"),
                ("Naknek Lake", "Naknek_Lake")],
    blurb="Nineteen thousand square kilometres of volcanoes, lakes and "
          "salmon streams holding around two thousand brown bears — more "
          "bears than the park has human visitors on most days.",
    fact="The park was created in 1918 not for the bears but for the "
         "volcanic aftermath of Novarupta, the largest eruption of the "
         "twentieth century, which happened six years earlier.",
    tip="Everyone knows the July run at Brooks. September is better: fewer "
        "people, bears fattened and calmer, and the tundra turned red."),

"brooks-falls": dict(
    name="Brooks Falls", slug="Brooks_Falls", country="United States",
    region="Alaska", type="nature", tag="famous",
    emoji="🐟", sounds=["waterfall.mp3"],
    highlights=[("Katmai National Park", "Katmai_National_Park_and_Preserve"),
                ("Naknek Lake", "Naknek_Lake"),
                ("King Salmon", "King_Salmon,_Alaska"),
                ("Valley of Ten Thousand Smokes", "Valley_of_Ten_Thousand_Smokes")],
    blurb="A two-metre step in a short river between two lakes, where "
          "sockeye pile up on their way upstream and brown bears stand in "
          "the lip of the falls catching them out of the air.",
    fact="The live webcams here draw tens of millions of views a year, and "
         "the park runs an online Fat Bear Week vote each autumn on which "
         "bear has best prepared for hibernation.",
    tip="Everyone must sit through bear school on arrival at Brooks Camp. "
        "The platform has a queue system in peak July — an hour on, then "
        "off. Early morning has the shortest wait."),

"valley-ten-thousand-smokes": dict(
    name="Valley of Ten Thousand Smokes", slug="Valley_of_Ten_Thousand_Smokes",
    country="United States", region="Alaska", type="nature", tag="hidden",
    emoji="🌋", sounds=["wind.mp3"],
    highlights=[("Novarupta", "Novarupta"),
                ("Mount Katmai", "Mount_Katmai"),
                ("Katmai National Park", "Katmai_National_Park_and_Preserve"),
                ("Kodiak", "Kodiak,_Alaska")],
    blurb="A hundred square kilometres of ash flow up to two hundred metres "
          "deep, cut by rivers into a pale canyoned desert that looks "
          "nothing like the rest of Alaska.",
    fact="Robert Griggs named it in 1916 for the thousands of steam "
         "fumaroles then venting through the ash. They cooled within a few "
         "decades and the valley is now silent.",
    tip="A single road runs 37 km from Brooks Camp to the overlook, on one "
        "bus a day. Ask to be dropped for the hike down to the Ukak River "
        "and Baked Mountain — almost nobody does it."),

"lake-clark": dict(
    name="Lake Clark", slug="Lake_Clark_National_Park_and_Preserve",
    country="United States", region="Alaska", type="nature", tag="hidden",
    emoji="🏔️", sounds=["wilderness.mp3"],
    highlights=[("Lake Clark", "Lake_Clark_(Alaska)"),
                ("Mount Redoubt", "Mount_Redoubt"),
                ("Port Alsworth", "Port_Alsworth,_Alaska"),
                ("Anchorage", "Anchorage,_Alaska")],
    blurb="Two active volcanoes, a turquoise lake sixty-five kilometres "
          "long and a coast of bear-grazed sedge flats, an hour's flight "
          "from Anchorage and visited by almost nobody.",
    fact="Dick Proenneke built a cabin at Twin Lakes here in 1968 with hand "
         "tools he made himself and lived in it alone for thirty years. The "
         "cabin still stands and can be visited.",
    tip="There are no roads at all. Fly to Silver Salmon Creek or Chinitna "
        "Bay in June and watch brown bears dig clams on the tide flats at "
        "a distance that feels illegal."),

"pribilof-islands": dict(
    name="Pribilof Islands", slug="Pribilof_Islands", country="United States",
    region="Alaska", type="island", tag="hidden",
    emoji="🦭", sounds=["ocean-waves.mp3"],
    highlights=[("Bering Sea", "Bering_Sea"),
                ("St. George", "St._George,_Alaska"),
                ("Aleutian Islands", "Aleutian_Islands"),
                ("Unalaska", "Unalaska,_Alaska")],
    blurb="Four small volcanic islands alone in the middle of the Bering "
          "Sea, fog-bound most of the summer, with cliffs holding around "
          "two million nesting seabirds.",
    fact="Roughly half the world's northern fur seals breed on these "
         "beaches. Russia forcibly resettled Aleut people here in the "
         "1780s to harvest them, and their descendants still live here.",
    tip="St. Paul is easier to reach; St. George has the bigger cliffs and "
        "fewer visitors. Bring wind-proof everything — the fog is not "
        "optional and neither is the wind."),

"aleutian-islands": dict(
    name="Aleutian Islands", slug="Aleutian_Islands", country="United States",
    region="Alaska", type="island", tag="hidden",
    emoji="🌋", sounds=["ocean-waves.mp3"],
    highlights=[("Unalaska", "Unalaska,_Alaska"),
                ("Attu Island", "Attu_Island"),
                ("Adak", "Adak,_Alaska"),
                ("Mount Shishaldin", "Mount_Shishaldin")],
    blurb="A chain of about seventy volcanic islands curving nineteen "
          "hundred kilometres from the Alaska Peninsula towards Kamchatka, "
          "separating the Bering Sea from the Pacific.",
    fact="The chain crosses the 180th meridian, which makes the far western "
         "islands the easternmost land in the United States by longitude — "
         "and the source of endless argument about it.",
    tip="The Alaska Marine Highway ferry runs the chain only a few times a "
        "year, three days each way from Homer to Unalaska. It is the "
        "cheapest and by far the best way to see it."),

# ================== WRANGELL–ST. ELIAS / EASTERN COAST ==================
"wrangell-st-elias": dict(
    name="Wrangell–St. Elias", slug="Wrangell–St._Elias_National_Park_and_Preserve",
    country="United States", region="Alaska", type="wilderness", tag="famous",
    emoji="🏔️", sounds=["mountain-wind.mp3"],
    highlights=[("Mount Saint Elias", "Mount_Saint_Elias"),
                ("Kennecott", "Kennecott,_Alaska"),
                ("Bagley Icefield", "Bagley_Icefield"),
                ("McCarthy", "McCarthy,_Alaska")],
    blurb="The largest national park in the United States — bigger than "
          "Switzerland — where four mountain ranges converge and nine of "
          "the sixteen highest peaks in the country stand.",
    fact="It is six times the size of Yellowstone and has two roads, both "
         "gravel, both dead ends. Most of the interior has never had a "
         "permanent human presence at all.",
    tip="The Nabesna Road on the north side gets a fraction of the traffic "
        "the McCarthy Road does, crosses streams with no bridges, and ends "
        "at a working gold mine."),

"mccarthy": dict(
    name="McCarthy", slug="McCarthy,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🌉", sounds=["wilderness.mp3"],
    search_name="McCarthy Alaska",
    highlights=[("Kennecott", "Kennecott,_Alaska"),
                ("McCarthy Road", "McCarthy_Road"),
                ("Kennicott Glacier", "Kennicott_Glacier"),
                ("Wrangell–St. Elias National Park", "Wrangell–St._Elias_National_Park_and_Preserve")],
    blurb="A village of about thirty people at the end of a hundred-"
          "kilometre gravel road, reached by a footbridge because vehicles "
          "are not allowed across the river.",
    fact="The road follows the bed of the old Copper River railway, and "
         "railroad spikes still work their way up through the gravel and "
         "into tyres. Locals carry two spares as a matter of course.",
    tip="Park at the river, walk the footbridge, and take the shuttle or "
        "walk the last eight kilometres up to Kennecott. In summer the bar "
        "in McCarthy is the whole town's living room."),

"kennecott": dict(
    name="Kennecott", slug="Kennecott,_Alaska", country="United States",
    region="Alaska", type="history", tag="hidden",
    emoji="🏭", sounds=["wind.mp3"],
    search_name="Kennecott mines Alaska",
    highlights=[("Kennicott Glacier", "Kennicott_Glacier"),
                ("McCarthy", "McCarthy,_Alaska"),
                ("Root Glacier", None),
                ("Bonanza Mine", None)],
    blurb="A fourteen-storey red mill building stepping down a mountainside "
          "above a glacier, abandoned in 1938 and left with the furniture "
          "still in the rooms.",
    fact="The ore here ran up to 70 percent copper, the richest ever found. "
         "When the price fell the company walked out — the last train left "
         "in November 1938 and nobody came back for decades.",
    tip="Walk the two kilometres past the mill onto the Root Glacier. The "
        "ice starts as grey rubble and turns white and cracked within "
        "twenty minutes of walking; crampons are rentable in the village."),

"mount-saint-elias": dict(
    name="Mount Saint Elias", slug="Mount_Saint_Elias", country="United States",
    region="Alaska", type="mountain", tag="hidden",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Icy Bay", "Icy_Bay"),
                ("Malaspina Glacier", "Malaspina_Glacier"),
                ("Yakutat", "Yakutat,_Alaska"),
                ("Bagley Icefield", "Bagley_Icefield")],
    blurb="A 5,489 m pyramid rising straight out of the sea on the "
          "Alaska–Yukon border, the second highest peak in both the United "
          "States and Canada, and one of the steepest anywhere.",
    fact="It goes from tidewater to summit in about sixteen kilometres "
         "horizontally — one of the greatest vertical reliefs on earth over "
         "such a short distance. It has been climbed only a few dozen times.",
    tip="It is almost never visible from the ground because the coast is "
        "under cloud. The flight between Yakutat and Cordova on a clear "
        "day passes it side-on and is the view."),

"hubbard-glacier": dict(
    name="Hubbard Glacier", slug="Hubbard_Glacier", country="United States",
    region="Alaska", type="nature", tag="hidden",
    emoji="🧊", sounds=["ocean-waves.mp3"],
    highlights=[("Disenchantment Bay", "Disenchantment_Bay"),
                ("Russell Fiord", "Russell_Fiord"),
                ("Yakutat", "Yakutat,_Alaska"),
                ("Mount Saint Elias", "Mount_Saint_Elias")],
    blurb="The largest tidewater glacier in North America, a hundred and "
          "twenty kilometres long, with a face ten kilometres wide and "
          "ninety metres high — and it is advancing, not retreating.",
    fact="Twice, in 1986 and 2002, it surged across the mouth of Russell "
         "Fiord and dammed it into a lake. Both times the ice dam burst, "
         "the second releasing the largest glacial flood since 1918.",
    tip="The calving here is on a different scale to the small glaciers — "
        "slabs the size of buildings. Ships hold two kilometres off and it "
        "still sounds like artillery."),

"malaspina-glacier": dict(
    name="Malaspina Glacier", slug="Malaspina_Glacier", country="United States",
    region="Alaska", type="nature", tag="hidden",
    emoji="🧊", sounds=["wind.mp3"],
    highlights=[("Yakutat", "Yakutat,_Alaska"),
                ("Mount Saint Elias", "Mount_Saint_Elias"),
                ("Icy Bay", "Icy_Bay"),
                ("Bagley Icefield", "Bagley_Icefield")],
    blurb="A lobe of ice spreading out of the mountains onto the coastal "
          "plain, larger than Rhode Island — the biggest piedmont glacier "
          "in the world.",
    fact="Its folded moraine bands look, from the air, like the growth "
         "rings of an enormous tree. Recent surveys found much of its bed "
         "lies below sea level, which makes it far more fragile than it "
         "looks.",
    tip="It is essentially invisible from the ground — a flat grey plain. "
        "The only way to understand it is from a plane out of Yakutat, and "
        "only on a rare clear day."),

"yakutat": dict(
    name="Yakutat", slug="Yakutat,_Alaska", country="United States",
    region="Alaska", type="village", tag="hidden",
    emoji="🏄", sounds=["ocean-waves.mp3"],
    search_name="Yakutat Alaska",
    highlights=[("Hubbard Glacier", "Hubbard_Glacier"),
                ("Malaspina Glacier", "Malaspina_Glacier"),
                ("Mount Saint Elias", "Mount_Saint_Elias"),
                ("Russell Fiord", "Russell_Fiord")],
    blurb="Six hundred people on an open stretch of Gulf coast between two "
          "enormous glaciers, with a WWII runway, some of the best surf in "
          "Alaska and no road to anywhere.",
    fact="People do surf here, in five-millimetre wetsuits, on beach breaks "
         "with brown bear tracks along the sand behind them. There is a "
         "surf shop, and it is the northernmost in North America.",
    tip="It rains about 3.8 m a year, which is why almost nobody stops. "
        "Come for steelhead in the Situk River, one of the most productive "
        "small rivers on the continent."),

# ========================= KENAI FJORDS =========================
"kenai-fjords": dict(
    name="Kenai Fjords", slug="Kenai_Fjords_National_Park",
    country="United States", region="Alaska", type="nature", tag="famous",
    emoji="🧊", sounds=["ocean-waves.mp3"],
    highlights=[("Harding Icefield", "Harding_Icefield"),
                ("Exit Glacier", "Exit_Glacier"),
                ("Aialik Bay", "Aialik_Bay"),
                ("Seward", "Seward,_Alaska")],
    blurb="A drowned coastline where an icefield on the mountain spine "
          "sends nearly forty glaciers down to the sea, and the valleys "
          "they carved are now fjords full of whales and puffins.",
    fact="The whole coast is sinking: the Kenai Peninsula dropped up to "
         "two metres in the 1964 earthquake, and the fjords themselves are "
         "glacial valleys the ocean has flooded.",
    tip="The day boat to Aialik Bay is the standard trip and it is worth "
        "it. But the hike beside Exit Glacier to the icefield overlook — "
        "1,000 m of climb — shows you the thing that makes all of it."),

"exit-glacier": dict(
    name="Exit Glacier", slug="Exit_Glacier", country="United States",
    region="Alaska", type="nature", tag="famous",
    emoji="🧊", sounds=["waterfall.mp3"],
    highlights=[("Harding Icefield", "Harding_Icefield"),
                ("Kenai Fjords National Park", "Kenai_Fjords_National_Park"),
                ("Seward", "Seward,_Alaska"),
                ("Resurrection Bay", None)],
    blurb="The only part of Kenai Fjords you can drive to: a glacier "
          "spilling off the Harding Icefield to within a short walk of a "
          "car park, and retreating fast enough to watch.",
    fact="The approach road is lined with year markers showing where the "
         "ice stood — 1815, 1899, 1951, 1998. Walking up it is walking "
         "through two centuries of retreat in about fifteen minutes.",
    tip="Take the Harding Icefield Trail even if only partway. At the "
        "'top of the cliffs' marker, four kilometres up, the glacier is "
        "below you and the icefield opens out beyond."),
}


# The one record that was already here. It shipped with an empty blurb, an
# empty fun_fact and a null tip — the three fields the arrival card actually
# reads — so it renders as a name and a photo and nothing else. `rb.fill()`
# only writes fields that are currently empty, so this cannot overwrite
# anything a human wrote later.
FILL = {
    "denali": dict(
        search_name="Denali National Park Alaska",
        blurb="Six million acres with one road into them, a single "
              "mountain that makes its own weather, and a rule that the "
              "wildlife has the right of way over the bus.",
        fact="Denali rises about 5,500 m from base to summit — a greater "
             "vertical rise than Everest, which starts from a plateau "
             "already 5,000 m up. It is also the coldest mountain of its "
             "height anywhere on earth.",
        tip="The mountain is fully visible on roughly one day in three. If "
            "it is out on the morning you arrive, change your plans and go "
            "that day; there is no guarantee of a second chance."),
}

# "Park Road" pointed at Denali_National_Park_and_Preserve — the record's own
# article. A self-referential highlight is worse than a dead one: it spends a
# monument slot re-searching the place the visitor is already standing in.
REPAIR = {
    "denali": [
        ("Denali", "Denali"),
        ("Wonder Lake", "Wonder_Lake_(Alaska)"),
        ("Kantishna", "Kantishna,_Alaska"),
        ("Talkeetna", "Talkeetna,_Alaska")],
}


def repair(locs, got, notes):
    """Replace the highlight lists named in REPAIR, on records already shipped.

    Runs as `rb.run(extra=)`, over the final list, after NEW and FILL. Each
    slug still goes through `rb.link()`, so a repair cannot introduce the thing
    it is fixing: a slug that redirects is stored canonical, a slug with no
    article stays a text chip, and a slug that resolves back to the record
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


def main():
    # usa.json spans 29 states; STATE_BOX is what keeps a Petersburg or a
    # Wrangell from resolving to its lower-48 namesake, and P17 cannot see
    # that difference because both are in the United States. A region with no
    # box is a region the guard silently skips.
    unboxed = sorted({s["region"] for s in NEW.values()} - set(STATE_BOX))
    if unboxed:
        raise SystemExit(f"NEW claims regions with no STATE_BOX row: {unboxed}")

    extra_slugs = [s for pairs in REPAIR.values() for _, s in pairs if s]
    rb.run(REGION, NEW, FILL, extra=repair, extra_slugs=extra_slugs)


if __name__ == "__main__":
    main()
