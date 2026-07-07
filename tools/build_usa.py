#!/usr/bin/env python3
"""
build_usa.py — generator for data/usa.json

Same compact row format as build_europe.py:
    (id, name, state, type, tag, emoji, lat, lng, wiki_slug,
     [ (highlight_name, highlight_wiki_slug), ... ])

All locations are country "United States" (flag 🇺🇸); `state` becomes the
sub-region shown under the name. Authored copy lives in BLURBS keyed by id;
everything else fills live from Wikipedia in the front-end.

Run:  python3 tools/build_usa.py
"""
import json
import os

FLAG = "🇺🇸"
SOUND = {
    "city": "city-hum.mp3", "history": "european-plaza.mp3",
    "coastal": "ocean-waves.mp3", "island": "ocean-waves.mp3",
    "mountain": "mountain-wind.mp3", "nature": "mountain-wind.mp3",
    "desert": "wilderness.mp3", "village": "european-plaza.mp3",
}


def H(*pairs):
    return [{"name": n, "wikipedia_slug": s} for (n, s) in pairs]


DEST = [
 ("new-york-city","New York City","New York","city","famous","🗽",40.7128,-74.0060,"New_York_City", H(
    ("Statue of Liberty","Statue_of_Liberty"),("Times Square","Times_Square"),
    ("Central Park","Central_Park"),("Empire State Building","Empire_State_Building"),
    ("Brooklyn Bridge","Brooklyn_Bridge"),("Metropolitan Museum of Art","Metropolitan_Museum_of_Art"),
    ("9/11 Memorial","National_September_11_Memorial_&_Museum"))),

 ("washington-dc","Washington, D.C.","District of Columbia","history","famous","🏛️",38.9072,-77.0369,"Washington,_D.C.", H(
    ("National Mall","National_Mall"),("The White House","White_House"),
    ("United States Capitol","United_States_Capitol"),("Lincoln Memorial","Lincoln_Memorial"),
    ("Smithsonian Institution","Smithsonian_Institution"))),

 ("boston","Boston","Massachusetts","history","famous","☘️",42.3601,-71.0589,"Boston", H(
    ("Freedom Trail","Freedom_Trail"),("Fenway Park","Fenway_Park"),
    ("Harvard University","Harvard_University"),("Boston Common","Boston_Common"))),

 ("philadelphia","Philadelphia","Pennsylvania","history","famous","🔔",39.9526,-75.1652,"Philadelphia", H(
    ("Liberty Bell","Liberty_Bell"),("Independence Hall","Independence_Hall"),
    ("Philadelphia Museum of Art","Philadelphia_Museum_of_Art"))),

 ("chicago","Chicago","Illinois","city","famous","🌆",41.8781,-87.6298,"Chicago", H(
    ("Millennium Park & Cloud Gate","Cloud_Gate"),("Willis Tower","Willis_Tower"),
    ("Navy Pier","Navy_Pier"),("Art Institute of Chicago","Art_Institute_of_Chicago"),
    ("The Riverwalk","Chicago_Riverwalk"))),

 ("new-orleans","New Orleans","Louisiana","city","famous","🎷",29.9511,-90.0715,"New_Orleans", H(
    ("French Quarter","French_Quarter"),("Bourbon Street","Bourbon_Street"),
    ("Garden District","Garden_District,_New_Orleans"),("Mardi Gras","Mardi_Gras_in_New_Orleans"))),

 ("miami","Miami","Florida","coastal","famous","🌴",25.7617,-80.1918,"Miami", H(
    ("South Beach","South_Beach"),("Art Deco Historic District","Miami_Beach_Architectural_District"),
    ("Wynwood Walls","Wynwood_Walls"),("Little Havana","Little_Havana"))),

 ("savannah","Savannah","Georgia","history","hidden","🌳",32.0809,-81.0912,"Savannah,_Georgia", H(
    ("Historic District","Savannah_Historic_District"),("Forsyth Park","Forsyth_Park"),
    ("River Street","Savannah,_Georgia"))),

 ("charleston","Charleston","South Carolina","history","hidden","🏘️",32.7765,-79.9311,"Charleston,_South_Carolina", H(
    ("The Battery","The_Battery_(Charleston)"),("Rainbow Row","Rainbow_Row"),
    ("Historic District","Charleston_Historic_District"))),

 ("nashville","Nashville","Tennessee","city","famous","🎸",36.1627,-86.7816,"Nashville,_Tennessee", H(
    ("Grand Ole Opry","Grand_Ole_Opry"),("Broadway","Broadway_(Nashville,_Tennessee)"),
    ("Country Music Hall of Fame","Country_Music_Hall_of_Fame_and_Museum"))),

 ("austin","Austin","Texas","city","hidden","🎶",30.2672,-97.7431,"Austin,_Texas", H(
    ("Texas State Capitol","Texas_State_Capitol"),("South Congress","South_Congress"),
    ("Lady Bird Lake","Lady_Bird_Lake"))),

 ("san-antonio","San Antonio","Texas","history","famous","🤠",29.4241,-98.4936,"San_Antonio", H(
    ("The Alamo","Alamo_Mission_in_San_Antonio"),("River Walk","San_Antonio_River_Walk"),
    ("San Antonio Missions","San_Antonio_Missions_National_Historical_Park"))),

 ("las-vegas","Las Vegas","Nevada","city","famous","🎰",36.1699,-115.1398,"Las_Vegas", H(
    ("The Strip","Las_Vegas_Strip"),("Fremont Street","Fremont_Street_Experience"),
    ("Bellagio Fountains","Fountains_of_Bellagio"))),

 ("los-angeles","Los Angeles","California","city","famous","🎬",34.0522,-118.2437,"Los_Angeles", H(
    ("Hollywood Sign","Hollywood_Sign"),("Griffith Observatory","Griffith_Observatory"),
    ("Santa Monica Pier","Santa_Monica_Pier"),("Getty Center","Getty_Center"),
    ("Walk of Fame","Hollywood_Walk_of_Fame"))),

 ("san-francisco","San Francisco","California","city","famous","🌉",37.7749,-122.4194,"San_Francisco", H(
    ("Golden Gate Bridge","Golden_Gate_Bridge"),("Alcatraz Island","Alcatraz_Island"),
    ("Fisherman's Wharf","Fisherman's_Wharf,_San_Francisco"),("Lombard Street","Lombard_Street_(San_Francisco)"),
    ("Cable Cars","San_Francisco_cable_car_system"))),

 ("san-diego","San Diego","California","coastal","famous","🐼",32.7157,-117.1611,"San_Diego", H(
    ("Balboa Park","Balboa_Park_(San_Diego)"),("San Diego Zoo","San_Diego_Zoo"),
    ("La Jolla Cove","La_Jolla"),("USS Midway Museum","USS_Midway_Museum"))),

 ("seattle","Seattle","Washington","city","famous","☕",47.6062,-122.3321,"Seattle", H(
    ("Space Needle","Space_Needle"),("Pike Place Market","Pike_Place_Market"),
    ("Chihuly Garden and Glass","Chihuly_Garden_and_Glass"),("Mount Rainier views","Mount_Rainier"))),

 ("portland-or","Portland","Oregon","city","hidden","🌹",45.5152,-122.6784,"Portland,_Oregon", H(
    ("Powell's City of Books","Powell's_Books"),("Washington Park","Washington_Park_(Portland,_Oregon)"),
    ("Columbia River Gorge","Columbia_River_Gorge"))),

 ("denver","Denver","Colorado","city","hidden","🏔️",39.7392,-104.9903,"Denver", H(
    ("Red Rocks Amphitheatre","Red_Rocks_Amphitheatre"),("Larimer Square","Larimer_Square"),
    ("Rocky Mountain gateway","Rocky_Mountains"))),

 ("santa-fe","Santa Fe","New Mexico","history","hidden","🎨",35.6870,-105.9378,"Santa_Fe,_New_Mexico", H(
    ("The Plaza","Santa_Fe_Plaza"),("Georgia O'Keeffe Museum","Georgia_O'Keeffe_Museum"),
    ("Canyon Road","Canyon_Road"))),

 ("honolulu","Honolulu (Oʻahu)","Hawaii","island","famous","🌺",21.3069,-157.8583,"Honolulu", H(
    ("Waikiki Beach","Waikiki"),("Pearl Harbor","Pearl_Harbor"),
    ("Diamond Head","Diamond_Head,_Hawaii"),("Hanauma Bay","Hanauma_Bay"))),

 ("grand-canyon","Grand Canyon","Arizona","nature","famous","🏜️",36.1069,-112.1129,"Grand_Canyon", H(
    ("South Rim","Grand_Canyon_National_Park"),("Colorado River","Colorado_River"),
    ("Havasu Falls","Havasu_Falls"),("Desert View Watchtower","Desert_View_Watchtower"))),

 ("yellowstone","Yellowstone","Wyoming","nature","famous","♨️",44.4280,-110.5885,"Yellowstone_National_Park", H(
    ("Old Faithful","Old_Faithful"),("Grand Prismatic Spring","Grand_Prismatic_Spring"),
    ("Grand Canyon of the Yellowstone","Grand_Canyon_of_the_Yellowstone"),("Mammoth Hot Springs","Mammoth_Hot_Springs"))),

 ("yosemite","Yosemite","California","nature","famous","🏞️",37.8651,-119.5383,"Yosemite_National_Park", H(
    ("El Capitan","El_Capitan"),("Half Dome","Half_Dome"),
    ("Yosemite Falls","Yosemite_Falls"),("Glacier Point","Glacier_Point"),("Mariposa Grove","Mariposa_Grove"))),

 ("zion","Zion","Utah","nature","famous","🧗",37.2982,-113.0263,"Zion_National_Park", H(
    ("The Narrows","The_Narrows_(Zion_National_Park)"),("Angels Landing","Angels_Landing"),
    ("Emerald Pools","Zion_National_Park"))),

 ("bryce-canyon","Bryce Canyon","Utah","nature","famous","🪨",37.5930,-112.1871,"Bryce_Canyon_National_Park", H(
    ("The Hoodoos","Hoodoo_(geology)"),("Bryce Amphitheater","Bryce_Canyon_National_Park"),
    ("Sunrise Point","Bryce_Canyon_National_Park"))),

 ("arches","Arches","Utah","nature","famous","🌉",38.7331,-109.5925,"Arches_National_Park", H(
    ("Delicate Arch","Delicate_Arch"),("Landscape Arch","Landscape_Arch"),
    ("Double Arch","Double_Arch_(Arches_National_Park)"))),

 ("grand-teton","Grand Teton","Wyoming","mountain","hidden","🏔️",43.7904,-110.6818,"Grand_Teton_National_Park", H(
    ("The Teton Range","Teton_Range"),("Jenny Lake","Jenny_Lake"),("Snake River","Snake_River"))),

 ("glacier-np","Glacier National Park","Montana","nature","hidden","🏔️",48.7596,-113.7870,"Glacier_National_Park_(U.S.)", H(
    ("Going-to-the-Sun Road","Going-to-the-Sun_Road"),("Lake McDonald","Lake_McDonald"),
    ("Logan Pass","Logan_Pass"))),

 ("rocky-mountain-np","Rocky Mountain National Park","Colorado","mountain","hidden","⛰️",40.3428,-105.6836,"Rocky_Mountain_National_Park", H(
    ("Trail Ridge Road","Trail_Ridge_Road"),("Bear Lake","Bear_Lake_(Colorado)"),
    ("Longs Peak","Longs_Peak"))),

 ("great-smoky-mountains","Great Smoky Mountains","Tennessee","nature","famous","🌫️",35.6118,-83.4895,"Great_Smoky_Mountains_National_Park", H(
    ("Clingmans Dome","Clingmans_Dome"),("Cades Cove","Cades_Cove"),
    ("Newfound Gap","Newfound_Gap"))),

 ("acadia","Acadia","Maine","coastal","hidden","🦞",44.3386,-68.2733,"Acadia_National_Park", H(
    ("Cadillac Mountain","Cadillac_Mountain"),("Bar Harbor","Bar_Harbor,_Maine"),
    ("Jordan Pond","Jordan_Pond"))),

 ("everglades","Everglades","Florida","nature","hidden","🐊",25.2866,-80.8987,"Everglades_National_Park", H(
    ("The Wetlands","Everglades"),("Anhinga Trail","Everglades_National_Park"),
    ("Ten Thousand Islands","Ten_Thousand_Islands"))),

 ("sequoia","Sequoia & Kings Canyon","California","nature","hidden","🌲",36.4864,-118.5658,"Sequoia_National_Park", H(
    ("General Sherman Tree","General_Sherman_(tree)"),("Giant Forest","Giant_Forest"),
    ("Moro Rock","Moro_Rock"))),

 ("death-valley","Death Valley","California","desert","hidden","🏜️",36.5054,-117.0794,"Death_Valley_National_Park", H(
    ("Badwater Basin","Badwater_Basin"),("Zabriskie Point","Zabriskie_Point"),
    ("Mesquite Flat Dunes","Death_Valley_National_Park"))),

 ("joshua-tree","Joshua Tree","California","desert","famous","🌵",33.8734,-115.9010,"Joshua_Tree_National_Park", H(
    ("Joshua Trees","Yucca_brevifolia"),("Hidden Valley","Joshua_Tree_National_Park"),
    ("Keys View","Joshua_Tree_National_Park"))),

 ("olympic-np","Olympic National Park","Washington","nature","hidden","🌲",47.8021,-123.6044,"Olympic_National_Park", H(
    ("Hoh Rain Forest","Hoh_Rainforest"),("Hurricane Ridge","Hurricane_Ridge"),
    ("Ruby Beach","Ruby_Beach"))),

 ("mount-rainier","Mount Rainier","Washington","mountain","famous","🗻",46.8523,-121.7603,"Mount_Rainier_National_Park", H(
    ("Paradise","Paradise,_Washington"),("Sunrise","Sunrise,_Washington"),
    ("Mount Rainier","Mount_Rainier"))),

 ("hawaii-volcanoes","Hawaiʻi Volcanoes","Hawaii","island","famous","🌋",19.4194,-155.2885,"Hawaii_Volcanoes_National_Park", H(
    ("Kīlauea","Kīlauea"),("Mauna Loa","Mauna_Loa"),
    ("Chain of Craters Road","Hawaii_Volcanoes_National_Park"))),

 ("denali","Denali","Alaska","mountain","hidden","🐻",63.0692,-151.0070,"Denali_National_Park_and_Preserve", H(
    ("Denali (Mt. McKinley)","Denali"),("Wonder Lake","Wonder_Lake_(Alaska)"),
    ("Park Road","Denali_National_Park_and_Preserve"))),

 ("monument-valley","Monument Valley","Arizona","desert","famous","🏜️",36.9980,-110.0985,"Monument_Valley", H(
    ("The Mittens","Monument_Valley"),("Navajo Tribal Park","Navajo_Nation"),
    ("Forrest Gump Point","Monument_Valley"))),

 ("antelope-canyon","Antelope Canyon","Arizona","desert","famous","🌀",36.8619,-111.3743,"Antelope_Canyon", H(
    ("Upper Antelope Canyon","Antelope_Canyon"),("Horseshoe Bend","Horseshoe_Bend_(Arizona)"),
    ("Lake Powell","Lake_Powell"))),

 ("sedona","Sedona","Arizona","desert","famous","🧡",34.8697,-111.7610,"Sedona,_Arizona", H(
    ("Cathedral Rock","Cathedral_Rock"),("Red Rock State Park","Red_Rock_State_Park"),
    ("Oak Creek Canyon","Oak_Creek_Canyon"))),

 ("mount-rushmore","Mount Rushmore","South Dakota","history","famous","🗿",43.8791,-103.4591,"Mount_Rushmore", H(
    ("The Presidents","Mount_Rushmore"),("Black Hills","Black_Hills"),
    ("Badlands National Park","Badlands_National_Park"))),

 ("lake-tahoe","Lake Tahoe","California","nature","famous","💎",39.0968,-120.0324,"Lake_Tahoe", H(
    ("Emerald Bay","Emerald_Bay_State_Park"),("Sand Harbor","Lake_Tahoe_Nevada_State_Park"),
    ("Heavenly","Heavenly_Mountain_Resort"))),

 ("big-sur","Big Sur","California","coastal","hidden","🌊",36.2704,-121.8081,"Big_Sur", H(
    ("Bixby Creek Bridge","Bixby_Creek_Bridge"),("McWay Falls","McWay_Falls"),
    ("Pfeiffer Beach","Big_Sur"))),

 ("maui","Maui","Hawaii","island","famous","🏝️",20.7984,-156.3319,"Maui", H(
    ("Road to Hana","Hana_Highway"),("Haleakalā","Haleakalā"),
    ("Lahaina","Lahaina,_Hawaii"),("Wailea Beach","Wailea,_Hawaii"))),

 ("kauai","Kauaʻi","Hawaii","island","hidden","🌈",22.0964,-159.5261,"Kauai", H(
    ("Nā Pali Coast","Na_Pali_Coast_State_Park"),("Waimea Canyon","Waimea_Canyon_State_Park"),
    ("Hanalei Bay","Hanalei_Bay"))),

 ("key-west","Key West","Florida","island","hidden","🐚",24.5551,-81.7800,"Key_West", H(
    ("Duval Street","Duval_Street"),("Southernmost Point","Southernmost_point_of_the_continental_United_States"),
    ("Ernest Hemingway House","Ernest_Hemingway_House"),("Mallory Square","Mallory_Square"))),

 ("outer-banks","Outer Banks","North Carolina","coastal","hidden","🪁",35.5582,-75.4665,"Outer_Banks", H(
    ("Cape Hatteras Lighthouse","Cape_Hatteras_Lighthouse"),("Wright Brothers Memorial","Wright_Brothers_National_Memorial"),
    ("Jockey's Ridge","Jockey's_Ridge_State_Park"))),
]

