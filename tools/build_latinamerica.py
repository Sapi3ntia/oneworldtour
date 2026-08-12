#!/usr/bin/env python3
"""
build_latinamerica.py — the South America batch (2026-08).

WHAT WAS WRONG
    `latinamerica.json` held 30 places and 21 of them were skeletons — empty
    `blurb`, empty `fun_fact`, empty `highlights`, null `hidden_gem_tip` — the
    same state China and Southeast Asia were in before their batches. Empty
    highlights is not just thin prose: `enrich_monuments.py` spends highlights
    as its search terms, so a place with none can never earn a monument tab,
    however famous it is. Buenos Aires had nothing to search.

    And South America was half a continent. **Ecuador, Venezuela, Guyana and
    Suriname had no places at all**, and Chile had none you could walk — only
    Rapa Nui in `ancient.json` and four telescopes in `observatory.json`, none
    of them a street. Brazil, a country of 8.5 million km², had Rio.

WHAT THIS DOES
    Adds the new places and fills the skeletons in one pass. Editorial choice
    is ours — which town, which landmark, what is worth saying — but every
    **coordinate comes from Wikidata P625** and every **slug is resolved live**
    and stored as the article's canonical title, per README "Filling a region
    out". Nothing here is recalled from memory except the prose.

    Re-runnable and additive: a place that already exists keeps every field it
    already has (and always keeps `walk`/`webcam`/`window`/`monuments` — those
    are the scene pipeline's, not ours). Only empty fields get filled.

Run:  python3 tools/build_latinamerica.py            # report only
      python3 tools/build_latinamerica.py --apply
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wiki import Resolver, haversine

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "data" / "latinamerica.json"

# How far a record may sit from its own article's P625 before we want a human
# to look. An `area` type legitimately sits far from its centroid point.
FAR_KM = 60.0
AREA_TYPES = {"nature", "desert", "island", "mountain"}

# ---------------------------------------------------------------------------
# THE CURATED CONTENT.
#
# highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, a
# dish, a dance, an era or a festival. That rule was learned the expensive way
# on the China batch (see enrich_monuments.NOT_A_MONUMENT) and applied here
# before the fact: no "carnival", no "tango", no "ceviche", no "Inca Empire".
# Each one is a thing that stands somewhere, so a video of it can exist.
#
# A `None` slug is deliberate: the UI renders highlights as text chips, so a
# name with no link costs nothing and a dead link is rot.
# ---------------------------------------------------------------------------
NEW = {
# ============================== ECUADOR ==============================
"quito": dict(
    name="Quito", slug="Quito", country="Ecuador", region="Pichincha",
    type="city", tag="famous", emoji="⛪", sounds=["city-hum.mp3"],
    highlights=[("Plaza Grande", "Plaza_de_la_Independencia"),
                ("Basílica del Voto Nacional", "Basílica_del_Voto_Nacional"),
                ("La Compañía de Jesús", "Church_of_La_Compañía,_Quito"),
                ("El Panecillo", "El_Panecillo"),
                ("TelefériQo", "TelefériQo")],
    blurb="Ecuador's capital runs north–south along a narrow Andean valley at "
          "2,850 m, hemmed in by the Pichincha volcano on one side and a line "
          "of peaks on the other. Its colonial centre is the largest and least "
          "altered in the Americas — 320 hectares of cloisters, courtyards and "
          "gilt interiors that were never pulled down and rebuilt.",
    fact="Quito and Kraków were the first two cities ever inscribed on the "
         "UNESCO World Heritage list, in 1978.",
    tip="Ride the TelefériQo up Pichincha in the morning — by early afternoon "
        "the cloud closes over the ridge and the whole valley disappears."),
"guayaquil": dict(
    name="Guayaquil", slug="Guayaquil", country="Ecuador", region="Guayas",
    type="city", tag="famous", emoji="🚢", sounds=["city-hum.mp3"],
    highlights=[("Malecón 2000", "Malecón_Simón_Bolívar"),
                ("Las Peñas", None),
                ("Parque Seminario", None),
                ("Guayas River", "Guayas_River")],
    blurb="Ecuador's largest city and its port, 100 km up a tidal river from "
          "the Pacific — hotter, flatter and blunter than Quito, and the place "
          "most Ecuadorean trade actually passes through. The riverfront was "
          "rebuilt end to end as a 2.5 km public promenade in the late 1990s.",
    fact="Parque Seminario in the middle of downtown is full of wild land "
         "iguanas, up to a metre long, that come down from the trees to be fed.",
    tip="Climb the 444 steps of Las Peñas at dusk — the painted houses on the "
        "way up are still lived in, and the lighthouse at the top looks back "
        "down the whole river."),
"cuenca": dict(
    name="Cuenca", slug="Cuenca,_Ecuador", country="Ecuador", region="Azuay",
    type="history", tag="famous", emoji="🏛️", sounds=["european-plaza.mp3"],
    highlights=[("New Cathedral", "New_Cathedral_of_Cuenca"),
                ("Parque Calderón", None),
                ("Pumapungo", "Pumapungo_Museum"),
                ("Tomebamba River", "Tomebamba_River")],
    blurb="A colonial city of blue-domed churches and cobbled streets at "
          "2,560 m, built on the ruins of the Inca city of Tomebamba and laid "
          "out on the grid the Spanish crown specified in 1557. Four rivers "
          "run through it; the Tomebamba's bank is the city's long green edge.",
    fact="The Panama hat is Ecuadorean, and most of them are woven around "
         "Cuenca — the name stuck because they were shipped out through Panama.",
    tip="Walk the Barranco steps down to the Tomebamba in the late afternoon, "
        "when the old riverside houses catch the light from below."),
"otavalo": dict(
    name="Otavalo", slug="Otavalo_(city)", country="Ecuador", region="Imbabura",
    type="village", tag="hidden", emoji="🧶", sounds=["plaza.mp3"],
    highlights=[("Plaza de los Ponchos", None),
                ("Peguche Waterfall", None),
                ("Cuicocha", "Cuicocha"),
                ("Imbabura", "Imbabura")],
    blurb="A highland market town between two volcanoes, and home to the "
          "Otavalo weavers whose textiles have been traded across the Andes "
          "since long before the Spanish arrived. The Saturday market spills "
          "out of the Plaza de los Ponchos into most of the surrounding grid.",
    fact="Otavaleño traders sell their weaving worldwide and traditionally "
         "keep the same dress at home — white trousers, a dark poncho, and a "
         "single long braid for the men.",
    tip="Get to the animal market on the edge of town before 8am on a "
        "Saturday; it is over by mid-morning and it is where the town actually "
        "does business."),
"banos": dict(
    name="Baños de Agua Santa", slug="Baños_de_Agua_Santa", country="Ecuador",
    region="Tungurahua", type="nature", tag="famous", emoji="♨️",
    sounds=["waterfall.mp3"],
    highlights=[("Pailón del Diablo", "Pailón_del_Diablo"),
                ("Casa del Árbol", None),
                ("Tungurahua", "Tungurahua"),
                ("Río Verde", None)],
    blurb="A small spa town wedged in a gorge below the Tungurahua volcano, "
          "where the Andes fall away toward the Amazon basin. Hot springs at "
          "one end, a road of waterfalls at the other, and a reputation as "
          "Ecuador's adventure-sports town that it has fully earned.",
    fact="Tungurahua erupted on and off from 1999 to 2016 and the town was "
         "evacuated more than once; residents kept moving back, and the "
         "eruptions became a tourist attraction in their own right.",
    tip="Walk or cycle the Ruta de las Cascadas down toward Río Verde — it is "
        "downhill nearly the whole way, and you can put the bike on a pickup "
        "for the ride back."),
"cotopaxi": dict(
    name="Cotopaxi", slug="Cotopaxi", country="Ecuador", region="Cotopaxi",
    type="mountain", tag="famous", emoji="🌋", sounds=["mountain-wind.mp3"],
    highlights=[("Cotopaxi National Park", "Cotopaxi_National_Park"),
                ("Limpiopungo", None),
                ("José Rivas Refuge", None)],
    blurb="An almost perfectly symmetrical glaciated cone rising to 5,897 m an "
          "hour south of Quito — one of the highest active volcanoes on Earth, "
          "and visible from the capital on a clear morning. The páramo "
          "grassland at its foot is wild horse country.",
    fact="Cotopaxi's summit is farther from the centre of the Earth than "
         "Everest's would be at the same altitude, because the planet bulges "
         "at the equator — the same quirk that makes nearby Chimborazo the "
         "single farthest point from Earth's core.",
    tip="Go on a weekday: the park road to the refuge car park is public, and "
        "at weekends half of Quito drives up it."),
"quilotoa": dict(
    name="Quilotoa", slug="Quilotoa", country="Ecuador", region="Cotopaxi",
    type="nature", tag="hidden", emoji="🏞️", sounds=["mountain-wind.mp3"],
    highlights=[("Quilotoa Loop", None),
                ("Chugchilán", None),
                ("Zumbahua", None)],
    blurb="A three-kilometre-wide caldera filled with meltwater the colour of "
          "old glass, 3,900 m up in the western Andes. The crater rim is a "
          "village and a viewpoint; the water is 250 m below it, down a steep "
          "sand path that is much easier going down than coming back.",
    fact="The lake's green comes from dissolved minerals, and the crater still "
         "vents gas at the bottom — it is a live volcano, not a dead one.",
    tip="Stay a night on the rim rather than day-tripping from Latacunga. The "
        "crowds leave by four and the crater goes completely silent."),
"mindo": dict(
    name="Mindo", slug="Mindo,_Ecuador", country="Ecuador", region="Pichincha",
    type="nature", tag="hidden", emoji="🐦", sounds=["wilderness.mp3"],
    highlights=[("Mindo-Nambillo Cloud Forest", None),
                ("Tarabita", None),
                ("Nambillo River", None)],
    blurb="A cloud-forest village two hours down the western slope from Quito, "
          "where the Andes drop into permanent mist and the birdlife goes "
          "quietly berserk. Around 500 bird species have been recorded in the "
          "valley, including dozens of hummingbirds that will sit an arm's "
          "length away.",
    fact="Mindo was the first Important Bird Area declared in South America, "
         "and the valley was saved from a power line running through it by a "
         "local campaign in the 1990s.",
    tip="Be at a hummingbird feeder station by 6.30am. By nine the mist has "
        "usually come up the valley and the forest goes quiet."),
"galapagos-islands": dict(
    name="Galápagos Islands", slug="Galápagos_Islands", country="Ecuador",
    region="Galápagos Province", type="island", tag="famous", emoji="🐢",
    sounds=["ocean-waves.mp3"],
    highlights=[("Puerto Ayora", "Puerto_Ayora"),
                ("Charles Darwin Research Station", "Charles_Darwin_Research_Station"),
                ("Tortuga Bay", "Tortuga_Bay"),
                ("Isabela Island", "Isabela_Island_(Galápagos)"),
                ("Bartolomé Island", "Bartolomé_Island")],
    blurb="Nineteen volcanic islands on the equator, 900 km off the Ecuadorean "
          "coast, where three ocean currents meet and nothing that lives there "
          "arrived by land. The animals never learned to be afraid of anything "
          "walking upright, which is why you can stand next to them.",
    fact="Darwin spent five weeks here in 1835 and did not work out what the "
         "finches meant until he was back in London and an ornithologist told "
         "him they were thirteen separate species.",
    tip="Santa Cruz is the island you can walk: Tortuga Bay is a 45-minute "
        "path from Puerto Ayora, free, and has no boat trip attached to it."),

# ============================== CHILE ==============================
"santiago": dict(
    name="Santiago", slug="Santiago", country="Chile",
    region="Santiago Metropolitan Region", type="city", tag="famous",
    emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Plaza de Armas", "Plaza_de_Armas_(Santiago)"),
                ("Cerro San Cristóbal", "San_Cristóbal_Hill"),
                ("La Moneda Palace", "La_Moneda_Palace"),
                ("Gran Torre Santiago", "Gran_Torre_Costanera"),
                ("Mercado Central", "Mercado_Central_de_Santiago")],
    blurb="Chile's capital sits in a bowl with the Andes standing over its "
          "eastern edge — on a clear winter morning the snow line looks close "
          "enough to touch from the middle of downtown. A city of glass towers, "
          "1930s arcades and hillside parks, and the base camp for both the ski "
          "fields and the coast, each about an hour away.",
    fact="The Gran Torre Santiago is the tallest building in South America at "
         "300 m, and it is built to ride out the magnitude-8 earthquakes this "
         "coast produces roughly once a decade.",
    tip="Take the funicular up Cerro San Cristóbal rather than the cable car — "
        "it is the 1925 original, and it stops at the zoo halfway up."),
"valparaiso": dict(
    name="Valparaíso", slug="Valparaíso", country="Chile",
    region="Valparaíso Region", type="coastal", tag="famous", emoji="🎨",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cerro Alegre", None),
                ("Cerro Concepción", None),
                ("Funiculars of Valparaíso", "Valparaíso_funiculars"),
                ("La Sebastiana", None),
                ("Muelle Prat", None)],
    blurb="A working port built up 42 hills in no order whatsoever, connected "
          "by stairs, alleys and a set of Victorian funicular lifts that are "
          "still the quickest way up. Every wall that can be painted has been.",
    fact="Valparaíso was the Pacific's great stopover for ships rounding Cape "
          "Horn — and the Panama Canal opening in 1914 ended that trade almost "
          "overnight, which is why so much grand 19th-century architecture is "
          "still standing unimproved.",
    tip="Ride the Ascensor Reina Victoria up and walk down a different set of "
        "stairs — the murals are on the routes nobody drives."),
"vina-del-mar": dict(
    name="Viña del Mar", slug="Viña_del_Mar", country="Chile",
    region="Valparaíso Region", type="coastal", tag="famous", emoji="🏖️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Reloj de Flores", None),
                ("Castillo Wulff", "Wulff_Castle"),
                ("Quinta Vergara", "Quinta_Vergara"),
                ("Playa Reñaca", None)],
    blurb="Valparaíso's neighbour and its opposite: laid out on a grid, green, "
          "orderly, and built for the beach. Chile's summer resort since the "
          "1870s, with a casino, a long seafront and gardens where the port "
          "city has stairs.",
    fact="The Reloj de Flores — a working clock face planted in flowers on the "
         "seafront — was built for the 1962 World Cup and is still replanted "
         "by hand every season.",
    tip="Walk the coast road north to Reñaca at sunset; the Humboldt Current "
        "keeps the water near 15°C all year, so almost nobody actually swims."),
"san-pedro-de-atacama": dict(
    name="San Pedro de Atacama", slug="San_Pedro_de_Atacama", country="Chile",
    region="Antofagasta Region", type="desert", tag="famous", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Valle de la Luna", "Valle_de_la_Luna_(Chile)"),
                ("El Tatio", "El_Tatio"),
                ("Licancabur", "Licancabur"),
                ("Salar de Atacama", "Salar_de_Atacama")],
    blurb="An adobe oasis town at 2,400 m in the driest non-polar desert on "
          "Earth, with a volcano on the skyline in most directions. Some "
          "weather stations in the Atacama have never recorded rain at all.",
    fact="The desert is so dry and so clear that NASA tests Mars rovers here, "
         "and the world's largest radio telescope array sits on the plateau "
         "above the town.",
    tip="El Tatio geysers only perform at dawn, which means leaving at 4am in "
        "sub-zero cold — bring far more clothing than the daytime heat suggests."),
"pisco-elqui": dict(
    # The Elqui Valley has an article but its Wikidata item carries no
    # P625, and a place with no coordinate cannot go on a map. Anchor the
    # record on the village at the top of the valley, which has both, and
    # keep the valley itself as the first highlight.
    name="Pisco Elqui", slug="Pisco_Elqui", country="Chile",
    region="Coquimbo Region", type="village", tag="hidden", emoji="✨",
    sounds=["wind.mp3"],
    highlights=[("Elqui Valley", "Elqui_Valley"),
                ("Vicuña", "Vicuña,_Chile"),
                ("Puclaro Reservoir", None)],
    blurb="A narrow green river valley cut into brown desert hills, terraced "
          "with vineyards for the grape brandy Chile and Peru both claim. It "
          "is also one of the clearest night skies anywhere, which is why the "
          "hilltops around it carry international observatories.",
    fact="The valley is at the heart of Chile's first International Dark Sky "
         "Sanctuary — outdoor lighting for hundreds of kilometres around is "
         "regulated by law to protect the telescopes.",
    tip="Stay in Pisco Elqui rather than Vicuña, and walk out of the village "
        "after moonset — you do not need a tour to see the Milky Way here."),
"chiloe": dict(
    name="Chiloé", slug="Chiloé_Archipelago", country="Chile",
    region="Los Lagos Region", type="island", tag="hidden", emoji="⛪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Churches of Chiloé", "Churches_of_Chiloé"),
                ("Castro", "Castro,_Chile"),
                ("Palafitos", None),
                ("Chiloé National Park", "Chiloé_National_Park")],
    blurb="A green, wet, wooded archipelago off southern Chile that spent "
          "centuries half cut off from the mainland and developed its own "
          "everything — architecture, mythology, potato varieties. The wooden "
          "churches the Jesuits built here are shipwright's work, not masons'.",
    fact="Sixteen of Chiloé's wooden churches are UNESCO World Heritage: they "
         "were built entirely of native timber with wooden pegs instead of "
         "nails, by boatbuilders using boatbuilding joints.",
    tip="Castro's palafitos — houses on stilts over the tidal channel — are "
        "best seen from the Gamboa bridge two hours either side of low water."),
"puerto-varas": dict(
    name="Puerto Varas", slug="Puerto_Varas", country="Chile",
    region="Los Lagos Region", type="nature", tag="hidden", emoji="🌋",
    sounds=["wilderness.mp3"],
    highlights=[("Osorno", "Osorno_(volcano)"),
                ("Llanquihue Lake", "Llanquihue_Lake"),
                ("Petrohué Falls", "Petrohué_Waterfalls"),
                ("Vicente Pérez Rosales National Park",
                 "Vicente_Pérez_Rosales_National_Park")],
    blurb="A town of German-settler timber houses on the shore of Chile's "
          "second-largest lake, with the near-perfect cone of Osorno standing "
          "across the water. The start of the Chilean lake district, and of "
          "the boat-and-bus crossing over the Andes into Argentina.",
    fact="The lake crossing to Bariloche has run since 1913 and is still the "
         "only way through this stretch of the Andes — there is no road.",
    tip="The volcano is usually clearest first thing; by afternoon the lake "
        "throws up cloud and Osorno vanishes for the rest of the day."),
"valdivia": dict(
    name="Valdivia", slug="Valdivia", country="Chile",
    region="Los Ríos Region", type="city", tag="hidden", emoji="🦭",
    sounds=["city-hum.mp3"],
    highlights=[("Feria Fluvial", None),
                ("Fort Niebla", "Niebla,_Chile"),
                ("Corral Bay", None),
                ("Calle-Calle River", None)],
    blurb="A river city in the Chilean south, founded in 1552, flattened by "
          "the largest earthquake ever recorded, and rebuilt as a university "
          "town of riverside markets and Valdivian rainforest on its doorstep.",
    fact="The 1960 Valdivia earthquake measured magnitude 9.5, the strongest "
         "ever instrumentally recorded; it dropped parts of the city several "
         "metres and sent a tsunami all the way to Japan.",
    tip="Sea lions haul out at the Feria Fluvial fish market and wait for "
        "scraps — go mid-morning when the stalls are gutting the catch."),
"torres-del-paine": dict(
    name="Torres del Paine", slug="Torres_del_Paine_National_Park",
    country="Chile", region="Magallanes Region", type="mountain", tag="famous",
    emoji="🏔️", sounds=["mountain-wind.mp3"],
    highlights=[("Cuernos del Paine", "Cuernos_del_Paine"),
                ("Grey Glacier", "Grey_Glacier"),
                ("Lake Pehoé", "Lake_Pehoé"),
                ("Base of the Towers", None)],
    blurb="Granite towers standing straight out of the Patagonian steppe at "
          "the bottom of the continent, ringed by turquoise lakes and a glacier "
          "coming off the Southern Patagonian Ice Field. The wind is the thing "
          "nobody warns you about properly.",
    fact="The dark bands capping the Cuernos are the older rock the granite "
         "was forced up into — the mountains are effectively upside down, with "
         "the ancient sedimentary layer sitting on top of the younger intrusion.",
    tip="The W trek's first leg to the towers' base is doable as a long day "
        "walk from Torres Central, so you can see the signature view without "
        "carrying a tent."),
"punta-arenas": dict(
    name="Punta Arenas", slug="Punta_Arenas", country="Chile",
    region="Magallanes Region", type="coastal", tag="hidden", emoji="🐧",
    sounds=["wind.mp3"],
    highlights=[("Strait of Magellan", "Strait_of_Magellan"),
                ("Magdalena Island", "Magdalena_Island,_Magallanes_Region"),
                ("Plaza Muñoz Gamero", None),
                ("Cerro de la Cruz", None)],
    blurb="One of the southernmost cities on Earth, on the Strait of Magellan "
          "— a wool-and-shipping boomtown before the Panama Canal, now the way "
          "in to Patagonia and out to Antarctica. Mansions built on sheep money "
          "line a square planted with wind-bent conifers.",
    fact="Before 1914 every ship between the Atlantic and Pacific came through "
         "the Strait, and Punta Arenas grew rich coaling them; the canal took "
         "the traffic and the town has never been that busy since.",
    tip="The Magdalena Island ferry runs December to February and lands you in "
        "the middle of a colony of over 100,000 Magellanic penguins."),

# ============================== VENEZUELA ==============================
"caracas": dict(
    name="Caracas", slug="Caracas", country="Venezuela",
    region="Capital District", type="city", tag="famous", emoji="🏙️",
    sounds=["city-hum.mp3"],
    highlights=[("Plaza Bolívar", "Bolívar_Square_(Caracas)"),
                ("El Ávila", "El_Ávila_National_Park"),
                ("Teatro Teresa Carreño", "Teresa_Carreño_Cultural_Complex"),
                ("Ciudad Universitaria de Caracas",
                 "University_City_of_Caracas")],
    blurb="Venezuela's capital fills a long narrow valley at 900 m, separated "
          "from the Caribbean by the green wall of the Ávila — a national park "
          "that rises straight off the northern edge of the city to 2,600 m. "
          "Oil money built the towers and the motorways in a single generation.",
    fact="The Ciudad Universitaria campus is a UNESCO World Heritage Site: "
         "Carlos Raúl Villanueva designed it in the 1940s and 50s as one "
         "continuous work of art, with murals and sculpture by Léger, Arp and "
         "Calder built into the buildings.",
    tip="The Warairarepano cable car climbs the Ávila from the city to the "
        "ridge in fifteen minutes, and the temperature drops about ten degrees "
        "on the way up."),
"angel-falls": dict(
    name="Angel Falls", slug="Angel_Falls", country="Venezuela",
    region="Bolívar", type="nature", tag="famous", emoji="💧",
    sounds=["waterfall.mp3"],
    highlights=[("Auyán-tepui", "Auyán-tepui"),
                ("Canaima National Park", "Canaima_National_Park"),
                ("Canaima Lagoon", None)],
    blurb="The highest uninterrupted waterfall on Earth — 979 m off the rim of "
          "Auyán-tepui, a flat-topped mountain in the Venezuelan Gran Sabana. "
          "It falls so far that in the dry season most of it becomes mist "
          "before it reaches the bottom.",
    fact="It is named after Jimmie Angel, a US pilot who landed on top of the "
         "tepui in 1937 looking for gold and sank his plane in the mud; the "
         "aircraft sat up there for 33 years before it was lifted out.",
    tip="The falls only really run from about June to November. Outside the "
        "wet season the river is too low for the boats that get you close."),
"mount-roraima": dict(
    name="Mount Roraima", slug="Mount_Roraima", country="Venezuela",
    region="Bolívar", type="mountain", tag="famous", emoji="🗻",
    sounds=["mountain-wind.mp3"],
    highlights=[("Gran Sabana", "Gran_Sabana"),
                ("Kukenán Tepui", "Kukenán-tepui"),
                ("La Rampa", None)],
    blurb="A 31 km² sandstone table standing 400 m above the savanna where "
          "Venezuela, Brazil and Guyana meet — the best known of the tepuis, "
          "and one of the oldest exposed rock surfaces on the planet at around "
          "two billion years. The top is a wet black moonscape of its own.",
    fact="Roraima's summit is thought to have inspired Conan Doyle's *The Lost "
         "World*, and it really does hold species found nowhere else, isolated "
         "up there since the plateau eroded away around them.",
    tip="A single natural ramp on the Venezuelan side is the only walk-up route "
        "to the summit — everything else is vertical, and the trek takes about "
        "six days round trip from Paraitepui."),
"merida": dict(
    name="Mérida", slug="Mérida,_Mérida", country="Venezuela",
    region="Mérida State", type="mountain", tag="hidden", emoji="🚡",
    sounds=["mountain-wind.mp3"],
    highlights=[("Mukumbarí cable car", "Mérida_cable_car"),
                ("Pico Bolívar", "Pico_Bolívar"),
                ("Sierra Nevada National Park",
                 "Sierra_Nevada_National_Park_(Venezuela)"),
                ("Los Nevados", None)],
    blurb="A university town at 1,600 m in the Venezuelan Andes, under the "
          "country's highest peaks, with a permanently mild climate and a "
          "student population that keeps it lively. The mountains behind it "
          "hold Venezuela's last glaciers — what is left of them.",
    fact="The Mukumbarí cable car is the highest and longest in the world: "
         "four stages, 12.5 km, ending at 4,765 m on Pico Espejo.",
    tip="Book the cable car for the first departure. Cloud usually fills the "
        "upper stages by late morning and the top station closes when it does."),
"los-roques": dict(
    name="Los Roques", slug="Los_Roques_Archipelago", country="Venezuela",
    region="Federal Dependencies", type="island", tag="hidden", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Gran Roque", None),
                ("Cayo de Agua", None),
                ("Francisquí", None)],
    blurb="A coral archipelago 160 km north of the Venezuelan coast — roughly "
          "350 islands and cays inside a barrier reef, almost all of them "
          "uninhabited sand. Everyone stays on Gran Roque, the one island with "
          "a village, and takes a boat somewhere different each morning.",
    fact="The whole archipelago is a national park and one of the largest "
         "marine reserves in the Caribbean; fishing is restricted to the local "
         "community and the sand streets of Gran Roque have almost no cars.",
    tip="Boats are shared and priced by island, so ask which cay the boatmen "
        "are going to before you pick where to spend the day."),

# ============================== GUYANA ==============================
"georgetown-guyana": dict(
    name="Georgetown", slug="Georgetown,_Guyana", country="Guyana",
    region="Demerara-Mahaica", type="city", tag="famous", emoji="⛪",
    sounds=["city-hum.mp3"],
    highlights=[("St George's Cathedral", "St._George's_Cathedral,_Georgetown"),
                ("Stabroek Market", "Stabroek_Market"),
                ("Guyana National Museum", "Guyana_National_Museum"),
                ("Promenade Gardens", None)],
    blurb="The capital of the only English-speaking country in South America, "
          "laid out by the Dutch and built by the British in white-painted "
          "timber. Most of it sits below sea level behind a sea wall and a "
          "grid of drainage canals that still run down the middle of the "
          "avenues.",
    fact="St George's Cathedral is one of the tallest wooden buildings in the "
         "world at about 43 m, built entirely of local greenheart timber and "
         "consecrated in 1894.",
    tip="Walk the sea wall in the early evening, when the whole city comes out "
        "to it — and look at the Stabroek Market clock tower, which is cast "
        "iron shipped in and bolted together on site."),
"kaieteur-falls": dict(
    name="Kaieteur Falls", slug="Kaieteur_Falls", country="Guyana",
    region="Potaro-Siparuni", type="nature", tag="famous", emoji="💦",
    sounds=["waterfall.mp3"],
    highlights=[("Kaieteur National Park", "Kaieteur_National_Park"),
                ("Potaro River", "Potaro_River"),
                ("Golden rocket frog", None)],
    blurb="The Potaro River falls 226 m in one clear drop in the middle of the "
          "Guyanese rainforest — about four times the height of Niagara, with "
          "a fraction of the infrastructure. There is a grass airstrip, a "
          "footpath and no railings.",
    fact="Kaieteur is often called the world's largest single-drop waterfall "
         "by volume, and the tiny golden rocket frog lives out its entire life "
         "in the pools of the giant tank bromeliads growing beside it.",
    tip="It is a day trip by light aircraft from Georgetown and the flight is "
        "weather-dependent — leave a spare day in the plan, because trips get "
        "turned back regularly."),

# ============================== SURINAME ==============================
"paramaribo": dict(
    name="Paramaribo", slug="Paramaribo", country="Suriname",
    region="Paramaribo District", type="history", tag="famous", emoji="🏘️",
    sounds=["city-hum.mp3"],
    highlights=[("Fort Zeelandia", "Fort_Zeelandia_(Paramaribo)"),
                ("Saint Peter and Paul Cathedral",
                 "Saint_Peter_and_Paul_Cathedral,_Paramaribo"),
                ("Waterkant", None),
                ("Neveh Shalom Synagogue", "Neveh_Shalom_Synagogue")],
    blurb="A Dutch colonial capital on the Suriname River built almost "
          "entirely in white-painted wood, and the most mixed city on the "
          "continent — Dutch, Javanese, Hindustani, Creole, Maroon and Chinese, "
          "with the languages and the food to match.",
    fact="Paramaribo's wooden Saint Peter and Paul Cathedral is one of the "
         "largest timber buildings in the Americas — and a mosque and a "
         "synagogue stand side by side on Keizerstraat, sharing a car park.",
    tip="Walk the Waterkant riverfront at dusk when the food stalls set up; "
        "the whole historic centre is UNESCO-listed and takes about an hour "
        "to cross on foot."),
"brownsberg": dict(
    name="Brownsberg Nature Park", slug="Brownsberg_Nature_Park",
    country="Suriname", region="Brokopondo District", type="nature",
    tag="hidden", emoji="🌳", sounds=["wilderness.mp3"],
    highlights=[("Brokopondo Reservoir", "Brokopondo_Reservoir"),
                ("Leo Falls", None),
                ("Mazaroni Plateau", None)],
    blurb="A forested plateau 500 m above the Surinamese interior, looking out "
          "over one of the largest reservoirs in the world. Howler monkeys, "
          "eight primate species and several hundred bird species live in the "
          "rainforest around the ridge.",
    fact="The Brokopondo Reservoir below the park flooded 1,560 km² of forest "
         "in the 1960s to power an aluminium smelter — dead trees still stand "
         "out of the water across much of it.",
    tip="Stay overnight at the plateau lodge. The howler monkeys start before "
        "dawn and they are the loudest land animal in the Americas."),

# ============================== BRAZIL ==============================
"sao-paulo": dict(
    name="São Paulo", slug="São_Paulo", country="Brazil", region="São Paulo",
    type="city", tag="famous", emoji="🌆", sounds=["city-hum.mp3"],
    highlights=[("Avenida Paulista", "Paulista_Avenue"),
                ("Ibirapuera Park", "Ibirapuera_Park"),
                ("Theatro Municipal", "Theatro_Municipal_(São_Paulo)"),
                ("Mercado Municipal", "Municipal_Market_of_São_Paulo"),
                ("Edifício Copan", "Edifício_Copan")],
    blurb="The largest city in the Americas and the engine of Brazil — 12 "
          "million people in the city, 22 million in the sprawl, and a skyline "
          "of raw concrete towers that runs to the horizon in every direction. "
          "It is a working city rather than a beautiful one, and it eats "
          "better than anywhere else on the continent.",
    fact="São Paulo banned outdoor advertising outright in 2007 — billboards, "
         "shop-front signage, transit ads — and the 'Clean City Law' stripped "
         "roughly 15,000 billboards off the streets in a year.",
    tip="Avenida Paulista closes to traffic every Sunday and fills with "
        "cyclists, buskers and food carts end to end."),
"salvador": dict(
    name="Salvador", slug="Salvador,_Bahia", country="Brazil", region="Bahia",
    type="history", tag="famous", emoji="🥁", sounds=["european-plaza.mp3"],
    highlights=[("Pelourinho", "Historic_Center_of_Salvador"),
                ("Elevador Lacerda", "Elevador_Lacerda"),
                ("Church of São Francisco", None),
                ("Barra Lighthouse", "Barra_Lighthouse"),
                ("Mercado Modelo", "Modelo_Market")],
    blurb="Brazil's first capital, built on a cliff above the Bay of All "
          "Saints, and the centre of Afro-Brazilian culture — candomblé, "
          "capoeira, and a drum-led music you hear from three streets away. "
          "The upper and lower towns are joined by a 1873 public lift.",
    fact="The gilded interior of the Church of São Francisco is said to hold "
         "somewhere around half a tonne of gold leaf, applied over carved "
         "cedar in the 18th century.",
    tip="Take the Elevador Lacerda down at sunset for the price of a few "
        "coins, then look back up at the cliff with the whole old city on it."),
"brasilia": dict(
    name="Brasília", slug="Brasília", country="Brazil",
    region="Federal District", type="city", tag="famous", emoji="🛸",
    sounds=["city-hum.mp3"],
    highlights=[("Cathedral of Brasília", "Cathedral_of_Brasília"),
                ("National Congress", "Brazilian_National_Congress"),
                ("Palácio da Alvorada", "Palácio_da_Alvorada"),
                ("Praça dos Três Poderes", "Praça_dos_Três_Poderes"),
                ("Itamaraty Palace", "Itamaraty_Palace")],
    blurb="A capital designed from nothing on empty savanna and built in 41 "
          "months, opened in 1960. Lúcio Costa laid it out in the shape of an "
          "aircraft and Oscar Niemeyer filled it with white curved concrete; "
          "it is a modernist city plan you can still walk around inside.",
    fact="Brasília is the only city built in the 20th century to be inscribed "
         "as a UNESCO World Heritage Site — listed in 1987, less than 30 years "
         "after it opened.",
    tip="The cathedral is entered by a dark ramp that comes up into the light "
        "under the stained glass. Go in the middle of the day, when the roof "
        "is at its brightest."),
"manaus": dict(
    name="Manaus", slug="Manaus", country="Brazil", region="Amazonas",
    type="city", tag="famous", emoji="🌳", sounds=["city-hum.mp3"],
    highlights=[("Amazon Theatre", "Amazon_Theatre"),
                ("Meeting of Waters", "Meeting_of_Waters"),
                ("Adolpho Lisboa Market", "Mercado_Adolpho_Lisboa"),
                ("Rio Negro", "Rio_Negro_(Amazon)")],
    blurb="A city of two million in the middle of the Amazon rainforest, 1,500 "
          "km up the river from the sea and reachable by boat or plane only. "
          "The rubber boom made it absurdly rich for about thirty years, and "
          "the opera house is what that money left behind.",
    fact="Just downstream, the black Rio Negro and the sandy Solimões run side "
         "by side in the same channel for about 6 km without mixing — "
         "different temperatures, speeds and densities, with a visible line "
         "between them.",
    tip="The Amazon Theatre still runs a season, and daytime guided visits are "
        "cheap — the roof tiles were shipped in from Alsace and the curtain "
        "was painted in Paris."),
"ouro-preto": dict(
    name="Ouro Preto", slug="Ouro_Preto", country="Brazil",
    region="Minas Gerais", type="history", tag="hidden", emoji="⛪",
    sounds=["european-plaza.mp3"],
    highlights=[("Church of Saint Francis of Assisi",
                 "Church_of_Saint_Francis_of_Assisi_(Ouro_Preto)"),
                ("Praça Tiradentes", None),
                ("Museu da Inconfidência", "Museu_da_Inconfidência"),
                ("Mina da Passagem", None)],
    blurb="A gold-rush town of steep cobbled streets and baroque churches in "
          "the mountains of Minas Gerais, barely altered since the 18th "
          "century. Half the gold that reached Europe in that period came out "
          "of these hills, and the town was for a while the largest in the "
          "Americas.",
    fact="Aleijadinho, the sculptor who shaped much of Minas baroque, "
         "progressively lost the use of his hands to disease and is said to "
         "have worked with the tools strapped to his wrists.",
    tip="Nothing here is flat. Start at Praça Tiradentes at the top and work "
        "downhill through the churches rather than the other way round."),
"paraty": dict(
    name="Paraty", slug="Paraty", country="Brazil", region="Rio de Janeiro",
    type="history", tag="hidden", emoji="⛵", sounds=["ocean-waves.mp3"],
    highlights=[("Santa Rita Church", None),
                ("Saco do Mamanguá", None),
                ("Trindade", None),
                ("Caminho do Ouro", None)],
    blurb="A whitewashed colonial port on the coast between Rio and São Paulo, "
          "where the mountains come down to a bay full of islands. The centre "
          "is closed to cars and paved in irregular stones the sea washes over "
          "at the highest tides — the streets were designed to be flushed out.",
    fact="Paraty was the Atlantic end of the Caminho do Ouro, the mule road "
         "over the mountains that carried Minas Gerais gold down to the ships; "
         "stretches of the original stone paving are still walkable.",
    tip="Check the tide table. A spring high tide floods the historic grid on "
        "purpose, and boats can be tied up in the streets."),
"florianopolis": dict(
    name="Florianópolis", slug="Florianópolis", country="Brazil",
    region="Santa Catarina", type="coastal", tag="famous", emoji="🏄",
    sounds=["ocean-waves.mp3"],
    highlights=[("Hercílio Luz Bridge", "Hercílio_Luz_Bridge"),
                ("Lagoa da Conceição", "Lagoa_da_Conceição"),
                ("Joaquina Beach", None),
                ("Santo Antônio de Lisboa", None)],
    blurb="Half of this city is on the mainland and most of it is on an island "
          "with 42 beaches — surf on the Atlantic side, calm water and Azorean "
          "fishing villages on the other. Brazilians call it Floripa and a lot "
          "of them move here.",
    fact="The Hercílio Luz Bridge, opened in 1926, is the longest eyebar-chain "
         "suspension bridge ever built; it was shut for 28 years and reopened "
         "to pedestrians and cyclists in 2019.",
    tip="The dunes between Joaquina and the lagoon are open to walk on, and "
        "the sandboarding is rented out at the top of them for very little."),
"fernando-de-noronha": dict(
    name="Fernando de Noronha", slug="Fernando_de_Noronha", country="Brazil",
    region="Pernambuco", type="island", tag="famous", emoji="🐬",
    sounds=["ocean-waves.mp3"],
    highlights=[("Baía do Sancho", None),
                ("Morro Dois Irmãos", None),
                ("Baía dos Porcos", None),
                ("Praia da Atalaia", None)],
    blurb="A volcanic archipelago 350 km off the Brazilian northeast, with one "
          "inhabited island, a hard cap on visitor numbers and a daily "
          "environmental fee. Spinner dolphins come into the Baía dos Golfinhos "
          "in their hundreds most mornings.",
    fact="Baía do Sancho is reached down a ladder bolted into a cleft in the "
         "cliff, and has repeatedly been voted the best beach in the world by "
         "TripAdvisor's travellers.",
    tip="The dolphin bay has a clifftop viewpoint open at dawn and the animals "
        "are reliably there — you are not allowed to swim with them, which is "
        "why they keep coming."),
"lencois-maranhenses": dict(
    name="Lençóis Maranhenses", slug="Lençóis_Maranhenses_National_Park",
    country="Brazil", region="Maranhão", type="nature", tag="famous",
    emoji="🏜️", sounds=["desert-wind.mp3"],
    highlights=[("Barreirinhas", "Barreirinhas"),
                ("Lagoa Azul", None),
                ("Atins", None),
                ("Preguiças River", None)],
    blurb="A thousand square kilometres of white sand dunes that are not a "
          "desert: it rains heavily here, and the rain collects between the "
          "dunes in thousands of clear freshwater lagoons that appear around "
          "June and dry out by the end of the year.",
    fact="The dunes get about 1,600 mm of rain a year — far too much to be a "
         "desert — and the lagoons hold fish, which arrive as eggs carried in "
         "by birds and in the mud on their feet.",
    tip="Timing is everything. Come between July and September; arrive in "
        "February and you get sand and no water at all."),
"pantanal": dict(
    name="Pantanal", slug="Pantanal", country="Brazil",
    region="Mato Grosso do Sul", type="nature", tag="famous", emoji="🐆",
    sounds=["wilderness.mp3"],
    highlights=[("Transpantaneira", "Transpantaneira"),
                ("Poconé", "Poconé"),
                ("Paraguay River", "Paraguay_River")],
    blurb="The largest tropical wetland on Earth, roughly the size of England "
          "and Wales together, flooding and draining every year. It is the best "
          "place on the continent to actually see wildlife — the vegetation is "
          "open, and the animals concentrate around the water as it retreats.",
    fact="The Pantanal holds the densest jaguar population anywhere; along the "
         "Cuiabá River in the dry season they are seen from boats on most days, "
         "which is true almost nowhere else.",
    tip="The Transpantaneira road runs 145 km into the northern Pantanal over "
        "more than a hundred wooden bridges, and the wildlife is on the road "
        "itself — drive it slowly at dawn."),
"olinda": dict(
    name="Olinda", slug="Olinda", country="Brazil", region="Pernambuco",
    type="history", tag="hidden", emoji="🎭", sounds=["european-plaza.mp3"],
    highlights=[("Alto da Sé", None),
                ("Convento de São Francisco", None),
                ("Sé Cathedral", None),
                ("Mercado da Ribeira", None)],
    blurb="A hill town of pastel houses, churches and mango trees on the coast "
          "just north of Recife — founded in 1535, burned by the Dutch, rebuilt "
          "in baroque, and now a UNESCO site full of studios and workshops.",
    fact="Olinda's carnival is danced through the streets behind giant papier-"
         "mâché puppets several metres tall, some of which have been paraded "
         "every year for decades and are kept in their own museum.",
    tip="Climb to the Alto da Sé in the late afternoon for the view back over "
        "the coconut palms to the Recife skyline."),

# ============================== COLOMBIA ==============================
"salento": dict(
    name="Salento", slug="Salento,_Quindío", country="Colombia",
    region="Quindío", type="village", tag="hidden", emoji="☕",
    sounds=["wilderness.mp3"],
    highlights=[("Cocora Valley", "Cocora_Valley"),
                ("Calle Real", None),
                ("Mirador Alto de la Cruz", None)],
    blurb="A small painted town in the coffee axis, with balconies in every "
          "colour on one main street and the Cocora Valley half an hour up the "
          "road in a jeep. It is the base for walking among the tallest palms "
          "in the world.",
    fact="The Quindío wax palm grows to 60 m — the tallest palm species "
         "anywhere — and it is Colombia's national tree; the valley's palms "
         "stand in open cattle pasture, which is why they look impossible.",
    tip="The Willys jeeps to Cocora leave from the main square when they fill "
        "up. Walk the valley loop anticlockwise and you climb in shade."),
"guatape": dict(
    name="Guatapé", slug="Guatapé", country="Colombia", region="Antioquia",
    type="village", tag="famous", emoji="🪨", sounds=["plaza.mp3"],
    highlights=[("El Peñón de Guatapé", "El_Peñón_de_Guatapé"),
                ("Peñol-Guatapé Reservoir", None),
                ("Plazoleta de los Zócalos", None)],
    blurb="A lakeside town two hours from Medellín where every building has a "
          "painted relief panel — zócalos — running along its base, showing "
          "what the household does or once did. Behind it stands a 200 m "
          "granite monolith with a staircase built into a crack in its face.",
    fact="The reservoir the town sits on drowned the old town of El Peñol in "
         "the 1970s; in dry spells the cross of the flooded church still "
         "appears above the water.",
    tip="659 steps up the Piedra, and the queue starts mid-morning — go at "
        "opening, and the reservoir below is still holding mist."),
"tayrona": dict(
    name="Tayrona", slug="Tayrona_National_Natural_Park", country="Colombia",
    region="Magdalena", type="nature", tag="famous", emoji="🏝️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cabo San Juan del Guía", None),
                ("Sierra Nevada de Santa Marta", "Sierra_Nevada_de_Santa_Marta"),
                ("Pueblito", None),
                ("Playa Cristal", None)],
    blurb="Where the Sierra Nevada de Santa Marta runs straight into the "
          "Caribbean: rainforest, boulders the size of houses, and a string of "
          "bays you reach on foot or by boat. The mountain behind it goes from "
          "sea level to 5,700 m in 42 km.",
    fact="The park closes for several weeks each year at the request of the "
         "four Indigenous peoples of the Sierra, who consider it sacred ground "
         "and use the time for its spiritual recovery.",
    tip="Most of the beaches have dangerous currents and only a couple are "
        "safe to swim — the signs are accurate, and people drown here."),
"villa-de-leyva": dict(
    name="Villa de Leyva", slug="Villa_de_Leyva", country="Colombia",
    region="Boyacá", type="history", tag="hidden", emoji="🏛️",
    sounds=["european-plaza.mp3"],
    highlights=[("Plaza Mayor", None),
                ("Casa Terracota", None),
                ("El Fósil", None),
                ("Pozos Azules", None)],
    blurb="A whitewashed colonial town three hours north of Bogotá, built "
          "around one of the largest cobbled squares in South America — 14,000 "
          "square metres with nothing in the middle of it. The desert-ish "
          "valley around it is full of fossils.",
    fact="A 120-million-year-old kronosaurus, about seven metres of marine "
         "reptile, was found in a field outside town and is displayed where it "
         "was dug up rather than in a museum.",
    tip="Come midweek. The square is a film set at 7am and a car park full of "
        "Bogotá weekenders by Saturday lunchtime."),
"cano-cristales": dict(
    name="Caño Cristales", slug="Caño_Cristales", country="Colombia",
    region="Meta", type="nature", tag="hidden", emoji="🌈",
    sounds=["waterfall.mp3"],
    highlights=[("Serranía de la Macarena", "Serranía_de_la_Macarena"),
                ("La Macarena", None),
                ("Los Ochos", None)],
    blurb="A river in the Serranía de la Macarena that turns red, yellow and "
          "green for a few months a year, when an endemic riverweed flowers "
          "under water in exactly the right amount of sunlight and flow.",
    fact="The colour comes from *Macarenia clavigera*, a plant that grows on "
         "the rock nowhere else on Earth — and the whole spectacle only runs "
         "from roughly June to November, between too much water and too little.",
    tip="Access is controlled and requires a licensed guide from La Macarena; "
        "sunscreen and insect repellent are banned in the river to protect the "
        "weed."),

# ============================== PERU ==============================
"lima": dict(
    name="Lima", slug="Lima", country="Peru", region="Lima Region",
    type="city", tag="famous", emoji="🍽️", sounds=["city-hum.mp3"],
    highlights=[("Plaza Mayor", "Plaza_Mayor,_Lima"),
                ("Basilica and Convent of San Francisco",
                 "Basilica_and_Convent_of_San_Francisco,_Lima"),
                ("Miraflores", "Miraflores_District,_Lima"),
                ("Barranco", "Barranco_District"),
                ("Huaca Pucllana", "Huaca_Pucllana")],
    blurb="A capital of ten million on a desert coast, built on cliffs above "
          "the Pacific and under a grey marine overcast for half the year. The "
          "colonial centre and the clifftop districts are two different cities, "
          "and the food is why a lot of people come at all.",
    fact="It almost never rains in Lima — under 10 mm a year — yet the city is "
         "damp and grey for months, because the cold Humboldt Current holds a "
         "permanent low cloud layer over it that never quite breaks.",
    tip="The catacombs under San Francisco hold thousands of stacked bones and "
        "are the one part of the old centre worth queueing for."),
"arequipa": dict(
    name="Arequipa", slug="Arequipa", country="Peru", region="Arequipa Region",
    type="history", tag="famous", emoji="🌋", sounds=["european-plaza.mp3"],
    highlights=[("Santa Catalina Monastery",
                 "Monastery_of_Santa_Catalina_de_Siena,_Arequipa"),
                ("Basilica Cathedral of Arequipa",
                 "Basilica_Cathedral_of_Arequipa"),
                ("Misti", "Misti"),
                ("Yanahuara", None),
                ("Plaza de Armas", None)],
    blurb="Peru's second city, built almost entirely out of white volcanic "
          "sillar stone under three volcanoes, at 2,335 m. The light off the "
          "buildings at midday is genuinely hard to look at, which is where "
          "the nickname La Ciudad Blanca comes from.",
    fact="Santa Catalina is a walled convent covering 20,000 m² — effectively "
         "a small painted town of its own inside the city, closed to outsiders "
         "for nearly 400 years until it opened in 1970.",
    tip="Go into Santa Catalina in the last two hours of the day, when the "
        "low sun hits the blue and red lanes and the tour groups have gone."),
"puno": dict(
    name="Puno", slug="Puno", country="Peru", region="Puno Region",
    type="city", tag="famous", emoji="🛶", sounds=["wind.mp3"],
    highlights=[("Lake Titicaca", "Lake_Titicaca"),
                ("Uros floating islands", None),
                ("Taquile", "Taquile_Island"),
                ("Sillustani", "Sillustani")],
    blurb="The Peruvian port on Lake Titicaca, at 3,830 m — a working "
          "altiplano town rather than a pretty one, and the way out onto the "
          "highest large navigable lake in the world. Bolivia is on the far "
          "shore.",
    fact="The Uros build their islands, houses and boats out of totora reed "
         "and have to keep adding fresh layers on top as the underside rots — "
         "an island lasts about 30 years.",
    tip="Taquile is worth the extra hours past the Uros: no vehicles, no dogs, "
        "and the men knit while they walk — the island's textiles are on "
        "UNESCO's intangible heritage list."),
"ollantaytambo": dict(
    name="Ollantaytambo", slug="Ollantaytambo", country="Peru",
    region="Cusco Region", type="ruin", tag="famous", emoji="🧱",
    sounds=["mountain-wind.mp3"],
    highlights=[("Sacred Valley", "Sacred_Valley"),
                ("Temple of the Sun", None),
                ("Pinkuylluna", None)],
    blurb="The best-preserved Inca town anywhere: people still live in the "
          "original grid, on the original stone foundations, drinking water "
          "from the original channels. The terraced fortress above it is one "
          "of the few places the Inca beat the Spanish in open battle.",
    fact="The six monoliths of the unfinished Sun Temple were quarried on the "
         "far side of the valley, 6 km away and 900 m up — the Inca moved "
         "them across a river and up a mountain without wheels or iron tools.",
    tip="Climb the Pinkuylluna storehouses opposite instead of only doing the "
        "main site: it is free, it takes 40 minutes, and it looks down on the "
        "whole terraced face."),
"colca-canyon": dict(
    name="Colca Canyon", slug="Colca_Canyon", country="Peru",
    region="Arequipa Region", type="nature", tag="famous", emoji="🦅",
    sounds=["mountain-wind.mp3"],
    highlights=[("Cruz del Cóndor", None),
                ("Chivay", "Chivay"),
                ("Colca River", "Colca_River"),
                ("Yanque", None)],
    blurb="A canyon over 3,000 m deep in the Peruvian Andes — roughly twice "
          "the depth of the Grand Canyon, though far less sheer — with "
          "pre-Inca terracing still farmed down its walls and Andean condors "
          "riding the morning thermals out of it.",
    fact="Andean condors have a wingspan over three metres and barely flap; "
         "they wait at the Cruz del Cóndor until the sun has warmed the canyon "
         "enough to lift them out of it, which is why the viewing is at 8am.",
    tip="Stay in Chivay or Yanque the night before. The day trip from Arequipa "
        "means a 3am start and you arrive at the viewpoint with everyone else."),
"huacachina": dict(
    name="Huacachina", slug="Huacachina", country="Peru", region="Ica Region",
    type="desert", tag="hidden", emoji="🏜️", sounds=["desert-wind.mp3"],
    highlights=[("Ica", "Ica,_Peru"),
                ("Cerro Blanco", None),
                ("Huacachina lagoon", None)],
    blurb="A village of about a hundred people built around a natural lagoon "
          "in the middle of coastal desert, ringed by palms and then by dunes "
          "several hundred metres high. It appears on the back of the Peruvian "
          "50-sol note.",
    fact="The oasis is fed by an underground aquifer that has been dropping "
         "for decades; the lagoon has had to be topped up artificially to stop "
         "it disappearing altogether.",
    tip="Climb the dune on the west side on foot for sunset — half an hour of "
        "hard walking in sand, and it is quiet up there while the buggies are "
        "all on the far side."),

# ============================== ARGENTINA ==============================
"salta": dict(
    name="Salta", slug="Salta", country="Argentina", region="Salta Province",
    type="history", tag="hidden", emoji="⛪", sounds=["european-plaza.mp3"],
    highlights=[("Salta Cathedral", "Salta_Cathedral"),
                ("Cabildo of Salta", None),
                ("Cerro San Bernardo", None),
                ("Tren a las Nubes", "Tren_a_las_Nubes")],
    blurb="A colonial city in Argentina's northwest, closer in feel to Bolivia "
          "than to Buenos Aires — pink and ochre churches, a colonnaded square, "
          "and folk music played in peñas until very late.",
    fact="The Tren a las Nubes climbs from Salta to 4,220 m and crosses the "
         "La Polvorilla viaduct, 64 m above a ravine, on a line built without "
         "a single tunnel switchback engine — it uses zigzags and spirals to "
         "gain height instead.",
    tip="The Museo de Arqueología de Alta Montaña displays one of the three "
        "Llullaillaco children at a time, rotated — an Inca burial found "
        "frozen at 6,700 m and preserved almost perfectly."),
"el-calafate": dict(
    name="El Calafate", slug="El_Calafate", country="Argentina",
    region="Santa Cruz Province", type="nature", tag="famous", emoji="🧊",
    sounds=["wind.mp3"],
    highlights=[("Perito Moreno Glacier", "Perito_Moreno_Glacier"),
                ("Los Glaciares National Park", "Los_Glaciares_National_Park"),
                ("Lago Argentino", "Lake_Argentino")],
    blurb="A steppe town on Lago Argentino that exists to get people to the "
          "Perito Moreno Glacier, 80 km west — a five-kilometre-wide wall of "
          "ice ending in a lake, with a boardwalk system built along the front "
          "of it.",
    fact="Perito Moreno is one of the very few glaciers on Earth that is not "
         "retreating. Every few years it dams an arm of the lake completely, "
         "the water rises behind it, and the ice bridge collapses in front of "
         "an audience.",
    tip="Spend the whole day on the walkways rather than taking the boat. The "
        "calving is unpredictable, the sound arrives a beat after the fall, "
        "and you need to be there when it happens."),
"el-chalten": dict(
    name="El Chaltén", slug="El_Chaltén", country="Argentina",
    region="Santa Cruz Province", type="mountain", tag="famous", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Monte Fitz Roy", "Fitz_Roy"),
                ("Cerro Torre", "Cerro_Torre"),
                ("Laguna de los Tres", None),
                ("Laguna Capri", None)],
    blurb="Argentina's trekking capital, founded in 1985 in a hurry to settle "
          "a border dispute, at the foot of Fitz Roy. Every trail starts from "
          "the village itself, so there is no shuttle and no entrance queue — "
          "you walk out of your door onto the mountain.",
    fact="Fitz Roy's Tehuelche name, Chaltén, means 'smoking mountain' — the "
         "peak generates its own cloud so persistently that early observers "
         "took it for a volcano.",
    tip="Laguna de los Tres is a 10-hour round trip with the climb at the end. "
        "If the forecast gives one clear morning, spend it on that and do the "
        "Torre trail on the grey day."),
"quebrada-de-humahuaca": dict(
    name="Quebrada de Humahuaca", slug="Quebrada_de_Humahuaca",
    country="Argentina", region="Jujuy Province", type="nature", tag="hidden",
    emoji="🎨", sounds=["desert-wind.mp3"],
    highlights=[("Purmamarca", "Purmamarca"),
                ("Cerro de los Siete Colores", None),
                ("Tilcara", "Tilcara"),
                ("Pucará de Tilcara", "Pucará_de_Tilcara"),
                ("Humahuaca", "Humahuaca")],
    blurb="A 155 km desert valley in Jujuy that has been a caravan route for "
          "10,000 years — Inca road, colonial silver road, and now a string of "
          "adobe villages under hills striped in mineral colours.",
    fact="The whole valley is a UNESCO World Heritage Site listed as a "
         "cultural route, not a landscape: what is protected is the fact that "
         "people have been moving goods along it continuously since the "
         "hunter-gatherers.",
    tip="The Cerro de los Siete Colores behind Purmamarca is at its most "
        "saturated in the first hour of light, and the village is a "
        "three-street walk before the buses arrive."),
"peninsula-valdes": dict(
    name="Península Valdés", slug="Valdés_Peninsula", country="Argentina",
    region="Chubut Province", type="nature", tag="famous", emoji="🐋",
    sounds=["ocean-waves.mp3"],
    highlights=[("Puerto Pirámides", "Puerto_Pirámides"),
                ("Punta Norte", None),
                ("Caleta Valdés", None),
                ("Puerto Madryn", "Puerto_Madryn")],
    blurb="A flat, treeless Patagonian peninsula joined to the mainland by a "
          "5 km isthmus, with almost nothing on it and a coastline that is one "
          "of the best marine wildlife sites in the world. Southern right "
          "whales calve in the sheltered gulfs either side of it.",
    fact="At Punta Norte, orcas deliberately beach themselves at high tide to "
         "take sea lion pups off the shingle and then work their way back into "
         "the water — behaviour taught to their young and seen almost nowhere "
         "else.",
    tip="Whale season runs roughly June to December. Puerto Pirámides is the "
        "only village, and in the peak weeks whales are visible from the beach "
        "without a boat at all."),
"cordoba": dict(
    name="Córdoba", slug="Córdoba,_Argentina", country="Argentina",
    region="Córdoba Province", type="city", tag="hidden", emoji="🎓",
    sounds=["city-hum.mp3"],
    highlights=[("Jesuit Block", "Jesuit_Block_and_Estancias_of_Córdoba"),
                ("Córdoba Cathedral", "Cathedral_of_Córdoba,_Argentina"),
                ("Cabildo of Córdoba", None),
                ("Nueva Córdoba", None)],
    blurb="Argentina's second city and its oldest university town, in the "
          "middle of the country with hills on its western side. The Jesuit "
          "core is 17th-century and the student population keeps the bars "
          "around it open very late.",
    fact="The National University of Córdoba was founded in 1613, making it "
         "one of the oldest universities in the Americas — older than the "
         "country it is in by two centuries.",
    tip="The Manzana Jesuítica is a single block you can walk in twenty "
        "minutes — church, university and school — and it is a UNESCO site in "
        "the middle of an ordinary shopping district."),

# ============================== BOLIVIA ==============================
"potosi": dict(
    name="Potosí", slug="Potosí", country="Bolivia", region="Potosí Department",
    type="history", tag="famous", emoji="⛏️", sounds=["european-plaza.mp3"],
    highlights=[("Cerro Rico", "Cerro_Rico"),
                ("Casa Nacional de Moneda", "National_Mint_of_Bolivia"),
                ("Plaza 10 de Noviembre", None),
                ("San Lorenzo de Carangas", None)],
    blurb="At 4,090 m, one of the highest cities in the world, built under a "
          "mountain of silver that funded the Spanish empire for two "
          "centuries. In 1600 Potosí was as big as London; the mountain is "
          "still worked today by cooperative miners in brutal conditions.",
    fact="'Vale un Potosí' — worth a Potosí — entered Spanish as the phrase "
         "for unimaginable wealth, and the mint here struck the pieces of "
         "eight that circulated as the first global currency.",
    tip="The Casa Nacional de Moneda is the serious visit: the original "
        "wooden coin-rolling machines, turned by mules, are still in place."),
"isla-del-sol": dict(
    name="Isla del Sol", slug="Isla_del_Sol", country="Bolivia",
    region="La Paz Department", type="island", tag="hidden", emoji="☀️",
    sounds=["wind.mp3"],
    highlights=[("Lake Titicaca", "Lake_Titicaca"),
                ("Chincana", None),
                ("Pilko Kaina", None),
                ("Yumani", None)],
    blurb="An island of terraced hillsides in the Bolivian half of Lake "
          "Titicaca, with no cars, no paved roads and about 800 families "
          "farming it. Inca myth has the sun itself born here, and the ruins "
          "at both ends of the island are pilgrimage sites.",
    fact="The Inca creation story places the origin of the sun at the "
         "Titikala rock on this island — the empire's most sacred site, "
         "which is why a road of shrines runs the length of the ridge.",
    tip="Boats land at Yumani and the village is straight up the Inca stairs "
        "from the jetty — at 3,800 m that climb is the hardest twenty minutes "
        "of the trip."),
"santa-cruz-de-la-sierra": dict(
    name="Santa Cruz de la Sierra", slug="Santa_Cruz_de_la_Sierra",
    country="Bolivia", region="Santa Cruz Department", type="city",
    tag="hidden", emoji="🌴", sounds=["city-hum.mp3"],
    highlights=[("Plaza 24 de Septiembre", None),
                ("Basílica Menor de San Lorenzo", None),
                ("Parque Urbano", None)],
    blurb="Bolivia's largest and richest city, and nothing like the Andean "
          "half of the country: it is lowland, hot, green and laid out in "
          "concentric ring roads on flat ground, growing faster than anywhere "
          "else in the country.",
    fact="Santa Cruz has gone from about 40,000 people in 1950 to well over a "
         "million and a half — one of the fastest urban growth rates recorded "
         "anywhere in the world.",
    tip="Sloths live in the trees of the main square. Look up on the north "
        "side and you will usually find at least one asleep."),
"madidi": dict(
    name="Madidi National Park", slug="Madidi_National_Park", country="Bolivia",
    region="La Paz Department", type="nature", tag="hidden", emoji="🐒",
    sounds=["wilderness.mp3"],
    highlights=[("Rurrenabaque", "Rurrenabaque"),
                ("Beni River", "Beni_River"),
                ("Tuichi River", None)],
    blurb="Nearly 19,000 km² running from Amazon lowland at 200 m up to Andean "
          "glaciers at 6,000 m — one of the most biodiverse protected areas on "
          "the planet, entered by boat from the river town of Rurrenabaque.",
    fact="Madidi is thought to hold around 11% of all the world's bird species "
         "inside a single park, largely because it spans almost every altitude "
         "band between rainforest and snow line.",
    tip="Community-run lodges up the Tuichi employ guides from the Indigenous "
        "communities that own them; going with those rather than a Rurrenabaque "
        "agency is the difference between a boat trip and being shown the "
        "forest."),

# ============================== URUGUAY ==============================
"cabo-polonio": dict(
    name="Cabo Polonio", slug="Cabo_Polonio", country="Uruguay",
    region="Rocha Department", type="coastal", tag="hidden", emoji="🦭",
    sounds=["ocean-waves.mp3"],
    highlights=[("Cabo Polonio National Park", None),
                ("Cabo Polonio Lighthouse", None),
                ("Barra de Valizas", None)],
    blurb="A village of about a hundred houses on a headland in the Uruguayan "
          "dunes, with no road in, no mains electricity and no mains water. "
          "You arrive in a four-wheel-drive truck across 7 km of sand, and the "
          "night sky over it is completely dark.",
    fact="The rocks below the lighthouse hold one of the largest sea lion "
         "colonies in South America — several thousand animals, audible from "
         "the village all night.",
    tip="Bring cash and a torch. There are no cash machines, most houses run "
        "on solar or wind, and after dark the only lights are the lighthouse "
        "and whatever you carry."),

# ============================== PARAGUAY ==============================
"encarnacion": dict(
    name="Encarnación", slug="Encarnación,_Paraguay", country="Paraguay",
    region="Itapúa", type="city", tag="hidden", emoji="🏖️",
    sounds=["ocean-waves.mp3"],
    highlights=[("La Santísima Trinidad de Paraná",
                 "La_Santísima_Trinidad_de_Paraná"),
                ("Jesús de Tavarangue", "Ruins_of_Jesús_de_Tavarangue"),
                ("Playa San José", None),
                ("Paraná River", "Paraná_River")],
    blurb="Paraguay's southern river city, rebuilt uphill when the Yacyretá "
          "dam raised the Paraná and drowned the old lower town — and given a "
          "sand beach and a promenade in the process. The great Jesuit mission "
          "ruins are half an hour up the road.",
    fact="The Jesuit reductions here were self-governing Guaraní towns of "
         "several thousand people, with their own orchestras and printing "
         "presses, until Spain expelled the order in 1767 and the settlements "
         "were abandoned to the forest.",
    tip="Go to Trinidad for the evening light-and-sound opening rather than in "
        "the middle of the day — the red sandstone carving reads much better "
        "at a low angle."),
"ciudad-del-este": dict(
    name="Ciudad del Este", slug="Ciudad_del_Este", country="Paraguay",
    region="Alto Paraná", type="city", tag="hidden", emoji="⚡",
    sounds=["city-hum.mp3"],
    highlights=[("Itaipu Dam", "Itaipu_Dam"),
                ("Saltos del Monday", "Saltos_del_Monday"),
                ("Friendship Bridge", "Friendship_Bridge_(Brazil–Paraguay)")],
    blurb="A frontier shopping city at the point where Paraguay, Brazil and "
          "Argentina meet — chaotic, duty-free, and permanently full of "
          "Brazilians crossing the Friendship Bridge with as much as they can "
          "carry. The world's second-largest hydroelectric dam is upstream.",
    fact="Itaipú generates around 90% of Paraguay's electricity and roughly a "
         "tenth of Brazil's, and until Three Gorges opened it was the largest "
         "power station on Earth by output.",
    tip="The Monday Falls, 10 km out of town, are 40 m high and almost empty "
        "— everyone drives past them to Iguazú, twenty minutes further on."),
}


# ---------------------------------------------------------------------------
# Places already in data/latinamerica.json that were never filled in: 21 of the
# 30 have an empty `highlights`, `blurb`, `fun_fact` and `hidden_gem_tip`, and
# all 30 have an empty `region`. A skeleton is worse than an absence — it takes
# up a pin on the map and the arrival card has nothing to say. Everything below
# is merged into whatever is already on disk; nothing here overwrites a field
# that already has a value.
# ---------------------------------------------------------------------------
FILL = {
# --- region only (these already have their editorial content) ---
"la-paz": dict(region="La Paz Department"),
"bogota": dict(region="Capital District"),
"montevideo": dict(region="Montevideo Department"),
"asuncion": dict(region="Capital District"),
"havana": dict(region="La Habana"),
"san-jose": dict(region="San José Province"),
"mexico-city": dict(region="Valley of Mexico"),
"cusco": dict(region="Cusco Region"),
"machu-picchu": dict(region="Cusco Region"),
"rio-de-janeiro": dict(
    region="Rio de Janeiro",
    tip="The Escadaria Selarón is free, always open and two minutes off the "
        "Lapa arches — 215 steps tiled with pieces sent from 60 countries by "
        "one man over 23 years."),

# --- ARGENTINA ---
"buenos-aires": dict(
    region="Buenos Aires",
    highlights=[("Teatro Colón", "Teatro_Colón"),
                ("Recoleta Cemetery", "La_Recoleta_Cemetery"),
                ("Caminito", "Caminito"),
                ("Plaza de Mayo", "Plaza_de_Mayo"),
                ("El Ateneo Grand Splendid", "El_Ateneo_Grand_Splendid")],
    blurb="A European-looking capital at the mouth of the Río de la Plata, "
          "with wide boulevards, Parisian apartment blocks and the longest "
          "dinner hours on the continent. Tango was invented in its port "
          "neighbourhoods and the city still argues about who owns it.",
    fact="Teatro Colón's acoustics are rated among the five best of any opera "
         "house in the world; the horseshoe auditorium was finished in 1908 "
         "after twenty years and three architects, two of whom died mid-build.",
    tip="El Ateneo Grand Splendid is a 1919 theatre turned bookshop — the "
        "boxes are reading nooks and the stage is a café. Free to walk into."),
"iguazu-falls": dict(
    region="Misiones Province",
    highlights=[("Devil's Throat", None),
                ("Iguazú National Park", "Iguazú_National_Park"),
                ("Iguazu River", "Iguazu_River"),
                ("Isla San Martín", None)],
    blurb="275 separate waterfalls spread along nearly three kilometres of "
          "the Argentina–Brazil border, dropping through subtropical forest "
          "full of coatis and toucans. The Argentine side puts you on top of "
          "them; the Brazilian side lets you see the whole thing at once.",
    fact="Iguazú carries roughly ten times the water of Niagara over a front "
         "more than twice as wide — Eleanor Roosevelt is supposed to have "
         "seen it and said only 'poor Niagara'.",
    tip="Walk the upper circuit first, then the Devil's Throat at the very "
        "end of the day — the walkway crosses a kilometre of flat river that "
        "gives no warning of what is about to happen to it."),
"bariloche": dict(
    region="Río Negro Province",
    highlights=[("Nahuel Huapi National Park", "Nahuel_Huapi_National_Park"),
                ("Cerro Catedral", "Cerro_Catedral"),
                ("Circuito Chico", None),
                ("Cerro Campanario", None),
                ("Civic Center", None)],
    blurb="An alpine-styled town of stone and timber on a glacial lake in "
          "northern Patagonia, surrounded by mountains and forest. Argentines "
          "come to ski in winter, walk in summer, and eat chocolate all year.",
    fact="Bariloche has more than a dozen artisan chocolate houses on one "
         "street, a legacy of the Swiss, German and Italian families who "
         "settled the lake district at the start of the 20th century.",
    tip="The chairlift up Cerro Campanario takes seven minutes and gives you "
        "the view of the lakes that every postcard of Patagonia uses."),
"mendoza": dict(
    region="Mendoza Province",
    highlights=[("Aconcagua", "Aconcagua"),
                ("Parque General San Martín", "General_San_Martín_Park"),
                ("Uco Valley", "Uco_Valley"),
                ("Maipú", "Maipú,_Mendoza"),
                ("Puente del Inca", "Puente_del_Inca")],
    blurb="Argentina's wine capital, a green grid of irrigated streets in "
          "high desert with the Andes filling the western horizon. Malbec "
          "arrived here from France and did far better than it ever did at "
          "home.",
    fact="The whole city is watered by acequias — open channels along every "
         "street, running off Andean snowmelt on a system begun by the "
         "Huarpe people long before the Spanish arrived.",
    tip="Rent a bike in Maipú rather than joining a minibus tour. The "
        "wineries are flat and close together, and you set your own pace."),
"ushuaia": dict(
    region="Tierra del Fuego",
    highlights=[("Tierra del Fuego National Park",
                 "Tierra_del_Fuego_National_Park"),
                ("Beagle Channel", "Beagle_Channel"),
                ("Les Éclaireurs Lighthouse", "Les_Eclaireurs_Lighthouse"),
                ("End of the World Train", "Southern_Fuegian_Railway"),
                ("Martial Glacier", None)],
    blurb="The southernmost city in the world, wedged between the Beagle "
          "Channel and a wall of snow-topped mountains. Most Antarctic "
          "expeditions leave from its docks, and everything in town is "
          "labelled 'end of the world'.",
    fact="The tourist railway out to the national park runs on the line built "
         "by prisoners of the Ushuaia penal colony, who cut the forest "
         "around the town for firewood and were carried out to work on it.",
    tip="The Martial Glacier trail starts at the edge of town and climbs to a "
        "view straight down the channel — two hours, no permit, and you can "
        "start it after lunch."),

# --- BOLIVIA ---
"salar-de-uyuni": dict(
    region="Potosí Department",
    highlights=[("Incahuasi Island", "Isla_Incahuasi"),
                ("Uyuni", "Uyuni"),
                ("Tunupa", "Tunupa"),
                ("Colchani", None),
                ("Train Cemetery", None)],
    blurb="The largest salt flat on Earth: 10,000 km² of hexagon-cracked "
          "white crust at 3,656 m, so flat and so empty that distance stops "
          "reading and photographs lose all sense of scale.",
    fact="The surface varies by less than one metre across its entire width, "
         "which makes it the calibration target for satellite altimeters — "
         "it is used to check the instruments measuring the world's oceans.",
    tip="After rain the flat holds a few centimetres of standing water and "
        "becomes a mirror to the horizon. That is January to March, which is "
        "also when parts of it become impossible to drive on."),
"sucre": dict(
    region="Chuquisaca Department",
    highlights=[("Casa de la Libertad", None),
                ("Metropolitan Cathedral of Sucre",
                 "Metropolitan_Cathedral_of_Sucre"),
                ("Parque Cretácico", None),
                ("La Recoleta", None),
                ("Mercado Central", None)],
    blurb="Bolivia's constitutional capital and its prettiest city — a "
          "whitewashed colonial centre at 2,810 m, warmer and gentler than "
          "La Paz, where independence was declared in 1825.",
    fact="A cement quarry on the edge of town exposed a near-vertical rock "
         "face carrying more than 5,000 dinosaur footprints — the largest "
         "single collection of tracks found anywhere in the world.",
    tip="Climb to the La Recoleta terrace at the top of the old town in the "
        "late afternoon: the whole white grid is below you with the hills "
        "behind it."),

# --- COLOMBIA ---
"cartagena": dict(
    region="Bolívar Department",
    highlights=[("Ciudad Amurallada", None),
                ("Castillo San Felipe de Barajas",
                 "Castillo_San_Felipe_de_Barajas"),
                ("Getsemaní", None),
                ("Rosario Islands", "Rosario_Islands"),
                ("Puerta del Reloj", "Puerta_del_Reloj")],
    blurb="A walled Caribbean port of balconied houses, bougainvillea and "
          "colour, built to hold the silver of the Americas and fortified "
          "against everyone who came to take it. It is hot, loud and one of "
          "the best-preserved colonial cities anywhere.",
    fact="The walls took roughly two centuries to finish and the fort of San "
         "Felipe is honeycombed with tunnels cut so that a whisper at one "
         "end carries to the other — an early alarm system against sappers.",
    tip="Getsemaní, just outside the walls, is where the city actually lives "
        "— street art, plaza music after dark, and none of the cruise crowd."),
"medellin": dict(
    region="Antioquia",
    highlights=[("Plaza Botero", None),
                ("Comuna 13", "Comuna_13,_Medellín"),
                ("Metrocable", "Metrocable_(Medellín)"),
                ("Parque Arví", "Arví_Park"),
                ("Museo de Antioquia", "Museum_of_Antioquia")],
    blurb="A city of two and a half million in a narrow Andean valley at a "
          "permanent spring temperature, with cable cars running up the "
          "hillsides as public transport. Its turnaround from the early "
          "1990s is the most studied urban recovery in the world.",
    fact="The Metrocable was the first gondola system anywhere built as mass "
         "transit rather than tourism — it connected the poorest hillside "
         "barrios to the city in minutes instead of hours, and has been "
         "copied from La Paz to Mexico City since.",
    tip="Comuna 13's outdoor escalators are free to ride, and the barrio "
        "guides who grew up there give the tour that the history deserves."),

# --- URUGUAY ---
"punta-del-este": dict(
    region="Maldonado Department",
    highlights=[("La Mano", "La_Mano_de_Punta_del_Este"),
                ("Casapueblo", "Casapueblo"),
                ("Isla de Lobos", None),
                ("Punta Ballena", None)],
    blurb="South America's flashiest beach resort, on a headland where the "
          "Río de la Plata finally becomes the Atlantic — quiet nine months "
          "of the year and full of Argentines and Brazilians for the other "
          "three.",
    fact="La Mano — five concrete fingers rising out of Brava beach — was "
         "built in 1982 in six days for a sculpture competition, and was "
         "meant to be a warning about drowning rather than a photo stop.",
    tip="Casapueblo, up the coast at Punta Ballena, is a whitewashed cliff "
        "house the painter Carlos Páez Vilaró built by hand over 36 years. "
        "It does a sunset ceremony with his own recorded farewell to the sun."),
"colonia-del-sacramento": dict(
    region="Colonia Department",
    highlights=[("Barrio Histórico", None),
                ("Colonia del Sacramento Lighthouse", None),
                ("Calle de los Suspiros", None),
                ("Puerta de Campo", None)],
    blurb="A Portuguese smuggling town founded in 1680 directly across the "
          "river from Buenos Aires, fought over by two empires for a century "
          "and swapped between them repeatedly. The cobbled quarter is "
          "hardly changed, and cars there are mostly rusted into scenery.",
    fact="You can tell the Portuguese houses from the Spanish ones by the "
         "roofline and the drainage: Portuguese roofs are tiled and slope to "
         "the street, Spanish ones are flat with gutters — the two occupations "
         "left their fingerprints on the same street.",
    tip="The ferry from Buenos Aires takes about an hour, so it is a day "
        "trip; stay the night instead and have the Calle de los Suspiros to "
        "yourself after the last boat leaves."),

# --- CUBA ---
"trinidad": dict(
    region="Sancti Spíritus",
    highlights=[("Plaza Mayor", None),
                ("Valle de los Ingenios", "Valle_de_los_Ingenios"),
                ("Iglesia de la Santísima Trinidad", None),
                ("Playa Ancón", None)],
    blurb="A sugar-money town of pastel houses and cobbles below the "
          "Escambray mountains, essentially frozen since the 1850s when the "
          "sugar economy collapsed and nobody had the money to modernise it.",
    fact="The Valle de los Ingenios next door held more than fifty sugar "
         "mills worked by tens of thousands of enslaved people; the "
         "Manaca Iznaga tower was built to watch them, and is climbable.",
    tip="The Casa de la Música is a flight of steps beside the main square, "
        "open to the air and free — the band starts around ten and the "
        "audience sits on the staircase."),
"varadero": dict(
    region="Matanzas",
    highlights=[("Hicacos Peninsula", None),
                ("Mansión Xanadú", None),
                ("Parque Josone", None),
                ("Cuevas de Bellamar", None)],
    blurb="Twenty kilometres of white sand on a thin peninsula east of "
          "Havana, and the centre of Cuban beach tourism — resorts along the "
          "whole spine, with a genuine little town at the western end.",
    fact="Mansión Xanadú was the DuPont family's private holiday house, built "
         "in 1930 with an Italian marble hall and a rooftop bar; after the "
         "revolution it became a restaurant and a golf clubhouse.",
    tip="Walk west past the hotel strip into Varadero town — ordinary "
        "streets, a market and paladares, and the same beach for nothing."),

# --- COSTA RICA ---
"arenal-volcano": dict(
    region="Alajuela Province",
    highlights=[("Arenal Volcano National Park",
                 "Arenal_Volcano_National_Park"),
                ("Lake Arenal", "Lake_Arenal"),
                ("La Fortuna Waterfall", "La_Fortuna_Waterfall_(Costa_Rica)"),
                ("Tabacón", None)],
    blurb="A near-perfect volcanic cone above the town of La Fortuna, with "
          "rainforest on its flanks and hot rivers running off it. It "
          "erupted continuously from 1968 to 2010 and now sits quiet, "
          "wrapped in cloud most afternoons.",
    fact="The 1968 eruption came without warning from a mountain everyone "
         "believed extinct, buried three villages and killed 87 people — and "
         "then kept going, with visible lava at night, for the next 42 years.",
    tip="The Río Chollín is a free hot river under a road bridge near "
        "Tabacón: the same volcanic water the resorts charge for, with "
        "somewhere to hang your towel."),
"monteverde": dict(
    region="Puntarenas Province",
    highlights=[("Monteverde Cloud Forest Reserve",
                 "Monteverde_Cloud_Forest_Reserve"),
                ("Santa Elena", None),
                ("Hanging bridges", None),
                ("Curi-Cancha Reserve", None)],
    blurb="Cloud forest on the continental divide at 1,400 m, where the trade "
          "winds hit the ridge and condense — the trees drip all day, "
          "everything is covered in moss and orchids, and the wildlife is "
          "heard far more often than seen.",
    fact="The reserve was bought and protected in 1972 by Quaker settlers who "
         "had moved to Costa Rica from Alabama in the 1950s, partly because "
         "the country had abolished its army.",
    tip="Go in at opening with the first guide of the day. Resplendent "
        "quetzals feed early, and the guides know which wild avocado trees "
        "they are working that week."),
"manuel-antonio": dict(
    region="Puntarenas Province",
    highlights=[("Playa Manuel Antonio", None),
                ("Playa Espadilla Sur", None),
                ("Cathedral Point", None),
                ("Quepos", "Quepos")],
    blurb="Costa Rica's smallest and busiest national park: rainforest "
          "running straight down to three white beaches, with sloths, "
          "capuchins and squirrel monkeys living along the trails at eye "
          "level.",
    fact="The park caps daily visitors and closes one day a week specifically "
         "to give the animals a break — a rule brought in after decades of "
         "monkeys learning to raid bags on the beach.",
    tip="Book online in advance, arrive at 7am, and keep your bag zipped. "
        "The raccoons here are professionals."),

# --- BELIZE ---
"belize-city": dict(
    region="Belize District",
    highlights=[("Swing Bridge", "Swing_Bridge_(Belize)"),
                ("St. John's Cathedral", "St._John's_Cathedral_(Belize_City)"),
                ("Belize Museum", None),
                ("Fort George Lighthouse", None)],
    blurb="Belize's largest town and old capital, at the mouth of the Haulover "
          "Creek on the Caribbean — low, wooden, hot, and the jumping-off "
          "point for the cayes and the reef.",
    fact="The Swing Bridge is one of the last manually operated swing bridges "
         "in the world: four men put poles into a capstan and walk it round "
         "to let boats through.",
    tip="The capital moved inland to Belmopan in 1970 after Hurricane Hattie "
        "flattened the city — which is why the country's government sits in "
        "a town of 20,000 an hour up the highway."),
"caracol": dict(
    region="Cayo District",
    highlights=[("Caana", None),
                ("Chiquibul Forest Reserve", None),
                ("Rio Frio Cave", None),
                ("Mountain Pine Ridge", "Mountain_Pine_Ridge_Forest_Reserve")],
    blurb="The largest Maya site in Belize, deep in the Chiquibul forest and "
          "reached down two hours of rough road. At its height it held more "
          "people than Belize City does today, and most of it is still under "
          "the trees.",
    fact="A carved altar here records Caracol's defeat of Tikal in AD 562 — a "
         "war between two superpowers 76 km apart that ended Tikal's "
         "monuments for over a century.",
    tip="Caana, the Sky Palace, is still one of the tallest structures in "
        "Belize at 43 m, and you are allowed to climb it."),
"ambergris-caye": dict(
    region="Belize District",
    highlights=[("Belize Barrier Reef", "Belize_Barrier_Reef"),
                ("Hol Chan Marine Reserve", "Hol_Chan_Marine_Reserve"),
                ("San Pedro", "San_Pedro_Town"),
                ("Great Blue Hole", "Great_Blue_Hole")],
    blurb="Belize's largest island, a sandy strip of golf carts and stilted "
          "bars a few hundred metres inside the second-largest barrier reef "
          "in the world. The reef breaks the swell, so the water is flat all "
          "the way to it.",
    fact="Ambergris Caye is geologically part of the Yucatán peninsula, "
         "separated from Mexico only by a narrow channel the Maya are "
         "believed to have dug themselves to shorten their trading route.",
    tip="Hol Chan's Shark Ray Alley is a 20-minute boat ride, and the nurse "
        "sharks and southern stingrays there turn up on their own — no "
        "feeding required, whatever the boat crews do."),
}


# ---------------------------------------------------------------------------
# MACHINERY
# ---------------------------------------------------------------------------
COUNTRY_CODE = {
    "Argentina": "AR", "Bolivia": "BO", "Brazil": "BR", "Chile": "CL",
    "Colombia": "CO", "Ecuador": "EC", "Guyana": "GY", "Paraguay": "PY",
    "Peru": "PE", "Suriname": "SR", "Uruguay": "UY", "Venezuela": "VE",
}

# Every NEW place is in South America. A P625 that lands outside this box means
# the slug resolved to a namesake somewhere else — the failure mode README
# warns about, where `Paradise_Cave` turns out to be in Poland. Wide enough for
# the Galápagos (-90.3°) and Fernando de Noronha (-32.4°) and nothing further.
SA_BOX = (-56.0, 13.5, -93.0, -28.0)          # lat_min, lat_max, lng_min, lng_max


def flag(code):
    """ISO alpha-2 -> flag emoji, the same derivation build_countries.py uses."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def slugs_wanted():
    """Every slug this batch needs an answer about, place-level and highlight."""
    out = []
    for spec in NEW.values():
        out.append(spec["slug"])
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
        order = {"UNRESOLVED": 0, "NOCOORD": 1, "OUTSIDE": 2, "MISSING": 3,
                 "SELF": 4, "FAR": 5, "REDIRECT": 6, "FIXENC": 7}
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
    if not (SA_BOX[0] <= lat <= SA_BOX[1] and SA_BOX[2] <= lng <= SA_BOX[3]):
        notes.add("OUTSIDE", pid, title,
                  f"P625 is {lat:.3f},{lng:.3f} — not South America")
        return None

    code = COUNTRY_CODE[spec["country"]]
    loc = {
        "id": pid,
        "name": spec["name"],
        "country": spec["country"],
        "country_code": code,
        "country_flag": flag(code),
        "continent": "South America",
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
                     ("hidden_gem_tip", "tip")):
        if spec.get(src) and not loc.get(key):
            loc[key] = spec[src]
            wrote.append(key)
    return wrote


def fix_encoding(locs, notes):
    """`Maracan%C3%A3_Stadium` is a URL, not a title.

    One slug in the corpus was stored percent-encoded. MediaWiki decodes it and
    answers anyway, so the audit never saw it — but it is the only one of 2,428
    written that way, and every consumer that concatenates it into a URL is one
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

    if notes.unresolved:
        # The whole point of the cache purge that preceded this batch: a
        # throttled request is not a verdict. Refuse to write a half-checked
        # file rather than silently drop the links the API never answered about.
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