BLURBS = {
 "new-york-city": {
   "blurb": "The city that never sleeps packs eight million stories into five boroughs of skyscrapers, neighbourhoods, and nonstop energy. From the bright chaos of Times Square to the green calm of Central Park, NYC is the world in one place.",
   "fun_fact": "The Statue of Liberty was a gift from France in 1886 — and her full copper skin is only about 2.4 mm thick, roughly the width of two stacked pennies."},
 "washington-dc": {
   "blurb": "The capital of the United States is a city of monuments, marble, and free museums. The National Mall lines up the Capitol, the Washington Monument, and the Lincoln Memorial in one grand sweep of history.",
   "fun_fact": "By a 1910 law, no building in Washington, D.C. may rise much above the width of its adjacent street — which is why the city has almost no skyscrapers."},
 "chicago": {
   "blurb": "Birthplace of the skyscraper, Chicago lines a Great Lake with bold architecture, deep-dish pizza, and a riverfront made for walking. Cloud Gate's mirrored curve has become the city's signature reflection.",
   "fun_fact": "Chicago reversed the flow of its own river in 1900 — an engineering feat that sent the water away from Lake Michigan instead of into it."},
 "san-francisco": {
   "blurb": "Famous for fog, hills, and the Golden Gate Bridge, San Francisco is a compact city of cable cars, painted Victorians, and Pacific views. Alcatraz sits offshore as a reminder of its wilder past.",
   "fun_fact": "The Golden Gate Bridge is painted 'International Orange', and a crew repaints it continuously — the job genuinely never ends."},
 "los-angeles": {
   "blurb": "Sprawling under near-permanent sunshine, Los Angeles is the home of Hollywood, Pacific beaches, and endless reinvention. The Hollywood Sign and Griffith Observatory crown the hills above the city.",
   "fun_fact": "The Hollywood Sign originally read 'HOLLYWOODLAND' and was just a 1923 real-estate advertisement meant to last only 18 months."},
 "new-orleans": {
   "blurb": "The birthplace of jazz, New Orleans is a gumbo of French, Spanish, Creole, and Caribbean cultures. The French Quarter's wrought-iron balconies and brass bands give the city a rhythm all its own.",
   "fun_fact": "New Orleans is built largely below sea level, so the dead are buried in above-ground tombs — earning its cemeteries the nickname 'Cities of the Dead'."},
 "las-vegas": {
   "blurb": "Rising straight out of the Mojave Desert, Las Vegas is a neon spectacle of casinos, shows, and replica wonders of the world. The Strip glows so brightly it's visible from space.",
   "fun_fact": "There are no clocks and few windows on most Vegas casino floors by design — to keep you happily unaware of how much time has passed."},
 "seattle": {
   "blurb": "Wedged between Puget Sound and the Cascade Mountains, Seattle gave the world grunge, global coffee culture, and the Space Needle. On clear days, Mount Rainier floats on the horizon.",
   "fun_fact": "Pike Place Market is home to the original Starbucks (1971) — and to fishmongers who famously throw customers' fish across the counter."},
 "grand-canyon": {
   "blurb": "Carved by the Colorado River over millions of years, the Grand Canyon is a mile deep and up to 18 miles wide — a chasm so vast it exposes two billion years of Earth's history in its walls.",
   "fun_fact": "The Grand Canyon is so large it creates its own weather, and temperatures at the bottom can be over 11°C warmer than at the rim."},
 "yellowstone": {
   "blurb": "The world's first national park sits atop a supervolcano, fuelling half of all the geysers on Earth. Bison, bears, and wolves roam its forests, canyons, and steaming geothermal basins.",
   "fun_fact": "Old Faithful is so reliable it can be predicted within about 10 minutes — it erupts roughly 17 times a day, shooting water over 30 metres high."},
 "yosemite": {
   "blurb": "Glacier-carved granite cliffs, giant sequoias, and thundering waterfalls make Yosemite a cathedral of the American wilderness. El Capitan and Half Dome are legends among climbers worldwide.",
   "fun_fact": "Yosemite Falls is North America's tallest waterfall at 739 metres — yet it can run completely dry by late summer."},
 "zion": {
   "blurb": "Towering red and cream sandstone cliffs hem in a lush canyon carved by the Virgin River. Zion's trails range from gentle riverside strolls to the knife-edge scramble up Angels Landing.",
   "fun_fact": "The Narrows hike is done mostly IN the river itself — for much of it, the canyon walls are too close to walk anywhere but the water."},
 "great-smoky-mountains": {
   "blurb": "The most-visited national park in the U.S. drapes the Appalachians in mist and old-growth forest. Its name comes from the natural blue haze that rises from the trees.",
   "fun_fact": "The Smokies' famous 'smoke' is actually fog produced by the forest — the trees release tiny organic compounds that scatter blue light."},
 "mount-rushmore": {
   "blurb": "Carved into a granite face in the Black Hills, the 18-metre heads of four U.S. presidents took 14 years and some 400 workers to complete. It remains one of America's most recognisable monuments.",
   "fun_fact": "Not a single worker died during the dangerous 14-year carving of Mount Rushmore, despite the heavy use of dynamite."},
 "maui": {
   "blurb": "Hawaiʻi's 'Valley Isle' pairs the switchbacking Road to Hana with the volcanic summit of Haleakalā, where you can watch the sunrise above the clouds. Below, golden beaches ring turquoise water.",
   "fun_fact": "From the seafloor to its summit, the Hawaiian volcano Mauna Kea is taller than Mount Everest — and you can watch sunrise above the clouds atop Maui's Haleakalā."},
 "san-antonio": {
   "blurb": "Anchored by the Alamo and threaded by its lively River Walk, San Antonio blends Texan and Mexican heritage. Its Spanish colonial missions form a UNESCO World Heritage Site.",
   "fun_fact": "'Remember the Alamo!' became a U.S. rallying cry after the 1836 siege — the mission is now Texas's most-visited landmark."},
}


def build():
    out = []
    seen = set()
    for (id_, name, state, type_, tag, emoji, lat, lng, slug, highlights) in DEST:
        assert id_ not in seen, f"duplicate id: {id_}"
        seen.add(id_)
        rec = {
            "id": id_, "name": name, "country": "United States", "country_flag": FLAG,
            "region": state, "type": type_, "tag": tag, "emoji": emoji,
            "coordinates": {"lat": lat, "lng": lng},
            "street_view": {"lat": lat, "lng": lng, "heading": 0, "pitch": 0, "fov": 90},
            "wikipedia_slug": slug,
            "sounds": [SOUND.get(type_, "city-hum.mp3")],
            "highlights": highlights,
            "blurb": BLURBS.get(id_, {}).get("blurb", ""),
            "fun_fact": BLURBS.get(id_, {}).get("fun_fact", ""),
            "hidden_gem_tip": BLURBS.get(id_, {}).get("hidden_gem_tip"),
        }
        out.append(rec)

    doc = {"country": "United States", "continent": "North America", "code": "US", "locations": out}
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "..", "data", "usa.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    hl = sum(len(r["highlights"]) for r in out)
    authored = sum(1 for r in out if r["blurb"])
    print(f"✓ wrote {len(out)} destinations, {hl} highlights "
          f"({authored} with authored copy) -> {os.path.normpath(dest)}")


if __name__ == "__main__":
    build()
