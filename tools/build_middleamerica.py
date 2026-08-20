#!/usr/bin/env python3
"""
build_middleamerica.py — the Mexico + Central America batch (2026-08).

WHAT WAS WRONG
    `latinamerica.json` held 93 places and was, in practice, a South America
    file. North of Colombia it had **twelve records**:

        Mexico      2   Mexico City, Cancún
        Costa Rica  4   San José, Arenal, Monteverde, Manuel Antonio
        Belize      3   Belize City, Caracol, Ambergris Caye
        Cuba        3   Havana, Trinidad, Varadero

    Two places for Mexico — 130 million people, 32 states, more UNESCO sites
    than any country in the Americas, and the atlas had the capital and one
    resort strip built on a sandbar in 1970. Oaxaca, Guanajuato, Mérida,
    Guadalajara, Monterrey, Chiapas, Baja and the whole Yucatán interior:
    nothing.

    And **four of the seven Central American countries were empty**.
    Guatemala — Tikal, Antigua, Lake Atitlán — had zero. So did Honduras
    (Copán, Roatán), El Salvador and Nicaragua. Panama had zero, which means
    the atlas did not contain the Panama Canal.

WHAT THIS DOES
    Adds Mexico and Central America to `latinamerica.json` on the frame in
    `tools/regionbuild.py`. Cuba moves out in the same round — see
    `build_caribbean.py`, which lifts the Caribbean into its own region
    because "Latin America" is the wrong shelf for Barbados and Aruba.

    Editorial choice is ours; every **coordinate comes from Wikidata P625**
    and every **slug is resolved live** and stored as the article's canonical
    title, per README "Filling a region out".

THE NAMESAKE PROBLEM HERE IS THE WORST IN THE ATLAS
    Canada's collisions were internal and Oceania's were rare. This region is
    bad in *three* directions at once, because it was named by the same empire
    that named half of Spain and then re-used every saint:

    · **Against Spain.** Mérida, Valladolid, Guadalajara, Córdoba, León,
      Granada, Salamanca, Santiago and Cartagena are all Spanish cities first
      on any search engine.
    · **Against South America.** La Paz is Bolivia's capital and a Baja
      fishing town. Córdoba is Argentina's second city. San Juan is
      Argentine, Puerto Rican and a dozen other things.
    · **Against each other.** León is in Nicaragua *and* Guanajuato, and both
      are in this batch. Santa Cruz, San Francisco, La Libertad, Santiago and
      San Pedro repeat across every isthmus country.

    So `search_name` is not an occasional patch here, it is the default: most
    records carry one. P17 catches the cross-border half at build time;
    nothing downstream can catch a namesake at search time, so it is said
    here, at the only point where we know which Mérida we meant.

STATE_BOX
    `regionbuild.subregion_check` gets Mexico's 32 states, for the same reason
    Canada got its provinces: P17 answers "Mexico" for the right Valladolid
    and for a wrong one 1,300 km away. Central American departments are NOT
    boxed — their namesakes are cross-border, which P17 already catches, and
    hand-drawing 60 department rectangles to guard against nothing would be
    ceremony. A missing key is simply skipped by the harness.

    Like P17 this is a WARNING. Some of these places genuinely straddle a
    state line (Popocatépetl is the Puebla/México/Morelos tripoint) and some
    belong to a state they are nowhere near — Revillagigedo is administered
    by Colima from 700 km offshore, which is why it gets its own row.

Run:  python3 tools/build_middleamerica.py                  # report only
      python3 tools/build_middleamerica.py --apply
      python3 tools/build_middleamerica.py --only oaxaca,tikal --apply
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regionbuild as rb

# Copied from build_countries.COUNTRIES — the NAME is the join key that
# build_countries.live_counts() matches on, so it is copied, never retyped.
COUNTRY_CODE = {
    "Mexico": "MX",
    "Guatemala": "GT",
    "Belize": "BZ",
    "El Salvador": "SV",
    "Honduras": "HN",
    "Nicaragua": "NI",
    "Costa Rica": "CR",
    "Panama": "PA",
}

# The coarse net, and the hard refusal. Mexico runs from the Guatemalan border
# (14.53°N) to the Rio Grande at 32.72°N, and from Guadalupe Island (118.4°W)
# to Isla Mujeres (86.7°W). Central America carries the south edge down to the
# Darién at 7.2°N and the east edge to Panama's Caribbean coast at 77.1°W.
# One rectangle covers both; the namesake work is STATE_BOX and search_name.
MA_LAT = (7.0, 33.0)
MA_LNG = (-118.6, -77.0)


def in_box(lat, lng):
    return MA_LAT[0] <= lat <= MA_LAT[1] and MA_LNG[0] <= lng <= MA_LNG[1]


# Hand-drawn and padded, because it is a warning and real places sit on real
# borders. Every string is also the user-visible `region` under the place name.
STATE_BOX = {
    "Baja California":        (27.9, 32.9, -118.5, -112.5),
    "Baja California Sur":    (22.7, 28.3, -115.6, -109.2),
    "Sonora":                 (26.1, 32.7, -115.3, -108.3),
    "Chihuahua":              (25.4, 32.0, -109.3, -103.1),
    "Coahuila":               (24.4, 30.1, -104.0, -99.6),
    "Nuevo León":             (23.0, 28.0, -101.4, -98.3),
    "Tamaulipas":             (22.1, 27.8, -100.3, -97.0),
    "Sinaloa":                (22.3, 27.2, -109.6, -105.2),
    "Durango":                (22.1, 27.0, -107.4, -102.3),
    "Zacatecas":              (20.9, 25.3, -104.5, -100.5),
    "San Luis Potosí":        (21.0, 24.6, -102.5, -98.1),
    "Nayarit":                (20.4, 23.2, -106.1, -103.5),
    "Jalisco":                (18.8, 22.9, -105.9, -101.3),
    "Aguascalientes":         (21.5, 22.6, -103.1, -101.7),
    "Guanajuato":             (19.8, 22.0, -102.4, -99.5),
    "Querétaro":              (19.9, 21.9, -100.8, -98.9),
    "Hidalgo":                (19.5, 21.6, -100.0, -97.8),
    "Colima":                 (18.5, 19.7, -104.9, -103.3),
    # Administered by Colima from 700 km offshore — a state box drawn around
    # the mainland would flag the archipelago every time. See the docstring.
    "Revillagigedo, Colima":  (18.2, 19.7, -115.3, -110.4),
    "Michoacán":              (17.7, 20.6, -103.9, -99.9),
    "State of Mexico":        (18.2, 20.4, -100.7, -98.4),
    "Valley of Mexico":       (18.9, 19.8, -99.5, -98.8),
    "Morelos":                (18.2, 19.3, -99.7, -98.4),
    "Tlaxcala":               (19.0, 19.9, -98.8, -97.4),
    "Puebla":                 (17.7, 21.0, -99.2, -96.6),
    "Veracruz":               (17.0, 22.6, -98.9, -93.4),
    "Guerrero":               (16.1, 19.0, -102.4, -97.8),
    "Oaxaca":                 (15.5, 18.8, -98.7, -93.6),
    "Chiapas":                (14.3, 18.0, -94.4, -90.2),
    "Tabasco":                (17.1, 18.8, -94.3, -90.8),
    "Campeche":               (17.6, 21.0, -92.6, -88.9),
    "Yucatán":                (19.4, 21.8, -90.6, -87.3),
    "Quintana Roo":           (17.7, 21.8, -89.5, -86.5),
}

REGION = rb.Region(
    target="latinamerica.json",
    continent="North America",
    country_code=COUNTRY_CODE,
    in_box=in_box,
    subregion_box=STATE_BOX,
)

# ---------------------------------------------------------------------------
# THE CURATED CONTENT.
#
# highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, a
# cuisine, an era, an animal or a festival. This region makes that rule very
# easy to break: "Day of the Dead", "Maya", "mariachi", "mole", "Garifuna",
# "Zapatistas", "quetzal", "Semana Santa" and "salsa" all read like places on
# the page and none of them is a thing a camera can be pointed at.
# `enrich_monuments.py` spends every highlight as a YouTube search term.
# (See enrich_monuments.NOT_A_MONUMENT.)
#
# A `None` slug is deliberate: the UI renders highlights as text chips, so a
# name with no link costs nothing and a dead link is rot.
# ---------------------------------------------------------------------------
NEW = {
# ========================= BAJA CALIFORNIA =========================
"tijuana": dict(
    name="Tijuana", slug="Tijuana", country="Mexico",
    region="Baja California", type="city", tag="famous",
    emoji="🛬", sounds=["city-hum.mp3"],
    highlights=[("Avenida Revolución", "Avenida_Revolución"),
                ("Tijuana Cultural Center", "Tijuana_Cultural_Center"),
                ("San Ysidro Port of Entry", "San_Ysidro_Port_of_Entry"),
                ("Playas de Tijuana", None),
                ("Border wall at the Pacific", None)],
    blurb="The busiest land border crossing on Earth ends here, and the city "
          "that grew around it is nothing like the punchline it spent the "
          "20th century being. Two million people, a Baja Med food scene that "
          "invented the Caesar salad, and a craft-brewing district that draws "
          "San Diegans back across the line every weekend.",
    fact="The border fence runs straight into the Pacific at Playas de "
         "Tijuana and stops in the surf. Families have talked through its "
         "bars for decades — the section there is known as Friendship Park.",
    tip="Skip Revolución and go to Pasaje Rodríguez, a covered 1960s shopping "
        "arcade that failed and was taken over by galleries, bookshops and "
        "coffee. Two blocks off the tourist strip and a different city."),
"ensenada": dict(
    name="Ensenada", slug="Ensenada,_Baja_California", country="Mexico",
    region="Baja California", type="coastal", tag="hidden",
    emoji="🍤", sounds=["ocean-waves.mp3"],
    search_name="Ensenada Baja California",
    highlights=[("La Bufadora", "La_Bufadora"),
                ("Riviera del Pacífico", None),
                ("Bahía de Todos Santos", None),
                ("Malecón de Ensenada", None)],
    blurb="A working port on a wide Pacific bay 100 km south of the border, "
          "and the front door to Baja's wine country. Cruise ships tie up at "
          "one end of the malecón; the fish market at the other end has been "
          "selling the taco the entire genre is descended from since 1958.",
    fact="La Bufadora is one of the largest marine geysers in the world — a "
         "sea cave that compresses incoming swell and fires it 30 m up the "
         "cliff, roughly once a minute, all day, for free.",
    tip="The fish market at the harbour end of the malecón opens at dawn. Eat "
        "a battered fish taco standing up at 7 a.m. and you have had the "
        "original, in the town that made it, before any tour bus arrives."),
"valle-de-guadalupe": dict(
    name="Valle de Guadalupe", slug="Valle_de_Guadalupe", country="Mexico",
    region="Baja California", type="nature", tag="hidden",
    emoji="🍷", sounds=["desert-wind.mp3"],
    highlights=[("Ruta del Vino", None),
                ("Museo de la Vid y el Vino", None),
                ("Bodegas de Santo Tomás", None),
                ("Ensenada", "Ensenada,_Baja_California")],
    blurb="A dry inland valley 30 km from the Pacific that produces roughly "
          "three-quarters of Mexico's wine, in a landscape of granite "
          "boulders and dust that looks far more like Paso Robles than like "
          "anything the word Baja suggests. The architecture is the draw as "
          "much as the wine — wineries here are built out of rusted steel, "
          "salvaged boats and rammed earth.",
    fact="The valley was settled in 1905 by Molokans, Russian pacifist "
         "dissenters fleeing the Tsar, who planted the first commercial "
         "vineyards. A few of their farmhouses are still standing.",
    tip="Go midweek. There is one dirt road through the valley, it has no "
        "shoulder, and on a Saturday the drive between two tasting rooms 4 km "
        "apart can take 40 minutes."),
"guadalupe-island": dict(
    name="Guadalupe Island", slug="Guadalupe_Island", country="Mexico",
    region="Baja California", type="island", tag="hidden",
    emoji="🦈", sounds=["ocean-waves.mp3"],
    highlights=[("Mount Augusta", None),
                ("Northeast Anchorage", None),
                ("Guadalupe fur seal rookeries", None)],
    blurb="A volcanic island 240 km off the Baja coast, so far out and so "
          "clear that it became the world's reference site for great white "
          "shark research: visibility routinely past 30 m, against the 5 m "
          "you get in South Africa or the Farallones. A biosphere reserve, "
          "with a small naval detachment and a fishing camp and nothing else.",
    fact="Mexico closed the island to shark cage-diving entirely in 2022 to "
         "protect the population — the site that made the footage everyone "
         "has seen is now off limits to the boats that shot it.",
    tip="You cannot casually visit; permits go to research and fishing. The "
        "island's real story is on land — goats introduced in the 1800s ate "
        "the cloud forest to bare rock, and a 2007 eradication has it slowly "
        "coming back."),
"mexicali": dict(
    name="Mexicali", slug="Mexicali", country="Mexico",
    region="Baja California", type="city", tag="hidden",
    emoji="🌵", sounds=["desert-wind.mp3"],
    highlights=[("La Chinesca", "La_Chinesca"),
                ("Bosque de la Ciudad", None),
                ("Cerro El Centinela", None),
                ("Laguna Salada", "Laguna_Salada_(Mexico)")],
    blurb="The state capital, sitting in the Colorado Desert at sea level "
          "where summer afternoons pass 48 °C. It was built by an American "
          "land company to farm cotton, and the labour came from Guangdong — "
          "which is why a Sonoran border city has one of the oldest "
          "Chinatowns in the Americas underneath its streets.",
    fact="La Chinesca is partly subterranean. Basements were dug as cool "
         "living space in the 1920s and grew into a connected underground "
         "quarter of shops and halls; a few tunnels are open again as a "
         "museum route.",
    tip="Mexicali's Chinese-Mexican food is its own cuisine, not a "
        "transplant. Ask for it *estilo Mexicali* and you get soy, chile and "
        "flour tortillas on the same plate."),
"bahia-de-los-angeles": dict(
    name="Bahía de los Ángeles", slug="Bahía_de_los_Ángeles", country="Mexico",
    region="Baja California", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Isla Ángel de la Guarda", "Isla_Ángel_de_la_Guarda"),
                ("Gulf of California", "Gulf_of_California"),
                ("Sierra de la Asamblea", None)],
    blurb="A desert bay on the Gulf side of Baja, ringed by sixteen islands "
          "and backed by mountains that come down to the water with no coast "
          "road for 200 km in either direction. Whale sharks feed in the bay "
          "from summer into autumn, in water shallow enough to stand in.",
    fact="The channel outside the bay has some of the strongest tidal "
         "currents in the Gulf of California, and the upwelling they drive is "
         "why an otherwise barren desert coast supports whales, sea lions and "
         "whale sharks in the same square kilometre.",
    tip="There is no bank, no chain hotel and, for most of the day, no phone "
        "signal. Fill the tank in Guerrero Negro or Cataviña before you turn "
        "off Highway 1 — the spur road is 68 km with nothing on it."),
# ========================= BAJA CALIFORNIA SUR =========================
"cabo-san-lucas": dict(
    name="Cabo San Lucas", slug="Cabo_San_Lucas", country="Mexico",
    region="Baja California Sur", type="coastal", tag="famous",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    highlights=[("El Arco de Cabo San Lucas", "El_Arco_de_Cabo_San_Lucas"),
                ("Playa del Amor", None),
                ("Marina Cabo San Lucas", None),
                ("Land's End", None)],
    blurb="The tip of the 1,250 km Baja peninsula, where the Sea of Cortez "
          "meets the Pacific at a granite headland that has been eroded into "
          "an arch. Jacques Cousteau called the water off it the world's "
          "aquarium; the town behind it is a marina, a strip of clubs and a "
          "wall of resorts.",
    fact="Playa del Amor and Playa del Divorcio are back-to-back on the same "
         "narrow spit — one faces the calm Sea of Cortez and is swimmable, "
         "the other faces the open Pacific and will kill you. Thirty metres "
         "apart.",
    tip="Take a panga out at sunrise rather than midday. The arch is "
        "east-facing, the light is behind you, and the sea-lion colony on the "
        "rocks is awake and noisy before the tour fleet arrives."),
"san-jose-del-cabo": dict(
    name="San José del Cabo", slug="San_José_del_Cabo", country="Mexico",
    region="Baja California Sur", type="city", tag="hidden",
    emoji="🎨", sounds=["ocean-waves.mp3"],
    highlights=[("Mission San José del Cabo Añuití",
                 "Misión_San_José_del_Cabo_Añuití"),
                ("Gallery District", None),
                ("Estero San José", None),
                ("Playa Palmilla", None)],
    blurb="The older, quieter half of the Los Cabos pair, 33 km up the coast "
          "from the marina and a century and a half older than it. A colonial "
          "grid around a mission church, a plaza with laurel trees, and an "
          "art district that fills the streets every Thursday evening from "
          "November to June.",
    fact="A freshwater estuary meets the sea at the edge of town — a rarity "
         "on a desert peninsula, and enough of one that some 200 bird species "
         "have been recorded in a lagoon a short walk from the beach resorts.",
    tip="The Art Walk on Thursday nights is genuinely the town at its best: "
        "galleries open late, streets close, and it is free. The rest of the "
        "week the same district is empty and worth walking anyway."),
"la-paz-bcs": dict(
    name="La Paz", slug="La_Paz,_Baja_California_Sur", country="Mexico",
    region="Baja California Sur", type="coastal", tag="hidden",
    emoji="🐠", sounds=["ocean-waves.mp3"],
    search_name="La Paz Baja California Sur Mexico",
    highlights=[("Malecón de La Paz", None),
                ("Balandra Beach", "Balandra_Beach"),
                ("Isla Espíritu Santo", "Isla_Espíritu_Santo"),
                ("Playa El Tecolote", None)],
    blurb="The state capital, on a sheltered bay of the Sea of Cortez, and "
          "the antidote to Los Cabos two hours south: a real city that "
          "happens to sit on turquoise water, with a 5 km waterfront "
          "promenade that the whole town walks at sunset. The sun sets over "
          "the sea here, which on the Gulf coast it has no business doing.",
    fact="Balandra's mushroom-shaped rock is so shallow that the whole bay is "
         "wadeable for hundreds of metres. The original rock collapsed in "
         "2005 and locals rebuilt it — the landmark on the postcards is a "
         "restoration.",
    tip="Swim with the sea lion colony at Los Islotes off Espíritu Santo. It "
        "is a permitted, capped activity, the animals are wild and curious, "
        "and it costs a fraction of what the same trip costs from Cabo."),
"loreto-bcs": dict(
    name="Loreto", slug="Loreto,_Baja_California_Sur", country="Mexico",
    region="Baja California Sur", type="coastal", tag="hidden",
    emoji="⛪", sounds=["ocean-waves.mp3"],
    search_name="Loreto Baja California Sur Mexico",
    highlights=[("Misión de Nuestra Señora de Loreto",
                 "Misión_de_Nuestra_Señora_de_Loreto_Conchó"),
                ("Bahía de Loreto National Park",
                 "Bahía_de_Loreto_National_Park"),
                ("Isla Coronado", None),
                ("Sierra de la Giganta", "Sierra_de_la_Giganta"),
                ("San Javier Mission", "Misión_San_Francisco_Javier_de_Viggé-Biaundó")],
    blurb="The first permanent Spanish settlement in the Californias, founded "
          "1697, and the capital of the whole territory for 132 years — the "
          "mission here is the mother church from which every mission up to "
          "Sonoma was founded. Today it is a town of 15,000 between a marine "
          "park and a 1,500 m escarpment.",
    fact="The stone over the mission door still reads *Cabeza y Madre de las "
         "Misiones de Baja y Alta California* — head and mother of the "
         "missions. San Diego, Los Angeles and San Francisco all descend from "
         "this doorway.",
    tip="Drive the 36 km mountain road to San Javier. It is the best-"
        "preserved mission in the Californias, built of cut stone in a canyon "
        "with an olive tree planted by the Jesuits still fruiting beside it."),
"todos-santos": dict(
    name="Todos Santos", slug="Todos_Santos,_Baja_California_Sur",
    country="Mexico",
    region="Baja California Sur", type="coastal", tag="hidden",
    emoji="🌴", sounds=["ocean-waves.mp3"],
    search_name="Todos Santos Baja California Sur",
    highlights=[("Hotel California", None),
                ("Playa Los Cerritos", None),
                ("Misión Santa Rosa de las Palmas", None),
                ("Sierra de la Laguna", "Sierra_de_la_Laguna")],
    blurb="A former sugar town on the Pacific side of the peninsula, an hour "
          "north of Cabo, which turned into an artists' colony when the mills "
          "closed and the surfers found the point breaks. Palm oases run down "
          "to a coast with no reef and serious water.",
    fact="The local Hotel California has no connection to the Eagles song — "
         "the band have said so repeatedly and sued over the merchandise — "
         "but the town has been happily selling the coincidence since 1993.",
    tip="Swim at Los Cerritos, 12 km south, and nowhere closer. The beach at "
        "the edge of town is beautiful, unpatrolled and has a rip that drowns "
        "people most years."),
"espiritu-santo-bcs": dict(
    name="Isla Espíritu Santo", slug="Isla_Espíritu_Santo", country="Mexico",
    region="Baja California Sur", type="island", tag="hidden",
    emoji="🦭", sounds=["ocean-waves.mp3"],
    highlights=[("Ensenada Grande", None),
                ("Los Islotes", None),
                ("Bahía San Gabriel", None),
                ("Gulf of California", "Gulf_of_California")],
    blurb="An uninhabited island of pink volcanic rock 25 km off La Paz, cut "
          "on its west side into a row of deep coves with white sand at the "
          "back of each one. It is a UNESCO site as part of the Islands and "
          "Protected Areas of the Gulf of California, and there is nothing "
          "built on it at all.",
    fact="The island has an endemic mammal found nowhere else on Earth — the "
         "black jackrabbit, *Lepus insularis*, which is the size of an ordinary "
         "jackrabbit and almost entirely dark.",
    tip="Camping is permitted with a park bracelet, on a handful of beaches, "
        "with everything carried in and out. A night at Ensenada Grande with "
        "no light on the water is the reason to go rather than day-trip."),
"cabo-pulmo": dict(
    name="Cabo Pulmo", slug="Cabo_Pulmo", country="Mexico",
    region="Baja California Sur", type="coastal", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    highlights=[("Cabo Pulmo National Park", None),
                ("Los Frailes", None),
                ("Sea of Cortez reef", None)],
    blurb="A village of about 150 people on the East Cape, in front of the "
          "only hard coral reef in the Gulf of California and one of very few "
          "in the eastern Pacific. It is also the most successful marine "
          "reserve anybody has measured.",
    fact="The fishing families themselves asked for the ban in 1995, after "
         "their catch collapsed. Ten years of full no-take protection "
         "increased the reef's fish biomass by more than 400 percent — the "
         "largest recovery ever recorded in a marine reserve.",
    tip="Dive or snorkel Los Islotes-style bull shark and jack aggregations "
        "here in late summer, then eat at one of the four palapas in the "
        "village. There is no ATM, no petrol and the road in is graded dirt."),
"guerrero-negro": dict(
    name="Guerrero Negro", slug="Guerrero_Negro", country="Mexico",
    region="Baja California Sur", type="coastal", tag="hidden",
    emoji="🐳", sounds=["ocean-waves.mp3"],
    highlights=[("Ojo de Liebre Lagoon", "Ojo_de_Liebre_Lagoon"),
                ("El Vizcaíno Biosphere Reserve",
                 "El_Vizcaíno_Biosphere_Reserve"),
                ("Guerrero Negro saltworks", None),
                ("Desierto de Vizcaíno", None)],
    blurb="A salt town at the 28th parallel, exactly halfway down the "
          "peninsula, next to the largest solar saltworks in the world. It "
          "exists for two reasons: salt, and the grey whales that swim 8,000 "
          "km from the Bering Sea to give birth in the lagoon beside it every "
          "winter.",
    fact="Ojo de Liebre is the main calving lagoon for the entire eastern "
         "Pacific grey whale population. Boats are permitted close in because "
         "the mothers approach them — the same lagoon where whalers nearly "
         "exterminated the species now has whales that come over to be "
         "touched.",
    tip="The season is roughly January to early April and the town is "
        "otherwise a salt works with a motel strip. Go in February, take the "
        "first boat of the morning, and stay somewhere else the rest of the "
        "year."),
"bahia-magdalena": dict(
    name="Magdalena Bay", slug="Magdalena_Bay", country="Mexico",
    region="Baja California Sur", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Isla Magdalena", None),
                ("Puerto San Carlos", None),
                ("Isla Santa Margarita", None),
                ("Boca de Soledad", None)],
    blurb="A 50 km lagoon system on the Pacific coast, shielded from the open "
          "ocean by two long barrier islands of pure dune. Mangroves at the "
          "back, sand mountains at the front, grey whales in the middle in "
          "winter and a marlin fishery outside the mouth all year.",
    fact="During the Second World War the bay was surveyed as a possible "
         "major naval base — deep, enclosed, invisible from the sea and "
         "almost completely uninhabited. Nothing was ever built.",
    tip="Cross the lagoon by panga to Isla Magdalena and walk over the dunes "
        "to the Pacific side. Twenty minutes on foot, and the beach on the "
        "far shore usually has nobody on it for its whole visible length."),
"sierra-de-san-francisco": dict(
    name="Sierra de San Francisco", slug="Rock_Paintings_of_Sierra_de_San_Francisco",
    country="Mexico",
    region="Baja California Sur", type="history", tag="hidden",
    emoji="🖐️", sounds=["desert-wind.mp3"],
    highlights=[("Cueva del Ratón", None),
                ("Cueva Pintada", None),
                ("San Ignacio", "San_Ignacio,_Baja_California_Sur"),
                ("El Vizcaíno Biosphere Reserve",
                 "El_Vizcaíno_Biosphere_Reserve")],
    blurb="A range of volcanic mesas in the middle of the peninsula holding "
          "several hundred painted rock shelters — life-size human figures in "
          "red and black, deer, whales and rays, on ceilings ten metres up. "
          "A UNESCO World Heritage Site, and one of the great rock art "
          "concentrations anywhere.",
    fact="The Jesuits who found them in the 1700s asked the local Cochimí who "
         "had painted them and were told: a race of giants from the north. "
         "The paintings are up to 7,500 years old and nobody has improved much "
         "on that answer since.",
    tip="Everything past the roadside Cueva del Ratón requires a licensed "
        "guide, a permit and a mule — Cueva Pintada is a full day's ride down "
        "into a canyon. Arrange it in San Ignacio, not online."),
# ========================= SONORA & THE NORTHWEST =========================
"puerto-penasco": dict(
    name="Puerto Peñasco", slug="Puerto_Peñasco", country="Mexico",
    region="Sonora", type="coastal", tag="hidden",
    emoji="🦀", sounds=["ocean-waves.mp3"],
    highlights=[("Gulf of California", "Gulf_of_California"),
                ("Cerro de la Ballena", None),
                ("Estero Morúa", None),
                ("Malecón de Puerto Peñasco", None)],
    blurb="A shrimping port at the top of the Gulf of California, four hours "
          "from Phoenix and known to most of its visitors as Rocky Point. The "
          "tide here runs up to seven metres — one of the biggest ranges on "
          "the Pacific side of the Americas — so the beach doubles in width "
          "twice a day and the tide pools it leaves are a marine biology "
          "field trip.",
    fact="The town sits between an ocean and a lava field: the Pinacate "
         "volcanic shield starts 50 km inland, and NASA sent Apollo crews "
         "there to train on its craters because it was the closest thing to "
         "the lunar surface they could drive to.",
    tip="Walk out at the lowest tide of the month at Sandy Beach. Kilometres "
        "of seafloor come up dry, full of sand dollars and octopus, and it "
        "costs nothing."),
"el-pinacate": dict(
    name="El Pinacate", slug="El_Pinacate_y_Gran_Desierto_de_Altar_Biosphere_Reserve",
    country="Mexico",
    region="Sonora", type="desert", tag="hidden",
    emoji="🌑", sounds=["desert-wind.mp3"],
    highlights=[("El Elegante Crater", None),
                ("Gran Desierto de Altar", "Gran_Desierto_de_Altar"),
                ("Cerro Pinacate", None),
                ("Sierra del Rosario", None)],
    blurb="A black shield volcano sitting in the largest active dune field in "
          "North America, on the Arizona border. Ten enormous maar craters, "
          "400 cinder cones, and then 5,000 km² of moving sand. A UNESCO "
          "World Heritage Site, and one of the hottest, driest places on the "
          "continent.",
    fact="Apollo astronauts trained in these craters in 1965 and 1970 — "
         "Aldrin, Armstrong and the Apollo 14 crew among them — because the "
         "maars are the best terrestrial analogue for lunar impact craters "
         "that exists on a road.",
    tip="El Elegante is 1.6 km across and 250 m deep and you can drive to "
        "within a short walk of the rim on a graded track. Carry all your own "
        "water; there is none in the reserve, at all."),
"san-carlos-sonora": dict(
    name="San Carlos", slug="San_Carlos,_Sonora", country="Mexico",
    region="Sonora", type="coastal", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    search_name="San Carlos Sonora Mexico",
    highlights=[("Cerro Tetakawi", None),
                ("Playa Los Algodones", None),
                ("Bahía San Francisco", None),
                ("Guaymas", "Guaymas")],
    blurb="A resort bay on the Sonoran coast under a twin-horned volcanic "
          "peak, where the Sonoran Desert runs straight into the Sea of "
          "Cortez and cardón cactus grow within sight of the water. Sheltered "
          "enough to be one of the biggest boat-storage harbours in Mexico.",
    fact="*Catch-22* was filmed here in 1969. The production built a full "
         "airfield with a fleet of restored B-25 bombers — briefly the "
         "twelfth-largest air force in the world — on the flats outside "
         "town.",
    tip="Climb Tetakawi at first light. It is a steep, unshaded 90 minutes to "
        "the saddle and the view takes in the whole bay, the desert behind it "
        "and the islands offshore before the heat arrives."),
"alamos": dict(
    name="Álamos", slug="Álamos", country="Mexico",
    region="Sonora", type="history", tag="hidden",
    emoji="🏛️", sounds=["plaza.mp3"],
    search_name="Álamos Sonora Pueblo Mágico",
    highlights=[("Plaza de Armas", None),
                ("Parroquia de la Purísima Concepción", None),
                ("Museo Costumbrista de Sonora", None),
                ("Sierra de Álamos", None)],
    blurb="A silver town in the foothills of the Sierra Madre Occidental "
          "that made a fortune in the 1700s, went bankrupt, emptied out, and "
          "was bought back street by street from the 1950s onwards. The "
          "result is a complete Andalusian colonial town of arcaded "
          "courtyard houses, at the northern edge of the tropical dry forest.",
    fact="The Mexican jumping bean is an Álamos export. The 'bean' is a seed "
         "capsule with a moth larva inside; the town has shipped them by the "
         "million and once held an annual festival for them.",
    tip="Almost every great house is a private courtyard behind a plain "
        "wall. The Friday morning house-and-garden tour run by the local "
        "library is the only way most of them are ever open to anyone."),
"hermosillo": dict(
    name="Hermosillo", slug="Hermosillo", country="Mexico",
    region="Sonora", type="city", tag="hidden",
    emoji="🌡️", sounds=["desert-wind.mp3"],
    highlights=[("Catedral de la Asunción", None),
                ("Cerro de la Campana", None),
                ("Museo de Culturas Populares e Indígenas de Sonora", None),
                ("Plaza Zaragoza", None)],
    blurb="The Sonoran state capital, a car-manufacturing and cattle city of "
          "just under a million people in the middle of a desert basin. It is "
          "reliably one of the hottest cities in Mexico — 45 °C in June is "
          "unremarkable — and its food culture is built almost entirely "
          "around beef and flour tortillas.",
    fact="Sonoran flour tortillas are stretched so thin they are translucent "
         "and can reach a metre across — the *tortilla sobaquera*, named for "
         "being draped over the forearm to stretch it.",
    tip="Climb the Cerro de la Campana at dusk. It is a small hill right in "
        "the centre with a road up it, and it is the only place the city's "
        "grid and the desert around it read as one thing."),
"copper-canyon": dict(
    name="Copper Canyon", slug="Copper_Canyon", country="Mexico",
    region="Chihuahua", type="nature", tag="famous",
    emoji="🚂", sounds=["mountain-wind.mp3"],
    highlights=[("Urique Canyon", None),
                ("Divisadero", None),
                ("Chihuahua–Pacific Railway", "Chihuahua_al_Pacífico"),
                ("Creel", "Creel,_Chihuahua"),
                ("Basaseachic Falls", "Basaseachic_Falls")],
    blurb="Six major canyons in the Sierra Madre Occidental, several of them "
          "deeper than the Grand Canyon and together covering four times its "
          "area. The Rarámuri have lived in them for centuries and still farm "
          "the canyon floors, which sit in the tropics while the rim above "
          "them gets snow.",
    fact="The railway through it took 90 years to finish, opening in 1961. "
         "Its 653 km cross 37 bridges and 86 tunnels and climb 2,400 m — one "
         "loop at Temoris crosses over itself on three levels to gain height.",
    tip="Get off the train. The great mistake is riding it end to end in a "
        "day; two nights at Divisadero or in Batopilas at the canyon bottom "
        "is the difference between a view and a place."),
"creel": dict(
    name="Creel", slug="Creel,_Chihuahua", country="Mexico",
    region="Chihuahua", type="mountain", tag="hidden",
    emoji="🌲", sounds=["mountain-wind.mp3"],
    highlights=[("Valle de los Hongos", None),
                ("Lago Arareko", None),
                ("Cusárare Falls", None),
                ("Recowata hot springs", None)],
    blurb="A logging and railway town at 2,340 m on the Copper Canyon rim, "
          "and the practical base for the whole sierra. Pine forest, cold "
          "nights, rock formations weathered into mushrooms and frogs, and "
          "the largest Rarámuri population of any town in Mexico.",
    fact="Rarámuri means 'those who run on foot'. Persistence running is a "
         "real and living practice here — *rarajipari*, a race in which teams "
         "kick a wooden ball along canyon trails, can run continuously for "
         "more than a day.",
    tip="Rent a bike rather than take the minibus loop. The Arareko lake "
        "circuit and the mushroom valley are within an easy ride on quiet "
        "forest roads, and you set your own stops."),
"batopilas": dict(
    name="Batopilas", slug="Batopilas,_Chihuahua", country="Mexico",
    region="Chihuahua", type="history", tag="hidden",
    emoji="⛏️", sounds=["mountain-wind.mp3"],
    highlights=[("Hacienda San Miguel", None),
                ("Lost Cathedral of Satevó", None),
                ("Batopilas River", None),
                ("Urique Canyon", None)],
    blurb="A silver town of 1,200 people on a river at the bottom of a "
          "canyon, 1,800 m below the rim and reached by a road of switchbacks "
          "that was not paved until 2018. It was the second town in Mexico to "
          "get electric light, in 1880, before most of Europe.",
    fact="Seven kilometres downstream stands a domed adobe church nobody can "
         "account for. There is no record of who built the Satevó church or "
         "when — the mission archives are simply silent about it — so it is "
         "known locally as the Lost Cathedral.",
    tip="The canyon floor is subtropical and 20 degrees warmer than Creel on "
        "the rim. Walk the river track down to Satevó in the early morning "
        "and hitch back up; it is flat, shaded and almost carless."),
"chihuahua-city": dict(
    name="Chihuahua", slug="Chihuahua_City", country="Mexico",
    region="Chihuahua", type="city", tag="hidden",
    emoji="🐎", sounds=["city-hum.mp3"],
    search_name="Chihuahua City Mexico",
    highlights=[("Chihuahua Cathedral", "Chihuahua_Cathedral"),
                ("Quinta Gameros", "Quinta_Gameros"),
                ("Casa de Pancho Villa", None),
                ("Palacio de Gobierno", None),
                ("Aqueduct of Chihuahua", None)],
    blurb="The capital of Mexico's largest state, a high-desert cattle and "
          "mining city with a baroque cathedral that took 91 years to build "
          "and an Art Nouveau mansion that would not be out of place in "
          "Brussels. It is the northern terminus of the Copper Canyon "
          "railway and the city Pancho Villa ran his division from.",
    fact="Miguel Hidalgo, who began the war of independence, was executed "
         "here in 1811. The cell he was held in is preserved beneath the "
         "state government offices, with the words he wrote on its wall.",
    tip="Quinta Gameros is the reason to stop. A 1907 mansion built for a "
        "mining engineer, kept with its original French furniture, and one of "
        "the best Art Nouveau interiors anywhere in the Americas."),
"basaseachic": dict(
    name="Basaseachic Falls", slug="Basaseachic_Falls", country="Mexico",
    region="Chihuahua", type="nature", tag="hidden",
    emoji="💦", sounds=["waterfall.mp3"],
    highlights=[("Candameña Canyon", None),
                ("Piedra Volada", None),
                ("Sierra Madre Occidental", "Sierra_Madre_Occidental")],
    blurb="A single 246 m drop into the Candameña Canyon — the second-highest "
          "waterfall in Mexico, in a national park of pine forest and rock "
          "walls that draws big-wall climbers to routes 900 m high. The "
          "falls run hardest from July to September.",
    fact="The highest waterfall in Mexico, Piedra Volada at 453 m, is in the "
         "same canyon and was only measured in 1995 — it flows for a few "
         "weeks a year and had been overlooked because most visitors came in "
         "the dry season.",
    tip="Two viewpoints: the rim one is a ten-minute walk and shows the whole "
        "drop, the pool at the bottom is a steep hour down and back. Do the "
        "bottom one first, while it is cool."),
"cuatro-cienegas": dict(
    name="Cuatro Ciénegas", slug="Cuatro_Ciénegas", country="Mexico",
    region="Coahuila", type="desert", tag="hidden",
    emoji="🦠", sounds=["desert-wind.mp3"],
    highlights=[("Poza Azul", None),
                ("Dunas de Yeso", None),
                ("Río Mezquites", None),
                ("Sierra de San Marcos", None)],
    blurb="A desert valley in Coahuila holding hundreds of spring-fed pools "
          "of astonishing blue, plus a dune field of pure white gypsum. The "
          "pools are biologically isolated and hold dozens of species found "
          "nowhere else, along with living stromatolites — the same microbial "
          "reefs that dominated Earth for two billion years.",
    fact="NASA has studied the valley for decades as a Mars analogue: the "
         "water is nearly devoid of phosphorus, and the bacteria living in it "
         "have evolved workarounds that look like nothing else on Earth.",
    tip="Only a few pools are open — Poza Azul is a boardwalk with no "
        "swimming, and the Río Mezquites and Playitas are where you can get "
        "in. Sunscreen is banned in the water and the rule is enforced."),
"saltillo": dict(
    name="Saltillo", slug="Saltillo", country="Mexico",
    region="Coahuila", type="city", tag="hidden",
    emoji="🧵", sounds=["city-hum.mp3"],
    highlights=[("Catedral de Santiago", "Cathedral_of_Saltillo"),
                ("Museo del Desierto", "Museo_del_Desierto"),
                ("Plaza de Armas", None),
                ("Sierra de Zapalinamé", None)],
    blurb="The oldest city in northeastern Mexico, founded 1577, at 1,600 m "
          "on a high desert plateau — which gives it a genuinely mild climate "
          "in a region that has none. Its churrigueresque cathedral facade is "
          "one of the most elaborate in northern Mexico, and it is now "
          "surrounded by one of the country's densest car-manufacturing belts.",
    fact="The *sarape de Saltillo* is the ancestor of the whole Mexican "
         "blanket tradition: a finely woven wool mantle with a diamond centre "
         "that was traded as far as Peru, and which the ponchos of a hundred "
         "westerns are copying badly.",
    tip="The Museo del Desierto is far better than a regional museum has any "
        "right to be — Coahuila is one of the richest dinosaur-fossil states "
        "in the Americas and most of what is on display was dug up nearby."),
"parras": dict(
    name="Parras de la Fuente", slug="Parras_de_la_Fuente", country="Mexico",
    region="Coahuila", type="history", tag="hidden",
    emoji="🍇", sounds=["desert-wind.mp3"],
    highlights=[("Casa Madero", "Casa_Madero"),
                ("Estanque de la Luz", None),
                ("Iglesia del Santo Madero", None),
                ("Sierra de Parras", None)],
    blurb="An oasis town in the Coahuila desert, fed by springs strong enough "
          "to irrigate vineyards and walnut groves in country that is "
          "otherwise scrub. It has been making wine since 1597, which makes "
          "it the oldest wine region in the Americas by nearly two centuries.",
    fact="Casa Madero, founded in 1597 as the Hacienda San Lorenzo, is the "
         "oldest winery in the Americas and still operating on the same site "
         "— its stone cellars predate every vineyard in California, Chile and "
         "Argentina.",
    tip="The town's springs feed open-air public pools — the *estanques* — "
        "that the whole town swims in through summer. They cost a few pesos "
        "and are the closest thing to the town's living room."),
"monterrey": dict(
    name="Monterrey", slug="Monterrey", country="Mexico",
    region="Nuevo León", type="city", tag="famous",
    emoji="🏔️", sounds=["city-hum.mp3"],
    highlights=[("Cerro de la Silla", "Cerro_de_la_Silla"),
                ("Macroplaza", "Macroplaza"),
                ("Parque Fundidora", "Parque_Fundidora"),
                ("Faro del Comercio", None),
                ("Museo de Arte Contemporáneo de Monterrey",
                 "Museo_de_Arte_Contemporáneo_de_Monterrey"),
                ("Barrio Antiguo", None)],
    blurb="Mexico's industrial capital and its wealthiest large city, wedged "
          "into a bowl of the Sierra Madre Oriental with a saddle-shaped "
          "mountain over one shoulder. Five million people, a skyline of "
          "corporate towers, and a decommissioned steelworks in the middle of "
          "it that has been turned into the best urban park in the country.",
    fact="The Macroplaza is one of the largest city squares in the world — "
         "40 hectares, created in the 1980s by demolishing dozens of downtown "
         "blocks. Only Tiananmen and a handful of others are bigger.",
    tip="Walk the Paseo Santa Lucía, a 2.5 km artificial river channel that "
        "links the Macroplaza to Fundidora. It cost a fortune, it is entirely "
        "artificial, and it is genuinely lovely at night."),
"cumbres-de-monterrey": dict(
    name="Cumbres de Monterrey", slug="Cumbres_de_Monterrey_National_Park",
    country="Mexico",
    region="Nuevo León", type="mountain", tag="hidden",
    emoji="🥾", sounds=["mountain-wind.mp3"],
    highlights=[("Cascada Cola de Caballo", None),
                ("Cañón de la Huasteca", None),
                ("Cerro de la Silla", "Cerro_de_la_Silla"),
                ("Matacanes", None)],
    blurb="A national park of 1,770 km² wrapped around Monterrey's western "
          "and southern edges — limestone canyons with 300 m vertical walls "
          "coming down to within sight of the ring road. It is the reason a "
          "heavy-industry city is also one of Latin America's best rock "
          "climbing and canyoning destinations.",
    fact="The Cañón de la Huasteca's rock is folded so violently that the "
         "strata stand vertically — the mountains here were laid down flat on "
         "a seabed and turned on end by the same collision that raised the "
         "Sierra Madre Oriental.",
    tip="Matacanes is a full-day canyon of jumps, rappels and an underground "
        "river swim, run by licensed guides only. Go in the wet season, "
        "June to September, or the river is a walk."),
"durango-city": dict(
    name="Durango", slug="Durango,_Durango", country="Mexico",
    region="Durango", type="city", tag="hidden",
    emoji="🤠", sounds=["city-hum.mp3"],
    search_name="Durango city Mexico Durango state",
    highlights=[("Durango Cathedral", "Durango_Cathedral"),
                ("Cerro del Mercado", None),
                ("Teatro Ricardo Castro", None),
                ("Villa del Oeste", None)],
    blurb="A colonial city on a high plain below the Sierra Madre, built on "
          "an iron hill that is one of the purest ore bodies in the world. "
          "For 40 years it was also Mexico's Hollywood: more than 150 "
          "westerns were shot on the plains outside town, and two of the "
          "standing sets are still there.",
    fact="Cerro del Mercado is a hill of nearly solid iron ore in the middle "
         "of the city — around 70 percent iron, mined continuously since "
         "1828, and visibly smaller than it was a century ago.",
    tip="The Espinazo del Diablo, the old highway from Durango to Mazatlán, "
        "is one of the great mountain drives in the Americas: 200 km of "
        "switchbacks along a knife-edge ridge, now empty because the traffic "
        "takes the new toll road and its 1.2 km bridge."),
"mazatlan": dict(
    name="Mazatlán", slug="Mazatlán", country="Mexico",
    region="Sinaloa", type="coastal", tag="famous",
    emoji="🎺", sounds=["ocean-waves.mp3"],
    highlights=[("Malecón de Mazatlán", None),
                ("Centro Histórico", None),
                ("Teatro Ángela Peralta", "Teatro_Ángela_Peralta"),
                ("El Faro", None),
                ("Isla de la Piedra", None)],
    blurb="A Pacific port and beach city with a 21 km seafront promenade — "
          "among the longest in the world — and a 19th-century old town of "
          "neoclassical facades that was derelict in the 1980s and has been "
          "brought back street by street. Its Carnival is the third largest "
          "anywhere.",
    fact="El Faro, on the rock at the harbour mouth, is one of the highest "
         "natural-elevation lighthouses in the world at 157 m above the sea. "
         "It is a 30-minute climb and the light is still working.",
    tip="Cross to Isla de la Piedra on the two-minute passenger ferry from "
        "the fishing harbour. It costs almost nothing and puts you on a "
        "coconut-palm beach with palapas and no hotel strip."),
"el-fuerte": dict(
    name="El Fuerte", slug="El_Fuerte,_Sinaloa", country="Mexico",
    region="Sinaloa", type="history", tag="hidden",
    emoji="🏰", sounds=["plaza.mp3"],
    search_name="El Fuerte Sinaloa Pueblo Mágico",
    highlights=[("Fuerte de Montesclaros", None),
                ("Río Fuerte", None),
                ("Plaza de Armas", None),
                ("Chihuahua–Pacific Railway", "Chihuahua_al_Pacífico")],
    blurb="A colonial river town founded in 1564, the western railhead for "
          "the Copper Canyon train and the last flat ground before the Sierra "
          "Madre. Cobbles, arcaded mansions and a reconstructed hilltop fort "
          "above a broad, slow river full of birds.",
    fact="Local tradition insists the first Zorro was a real *hacendado* from "
         "El Fuerte. The claim is unprovable and the town has a bronze statue "
         "of him anyway.",
    tip="Take the dawn boat on the Río Fuerte before catching the train. An "
        "hour on the water with a local boatman turns up herons, cormorants "
        "and kingfishers, and the train does not leave until eight."),
"tampico": dict(
    name="Tampico", slug="Tampico", country="Mexico",
    region="Tamaulipas", type="coastal", tag="hidden",
    emoji="🛢️", sounds=["ocean-waves.mp3"],
    highlights=[("Plaza de la Libertad", None),
                ("Edificio de la Aduana", None),
                ("Laguna del Carpintero", None),
                ("Playa Miramar", None)],
    blurb="An oil port on the Pánuco River near the Gulf, whose centre is a "
          "surprise: two squares of cast-iron balconied buildings put up "
          "during the 1900s boom by companies with New Orleans architects, so "
          "the old town looks like the French Quarter with palms.",
    fact="The Tampico oil field made this one of the richest cities on Earth "
         "per capita in the 1920s, briefly handling a quarter of world oil "
         "exports. *The Treasure of the Sierra Madre* opens here for that "
         "reason.",
    tip="Walk the two adjoining plazas — Libertad and Armas — in the evening. "
        "The iron balconies are the only ensemble of their kind in Mexico, "
        "and almost no visitor to the coast bothers going into the centre."),
# ========================= THE BAJÍO & THE CENTRE-WEST =========================
"zacatecas": dict(
    name="Zacatecas", slug="Zacatecas_City", country="Mexico",
    region="Zacatecas", type="history", tag="famous",
    emoji="🥈", sounds=["plaza.mp3"],
    search_name="Zacatecas City Mexico",
    highlights=[("Zacatecas Cathedral", "Zacatecas_Cathedral"),
                ("Cerro de la Bufa", None),
                ("Mina El Edén", None),
                ("Museo Rafael Coronel", "Museo_Rafael_Coronel"),
                ("Teleférico de Zacatecas", None)],
    blurb="A silver city of pink stone crammed into a narrow ravine at "
          "2,440 m, with a cathedral facade so densely carved it is the "
          "high-water mark of Mexican churrigueresque. Its mines financed the "
          "Spanish empire for two centuries, and one of them runs directly "
          "under the historic centre.",
    fact="A cable car crosses the whole city from one hilltop to the other, "
         "and one end of the ride is inside the El Edén mine — you can enter "
         "the mountain by lift, walk through the workings and leave by "
         "gondola over the rooftops.",
    tip="The Rafael Coronel museum holds around 10,000 Mexican masks in the "
        "ruins of a 16th-century convent. It is the largest mask collection "
        "in the world and half the pleasure is that the roof is missing."),
"real-de-catorce": dict(
    name="Real de Catorce", slug="Real_de_Catorce", country="Mexico",
    region="San Luis Potosí", type="history", tag="hidden",
    emoji="👻", sounds=["desert-wind.mp3"],
    highlights=[("Ogarrio Tunnel", None),
                ("Templo de la Purísima Concepción", None),
                ("Pueblo Fantasma", None),
                ("Cerro del Quemado", None),
                ("Wirikuta", None)],
    blurb="A silver town at 2,750 m in the high desert of San Luis Potosí "
          "that had 15,000 people in 1900 and around 1,000 now. The only road "
          "in is a 2.3 km single-lane mine tunnel with traffic lights at each "
          "end; on the far side are cobbled streets, roofless mansions and a "
          "church floor of hinged wooden panels.",
    fact="The desert below the town is Wirikuta, the end point of the "
         "Wixárika (Huichol) pilgrimage — a 400 km walk made for centuries to "
         "a place their cosmology treats as where the sun was born. It is a "
         "protected sacred site.",
    tip="Ride up to the Cerro del Quemado at dawn on a rented horse or on "
        "foot. It is the sacred summit above the town, the desert below "
        "stretches for 100 km, and the light at that hour is why people who "
        "come for one night stay for four."),
"huasteca-potosina": dict(
    name="Huasteca Potosina", slug="Huasteca_Potosina", country="Mexico",
    region="San Luis Potosí", type="nature", tag="hidden",
    emoji="🏞️", sounds=["waterfall.mp3"],
    highlights=[("Cascada de Tamul", None),
                ("Las Pozas", "Las_Pozas"),
                ("Sótano de las Golondrinas", "Sótano_de_las_Golondrinas"),
                ("Puente de Dios", None),
                ("Cascadas de Micos", None)],
    blurb="A green, humid corner of an otherwise dry state where rivers run "
          "over limestone and turn an unlikely turquoise. Waterfalls, "
          "travertine terraces, a 105 m plunge into a gorge at Tamul, and a "
          "cave shaft deep enough to drop the Eiffel Tower into.",
    fact="Sótano de las Golondrinas is a free-fall pit 376 m deep — an "
         "object dropped in takes about ten seconds to hit the bottom. Tens "
         "of thousands of swifts spiral out of it at dawn and drop back into "
         "it at dusk.",
    tip="Las Pozas at Xilitla is the other reason to come: a surrealist "
        "concrete garden of stairs to nowhere, built in the jungle by the "
        "English poet Edward James over 20 years. Go on a weekday and early."),
"san-luis-potosi": dict(
    name="San Luis Potosí", slug="San_Luis_Potosí_City", country="Mexico",
    region="San Luis Potosí", type="city", tag="hidden",
    emoji="⛲", sounds=["plaza.mp3"],
    highlights=[("Templo del Carmen", None),
                ("Plaza de Armas", None),
                ("Museo Federico Silva", None),
                ("Caja del Agua", None)],
    blurb="A colonial silver city of squares — seven of them in the centre, "
          "each with a different character — at the point where the "
          "highlands meet the desert. The Templo del Carmen's altarpiece and "
          "camarín are among the most extravagant baroque interiors in the "
          "country.",
    fact="The city gave its name to a currency. Spanish silver dollars "
         "minted from Potosí-region silver circulated so widely in Asia that "
         "they became the model for the Chinese yuan and the Japanese yen.",
    tip="Plaza de San Francisco at dusk, when the fountain runs and the "
        "orange-stone church front catches the last light, is the best "
        "half-hour in the city and costs nothing."),
"guanajuato": dict(
    name="Guanajuato", slug="Guanajuato_City", country="Mexico",
    region="Guanajuato", type="history", tag="famous",
    emoji="🎭", sounds=["plaza.mp3"],
    search_name="Guanajuato City Mexico",
    highlights=[("Callejón del Beso", None),
                ("Teatro Juárez", "Teatro_Juárez"),
                ("Basílica de Nuestra Señora de Guanajuato", None),
                ("Alhóndiga de Granaditas", "Alhóndiga_de_Granaditas"),
                ("Monumento al Pípila", None),
                ("Universidad de Guanajuato", None)],
    blurb="A silver city poured into a steep ravine, painted every colour, "
          "with most of its through-traffic running in tunnels under the "
          "streets — former river courses, roofed over after the floods. "
          "Above ground it is stairs, alleys and plazas, and a UNESCO site "
          "for the whole ensemble.",
    fact="The tunnels were not built for cars. They were dug in the 1800s to "
         "divert the river that repeatedly drowned the city; when a dam "
         "upstream made them dry, Guanajuato simply paved them and drove in.",
    tip="Climb to the Pípila monument at sunset — the funicular runs, but the "
        "stairs from Plaza Baratillo take fifteen minutes and pass the parts "
        "of town no tour goes near."),
"san-miguel-de-allende": dict(
    name="San Miguel de Allende", slug="San_Miguel_de_Allende", country="Mexico",
    region="Guanajuato", type="history", tag="famous",
    emoji="🌸", sounds=["plaza.mp3"],
    highlights=[("Parroquia de San Miguel Arcángel",
                 "Parroquia_de_San_Miguel_Arcángel"),
                ("El Jardín", None),
                ("Fábrica La Aurora", None),
                ("Santuario de Atotonilco", "Sanctuary_of_Atotonilco"),
                ("Charco del Ingenio", None)],
    blurb="A hill town of pink stone and bougainvillea in the Bajío, whose "
          "parish church was rebuilt in the 1880s by a self-taught local "
          "mason working from postcards of European Gothic cathedrals. The "
          "result is unlike anything else in Mexico, and it is the town's "
          "signature.",
    fact="Zeferino Gutiérrez, the mason, was illiterate. He is said to have "
         "drawn the day's plan in the sand each morning for his workers, "
         "having reverse-engineered Gothic proportion from lithographs.",
    tip="Walk out to the Santuario de Atotonilco, 14 km north — a plain shell "
        "containing a riot of folk-baroque murals covering every surface, "
        "sometimes called the Sistine Chapel of Mexico, and nearly empty."),
"dolores-hidalgo": dict(
    name="Dolores Hidalgo", slug="Dolores_Hidalgo", country="Mexico",
    region="Guanajuato", type="history", tag="hidden",
    emoji="🔔", sounds=["plaza.mp3"],
    highlights=[("Parroquia de Nuestra Señora de los Dolores", None),
                ("Casa de Hidalgo", None),
                ("Plaza Principal", None),
                ("Museo José Alfredo Jiménez", None)],
    blurb="A small Bajío town with an outsized claim: on 16 September 1810 "
          "the parish priest rang the church bell here and called for "
          "rebellion against Spain. Every Mexican president since has "
          "re-enacted the shout from a balcony in the capital, and the "
          "original bell hangs over the door of the National Palace.",
    fact="The town is also, improbably, famous for ice cream in flavours "
         "that should not work — avocado, mole, shrimp, beer, chicharrón — "
         "sold from carts around the square where independence was declared.",
    tip="The church front is the photograph, but the Casa de Hidalgo behind "
        "it is the better visit: the priest's own house, with the workshops "
        "where he taught pottery and silk-making to his parishioners."),
"queretaro": dict(
    name="Querétaro", slug="Santiago_de_Querétaro", country="Mexico",
    region="Querétaro", type="city", tag="hidden",
    emoji="🏛️", sounds=["plaza.mp3"],
    search_name="Santiago de Querétaro Mexico",
    highlights=[("Aqueduct of Querétaro", "Aqueduct_of_Querétaro"),
                ("Templo de Santa Rosa de Viterbo", None),
                ("Cerro de las Campanas", None),
                ("Andador 5 de Mayo", None),
                ("Convento de la Santa Cruz", None)],
    blurb="A colonial city that has quietly become one of Mexico's fastest-"
          "growing and safest, with a historic centre of shaded pedestrian "
          "streets that is a UNESCO site, and a 1,280 m aqueduct of 74 stone "
          "arches walking straight through the middle of it.",
    fact="Maximilian, the Habsburg archduke installed as emperor of Mexico by "
         "France, was executed on the hill at the edge of this city in 1867 — "
         "the event Manet painted five times without ever seeing it.",
    tip="Walk the aqueduct's length at night when the arches are lit. It "
        "still carried the city's water until the 1970s and the mirador at "
        "its high end is a local hangout rather than a viewpoint."),
"pena-de-bernal": dict(
    name="Peña de Bernal", slug="Peña_de_Bernal", country="Mexico",
    region="Querétaro", type="mountain", tag="hidden",
    emoji="🪨", sounds=["wind.mp3"],
    highlights=[("San Sebastián Bernal", None),
                ("Capilla de las Ánimas", None),
                ("Sierra Gorda", "Sierra_Gorda")],
    blurb="One of the tallest freestanding monoliths on Earth — a 350 m plug "
          "of solidified magma standing over a small town of white houses and "
          "red roofs in the Querétaro semi-desert. It is a Sunday destination "
          "for half of central Mexico and a climbing crag for the rest.",
    fact="Only Gibraltar and Sugarloaf are routinely ranked above it, and the "
         "rock is thought to be around 100 million years old — it was the "
         "throat of a volcano whose cone has entirely eroded away.",
    tip="The marked path stops at a chapel two-thirds up; the summit needs "
        "ropes. Go early on a weekday — by Sunday noon the trail is a queue "
        "and the town below is a car park."),
"sierra-gorda": dict(
    name="Sierra Gorda", slug="Sierra_Gorda", country="Mexico",
    region="Querétaro", type="nature", tag="hidden",
    emoji="⛰️", sounds=["wilderness.mp3"],
    highlights=[("Mission of Jalpan", None),
                ("Mission of Concá", None),
                ("Sótano del Barro", None),
                ("Puente de Dios", None),
                ("Cascada El Chuveje", None)],
    blurb="A folded limestone range northeast of Querétaro that packs "
          "semi-desert, cloud forest and tropical jungle into one biosphere "
          "reserve, and holds five Franciscan mission churches whose facades "
          "were carved by local Pame craftsmen into something no Spaniard "
          "would have designed. All five are UNESCO listed.",
    fact="The missions were the last work of Junípero Serra before he went "
         "north to found the California missions — the ornamental language he "
         "left behind here is far wilder than anything he built afterwards.",
    tip="Sótano del Barro is a 410 m sinkhole with a colony of green macaws "
        "nesting on its walls. They fly out at first light; being on the rim "
        "for that means camping or a very early start from Jalpan."),
"aguascalientes": dict(
    name="Aguascalientes", slug="Aguascalientes_City", country="Mexico",
    region="Aguascalientes", type="city", tag="hidden",
    emoji="💀", sounds=["city-hum.mp3"],
    search_name="Aguascalientes City Mexico",
    highlights=[("Museo José Guadalupe Posada", None),
                ("Templo de San Antonio", None),
                ("Plaza de la Patria", None),
                ("Jardín de San Marcos", None)],
    blurb="A compact state capital named for its hot springs, built over a "
          "network of tunnels nobody has fully mapped, and home to the "
          "engraver whose skeleton cartoons became the visual language of the "
          "Day of the Dead everywhere.",
    fact="La Catrina — the elegant skeleton in the feathered hat — was drawn "
         "here by José Guadalupe Posada around 1910 as a satire of Mexicans "
         "who denied their indigenous ancestry. It was never meant as a "
         "holiday decoration.",
    tip="The Feria de San Marcos in April is the largest fair in Mexico and "
        "swallows the city whole. If that is not what you want, come any "
        "other month and the Posada museum is nearly empty."),
"guadalajara": dict(
    name="Guadalajara", slug="Guadalajara", country="Mexico",
    region="Jalisco", type="city", tag="famous",
    emoji="🎻", sounds=["city-hum.mp3"],
    search_name="Guadalajara Jalisco Mexico",
    highlights=[("Guadalajara Cathedral", "Guadalajara_Cathedral"),
                ("Hospicio Cabañas", "Hospicio_Cabañas"),
                ("Teatro Degollado", "Teatro_Degollado"),
                ("Mercado San Juan de Dios", "Mercado_Libertad"),
                ("Tlaquepaque", "Tlaquepaque"),
                ("Plaza de Armas", None)],
    blurb="Mexico's second city and the source of most of what the world "
          "thinks Mexico is: mariachi, tequila, the charreada and the "
          "wide-brimmed hat all come from Jalisco. Five million people, a "
          "colonial core of squares laid out as a cross, and a tech industry "
          "that has it called the Silicon Valley of Mexico.",
    fact="The Hospicio Cabañas, an orphanage built in 1810, has a chapel "
         "ceiling covered by Orozco's *Man of Fire* — considered the finest "
         "mural cycle in the Americas, and a UNESCO World Heritage Site in "
         "its own right.",
    tip="Go to Plaza de los Mariachis at around 9 p.m., but eat first at "
        "Mercado San Juan de Dios — the largest indoor market in Latin "
        "America, three floors, and lunch upstairs costs almost nothing."),
"tequila": dict(
    name="Tequila", slug="Tequila,_Jalisco", country="Mexico",
    region="Jalisco", type="history", tag="famous",
    emoji="🥃", sounds=["plaza.mp3"],
    search_name="Tequila Jalisco town Mexico",
    highlights=[("Agave Landscape of Tequila",
                 "Agave_Landscape_and_Ancient_Industrial_Facilities_of_Tequila"),
                ("Volcán de Tequila", None),
                ("Mundo Cuervo", None),
                ("Plaza Principal", None)],
    blurb="The town the drink is named after, at the foot of a dormant "
          "volcano in a valley of blue agave that runs to the horizon in "
          "rows. The distilleries in the centre have been working since the "
          "1750s, and the fields and the old factories together are a UNESCO "
          "World Heritage Site.",
    fact="Only spirit distilled from blue agave grown in five designated "
         "Mexican states may be called tequila — a protected designation of "
         "origin that predates most European ones, and the reason the drink "
         "cannot legally be made anywhere else.",
    tip="The agave fields are the point, not the tasting rooms. Ride the "
        "Herradura train or simply drive the back road toward Amatitán at "
        "sunset, when the blue rows go silver."),
"lake-chapala": dict(
    name="Lake Chapala", slug="Lake_Chapala", country="Mexico",
    region="Jalisco", type="nature", tag="hidden",
    emoji="🕊️", sounds=["wind.mp3"],
    highlights=[("Ajijic", "Ajijic"),
                ("Chapala", None),
                ("Isla de los Alacranes", None),
                ("Malecón de Ajijic", None)],
    blurb="Mexico's largest freshwater lake, an hour south of Guadalajara at "
          "1,500 m, ringed by mountains and by villages with a climate that "
          "has been called the second best in the world. Ajijic on the north "
          "shore has one of the largest concentrations of foreign retirees "
          "anywhere in Latin America.",
    fact="D. H. Lawrence wrote most of *The Plumed Serpent* in Chapala in "
         "1923, and the lake stands in for the novel's setting almost "
         "unchanged.",
    tip="Ajijic's lanes are painted with murals and the malecón is a proper "
        "promenade, but the lake itself is best seen from the Mirador above "
        "the village on the road to San Juan Cosalá."),
"puerto-vallarta": dict(
    name="Puerto Vallarta", slug="Puerto_Vallarta", country="Mexico",
    region="Jalisco", type="coastal", tag="famous",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    highlights=[("Malecón de Puerto Vallarta", None),
                ("Parish of Our Lady of Guadalupe",
                 "Parish_of_Our_Lady_of_Guadalupe_(Puerto_Vallarta)"),
                ("Zona Romántica", None),
                ("Playa Las Ánimas", None),
                ("Los Arcos de Mismaloya", None)],
    blurb="A fishing village on the Bahía de Banderas that became a resort "
          "city almost overnight in 1964, and kept its cobbled centre while "
          "doing it. The bay is one of the largest in Mexico, deep enough for "
          "humpbacks to winter in it, with the Sierra Madre falling straight "
          "into the water on the south side.",
    fact="The town was made famous by the filming of *The Night of the "
         "Iguana* at Mismaloya in 1963 — less for the film than for the "
         "press pack that followed Richard Burton and Elizabeth Taylor there "
         "and never stopped writing about the place.",
    tip="Take a water taxi from Boca de Tomatlán to Yelapa or Las Ánimas. "
        "There is no road to either; twenty minutes on the water gets you to "
        "beaches the hotel zone cannot reach."),
"sayulita": dict(
    name="Sayulita", slug="Sayulita", country="Mexico",
    region="Nayarit", type="coastal", tag="hidden",
    emoji="🏄", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Sayulita", None),
                ("Playa de los Muertos", None),
                ("Monkey Mountain", None),
                ("San Pancho", None)],
    blurb="A surf town of coloured flags and dirt streets on the Nayarit "
          "Riviera, 40 minutes north of Puerto Vallarta, with a beach break "
          "gentle enough that half the town is learning on it. It went from "
          "unknown to crowded in about fifteen years and is still, on a "
          "Tuesday morning, lovely.",
    fact="The Wixárika (Huichol) sell beadwork here that is not souvenir "
          "work: the yarn paintings and beaded jaguar heads are votive "
          "objects made in the same tradition as the offerings left in "
          "Wirikuta, 700 km inland.",
    tip="Walk 25 minutes north over the headland to San Pancho. Same coast, "
        "one-tenth the crowd, a better beach and the polo field nobody "
        "expects to find there."),
"islas-marietas": dict(
    name="Islas Marietas", slug="Marieta_Islands", country="Mexico",
    region="Nayarit", type="island", tag="hidden",
    emoji="🕳️", sounds=["ocean-waves.mp3"],
    highlights=[("Playa del Amor", None),
                ("Bahía de Banderas", "Bahía_de_Banderas"),
                ("Isla Redonda", None),
                ("Isla Larga", None)],
    blurb="Two uninhabited islands in the mouth of the Bahía de Banderas "
          "with a beach at the bottom of a crater — a circular hole in the "
          "island's roof opening onto sand and green water, reachable only by "
          "swimming through a tunnel from the sea.",
    fact="The crater is not natural. The islands were used for bombing "
         "practice by the Mexican military in the early 1900s, and the hidden "
         "beach is a bomb crater that the sea broke into.",
    tip="Access is capped at a few hundred people a day with certified "
        "operators only, after the reef was wrecked by unregulated tourism. "
        "Book weeks ahead, and know that a swell closes it entirely."),
"colima-volcano": dict(
    name="Colima Volcano", slug="Volcán_de_Colima", country="Mexico",
    region="Colima", type="mountain", tag="hidden",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    highlights=[("Nevado de Colima", None),
                ("Comala", "Comala"),
                ("Laguna La María", None),
                ("Colima", None)],
    blurb="The most active volcano in Mexico — a 3,850 m cone that has "
          "erupted more than 40 times since 1576 and is monitored "
          "continuously. Its dead twin, the Nevado, stands beside it 500 m "
          "higher and holds snow, so the pair are usually seen together: one "
          "smoking, one white.",
    fact="It is sometimes called the Volcán de Fuego, and it sits at the "
         "western end of the Trans-Mexican Volcanic Belt, the fracture that "
         "runs across the country and carries almost all of its active "
         "volcanoes.",
    tip="Comala, the white-painted town at its foot, is the viewpoint — and "
        "the model for the ghost village in Juan Rulfo's *Pedro Páramo*. "
        "Sit on the arcaded plaza in the late afternoon and the cone appears "
        "over the roofline."),
"morelia": dict(
    name="Morelia", slug="Morelia", country="Mexico",
    region="Michoacán", type="history", tag="famous",
    emoji="🕯️", sounds=["plaza.mp3"],
    highlights=[("Morelia Cathedral", "Morelia_Cathedral"),
                ("Acueducto de Morelia", None),
                ("Palacio Clavijero", None),
                ("Callejón del Romance", None),
                ("Santuario de Guadalupe", None)],
    blurb="A UNESCO city built entirely from pink volcanic trachyte, laid out "
          "in 1541 on a Renaissance grid and remarkably unaltered since. Its "
          "cathedral towers were the tallest in the Americas when they went "
          "up, and a 253-arch aqueduct walks in from the east.",
    fact="Every Saturday night the cathedral facade is used for a fireworks "
         "display that has been running for decades — the whole front of a "
         "16th-century cathedral wired for pyrotechnics, free, from the "
         "square.",
    tip="Walk the Calzada Fray Antonio de San Miguel, the tree-lined avenue "
        "beside the aqueduct, and turn into the Callejón del Romance. It is a "
        "single lane of fountains and verses and it takes four minutes."),
"patzcuaro": dict(
    name="Pátzcuaro", slug="Pátzcuaro", country="Mexico",
    region="Michoacán", type="history", tag="hidden",
    emoji="🛶", sounds=["plaza.mp3"],
    highlights=[("Lake Pátzcuaro", "Lake_Pátzcuaro"),
                ("Basílica de Nuestra Señora de la Salud", None),
                ("Plaza Vasco de Quiroga", None),
                ("Janitzio", "Janitzio"),
                ("Tzintzuntzan", "Tzintzuntzan")],
    blurb="A town of white walls and red-tiled roofs above a highland lake "
          "that was the centre of the Purépecha empire — the one state the "
          "Aztecs never managed to conquer. Its plaza is one of the finest in "
          "Mexico and its craft villages still each make one thing: copper, "
          "guitars, lacquer, straw.",
    fact="Bishop Vasco de Quiroga assigned a different trade to each village "
         "around the lake in the 1530s, modelled on More's *Utopia*, which he "
         "had read. Four centuries later most of those villages still make "
         "the same object.",
    tip="Tzintzuntzan, 15 km up the lake, has five round Purépecha pyramids "
        "on a terrace above the water — a shape found almost nowhere else in "
        "Mesoamerica — and hardly anybody at them."),
"monarch-reserve": dict(
    name="Monarch Butterfly Reserve",
    slug="Monarch_Butterfly_Biosphere_Reserve", country="Mexico",
    region="Michoacán", type="nature", tag="famous",
    emoji="🦋", sounds=["wilderness.mp3"],
    highlights=[("El Rosario Sanctuary", None),
                ("Sierra Chincua", None),
                ("Angangueo", "Angangueo"),
                ("Cerro Pelón", None)],
    blurb="A handful of oyamel fir forests at 3,000 m in the mountains "
          "between Michoacán and the State of Mexico where, every November, "
          "the entire eastern North American monarch population arrives after "
          "a flight of up to 4,500 km. Branches bend under the weight of "
          "them.",
    fact="No individual butterfly makes the round trip. The generation that "
         "flies south lives eight months; it takes three or four shorter-lived "
         "generations to get back north the following summer, and nobody "
         "fully understands how the route is inherited.",
    tip="Season is roughly late November to March, and a cold morning is a "
        "still morning — the butterflies only fly once the sun warms them, so "
        "arrive by ten and wait for the air to move."),
"paricutin": dict(
    name="Parícutin", slug="Parícutin", country="Mexico",
    region="Michoacán", type="mountain", tag="hidden",
    emoji="⛰️", sounds=["wind.mp3"],
    highlights=[("San Juan Parangaricutiro church", None),
                ("Angahuan", None),
                ("Lava field", None)],
    blurb="A cinder cone 424 m high that did not exist in 1943. It began as a "
          "crack in a cornfield, grew five storeys in a week, and erupted for "
          "nine years — the only volcano in recorded history whose entire "
          "life cycle, from first crack to last ash, was watched by "
          "scientists from the start.",
    fact="The lava buried two towns and left one thing standing: the front "
         "wall and bell tower of the San Juan church rise out of a black "
         "field of frozen lava, with the altar still visible inside.",
    tip="Ride from Angahuan on a hired horse — it is three hours each way "
        "over lava to the cone, and the walk is brutal in the sun. The church "
        "ruin alone is a 40-minute walk and worth the trip by itself."),
# ========================= CENTRAL MEXICO =========================
"teotihuacan": dict(
    name="Teotihuacan", slug="Teotihuacan", country="Mexico",
    region="State of Mexico", type="history", tag="famous",
    emoji="🔺", sounds=["wind.mp3"],
    highlights=[("Pyramid of the Sun", "Pyramid_of_the_Sun"),
                ("Pyramid of the Moon", "Pyramid_of_the_Moon"),
                ("Avenue of the Dead", "Avenue_of_the_Dead"),
                ("Temple of the Feathered Serpent",
                 "Temple_of_the_Feathered_Serpent,_Teotihuacan"),
                ("Palace of Quetzalpapálotl", None)],
    blurb="The largest city in the Americas before the Spanish arrived, and "
          "one of the largest in the world in its day — perhaps 125,000 "
          "people at its peak around 450 AD, laid out on a rigid grid around "
          "a 2.4 km ceremonial avenue. It was already an abandoned ruin when "
          "the Aztecs found it and named it.",
    fact="Nobody knows what its builders called it, what language they spoke, "
         "or who ruled it. Teotihuacan — 'the place where the gods were "
         "created' — is the Nahuatl name given by people who arrived seven "
         "centuries after it fell.",
    tip="A tunnel under the Feathered Serpent pyramid, sealed for 1,800 "
        "years, was reopened in 2003 and found to contain liquid mercury and "
        "thousands of offerings. It is not open to visitors, but the museum "
        "on site shows what came out of it."),
"valle-de-bravo": dict(
    name="Valle de Bravo", slug="Valle_de_Bravo", country="Mexico",
    region="State of Mexico", type="nature", tag="hidden",
    emoji="🪂", sounds=["wind.mp3"],
    highlights=[("Lago Avándaro", None),
                ("Velo de Novia waterfall", None),
                ("Cerro Gordo", None),
                ("Piedra Herrada", None)],
    blurb="A white-and-red-tiled town on a reservoir in pine mountains two "
          "hours west of Mexico City, and the capital's weekend escape. The "
          "thermals over the ridge above it are so reliable that it is one of "
          "the world's great paragliding sites, and the sky is usually full "
          "of wings.",
    fact="The lake is artificial: the original village was flooded in 1947 "
         "for a hydroelectric scheme, and the town you see was rebuilt higher "
         "up the slope. In a dry year the old church tower reappears.",
    tip="A monarch butterfly sanctuary, Piedra Herrada, is 30 minutes away "
        "and far less visited than El Rosario. Same butterflies, same season, "
        "a fraction of the queue."),
"nevado-de-toluca": dict(
    name="Nevado de Toluca", slug="Nevado_de_Toluca", country="Mexico",
    region="State of Mexico", type="mountain", tag="hidden",
    emoji="🏔️", sounds=["mountain-wind.mp3"],
    highlights=[("Laguna del Sol", None),
                ("Laguna de la Luna", None),
                ("Pico del Fraile", None)],
    blurb="A dormant stratovolcano of 4,680 m whose summit crater holds two "
          "lakes — the Sun and the Moon — at an altitude where the water "
          "regularly freezes. A road climbs almost to the crater rim, which "
          "makes it the most accessible high-altitude place in Mexico and one "
          "of the highest drivable points in North America.",
    fact="Divers have recovered hundreds of Aztec offerings from the bottom "
         "of the Laguna de la Luna — copal incense cones and lightning-bolt "
         "sceptres thrown into the crater lakes as offerings to the rain "
         "gods, still lying where they landed.",
    tip="The road is gated and the altitude is real: 4,200 m at the car park, "
        "where a short walk feels like a hard one. Go on a clear winter "
        "morning and be down before the afternoon cloud closes in."),
"tepoztlan": dict(
    name="Tepoztlán", slug="Tepoztlán", country="Mexico",
    region="Morelos", type="history", tag="hidden",
    emoji="🔮", sounds=["plaza.mp3"],
    highlights=[("Tepozteco pyramid", None),
                ("Ex-Convento de la Natividad", None),
                ("Mercado de Tepoztlán", None),
                ("Cerro del Tepozteco", None)],
    blurb="A town under a wall of eroded cliffs an hour south of Mexico City, "
          "with a small Aztec-era pyramid on a crag 400 m above it. It has a "
          "long-standing reputation as a place of unusual energy, which means "
          "the weekend market sells crystals alongside the ice cream.",
    fact="The 16th-century Dominican convent in the centre is a UNESCO World "
         "Heritage Site as one of the fourteen monasteries on the slopes of "
         "Popocatépetl — fortress-monasteries built within a single "
         "generation of the conquest.",
    tip="The climb to the Tepozteco pyramid is 2 km of steep stone steps and "
        "takes about an hour. Start at opening time; by midday it is a "
        "single-file queue in full sun."),
"cuernavaca": dict(
    name="Cuernavaca", slug="Cuernavaca", country="Mexico",
    region="Morelos", type="city", tag="hidden",
    emoji="🌺", sounds=["city-hum.mp3"],
    highlights=[("Palacio de Cortés", "Palacio_de_Cortés"),
                ("Cuernavaca Cathedral", None),
                ("Jardín Borda", "Jardín_Borda"),
                ("Salto de San Antón", None)],
    blurb="Known for four hundred years as the city of eternal spring, an "
          "hour down from the capital and a thousand metres lower, which is "
          "the whole point: Aztec emperors, Cortés, Maximilian and a long "
          "line of Mexico City weekenders have all kept gardens here to "
          "escape the altitude.",
    fact="The Palacio de Cortés, built on top of an Aztec tribute-collection "
         "platform in the 1520s, is the oldest surviving colonial civil "
         "building in the Americas — and Diego Rivera covered its loggia with "
         "a mural of the conquest seen from the losing side.",
    tip="The cathedral's nave was stripped back in the 1950s and revealed "
        "16th-century murals of the martyrdom of Mexican missionaries in "
        "Japan, painted by an unknown hand. Nothing else in Mexico looks like "
        "them."),
"xochicalco": dict(
    name="Xochicalco", slug="Xochicalco", country="Mexico",
    region="Morelos", type="history", tag="hidden",
    emoji="🐍", sounds=["wind.mp3"],
    highlights=[("Temple of the Feathered Serpent", None),
                ("Observatory cave", None),
                ("Great Ballcourt", None)],
    blurb="A fortified hilltop city that rose exactly when Teotihuacan fell, "
          "around 700 AD, and was itself burned two centuries later. Terraced "
          "into an entire hill above the Morelos valleys, with a UNESCO "
          "listing and a fraction of the visitors of the sites either side of "
          "it in time.",
    fact="A cave under the site was cut with a vertical shaft to the surface "
         "that acts as a zenith tube: for a few weeks around midsummer the "
         "sun passes directly overhead and drops a beam of light onto the "
         "cave floor. It was almost certainly a calendar.",
    tip="Go on a weekday and you may have the hill to yourself. The "
        "carved serpent frieze wrapping the main pyramid is the single best "
        "piece of Mesoamerican relief sculpture outside a museum."),
"taxco": dict(
    name="Taxco", slug="Taxco", country="Mexico",
    region="Guerrero", type="history", tag="famous",
    emoji="💍", sounds=["plaza.mp3"],
    highlights=[("Santa Prisca Church", "Santa_Prisca_Church"),
                ("Plaza Borda", None),
                ("Cristo Monumental", None),
                ("Grutas de Cacahuamilpa", "Grutas_de_Cacahuamilpa_National_Park")],
    blurb="A silver town poured down a mountainside in Guerrero, all white "
          "walls, red roofs and cobbled lanes too steep and narrow for "
          "anything but the fleet of white VW Beetles that serve as taxis. "
          "Its pink baroque church was paid for outright by one man who "
          "struck a vein in 1743.",
    fact="Taxco's modern silver trade was created almost single-handedly in "
         "1931 by an American architect, William Spratling, who set up a "
         "workshop and trained local apprentices. Within a decade the town "
         "was exporting silverwork worldwide.",
    tip="The Cacahuamilpa caves, 30 km north, are among the largest cave "
        "systems open anywhere — a lit walkway runs 2 km into chambers up to "
        "80 m high, with a river running out of the mountain beside it."),
"puebla": dict(
    name="Puebla", slug="Puebla_(city)", country="Mexico",
    region="Puebla", type="city", tag="famous",
    emoji="🍫", sounds=["plaza.mp3"],
    search_name="Puebla City Mexico",
    highlights=[("Puebla Cathedral", "Puebla_Cathedral"),
                ("Capilla del Rosario", None),
                ("Biblioteca Palafoxiana", "Biblioteca_Palafoxiana"),
                ("Callejón de los Sapos", None),
                ("Museo Amparo", "Museo_Amparo"),
                ("Barrio del Artista", None)],
    blurb="A UNESCO city of 2,600 listed colonial buildings, founded on empty "
          "ground in 1531 so the Spanish would not have to live in a "
          "conquered town. Its speciality is talavera tilework, which covers "
          "church domes and whole house fronts, and its kitchens produced "
          "mole poblano and chiles en nogada.",
    fact="The Biblioteca Palafoxiana, founded 1646, is the oldest public "
         "library in the Americas and still holds its original shelving and "
         "45,000 volumes — a reading room that has barely changed in 350 "
         "years.",
    tip="The Rosary Chapel inside Santo Domingo is entirely covered in gilded "
        "plaster and was called the eighth wonder of the world when it opened "
        "in 1690. It is free, it is a side chapel, and most people walk past "
        "the door."),
"cholula": dict(
    name="Cholula", slug="Cholula,_Puebla", country="Mexico",
    region="Puebla", type="history", tag="hidden",
    emoji="⛪", sounds=["plaza.mp3"],
    highlights=[("Great Pyramid of Cholula", "Great_Pyramid_of_Cholula"),
                ("Iglesia de Nuestra Señora de los Remedios", None),
                ("Popocatépetl", "Popocatépetl"),
                ("Capilla Real", None)],
    blurb="A town beside Puebla built around what looks like a hill with a "
          "yellow church on top. It is not a hill. It is the largest pyramid "
          "by volume on Earth — roughly twice the mass of the Great Pyramid "
          "of Giza — grassed over and mistaken for terrain for four hundred "
          "years.",
    fact="The Spanish put a church on the summit in 1594 without realising "
         "what they were building on. The monument is therefore both an "
         "active Catholic shrine and a pre-Columbian pyramid, and 8 km of "
         "excavated tunnels run through the inside.",
    tip="Walk the tunnel route through the pyramid's core, then climb to the "
        "church for the view of Popocatépetl smoking 25 km away. On a clear "
        "winter morning it is the best volcano view in central Mexico."),
"popocatepetl": dict(
    name="Popocatépetl", slug="Popocatépetl", country="Mexico",
    region="Puebla", type="mountain", tag="famous",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    highlights=[("Iztaccíhuatl", "Iztaccíhuatl"),
                ("Paso de Cortés", None),
                ("Izta-Popo Zoquiapan National Park", None),
                ("Cholula", "Cholula,_Puebla")],
    blurb="An active 5,393 m stratovolcano 70 km from Mexico City, "
          "continuously restless since 1994 and visible from the capital on a "
          "clear day. Beside it stands Iztaccíhuatl, dormant and snow-covered, "
          "whose ridgeline is said to be a sleeping woman.",
    fact="Popocatépetl means 'smoking mountain' in Nahuatl, and it has been "
         "living up to it since before the Aztecs — 16th-century codices "
         "already draw it with a plume. Around 25 million people live within "
         "100 km of the crater.",
    tip="Climbing Popo has been banned for thirty years. Iztaccíhuatl beside "
        "it is open, and the drive up to the Paso de Cortés between the two "
        "gets you to 3,600 m with both cones filling the windscreen."),
"cuetzalan": dict(
    name="Cuetzalan", slug="Cuetzalan", country="Mexico",
    region="Puebla", type="history", tag="hidden",
    emoji="☕", sounds=["waterfall.mp3"],
    highlights=[("Parroquia de San Francisco de Asís", None),
                ("Yohualichan", None),
                ("Cascada Las Brisas", None),
                ("Santuario de Guadalupe", None)],
    blurb="A steep cobbled town in the cloud forest of the northern Puebla "
          "sierra, permanently damp, permanently green, and reached by a road "
          "of hairpins. Coffee, pepper and vanilla grow around it, and the "
          "Sunday market draws Nahua families down from the surrounding "
          "hills.",
    fact="Yohualichan, 8 km away, has the same niched pyramid architecture as "
         "El Tajín — hundreds of square recesses cut into the terraces — "
         "which is the main physical evidence linking the two cultures.",
    tip="The waterfalls in the ravines below town are the reason to stay two "
        "nights rather than one. Las Brisas and Corcovado are both a walk "
        "plus a scramble, and neither has a ticket office."),
"tlaxcala": dict(
    name="Tlaxcala", slug="Tlaxcala_City", country="Mexico",
    region="Tlaxcala", type="history", tag="hidden",
    emoji="🎨", sounds=["plaza.mp3"],
    search_name="Tlaxcala City Mexico",
    highlights=[("Ex-Convento de San Francisco", None),
                ("Basílica de Ocotlán", None),
                ("Palacio de Gobierno", None),
                ("Cacaxtla", "Cacaxtla")],
    blurb="The capital of Mexico's smallest state, and the city whose "
          "decision changed the continent: the Tlaxcalans, hemmed in and "
          "hostile to the Aztecs, allied with Cortés in 1519 and supplied the "
          "army that took Tenochtitlan. The town they were rewarded with is "
          "quiet, ochre-coloured and barely visited.",
    fact="The convent of San Francisco here, begun in 1524, has a Moorish "
         "coffered wooden ceiling and is one of the four oldest surviving "
         "monasteries in the Americas — and its church floor is where the "
         "first indigenous converts in New Spain were baptised.",
    tip="Cacaxtla, 20 km away, has the best-preserved Mesoamerican murals "
        "anywhere: a full-size battle frieze in blues and reds under a huge "
        "shelter roof, with the paint still bright."),
"pachuca": dict(
    name="Pachuca", slug="Pachuca", country="Mexico",
    region="Hidalgo", type="city", tag="hidden",
    emoji="⚽", sounds=["city-hum.mp3"],
    highlights=[("Reloj Monumental", "Reloj_Monumental_de_Pachuca"),
                ("Macromural Pachuca", None),
                ("Real del Monte", "Mineral_del_Monte"),
                ("Museo de Fotografía", None)],
    blurb="A silver city in a windy gap in the Hidalgo mountains — the "
          "*Bella Airosa* — whose hillside neighbourhoods have been painted "
          "as a single continuous mural covering 200 houses. Cornish miners "
          "came here in the 1820s and left behind pasties, Methodist "
          "cemeteries and the first football club in Mexico.",
    fact="Pachuca CF, founded in 1901 by Cornish miners, is the oldest "
         "football club in Mexico. The mining town of Real del Monte above it "
         "still sells *pastes* — Cornish pasties, with the crimp on the "
         "side — from a dozen shops.",
    tip="Drive up to Real del Monte for the pasties and the English cemetery, "
        "where the graves face Cornwall. One of them, by local tradition, "
        "faces the other way: the clown Ricardo Bell."),
"huasca-de-ocampo": dict(
    name="Huasca de Ocampo", slug="Huasca_de_Ocampo", country="Mexico",
    region="Hidalgo", type="nature", tag="hidden",
    emoji="🧊", sounds=["waterfall.mp3"],
    highlights=[("Prismas Basálticos", None),
                ("Hacienda Santa María Regla", None),
                ("Presa San Antonio", None),
                ("Bosque de las Truchas", None)],
    blurb="A small town in the Hidalgo pine country next to a canyon whose "
          "walls are made of hexagonal basalt columns 30 m high, with a "
          "waterfall dropping over them. Alexander von Humboldt came to draw "
          "the columns in 1803 and they have been a Mexican landmark ever "
          "since.",
    fact="The water going over the prisms is not natural. It comes from an "
         "18th-century aqueduct built to serve the silver refining haciendas "
         "downstream — the postcard waterfall is a piece of colonial "
         "industrial plumbing.",
    tip="The ruined haciendas around the town — Santa María Regla and San "
        "Miguel Regla — are enormous, half-roofless silver refineries you can "
        "walk into, and they get a tiny fraction of the prisms' crowd."),
"tula": dict(
    name="Tula", slug="Tula_(Mesoamerican_site)", country="Mexico",
    region="Hidalgo", type="history", tag="hidden",
    emoji="🗿", sounds=["wind.mp3"],
    search_name="Tula Hidalgo Toltec ruins",
    highlights=[("Atlantean figures of Tula", "Atlantean_figures"),
                ("Pyramid B", None),
                ("Coatepantli", None),
                ("Ballcourt", None)],
    blurb="The capital of the Toltecs, who came after Teotihuacan and before "
          "the Aztecs, and whom the Aztecs regarded as the source of all "
          "civilisation. On top of its main pyramid stand four basalt "
          "warriors 4.6 m tall that once held up a roof.",
    fact="The same warrior columns, the same chacmool figures and the same "
         "colonnades appear at Chichén Itzá, 1,200 km away across the Gulf. "
         "Which city copied which — or whether one conquered the other — is "
         "still argued about.",
    tip="Stand at the foot of the Atlanteans in the late afternoon when the "
        "relief on their chest plates and sandals picks up a low sun. The "
        "site is small, an hour is plenty, and it is usually empty."),
# ========================= VERACRUZ & THE GULF =========================
"veracruz": dict(
    name="Veracruz", slug="Veracruz_(city)", country="Mexico",
    region="Veracruz", type="coastal", tag="famous",
    emoji="🎶", sounds=["ocean-waves.mp3"],
    search_name="Veracruz city port Mexico",
    highlights=[("San Juan de Ulúa", "San_Juan_de_Ulúa"),
                ("Zócalo de Veracruz", None),
                ("Malecón de Veracruz", None),
                ("Boca del Río", None),
                ("Acuario de Veracruz", None)],
    blurb="The oldest European-founded city in the Americas still on its "
          "site, established by Cortés in 1519 and the only legal port "
          "between Spain and its colonies for three centuries. The arcades "
          "around its square fill every night with danzón dancers and "
          "marimba, and the humidity never lets up.",
    fact="Veracruz has been invaded four times — by Spain, France twice and "
         "the United States twice. The city's formal title is *Cuatro Veces "
         "Heroica*, four times heroic, one for each defence.",
    tip="San Juan de Ulúa, the coral-stone fortress on an island across the "
        "harbour, was the treasure depot, the last Spanish holdout after "
        "independence and then Mexico's worst prison. It is reachable by "
        "causeway and is far more interesting than the aquarium."),
"xalapa": dict(
    name="Xalapa", slug="Xalapa", country="Mexico",
    region="Veracruz", type="city", tag="hidden",
    emoji="🌿", sounds=["city-hum.mp3"],
    highlights=[("Museo de Antropología de Xalapa",
                 "Museum_of_Anthropology_of_Xalapa"),
                ("Parque Los Berros", None),
                ("Cofre de Perote", "Cofre_de_Perote"),
                ("Callejón del Diamante", None)],
    blurb="The state capital, 1,400 m up in permanent mist on the flank of a "
          "volcano — cool, green, drizzly and full of students, which is why "
          "it is the cultural capital of the Gulf. Coffee grows on the slopes "
          "below it and the jalapeño is named after it.",
    fact="Its anthropology museum is the second best in Mexico after the "
         "national one, and it is the place to see the Olmec colossal heads: "
         "seven of the seventeen ever found are in one long sloping gallery "
         "here.",
    tip="Xalapa's weather is a real thing — the *chipi-chipi*, a fine "
        "permanent drizzle that can last for days. Bring a jacket to a "
        "tropical state and drink the coffee, which is genuinely excellent."),
"coatepec": dict(
    name="Coatepec", slug="Coatepec,_Veracruz", country="Mexico",
    region="Veracruz", type="history", tag="hidden",
    emoji="☕", sounds=["plaza.mp3"],
    search_name="Coatepec Veracruz Pueblo Mágico",
    highlights=[("Parroquia de San Jerónimo", None),
                ("Cascada de Bola de Oro", None),
                ("Xico", None),
                ("Cafetal Apan", None)],
    blurb="A coffee town in the misty hills below Xalapa, with pastel "
          "arcaded streets and roasteries on half of them. It is the centre "
          "of Mexico's best-known coffee-growing area, and the whole town "
          "smells of it in harvest season.",
    fact="Coffee reached Veracruz from Cuba in the 1790s, and the "
         "shade-grown plantations that resulted are one of the reasons the "
         "cloud forest here survived at all — the canopy was left standing to "
         "shelter the crop.",
    tip="Walk or drive on to Xico, 8 km further up, for the Texolo waterfall "
        "in a gorge below the town. *Romancing the Stone* was shot there and "
        "the iron footbridge is still across the top of the falls."),
"tlacotalpan": dict(
    name="Tlacotalpan", slug="Tlacotalpan", country="Mexico",
    region="Veracruz", type="history", tag="hidden",
    emoji="🏘️", sounds=["plaza.mp3"],
    highlights=[("Papaloapan River", "Papaloapan_River"),
                ("Parroquia de San Cristóbal", None),
                ("Plaza Zaragoza", None),
                ("Casa Museo Agustín Lara", None)],
    blurb="A river port on the Papaloapan whose entire centre is single-"
          "storey houses with columned porches, each painted a different "
          "saturated colour — pink beside turquoise beside lime. A UNESCO "
          "World Heritage Site for exactly that: an unbroken 18th and "
          "19th-century Caribbean-Spanish streetscape.",
    fact="The town was the birthplace of the *son jarocho*, the string-and-"
         "harp music of the Veracruz lowlands whose best-known tune, "
         "*La Bamba*, is a 300-year-old wedding song.",
    tip="Come for the Candelaria festival on 2 February if you want the town "
        "at full volume — bulls run through the streets and the Virgin goes "
        "down the river on a boat. Come any other week and it is silent."),
"el-tajin": dict(
    name="El Tajín", slug="El_Tajín", country="Mexico",
    region="Veracruz", type="history", tag="famous",
    emoji="🕳️", sounds=["wilderness.mp3"],
    highlights=[("Pyramid of the Niches", None),
                ("Papantla", "Papantla"),
                ("Great Ballcourt", None),
                ("Building of the Columns", None)],
    blurb="A Classic-period city in the humid lowlands of northern Veracruz, "
          "hidden in vanilla country and not rediscovered until 1785. Its "
          "signature building is a stepped pyramid pierced by 365 square "
          "niches, one for each day of the solar year, and it has seventeen "
          "ballcourts — more than any other Mesoamerican site.",
    fact="The reliefs on the ballcourt walls show, in sequence and without "
         "ambiguity, a player being sacrificed by having his chest opened "
         "with a flint knife. It is the clearest surviving depiction of what "
         "the ballgame could mean.",
    tip="The Papantla flyers perform outside the entrance: five men climb a "
        "30 m pole, four launch backwards on ropes and rotate down while the "
        "fifth plays a flute on top. It is a UNESCO-listed ritual, not a "
        "show, and it is free."),
"pico-de-orizaba": dict(
    name="Pico de Orizaba", slug="Pico_de_Orizaba", country="Mexico",
    region="Veracruz", type="mountain", tag="famous",
    emoji="🗻", sounds=["mountain-wind.mp3"],
    highlights=[("Jamapa Glacier", None),
                ("Tlachichuca", None),
                ("Piedra Grande", None),
                ("Sierra Negra", None)],
    blurb="At 5,636 m the highest mountain in Mexico and the third highest in "
          "North America — a near-perfect dormant cone standing 4,000 m above "
          "the plain, visible from ships in the Gulf a hundred kilometres "
          "away. It carries the country's largest glacier on its north face.",
    fact="Its Nahuatl name, Citlaltépetl, means 'star mountain'. Because it "
         "stands so far out from any range, sailors used it as a landfall "
         "mark for the run into Veracruz for four centuries.",
    tip="The standard route from the Piedra Grande hut is a non-technical "
        "glacier climb but a serious one — 1,600 m of ascent at altitude, "
        "with crampons and a rope. Most people who summit spend three days "
        "acclimatising in Tlachichuca first."),
"catemaco": dict(
    name="Catemaco", slug="Catemaco", country="Mexico",
    region="Veracruz", type="nature", tag="hidden",
    emoji="🐒", sounds=["wilderness.mp3"],
    highlights=[("Lake Catemaco", "Lake_Catemaco"),
                ("Los Tuxtlas Biosphere Reserve", None),
                ("Salto de Eyipantla", None),
                ("Nanciyaga", None)],
    blurb="A lake town in the Los Tuxtlas volcanic range, where the "
          "northernmost rainforest in the Americas comes down to a crater "
          "lake with islands of macaques in it. It is also the best-known "
          "centre of *brujería* in Mexico, and holds a witches' congress "
          "every March.",
    fact="The macaques on the lake islands are not native to anything within "
         "10,000 km. They were released by a university research project in "
         "the 1970s and simply stayed.",
    tip="*Apocalypto* and *Medicine Man* were both shot in this forest. The "
        "Eyipantla falls, 12 km away, are 50 m across and the walk down to "
        "the base is 250 steps — worth it for the noise alone."),
# ========================= OAXACA =========================
"oaxaca-city": dict(
    name="Oaxaca", slug="Oaxaca_City", country="Mexico",
    region="Oaxaca", type="city", tag="famous",
    emoji="🌶️", sounds=["plaza.mp3"],
    search_name="Oaxaca City Mexico",
    highlights=[("Santo Domingo de Guzmán", "Church_of_Santo_Domingo_de_Guzmán,_Oaxaca"),
                ("Zócalo de Oaxaca", None),
                ("Mercado 20 de Noviembre", None),
                ("Monte Albán", "Monte_Albán"),
                ("Andador Macedonio Alcalá", None),
                ("Jardín Etnobotánico", None)],
    blurb="A green-stone colonial city in a high valley, and by common "
          "consent the best place to eat in Mexico. Sixteen indigenous "
          "peoples live in the state; their markets, textiles, languages and "
          "seven varieties of mole all converge here, and the whole centre is "
          "UNESCO listed.",
    fact="The gilded ceiling of Santo Domingo carries a genealogical tree of "
         "the Dominican order in three-dimensional plaster figures. The "
         "church took two centuries to finish and its gold leaf covers "
         "roughly 60,000 square feet of vault.",
    tip="Eat in the smoke of the Pasillo de Humo inside the 20 de Noviembre "
        "market: you buy raw meat from one stall, hand it over the grill, and "
        "eat it at a shared table with tortillas from the woman next to you."),
"monte-alban": dict(
    name="Monte Albán", slug="Monte_Albán", country="Mexico",
    region="Oaxaca", type="history", tag="famous",
    emoji="🏔️", sounds=["wind.mp3"],
    highlights=[("Gran Plaza", None),
                ("Los Danzantes", None),
                ("Building J", None),
                ("Juego de Pelota", None)],
    blurb="The Zapotec capital, built on an artificially flattened mountain "
          "top 400 m above the Oaxaca valley floor around 500 BC and occupied "
          "for 1,300 years. The whole summit was levelled by hand to make one "
          "enormous plaza, with pyramids on all four sides and a 360-degree "
          "view of three valleys.",
    fact="The *danzantes* carvings, long read as dancers, are now understood "
         "as slain captives — hundreds of naked figures with closed eyes and "
         "mutilations, one of the earliest political monuments in "
         "Mesoamerica.",
    tip="Building J sits at an odd angle to everything else and is pierced by "
        "a tunnel aligned with the rising of the star Capella. Go up for the "
        "8 a.m. opening: cool, empty, and the light rakes the reliefs."),
"hierve-el-agua": dict(
    name="Hierve el Agua", slug="Hierve_el_Agua", country="Mexico",
    region="Oaxaca", type="nature", tag="hidden",
    emoji="💧", sounds=["wind.mp3"],
    highlights=[("Petrified waterfalls", None),
                ("Mitla", "Mitla"),
                ("Cascada Chica", None)],
    blurb="Two mineral-spring formations on a cliff edge in the Oaxacan "
          "sierra that look exactly like frozen waterfalls — 60 m of white "
          "calcium carbonate hanging over a valley, built up drip by drip "
          "over thousands of years, with turquoise spring pools at the top.",
    fact="Above the falls are the remains of a Zapotec irrigation system "
         "roughly 2,500 years old — canals and terraces cut to use the same "
         "mineral springs, which is why some of the formations are partly "
         "artificial.",
    tip="Get there at opening or stay overnight in the campsite at the top. "
        "The pools face west across the sierra and the sunset from the edge "
        "is the whole reason people make the two-hour drive."),
"mitla": dict(
    name="Mitla", slug="Mitla", country="Mexico",
    region="Oaxaca", type="history", tag="hidden",
    emoji="🔷", sounds=["wind.mp3"],
    highlights=[("Columns Group", None),
                ("Church Group", None),
                ("Grecas mosaics", None),
                ("Árbol del Tule", "Árbol_del_Tule")],
    blurb="A Zapotec religious centre whose walls carry the finest stone "
          "mosaic work in the Americas: geometric fretwork made of thousands "
          "of individually cut pieces set without mortar, in fourteen "
          "distinct patterns, none of them repeated at random.",
    fact="Mitla means 'place of the dead' in Nahuatl. The Spanish built a "
         "church directly on top of one of its five palace groups using the "
         "site's own stone — you can see re-used mosaic panels in the church "
         "wall.",
    tip="Stop at Santa María del Tule on the way back. The cypress in the "
        "churchyard has the stoutest trunk of any tree on Earth, over 14 m "
        "across, and is somewhere around 1,500 years old."),
"puerto-escondido": dict(
    name="Puerto Escondido", slug="Puerto_Escondido,_Oaxaca", country="Mexico",
    region="Oaxaca", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    search_name="Puerto Escondido Oaxaca Mexico",
    highlights=[("Playa Zicatela", None),
                ("Playa Carrizalillo", None),
                ("Laguna de Manialtepec", None),
                ("Punta Zicatela", None)],
    blurb="A surf town on the Oaxacan coast built around one of the heaviest "
          "beach breaks in the world — the Mexican Pipeline, which throws "
          "closeout barrels onto sand and breaks boards and people in equal "
          "numbers. Around the headland the coves are calm and the town is "
          "not.",
    fact="The lagoon 15 km west is bioluminescent: microscopic dinoflagellates "
         "light up when the water is disturbed, so on a moonless night your "
         "hands and the boat's wake glow blue.",
    tip="Do not swim at Zicatela. Carrizalillo, down 170 steps in a cove, is "
        "the swimming and learning beach, and the sunset from the top of "
        "those steps is the town's other attraction."),
"huatulco": dict(
    name="Huatulco", slug="Huatulco", country="Mexico",
    region="Oaxaca", type="coastal", tag="hidden",
    emoji="🐢", sounds=["ocean-waves.mp3"],
    highlights=[("Bahía de Santa Cruz", None),
                ("Bahía Cacaluta", None),
                ("Huatulco National Park", None),
                ("La Crucecita", None)],
    blurb="Nine bays and 36 beaches on the Oaxacan coast, developed from 1984 "
          "as a planned resort but with roughly half the land written into a "
          "national park before building started. The result is a resort "
          "coast where most of the coves have no road to them at all.",
    fact="Huatulco was the first tourist destination in the Americas — and "
         "one of the first anywhere — certified as a Green Globe sustainable "
         "community, which it has held since 2005.",
    tip="Hire a panga at Santa Cruz harbour and get dropped at Cacaluta or "
        "San Agustín for the day. There is no road, no vendor and no shade "
        "but the trees, so take water and agree the pickup time."),
"san-cristobal-de-las-casas": dict(
    name="San Cristóbal de las Casas", slug="San_Cristóbal_de_las_Casas",
    country="Mexico",
    region="Chiapas", type="history", tag="famous",
    emoji="🧶", sounds=["plaza.mp3"],
    highlights=[("Templo de Santo Domingo", None),
                ("Andador Guadalupano", None),
                ("San Juan Chamula", "San_Juan_Chamula"),
                ("Museo Na Bolom", None),
                ("Zinacantán", None)],
    blurb="A highland colonial town at 2,200 m in Chiapas, cold at night, "
          "surrounded by Tzotzil and Tzeltal Maya villages whose people fill "
          "its markets daily. It was the seat of Bartolomé de las Casas, who "
          "spent his life arguing that the conquest was a crime, and it was "
          "seized by the Zapatistas on New Year's Day 1994.",
    fact="The church at San Juan Chamula, 10 km away, has no pews, no priest "
         "and a floor covered in pine needles and candles. What happens "
         "inside is a Maya rite using Catholic saints, and photography is "
         "absolutely forbidden.",
    tip="Take a colectivo to Chamula and Zinacantán with a local guide rather "
        "than going alone — the customs are strict, the rules are enforced by "
        "the community, and a guide is the difference between being welcome "
        "and being asked to leave."),
"palenque": dict(
    name="Palenque", slug="Palenque", country="Mexico",
    region="Chiapas", type="history", tag="famous",
    emoji="🌴", sounds=["wilderness.mp3"],
    highlights=[("Temple of the Inscriptions", "Temple_of_the_Inscriptions"),
                ("The Palace", None),
                ("Temple of the Cross", None),
                ("Misol-Ha", None),
                ("Agua Azul", "Agua_Azul")],
    blurb="A Maya city at the edge of the Chiapas jungle, small by area but "
          "unmatched in the refinement of its architecture and the amount it "
          "can tell us — its carved texts are the most complete dynastic "
          "record from the Maya world. Howler monkeys roar in the canopy over "
          "the plaza at dawn.",
    fact="In 1952 Alberto Ruz lifted a slab in the Temple of the "
         "Inscriptions, found a hidden staircase packed with rubble, spent "
         "four seasons clearing it, and reached the intact tomb of Pakal the "
         "Great — the first royal burial ever found inside a Maya pyramid.",
    tip="Take the jungle path out of the site past the museum instead of "
        "leaving by the main gate. It follows a stream past unexcavated "
        "mounds and waterfalls and almost nobody uses it."),
"sumidero-canyon": dict(
    name="Sumidero Canyon", slug="Sumidero_Canyon", country="Mexico",
    region="Chiapas", type="nature", tag="hidden",
    emoji="🛥️", sounds=["wilderness.mp3"],
    highlights=[("Grijalva River", "Grijalva_River"),
                ("Árbol de Navidad waterfall", None),
                ("Chiapa de Corzo", "Chiapa_de_Corzo,_Chiapas"),
                ("Chicoasén Dam", None)],
    blurb="A gorge on the Grijalva River with walls up to 1,000 m high, cut "
          "through limestone and now partly flooded by a hydroelectric dam — "
          "which means you go through it by boat, looking almost straight up. "
          "Crocodiles on the banks, vultures and spider monkeys above.",
    fact="The canyon appears on the Chiapas coat of arms because of a story "
         "from 1528: rather than submit to the Spanish, several hundred "
         "Chiapanec warriors are said to have thrown themselves from the rim.",
    tip="Boats leave from Chiapa de Corzo, a colonial town with an "
        "extraordinary 16th-century brick fountain on its plaza. Take the "
        "first departure — the light is better and the wind picks up later."),
"montebello-lakes": dict(
    name="Lagunas de Montebello", slug="Lagunas_de_Montebello_National_Park",
    country="Mexico",
    region="Chiapas", type="nature", tag="hidden",
    emoji="🏞️", sounds=["wilderness.mp3"],
    highlights=[("Laguna Pojoj", None),
                ("Laguna Montebello", None),
                ("Cinco Lagos", None),
                ("Chinkultic", None)],
    blurb="Around sixty lakes in the pine and cloud forest along the "
          "Guatemalan border, each a different colour — emerald, turquoise, "
          "indigo, near-black — depending on its depth, its minerals and what "
          "grows in it. The first national park Mexico declared in Chiapas, "
          "in 1959.",
    fact="The colour differences are real and stable, not a trick of the "
         "light: neighbouring lakes a few hundred metres apart hold "
         "measurably different suspended minerals, and the locals name them "
         "accordingly.",
    tip="Chinkultic, just outside the park, is a Maya site on a cliff above a "
        "cenote with a ball court and a stela field, and it usually has "
        "nobody in it. The climb up the acropolis takes ten minutes."),
"palenque-yaxchilan": dict(
    name="Yaxchilán", slug="Yaxchilan", country="Mexico",
    region="Chiapas", type="history", tag="hidden",
    emoji="🛶", sounds=["wilderness.mp3"],
    highlights=[("Structure 33", None),
                ("Usumacinta River", None),
                ("Bonampak", "Bonampak"),
                ("The Labyrinth", None)],
    blurb="A Maya city on a horseshoe bend of the Usumacinta, on the "
          "Guatemalan border, reachable only by boat through the Lacandon "
          "jungle. Its carved lintels — showing bloodletting rites in "
          "extraordinary detail — are among the finest Maya sculpture ever "
          "found.",
    fact="Nearby Bonampak holds the best-preserved Maya murals in existence: "
         "three rooms painted in 790 AD with a battle, a court ceremony and "
         "the torture of prisoners, in colours that survived because a "
         "limestone seep sealed them.",
    tip="You reach it by an hour's *lancha* ride downriver from Frontera "
        "Corozal. Go early enough to be in the plaza when the howler monkeys "
        "start — they are much louder than you expect and impossible to see."),
# ========================= THE GUERRERO COAST =========================
"acapulco": dict(
    name="Acapulco", slug="Acapulco", country="Mexico",
    region="Guerrero", type="coastal", tag="famous",
    emoji="🤿", sounds=["ocean-waves.mp3"],
    highlights=[("La Quebrada", "La_Quebrada"),
                ("Fuerte de San Diego", "Fort_of_San_Diego"),
                ("Bahía de Acapulco", None),
                ("Playa Caleta", None),
                ("Isla la Roqueta", None)],
    blurb="A near-circular deep-water bay that was Spain's Pacific terminus "
          "for 250 years and Hollywood's favourite resort for thirty. The "
          "Manila galleon docked here with Chinese silk and porcelain; later "
          "the same bay took Sinatra, Kennedy and Elizabeth Taylor's wedding.",
    fact="The Manila galleon ran between Acapulco and the Philippines from "
         "1565 to 1815 — the longest-running regular shipping line in "
         "history, and the first sustained trade route to link Asia and the "
         "Americas.",
    tip="The La Quebrada divers go off a 35 m cliff into a 4 m-wide inlet, "
        "timing the jump to an incoming swell, five times a day and once by "
        "torchlight. Watch from the public terrace rather than the hotel bar "
        "above it."),
"zihuatanejo": dict(
    name="Zihuatanejo", slug="Zihuatanejo", country="Mexico",
    region="Guerrero", type="coastal", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    highlights=[("Playa La Ropa", None),
                ("Playa Las Gatas", None),
                ("Paseo del Pescador", None),
                ("Ixtapa", "Ixtapa")],
    blurb="A fishing town on a sheltered bay on the Guerrero coast, with a "
          "purpose-built resort strip 7 km up the road at Ixtapa that "
          "absorbed all the high-rise development and left the old town its "
          "harbour, its market and its pace.",
    fact="This is the town at the end of *The Shawshank Redemption* — the "
         "Pacific with no memory, where Andy plans to fix up an old boat. "
         "None of the film was actually shot here; the final scene was filmed "
         "in the US Virgin Islands.",
    tip="Playa Las Gatas is reached by a five-minute panga from the town pier "
        "and is protected by a stone breakwater said to have been built by a "
        "Purépecha king for his daughter. Calm, shallow and full of fish."),
# ========================= TABASCO & CAMPECHE =========================
"villahermosa": dict(
    name="Villahermosa", slug="Villahermosa", country="Mexico",
    region="Tabasco", type="city", tag="hidden",
    emoji="🗿", sounds=["city-hum.mp3"],
    highlights=[("Parque-Museo La Venta", "Parque-Museo_La_Venta"),
                ("Grijalva River", None),
                ("Museo Regional de Antropología", None),
                ("Laguna de las Ilusiones", None)],
    blurb="The capital of Tabasco, hot and flat on the Grijalva River in the "
          "wettest state in Mexico. Its reason to exist for a visitor is an "
          "outdoor museum where the colossal Olmec heads and altars from La "
          "Venta were re-erected in a jungle park when the original site was "
          "threatened by oil drilling.",
    fact="The Olmecs carved their multi-tonne basalt heads from stone "
         "quarried in the Tuxtla mountains and moved them roughly 100 km "
         "across swamp and river, three thousand years ago, without wheels or "
         "draught animals.",
    tip="Go to La Venta park in the last two hours before closing. The heads "
        "sit along a jungle path with howler monkeys and coatis loose in the "
        "trees, and the low light is much better on basalt."),
"campeche": dict(
    name="Campeche", slug="Campeche_City", country="Mexico",
    region="Campeche", type="history", tag="famous",
    emoji="🏰", sounds=["ocean-waves.mp3"],
    search_name="Campeche City Mexico walled",
    highlights=[("Walled city of Campeche", None),
                ("Fuerte de San Miguel", None),
                ("Puerta de Tierra", None),
                ("Malecón de Campeche", None),
                ("Catedral de Campeche", None)],
    blurb="A pastel-coloured walled port on the Gulf, and the only fully "
          "fortified colonial city left in the Americas — a hexagon of "
          "ramparts and eight bastions built to keep out the pirates who "
          "sacked it repeatedly in the 1600s. A UNESCO site, and immaculate.",
    fact="The city was raided so often that the crown eventually paid for a "
          "2.5 km wall around the whole town. It worked: after it was "
          "finished in 1704 Campeche was never successfully sacked again.",
    tip="Walk the ramparts at sunset from Baluarte de Santiago round to the "
        "sea gate, then keep going along the malecón. The whole circuit is "
        "about an hour and the Gulf sunsets here are absurd."),
"calakmul": dict(
    name="Calakmul", slug="Calakmul", country="Mexico",
    region="Campeche", type="history", tag="hidden",
    emoji="🐆", sounds=["wilderness.mp3"],
    highlights=[("Structure II", None),
                ("Calakmul Biosphere Reserve", None),
                ("Balamkú", None),
                ("Structure I", None)],
    blurb="One of the two Maya superpowers — the Kaan or Snake Kingdom, "
          "Tikal's great rival — buried 60 km down a jungle road in the "
          "largest tropical forest reserve in Mexico. Its main pyramid is "
          "among the tallest in the Maya world and you climb it out of the "
          "canopy into a view of unbroken green in every direction.",
    fact="Calakmul has 6,750 recorded structures and 117 carved stelae, more "
         "than any other Maya site. Almost all of it is still under forest, "
         "and the reserve around it holds one of the last viable jaguar "
         "populations in Mexico.",
    tip="Stay at Xpujil the night before and be at the gate when it opens. "
        "The 60 km approach road takes 90 minutes, and being on top of "
        "Structure II in the morning mist is the entire reason to come."),
"edzna": dict(
    name="Edzná", slug="Edzná", country="Mexico",
    region="Campeche", type="history", tag="hidden",
    emoji="🏯", sounds=["wilderness.mp3"],
    highlights=[("Five-Storey Building", None),
                ("Great Acropolis", None),
                ("Temple of the Masks", None)],
    blurb="A Maya city an hour from Campeche whose main structure is a "
          "five-storey palace-pyramid — an unusual hybrid of temple and "
          "residence — rising from a raised acropolis at the end of a huge "
          "plaza. It also had one of the most sophisticated water systems in "
          "the Maya lowlands.",
    fact="The valley around Edzná was engineered with more than 20 km of "
         "canals and dozens of reservoirs to survive a region with no rivers "
         "and a long dry season. It supported the city for over a thousand "
         "years.",
    tip="Almost nobody comes here, which is the point. Late afternoon light "
        "hits the west face of the Five-Storey Building directly, and you can "
        "usually sit on the acropolis steps alone."),
# ========================= YUCATÁN =========================
"merida-yucatan": dict(
    name="Mérida", slug="Mérida,_Yucatán", country="Mexico",
    region="Yucatán", type="city", tag="famous",
    emoji="🎩", sounds=["plaza.mp3"],
    search_name="Mérida Yucatán Mexico",
    highlights=[("Paseo de Montejo", "Paseo_de_Montejo"),
                ("Mérida Cathedral", "Mérida_Cathedral"),
                ("Casa de Montejo", "Casa_de_Montejo"),
                ("Gran Museo del Mundo Maya", None),
                ("Mercado Lucas de Gálvez", None)],
    blurb="The capital of Yucatán, built in 1542 on top of the Maya city of "
          "T'hó using its stone, and rich enough by 1900 from henequen fibre "
          "that it was said to have more millionaires than anywhere on Earth. "
          "They built a boulevard of French mansions, and it is still there.",
    fact="Mérida's cathedral, finished in 1598, is the oldest cathedral on "
         "the American mainland — and its stones were quarried from the Maya "
         "pyramids that stood on the same square.",
    tip="On Sunday the centre closes to traffic, the *Mérida en Domingo* "
        "market fills the plaza, and there is free danzón in Parque Santa "
        "Lucía in the evening. It is the best day of the week to be here."),
"chichen-itza": dict(
    name="Chichén Itzá", slug="Chichen_Itza", country="Mexico",
    region="Yucatán", type="history", tag="famous",
    emoji="🐍", sounds=["wind.mp3"],
    highlights=[("El Castillo", "El_Castillo,_Chichen_Itza"),
                ("Great Ball Court", "Great_Ball_Court"),
                ("Temple of the Warriors", None),
                ("Sacred Cenote", "Sacred_Cenote"),
                ("El Caracol", "El_Caracol,_Chichen_Itza")],
    blurb="The largest and most-visited Maya site, a city that dominated the "
          "northern Yucatán from around 600 to 1200 AD and mixes Maya and "
          "central-Mexican Toltec forms in a way no other site does. El "
          "Castillo, the stepped pyramid at its centre, is a calendar built "
          "in stone.",
    fact="The pyramid has 91 steps on each of four sides plus the top "
         "platform: 365. At the equinoxes the corner terracing throws a "
         "shadow down the northern balustrade in seven triangles, and the "
         "serpent head at the bottom appears to grow a body.",
    tip="Clap once, hard, in front of El Castillo's staircase. The echo comes "
        "back as a chirp — an acoustic effect that matches the call of the "
        "quetzal, and one that acousticians think was deliberate."),
"uxmal": dict(
    name="Uxmal", slug="Uxmal", country="Mexico",
    region="Yucatán", type="history", tag="famous",
    emoji="🏛️", sounds=["wind.mp3"],
    highlights=[("Pyramid of the Magician", "Pyramid_of_the_Magician"),
                ("Nunnery Quadrangle", "Nunnery_Quadrangle"),
                ("Governor's Palace", None),
                ("House of the Turtles", None),
                ("Kabah", "Kabah_(Maya_site)")],
    blurb="The high point of Puuc architecture — long low palaces faced with "
          "thousands of precisely cut stone mosaic pieces, with a pyramid "
          "that is oval in plan rather than square. It is a fraction as busy "
          "as Chichén Itzá and, to a great many people, better.",
    fact="The Governor's Palace is aligned not to the cardinal points but to "
          "the southernmost rising point of Venus, which happens roughly "
          "every eight years — and Venus glyphs are carved into its frieze.",
    tip="Kabah, 20 km down the Puuc route, has a palace facade covered with "
        "roughly 250 stone masks of the rain god Chaac, stacked in rows. "
        "There is nothing else like it and there is usually nobody there."),
"valladolid-yucatan": dict(
    name="Valladolid", slug="Valladolid,_Yucatán", country="Mexico",
    region="Yucatán", type="history", tag="hidden",
    emoji="🕳️", sounds=["plaza.mp3"],
    search_name="Valladolid Yucatán Mexico",
    highlights=[("Cenote Zací", None),
                ("Convento de San Bernardino de Siena", None),
                ("Calzada de los Frailes", None),
                ("Cenote Suytun", None),
                ("Ek' Balam", "Ek'_Balam")],
    blurb="A colonial town in the middle of the Yucatán with a cenote in the "
          "middle of it — an open limestone sinkhole full of clear water, "
          "with a public swimming platform, two blocks from the main square. "
          "It is the best base for the Maya sites and cenotes of the "
          "interior.",
    fact="The peninsula has no rivers at all. Every drop of fresh water is "
          "underground, in a flooded cave network of thousands of cenotes "
          "created by the same meteorite impact that ended the Cretaceous.",
    tip="Ek' Balam, 25 minutes north, still lets you climb its main pyramid — "
        "and near the top is a preserved stucco doorway carved as a monster's "
        "jaws, with the original modelling intact."),
"izamal": dict(
    name="Izamal", slug="Izamal", country="Mexico",
    region="Yucatán", type="history", tag="hidden",
    emoji="🟡", sounds=["plaza.mp3"],
    highlights=[("Convento de San Antonio de Padua", None),
                ("Kinich Kak Moo", None),
                ("Centro Histórico", None)],
    blurb="The yellow city — almost every building in the centre is painted "
          "the same ochre, and has been since a papal visit in 1993. It is "
          "built on and out of a Maya city: the monastery's vast atrium sits "
          "directly on a levelled pyramid platform.",
    fact="The atrium of the San Antonio monastery is the second largest of "
         "any Christian building in the world, after St Peter's. It was built "
         "in 1561 from the stones of the Maya temple it replaced.",
    tip="Kinich Kak Moo, the surviving pyramid, is right in town, free, "
        "unfenced and climbable, and from the top you can see how completely "
        "the yellow grid was laid over the older city."),
"celestun": dict(
    name="Celestún", slug="Celestún", country="Mexico",
    region="Yucatán", type="nature", tag="hidden",
    emoji="🦩", sounds=["ocean-waves.mp3"],
    highlights=[("Celestún Biosphere Reserve", None),
                ("Ría Celestún", None),
                ("Petrified forest", None),
                ("Ojo de agua", None)],
    blurb="A fishing village on the Gulf coast at the mouth of an estuary "
          "where fresh groundwater meets the sea, and where several thousand "
          "American flamingos feed through the winter. Mangrove tunnels, "
          "freshwater springs bubbling up through the lagoon floor, and a "
          "beach of white sand nobody is on.",
    fact="The flamingos are pink because of what the estuary feeds them: "
          "carotenoid pigments from the brine shrimp and algae in the "
          "shallows. A flamingo raised without them is white.",
    tip="Take the boat from the bridge on the road into town, not from the "
        "beach — it is cheaper, the same route, and the operators are the "
        "village co-operative."),
"rio-lagartos": dict(
    name="Río Lagartos", slug="Río_Lagartos", country="Mexico",
    region="Yucatán", type="nature", tag="hidden",
    emoji="🦎", sounds=["ocean-waves.mp3"],
    highlights=[("Ría Lagartos Biosphere Reserve", None),
                ("Las Coloradas", "Las_Coloradas"),
                ("El Cuyo", None),
                ("Punta Mecoh", None)],
    blurb="A fishing village on the north coast beside a long saltwater "
          "lagoon that holds the largest flamingo breeding colony in Mexico, "
          "crocodiles, and — 15 km east — a set of salt evaporation ponds "
          "that are an intense, unreal pink.",
    fact="The pink of Las Coloradas comes from halophile microorganisms and "
          "brine shrimp concentrating in water four times saltier than the "
          "sea. It is a working industrial saltworks, not a natural "
          "phenomenon, and it has been in production since Maya times.",
    tip="The ponds are now fenced with a paid viewpoint after years of people "
        "swimming in them. The lagoon boat trip from Río Lagartos at dawn is "
        "the better half of the day anyway."),
"progreso": dict(
    name="Progreso", slug="Progreso,_Yucatán", country="Mexico",
    region="Yucatán", type="coastal", tag="hidden",
    emoji="🛳️", sounds=["ocean-waves.mp3"],
    search_name="Progreso Yucatán Mexico",
    highlights=[("Muelle de Progreso", None),
                ("Malecón de Progreso", None),
                ("Chicxulub", "Chicxulub_Puerto"),
                ("Xcambó", None)],
    blurb="Mérida's beach town on the Gulf, with the longest pier in the "
          "world — 6.5 km of concrete reaching out to water deep enough for "
          "ships, across a shelf so shallow that nothing else would work. "
          "Warm flat water, a long malecón and a cruise terminal.",
    fact="The village of Chicxulub next door gave its name to the 180 km "
          "crater buried under the seabed and limestone here — the impact "
          "that ended the age of dinosaurs, whose rim is traceable today as "
          "a ring of cenotes across the peninsula.",
    tip="The pier's original 1940s section used a nickel-alloy reinforcement "
        "that has outlasted every later extension — engineers still study it. "
        "You can walk a fair way out along the parallel fishing pier."),
# ========================= QUINTANA ROO =========================
"tulum": dict(
    name="Tulum", slug="Tulum", country="Mexico",
    region="Quintana Roo", type="history", tag="famous",
    emoji="🏖️", sounds=["ocean-waves.mp3"],
    highlights=[("Tulum ruins", None),
                ("El Castillo", None),
                ("Gran Cenote", None),
                ("Playa Paraíso", None),
                ("Sian Ka'an", "Sian_Ka'an")],
    blurb="The only major Maya city built on the coast — a walled port on a "
          "12 m cliff over the Caribbean, still occupied when the Spanish "
          "sailed past it in 1518 and reported a town 'as large as Seville'. "
          "The beach directly below the ruins is the most photographed in "
          "Mexico.",
    fact="A small window in the Castillo lines up with a gap in the offshore "
          "reef. Set a canoe on the line where the light shows and you are "
          "steering through the only safe passage for kilometres — the "
          "building worked as a lighthouse.",
    tip="The ruins open at 8 and the tour buses arrive at 10. Go at opening, "
        "then drive the beach road south into the Sian Ka'an biosphere, where "
        "the development stops abruptly and the coast goes back to nothing."),
"playa-del-carmen": dict(
    name="Playa del Carmen", slug="Playa_del_Carmen", country="Mexico",
    region="Quintana Roo", type="coastal", tag="famous",
    emoji="🍹", sounds=["ocean-waves.mp3"],
    highlights=[("Quinta Avenida", None),
                ("Playacar", None),
                ("Cozumel ferry", None),
                ("Parque Fundadores", None)],
    blurb="A fishing village of 1,500 people in 1990 and a city of 300,000 "
          "now — one of the fastest-growing places in Latin America. Its "
          "spine is Quinta Avenida, four kilometres of pedestrian street "
          "running parallel to the beach, and it is the jumping-off point for "
          "Cozumel.",
    fact="The Riviera Maya's growth is measurable from orbit: satellite "
          "imagery from 1990 and today shows a continuous 130 km strip of "
          "development where there was jungle and a handful of coconut "
          "plantations.",
    tip="Walk five blocks inland from Quinta and the prices halve and the "
        "Spanish returns. Colonia Colosio and the Calle 30 taquerías are "
        "where the people who work on the beach actually eat."),
"cozumel": dict(
    name="Cozumel", slug="Cozumel", country="Mexico",
    region="Quintana Roo", type="island", tag="famous",
    emoji="🤿", sounds=["ocean-waves.mp3"],
    highlights=[("Palancar Reef", None),
                ("San Gervasio", None),
                ("Punta Sur", None),
                ("San Miguel de Cozumel", None),
                ("Mesoamerican Barrier Reef", "Mesoamerican_Barrier_Reef_System")],
    blurb="Mexico's largest island, 19 km off the Yucatán coast on the "
          "Mesoamerican Barrier Reef, and one of the best-known wall-diving "
          "destinations in the world — vertical reef dropping into blue with "
          "a current that carries you along it.",
    fact="Cousteau filmed here in 1961 and called Palancar one of the finest "
          "dive sites on Earth, which effectively created the island's "
          "industry. Before that it was a chicle port and, before that, a "
          "Maya pilgrimage island sacred to the goddess Ixchel.",
    tip="Rent a scooter or a car and drive the windward side. The east coast "
        "has no hotels, no power lines and a series of empty rough-water "
        "beaches with one bar every few kilometres."),
"isla-mujeres": dict(
    name="Isla Mujeres", slug="Isla_Mujeres", country="Mexico",
    region="Quintana Roo", type="island", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Norte", None),
                ("Punta Sur", None),
                ("MUSA underwater museum", "Cancún_Underwater_Museum"),
                ("Isla Contoy", "Isla_Contoy")],
    blurb="An island 13 km off Cancún, 7 km long and 650 m wide, with a "
          "shallow turquoise beach at the north end that is routinely called "
          "the best in Mexico. Golf carts instead of cars, and the easternmost "
          "point of the country at the far end.",
    fact="Whale sharks — the largest fish alive — gather in their hundreds in "
          "the water north of here from June to September to feed on tuna "
          "spawn. It is one of the biggest known aggregations of the species "
          "anywhere.",
    tip="Take the first ferry over and the last one back, and rent a cart to "
        "reach Punta Sur at the southern tip, where a Maya temple to Ixchel "
        "stands on a low cliff above the open Caribbean."),
"holbox": dict(
    name="Isla Holbox", slug="Isla_Holbox", country="Mexico",
    region="Quintana Roo", type="island", tag="hidden",
    emoji="🦈", sounds=["ocean-waves.mp3"],
    highlights=[("Punta Cocos", None),
                ("Yum Balam reserve", None),
                ("Isla Pájaros", None),
                ("Punta Mosquito", None)],
    blurb="A sandbar island at the top of the peninsula where the Caribbean "
          "meets the Gulf, separated from the mainland by a lagoon. No cars, "
          "sand streets, shallow water you can wade a long way out into, and "
          "bioluminescent plankton in the summer.",
    fact="Holbox sits inside the Yum Balam protected area and is the shore "
          "base for the same whale shark aggregation as Isla Mujeres — the "
          "animals feed just offshore, and the season here runs from mid-May "
          "into September.",
    tip="Walk east along the beach at low tide towards Punta Mosquito. After "
        "20 minutes the hotels stop, and there are usually flamingos on the "
        "sandflats with nobody watching them."),
"bacalar": dict(
    name="Bacalar", slug="Bacalar", country="Mexico",
    region="Quintana Roo", type="nature", tag="hidden",
    emoji="💙", sounds=["wind.mp3"],
    highlights=[("Laguna de Bacalar", "Bacalar_Lagoon"),
                ("Fuerte de San Felipe", None),
                ("Cenote Azul", None),
                ("Canal de los Piratas", None),
                ("Los Rápidos", None)],
    blurb="A freshwater lagoon 42 km long over a white limestone bed, which "
          "makes it read as seven distinct shades of blue in a single view — "
          "hence the name, the lagoon of seven colours. A small town and a "
          "17th-century pirate fort sit on the western shore.",
    fact="The lagoon holds one of the largest freshwater stromatolite "
          "colonies in the world — living microbial reefs, the oldest form of "
          "life still visibly building structures, which is why touching or "
          "standing on them is banned.",
    tip="Kayak at dawn rather than take a motorboat. The water is glass "
        "before eight, the colours are at their best with the sun low, and "
        "the wake from tour boats is what damages the stromatolites."),
"sian-kaan": dict(
    name="Sian Ka'an", slug="Sian_Ka'an", country="Mexico",
    region="Quintana Roo", type="nature", tag="hidden",
    emoji="🐊", sounds=["wilderness.mp3"],
    highlights=[("Muyil", None),
                ("Boca Paila", None),
                ("Punta Allen", None),
                ("Mesoamerican Barrier Reef", "Mesoamerican_Barrier_Reef_System")],
    blurb="A 5,280 km² biosphere reserve immediately south of Tulum — "
          "mangrove, marsh, tropical forest, a barrier reef and a stretch of "
          "coast with one sand track down it. Its name means 'origin of the "
          "sky' in Maya, and it is a UNESCO World Heritage Site.",
    fact="Maya canals cut through the marsh over a thousand years ago are "
          "still open and still navigable. The float trip most visitors do "
          "here drifts down a pre-Columbian trade route.",
    tip="Drive the coast track to Punta Allen only if you have high clearance "
        "and three spare hours each way. Otherwise enter at Muyil, where the "
        "boardwalk, the lagoon and the canal float all start from the road."),
"coba": dict(
    name="Cobá", slug="Coba", country="Mexico",
    region="Quintana Roo", type="history", tag="hidden",
    emoji="🚲", sounds=["wilderness.mp3"],
    highlights=[("Nohoch Mul", None),
                ("Sacbe causeways", None),
                ("Lake Cobá", None),
                ("Macanxoc group", None)],
    blurb="A large Maya city spread through jungle around two lakes, whose "
          "groups of buildings are far enough apart that people get around "
          "the site by bicycle. At its height it controlled a network of "
          "raised limestone roads running dead straight for up to 100 km.",
    fact="One *sacbe* from Cobá runs 100 km west to Yaxuná near Chichén Itzá "
          "— built by hand, raised above the forest floor, and straight "
          "enough to be traced from the air today.",
    tip="Nohoch Mul, at 42 m the tallest pyramid in the northern Yucatán, was "
        "closed to climbing in 2020. The site is still worth it for the "
        "scale, the bikes and the fact that most of it is still under trees."),
"puerto-morelos": dict(
    name="Puerto Morelos", slug="Puerto_Morelos", country="Mexico",
    region="Quintana Roo", type="coastal", tag="hidden",
    emoji="🐠", sounds=["ocean-waves.mp3"],
    highlights=[("Leaning lighthouse", None),
                ("Puerto Morelos Reef National Park", None),
                ("Ruta de los Cenotes", None),
                ("Jardín Botánico Yaax Che", None)],
    blurb="A small town between Cancún and Playa del Carmen that somehow "
          "stayed a town — a square, a fishing pier, a leaning lighthouse "
          "knocked out of true by a 1967 hurricane, and a reef 500 m offshore "
          "that is a strictly protected national park.",
    fact="The reef here is close enough to snorkel to from the beach, and "
          "because it has been a no-take park since 1998 the fish life on it "
          "is markedly better than on the same reef further south.",
    tip="The Ruta de los Cenotes runs inland from the highway junction: "
        "twenty-odd cenotes on one back road, most of them run by ejido "
        "families, and almost all cheaper and emptier than the famous ones."),
"mahahual": dict(
    name="Mahahual", slug="Mahahual", country="Mexico",
    region="Quintana Roo", type="coastal", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Banco Chinchorro", "Banco_Chinchorro"),
                ("Costa Maya", None),
                ("Xcalak", None),
                ("Malecón de Mahahual", None)],
    blurb="A one-street beach village on the Costa Maya in the far south of "
          "the state, with a cruise pier at one end and, after that, nothing "
          "much for 50 km down to the Belize border. The reef is a few "
          "hundred metres out and the water is glass.",
    fact="Banco Chinchorro, 30 km offshore, is the largest coral atoll in the "
          "northern hemisphere and a ship graveyard — dozens of wrecks from "
          "the 16th century onward are scattered on its reefs.",
    tip="On a day with no ship in, the malecón is empty. Check the cruise "
        "schedule before booking; the difference between a ship day and a "
        "quiet day in Mahahual is total."),
"chetumal": dict(
    name="Chetumal", slug="Chetumal", country="Mexico",
    region="Quintana Roo", type="city", tag="hidden",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    highlights=[("Museo de la Cultura Maya", None),
                ("Boulevard Bahía", None),
                ("Bahía de Chetumal", None),
                ("Kohunlich", "Kohunlich")],
    blurb="The state capital, on a bay at the mouth of the Río Hondo with "
          "Belize on the far bank. It was flattened by a hurricane in 1955 "
          "and rebuilt in Caribbean clapboard-and-concrete, so it looks and "
          "sounds far more Belizean than Mexican.",
    fact="Its Maya culture museum is one of the best in the country and "
          "almost unvisited — three floors organised as the Maya underworld, "
          "middle world and heavens, with a full-scale walk-through model of "
          "a temple.",
    tip="Kohunlich, an hour west, has a pyramid flanked by six giant stucco "
        "masks of the sun god, each two metres high and still under their "
        "original palapa shelters. Almost nobody goes."),
# ========================= GUATEMALA =========================
# The country had ZERO places before this batch. Departments are used as the
# `region` string; they are not boxed (see the module docstring) because
# Guatemala's namesakes are cross-border, which P17 already catches.
"antigua-guatemala": dict(
    name="Antigua Guatemala", slug="Antigua_Guatemala", country="Guatemala",
    region="Sacatepéquez", type="history", tag="famous",
    emoji="🌋", sounds=["plaza.mp3"],
    search_name="Antigua Guatemala city",
    highlights=[("Santa Catalina Arch", None),
                ("Parque Central", None),
                ("Convento de las Capuchinas", None),
                ("Iglesia de La Merced", None),
                ("Cerro de la Cruz", None),
                ("Volcán de Agua", "Volcán_de_Agua")],
    blurb="The colonial capital of all Spanish Central America until an "
          "earthquake destroyed it in 1773 and the government moved away — "
          "which is why it survives as a complete 18th-century city of "
          "cobbles, low ochre walls and roofless baroque churches, ringed by "
          "three volcanoes and UNESCO listed since 1979.",
    fact="One of the three volcanoes over the town, Fuego, erupts more or "
         "less constantly. From a rooftop in Antigua on a clear night you can "
         "watch it throw glowing rock into the air every few minutes.",
    tip="Walk up to the Cerro de la Cruz at first light — twenty minutes, "
        "with a police post on the path — for the town laid out below and "
        "Agua directly behind it before the cloud builds."),
"tikal": dict(
    name="Tikal", slug="Tikal", country="Guatemala",
    region="Petén", type="history", tag="famous",
    emoji="🦜", sounds=["wilderness.mp3"],
    highlights=[("Temple I", "Tikal_Temple_I"),
                ("Temple IV", "Tikal_Temple_IV"),
                ("Gran Plaza", None),
                ("Mundo Perdido", None),
                ("North Acropolis", None)],
    blurb="The greatest of the Maya cities — capital of the Mutal kingdom, "
          "home to perhaps 90,000 people, abandoned around 900 AD and "
          "swallowed by the Petén rainforest until the 1850s. Six steep "
          "temple-pyramids push up through the canopy, and howler monkeys and "
          "toucans are louder than the visitors.",
    fact="Temple IV, at 70 m, is the tallest pre-Columbian structure standing "
         "in the Americas. The view from its top over the jungle canopy was "
         "used as the rebel base on Yavin 4 in the original *Star Wars*.",
    tip="Buy the sunrise ticket and be on Temple IV before six. What you get "
        "is usually not a sunrise but a sea of mist over the canopy with "
        "temple roofs coming out of it, and the howlers starting up."),
"lake-atitlan": dict(
    name="Lake Atitlán", slug="Lake_Atitlán", country="Guatemala",
    region="Sololá", type="nature", tag="famous",
    emoji="🛶", sounds=["wind.mp3"],
    highlights=[("Panajachel", "Panajachel"),
                ("San Juan la Laguna", None),
                ("San Pedro Volcano", "San_Pedro_(volcano)"),
                ("Santiago Atitlán", "Santiago_Atitlán"),
                ("Indian Nose", None)],
    blurb="A lake in a collapsed volcanic caldera at 1,560 m, up to 340 m "
          "deep, with three volcanoes standing on its southern shore and a "
          "dozen Maya villages around its edge, most reached only by boat. "
          "Aldous Huxley called it the most beautiful lake in the world and "
          "the claim has stuck.",
    fact="The caldera was formed by an eruption around 84,000 years ago that "
         "threw ash as far as Florida and Ecuador — one of the largest "
         "volcanic events of the last hundred thousand years.",
    tip="Take the public lancha rather than a tour. It costs a few quetzales "
        "between villages, and San Juan la Laguna — weaving co-operatives, "
        "painted streets, almost no bars — is the one most people miss."),
"guatemala-city": dict(
    name="Guatemala City", slug="Guatemala_City", country="Guatemala",
    region="Guatemala Department", type="city", tag="famous",
    emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Palacio Nacional de la Cultura",
                 "National_Palace_(Guatemala)"),
                ("Catedral Metropolitana", None),
                ("Mapa en Relieve", "Mapa_en_Relieve"),
                ("Zona 1 Centro Histórico", None),
                ("Museo Popol Vuh", None)],
    blurb="The largest city in Central America, founded in 1776 after the "
          "earthquake that finished Antigua, and spread across a plateau cut "
          "by deep ravines. Three million people in the metropolitan area, a "
          "green-stone national palace, and one of the best pre-Columbian art "
          "collections anywhere.",
    fact="The Mapa en Relieve, built in 1905, is an open-air concrete relief "
         "map of the whole country, 1,800 m², with the vertical scale "
         "exaggerated so the mountains read properly. It predates aerial "
         "survey entirely — it was made from ground measurements.",
    tip="Zona 1's centre and Zona 4's converted warehouse district are the "
        "parts worth walking, in daylight. The Popol Vuh and Ixchel museums "
        "in Zona 10 are both on a university campus and both excellent."),
"semuc-champey": dict(
    name="Semuc Champey", slug="Semuc_Champey", country="Guatemala",
    region="Alta Verapaz", type="nature", tag="hidden",
    emoji="💚", sounds=["waterfall.mp3"],
    highlights=[("Cahabón River", None),
                ("Lanquín Caves", None),
                ("El Mirador", None)],
    blurb="A 300 m natural limestone bridge in the Alta Verapaz jungle, with "
          "a staircase of turquoise pools on top of it — while the full "
          "Cahabón River thunders through a cave underneath, invisible, and "
          "comes out the far end. The road in is three hours of dirt.",
    fact="The pools are fed by small streams and springs on the bridge "
         "itself, which is why they are calm and clear while a river in flood "
         "is passing directly beneath them.",
    tip="Climb to the mirador first — 30 minutes of steep steps and ladders "
        "for the view straight down the length of the pools — then swim. "
        "Doing it the other way round in that humidity is miserable."),
"chichicastenango": dict(
    name="Chichicastenango", slug="Chichicastenango", country="Guatemala",
    region="Quiché", type="history", tag="hidden",
    emoji="🧺", sounds=["plaza.mp3"],
    highlights=[("Iglesia de Santo Tomás", None),
                ("Chichicastenango Market", None),
                ("Pascual Abaj", None),
                ("Cementerio de Chichicastenango", None)],
    blurb="A K'iche' Maya town in the western highlands whose Thursday and "
          "Sunday market is the largest in Central America — the whole "
          "central grid filled with textiles, masks, pottery and produce, "
          "and a white church at the top of the steps where copal smoke never "
          "stops.",
    fact="The Popol Vuh, the K'iche' creation epic and the most important "
         "surviving Maya text, was written down and hidden here in the 1550s "
         "and found in this church's convent 150 years later.",
    tip="The eighteen steps of Santo Tomás are a Maya platform — one for each "
        "month of the 260-day calendar — and prayers are said on them, not "
        "in the church. Go up the side stairs and do not photograph anyone "
        "praying."),
"quetzaltenango": dict(
    name="Quetzaltenango", slug="Quetzaltenango", country="Guatemala",
    region="Quetzaltenango", type="city", tag="hidden",
    emoji="🏛️", sounds=["city-hum.mp3"],
    search_name="Quetzaltenango Xela Guatemala",
    highlights=[("Parque Centro América", None),
                ("Teatro Municipal", None),
                ("Fuentes Georginas", None),
                ("Santa María Volcano", "Santa_María_(volcano)"),
                ("Laguna Chicabal", None)],
    blurb="Guatemala's second city, known to everyone as Xela, at 2,330 m in "
          "the western highlands. Neoclassical grey stone from a coffee boom, "
          "a large K'iche' population, cold evenings and a dozen Spanish "
          "schools — the reason a lot of travellers stay a month.",
    fact="Santa María, over the city, produced one of the four largest "
         "eruptions of the 20th century in 1902. Its 1922 side vent, "
         "Santiaguito, has been erupting continuously ever since — over a "
         "century of unbroken activity.",
    tip="Fuentes Georginas is a set of hot springs in a cloud forest ravine "
        "on the flank of Zunil, 45 minutes away, with steam coming off the "
        "pools and ferns hanging over them. Go late afternoon."),
"flores-guatemala": dict(
    name="Flores", slug="Flores,_El_Petén", country="Guatemala",
    region="Petén", type="island", tag="hidden",
    emoji="🏝️", sounds=["wind.mp3"],
    search_name="Flores Petén Guatemala island",
    highlights=[("Lake Petén Itzá", "Lake_Petén_Itzá"),
                ("Santa Elena", None),
                ("El Remate", None),
                ("Tayasal", None)],
    blurb="A red-roofed town on a small island in Lake Petén Itzá, joined to "
          "the mainland by a causeway and walkable end to end in fifteen "
          "minutes. It is the base for Tikal, an hour north, and lovely in "
          "its own right at dusk when the lake goes still.",
    fact="The island was Nojpetén, capital of the Itzá — the very last "
          "independent Maya kingdom, which held out until 1697, more than "
          "170 years after the fall of the Aztec empire. The Spanish "
          "levelled its temples and built the church on top.",
    tip="Swim off the north-shore steps at sunset, then eat on a terrace "
        "facing west. The whole island turns orange, and it costs the price "
        "of a beer."),
"rio-dulce": dict(
    name="Río Dulce", slug="Río_Dulce_(Guatemala)", country="Guatemala",
    region="Izabal", type="nature", tag="hidden",
    emoji="⛵", sounds=["wilderness.mp3"],
    highlights=[("Castillo de San Felipe de Lara",
                 "Castillo_de_San_Felipe_de_Lara"),
                ("Lake Izabal", "Lake_Izabal"),
                ("El Boquerón", None),
                ("Lívingston", "Livingston,_Guatemala")],
    blurb="A short river running from Guatemala's largest lake to the "
          "Caribbean through a gorge with 100 m limestone walls hung with "
          "jungle. It is a hurricane hole — yachts from all over the "
          "Caribbean come up it to sit out the season — and the only way "
          "downstream is by boat.",
    fact="The Spanish built the San Felipe fort at the lake mouth in 1652 "
          "specifically to stop English pirates raiding the warehouses "
          "upstream. It was sacked anyway, more than once.",
    tip="Take the public lancha down the gorge to Lívingston rather than a "
        "tour. It stops at the hot spring waterfall where sulphur water pours "
        "into the cold river, and it costs a fraction as much."),
"livingston-guatemala": dict(
    name="Lívingston", slug="Livingston,_Guatemala", country="Guatemala",
    region="Izabal", type="coastal", tag="hidden",
    emoji="🥁", sounds=["ocean-waves.mp3"],
    search_name="Livingston Izabal Guatemala Garifuna",
    highlights=[("Siete Altares", None),
                ("Playa Blanca", None),
                ("Río Dulce", "Río_Dulce_(Guatemala)"),
                ("Punta de Manabique", None)],
    blurb="A Garifuna town at the mouth of the Río Dulce with no road to it "
          "at all — you arrive by boat from Puerto Barrios or down the gorge. "
          "The language on the street is Garifuna, the music is punta, and it "
          "feels like a piece of the eastern Caribbean attached to "
          "Guatemala.",
    fact="The Garifuna descend from shipwrecked West Africans and Carib "
          "islanders on St Vincent, deported en masse by the British in 1797 "
          "to an island off Honduras. Their language and music are on "
          "UNESCO's intangible heritage list.",
    tip="Siete Altares is a chain of seven waterfall pools an hour's walk up "
        "the coast. Go with the tide out and after rain, or the lower pools "
        "are dry."),
"acatenango": dict(
    name="Acatenango", slug="Acatenango", country="Guatemala",
    region="Chimaltenango", type="mountain", tag="hidden",
    emoji="🔥", sounds=["mountain-wind.mp3"],
    highlights=[("Volcán de Fuego", "Volcán_de_Fuego"),
                ("Antigua Guatemala", "Antigua_Guatemala"),
                ("La Meseta", None)],
    blurb="A 3,976 m volcano above Antigua that people climb for one reason: "
          "it stands directly opposite Fuego, which erupts every few minutes, "
          "and the standard trip is to camp on its shoulder and watch. On a "
          "clear night you see lava thrown up against the stars from a "
          "kilometre away.",
    fact="Fuego has been in near-continuous eruption since 1524, when the "
          "conquistadors first recorded it. Its 2018 eruption was lethal and "
          "the routes have been reorganised since; the mountain is not a "
          "theme park.",
    tip="It is a hard climb — 1,500 m of ascent on volcanic scree at "
        "altitude, in cold that surprises everyone. Go with a licensed "
        "operator who provides the tent and the layers, and train for it."),
"pacaya": dict(
    name="Pacaya", slug="Pacaya", country="Guatemala",
    region="Escuintla", type="mountain", tag="hidden",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    highlights=[("Cerro Chino", None),
                ("Lava fields", None),
                ("Lake Amatitlán", "Lake_Amatitlán")],
    blurb="An active volcano an hour from Guatemala City, and the easy one — "
          "a 90-minute walk brings you onto warm black lava fields with the "
          "cone smoking above. It has erupted more or less constantly since "
          "1965 and the surface underfoot is often only a few years old.",
    fact="Guides at the top toast marshmallows over vents in the rock where "
          "the ground is still hot enough to do it. That is genuinely how "
          "close the heat is to the surface.",
    tip="Take the afternoon departure to be up there at sunset — the lava "
        "field goes orange, the Pacific haze lights up, and you come down by "
        "head torch. Wear boots you do not mind ruining."),
"quirigua": dict(
    name="Quiriguá", slug="Quiriguá", country="Guatemala",
    region="Izabal", type="history", tag="hidden",
    emoji="🗿", sounds=["wilderness.mp3"],
    highlights=[("Stela E", None),
                ("Zoomorph P", None),
                ("Great Plaza", None),
                ("Copán", "Copán")],
    blurb="A small Maya site in a banana plantation in the Motagua valley, "
          "with the tallest carved stone monuments in the Americas. Nine "
          "sandstone stelae stand in one plaza, the largest of them 10.6 m "
          "high and cut from a single block.",
    fact="Quiriguá was a vassal of Copán until 738 AD, when its king "
          "captured and beheaded his overlord. Everything you see was put up "
          "in the seventy years of independence that followed — the whole "
          "site is a victory monument.",
    tip="It is a 45-minute detour from the Guatemala City–Puerto Barrios "
        "road and takes an hour to see. The stelae are under thatched "
        "shelters, so it works even in the valley's frequent rain."),
"yaxha": dict(
    name="Yaxhá", slug="Yaxha", country="Guatemala",
    region="Petén", type="history", tag="hidden",
    emoji="🌅", sounds=["wilderness.mp3"],
    highlights=[("Structure 216", None),
                ("Lake Yaxhá", None),
                ("Topoxté", None),
                ("Nakum", None)],
    blurb="The third largest Maya city in Guatemala, on a ridge between two "
          "lakes in the Petén, with over 500 structures and a fraction of a "
          "percent of Tikal's visitors. Its tallest temple looks west down "
          "the length of the lake.",
    fact="*Survivor: Guatemala* was filmed here in 2005, which paid for a "
          "good deal of the site's consolidation work — an unusual funding "
          "source for Maya archaeology, and a visible one.",
    tip="Climb Structure 216 for sunset over Lake Yaxhá and stay for the "
        "bats coming off the temple. There is a basic campsite at the lake "
        "shore, and after the gate closes you are effectively alone."),
# ========================== BELIZE ===========================
# belize-city, caracol and ambergris-caye already existed; these fill the
# rest of the country. Districts are used as the `region` string.
"san-ignacio": dict(
    name="San Ignacio", slug="San_Ignacio,_Belize", country="Belize",
    region="Cayo District", type="city", tag="hidden",
    emoji="🌿", sounds=["wilderness.mp3"],
    search_name="San Ignacio Cayo Belize",
    highlights=[("Cahal Pech", "Cahal_Pech"),
                ("Hawkesworth Bridge", None),
                ("Macal River", "Macal_River"),
                ("Green Iguana Conservation Project", None)],
    blurb="The hub of western Belize, on a hill between two rivers an hour "
          "from the Guatemalan border. Everything inland runs from here — the "
          "caves, the Maya sites, the Mountain Pine Ridge — and the Saturday "
          "market draws Creole, Maya, Mennonite and Lebanese Belize into one "
          "street.",
    fact="The Hawkesworth Bridge, built in 1949, is the only suspension "
          "bridge in Belize, and it is single-lane: traffic alternates by "
          "eye contact, which mostly works.",
    tip="Cahal Pech is a genuine Maya palace complex fifteen minutes' walk "
        "uphill from the town centre and it is almost always empty. Go at "
        "five, when the light comes in low through the courtyards."),
"caye-caulker": dict(
    name="Caye Caulker", slug="Caye_Caulker", country="Belize",
    region="Belize District", type="island", tag="hidden",
    emoji="🩴", sounds=["ocean-waves.mp3"],
    highlights=[("The Split", None),
                ("Belize Barrier Reef", "Belize_Barrier_Reef"),
                ("Shark Ray Alley", None),
                ("Caye Caulker Forest Reserve", None)],
    blurb="A sand island five miles long with three streets, no cars to "
          "speak of, and a town motto of 'Go Slow' painted on half the walls. "
          "Golf carts and bicycles only, the reef a fifteen-minute boat ride "
          "east, and lobster on a barbecue by the water most evenings.",
    fact="The Split — the channel that cuts the island in two — was opened "
          "by Hurricane Hattie in 1961 and has been widened by every storm "
          "since. It is now the island's main swimming spot.",
    tip="The water taxi from Belize City takes 45 minutes and runs all day, "
        "so this works as a stop rather than a stay. Snorkel Hol Chan and "
        "Shark Ray Alley on the half-day trip out of here — it is cheaper "
        "than the same trip from Ambergris."),
"great-blue-hole": dict(
    name="Great Blue Hole", slug="Great_Blue_Hole", country="Belize",
    region="Belize District", type="coastal", tag="famous",
    emoji="🕳️", sounds=["ocean-waves.mp3"],
    highlights=[("Lighthouse Reef", "Lighthouse_Reef"),
                ("Half Moon Caye", "Half_Moon_Caye"),
                ("Belize Barrier Reef", "Belize_Barrier_Reef")],
    blurb="A perfectly circular marine sinkhole 318 m across and 124 m deep, "
          "sitting in the middle of Lighthouse Reef 70 km offshore — a "
          "near-black disc in turquoise shallows that is one of the most "
          "recognisable shapes on Earth from the air.",
    fact="It is a drowned cave. Stalactites hang 40 m down its walls, formed "
          "when this was dry land during the last ice age, before the sea "
          "rose and the roof collapsed. Jacques Cousteau brought his ship "
          "*Calypso* here in 1971 and made it famous.",
    tip="Unless you are a certified diver comfortable at 40 m, the scenic "
        "flight is the better trip and a fraction of the price — the hole is "
        "a shape, and the shape is the point."),
"xunantunich": dict(
    name="Xunantunich", slug="Xunantunich", country="Belize",
    region="Cayo District", type="history", tag="hidden",
    emoji="🏛️", sounds=["wilderness.mp3"],
    highlights=[("El Castillo", None),
                ("Mopan River", "Mopan_River"),
                ("Plaza A-1", None),
                ("San Jose Succotz", None)],
    blurb="A Maya ceremonial centre on a ridge above the Mopan River, "
          "reached by a hand-cranked cable ferry that takes one car at a "
          "time. Its pyramid, El Castillo, is 40 m high and carries a "
          "restored stucco frieze of the sun god and the moon.",
    fact="The name means 'Stone Woman' in Maya and dates only from the "
          "1890s, when a local reported seeing a woman in white with glowing "
          "red eyes climb the pyramid and vanish into a wall. Nobody knows "
          "the city's original name.",
    tip="The ferry is free and runs on demand until five. From the top of El "
        "Castillo you can see across the border into Guatemala — the "
        "clearing on the horizon is Melchor de Mencos."),
"actun-tunichil-muknal": dict(
    name="Actun Tunichil Muknal", slug="Actun_Tunichil_Muknal",
    country="Belize",
    region="Cayo District", type="nature", tag="hidden",
    emoji="🔦", sounds=["waterfall.mp3"],
    search_name="Actun Tunichil Muknal ATM cave Belize",
    highlights=[("Crystal Maiden", None),
                ("Roaring Creek", None),
                ("Tapir Mountain Nature Reserve", None)],
    blurb="A river cave in the Tapir Mountain reserve that the Maya used for "
          "sacrifice, and which was found essentially untouched in 1989. You "
          "swim into the entrance, wade upstream for a kilometre, then climb "
          "into dry chambers holding pots and skeletons exactly where they "
          "were left.",
    fact="The 'Crystal Maiden' is the calcified skeleton of a teenager, "
          "sparkling because the cave has coated the bones in calcite over "
          "1,100 years. Cameras were banned outright in 2012 after a tourist "
          "dropped one on a skull.",
    tip="Licensed guides only, socks compulsory in the chambers, and no "
        "cameras of any kind. It is a full physical day — swimming, "
        "squeezing, climbing — and not for anyone unhappy in tight dark "
        "spaces."),
"placencia": dict(
    name="Placencia", slug="Placencia", country="Belize",
    region="Stann Creek District", type="coastal", tag="hidden",
    emoji="🌴", sounds=["ocean-waves.mp3"],
    highlights=[("Placencia Sidewalk", None),
                ("Silk Cayes", None),
                ("Monkey River", None),
                ("Placencia Lagoon", None)],
    blurb="A fishing village at the tip of a sixteen-mile sand peninsula, "
          "with the Caribbean on one side and a lagoon on the other. It has "
          "the best mainland beaches in Belize and a main street that is "
          "literally a concrete footpath.",
    fact="That footpath — the Placencia Sidewalk — was once in the Guinness "
          "Book as the narrowest main street in the world, at four feet "
          "wide. It is still how the village is laid out.",
    tip="Whale sharks gather off Gladden Spit around the full moons of March "
        "to June, when the snappers spawn. Outside that window, the Silk "
        "Cayes snorkel trip is the one to take."),
"hopkins": dict(
    name="Hopkins", slug="Hopkins,_Belize", country="Belize",
    region="Stann Creek District", type="coastal", tag="hidden",
    emoji="🥁", sounds=["ocean-waves.mp3"],
    search_name="Hopkins village Belize Garifuna",
    highlights=[("Sittee River", None),
                ("Cockscomb Basin", "Cockscomb_Basin_Wildlife_Sanctuary"),
                ("Lebeha Drumming Center", None),
                ("False Caye", None)],
    blurb="A Garifuna village strung along four miles of beach, with the "
          "Maya Mountains rising behind it and drumming most nights. It is "
          "the cultural centre of Garifuna Belize and the closest coast to "
          "the jaguar reserve.",
    fact="Garifuna Settlement Day, 19 November, is a national holiday in "
          "Belize and it is re-enacted here — boats coming ashore with "
          "cassava and drums, marking the 1832 arrival from Honduras.",
    tip="The Lebeha centre gives drumming lessons to anyone who turns up in "
        "the evening, and the money goes to the village's kids. Hudut — fish "
        "in coconut broth with mashed plantain — is the dish to order."),
"cockscomb-basin": dict(
    name="Cockscomb Basin", slug="Cockscomb_Basin_Wildlife_Sanctuary",
    country="Belize",
    region="Stann Creek District", type="wilderness", tag="hidden",
    emoji="🐆", sounds=["wilderness.mp3"],
    highlights=[("Victoria Peak", "Victoria_Peak_(Belize)"),
                ("Tiger Fern Falls", None),
                ("South Stann Creek", None),
                ("Maya Mountains", "Maya_Mountains")],
    blurb="150,000 acres of rainforest in the Maya Mountains, set aside in "
          "1990 as the world's first jaguar preserve. You will almost "
          "certainly not see a jaguar — the density here is among the "
          "highest anywhere, and they are still invisible — but the trails, "
          "waterfalls and birds are reason enough.",
    fact="The sanctuary was created after a study radio-collared jaguars "
          "here in the early 1980s and found the population was far larger "
          "than anyone believed. It remains the model that other big-cat "
          "reserves copied.",
    tip="The Tiger Fern trail is two steep hours to a twin waterfall with a "
        "swimming pool and a view over the whole basin. Start early; the "
        "afternoon rain in these mountains is reliable."),
"lamanai": dict(
    name="Lamanai", slug="Lamanai", country="Belize",
    region="Orange Walk District", type="history", tag="hidden",
    emoji="🐊", sounds=["wilderness.mp3"],
    highlights=[("High Temple", None),
                ("Mask Temple", None),
                ("New River Lagoon", None),
                ("Jaguar Temple", None)],
    blurb="A Maya city on the New River Lagoon that was occupied for over "
          "three thousand years — longer than almost any other in the Maya "
          "world — and was still lived in when Spanish friars arrived and "
          "built a church in the middle of it. The approach is an hour by "
          "boat up the river.",
    fact="The name means 'submerged crocodile' in Maya, and it is original — "
          "recorded by the Spanish in the 1570s. Crocodile imagery turns up "
          "on the pottery, the architecture, and in the lagoon itself.",
    tip="The boat trip is half the visit: howler monkeys in the riverside "
        "trees, jacanas walking on the lilies, and a good chance of a "
        "Morelet's crocodile. Go by river even if the road is passable."),
"belmopan": dict(
    name="Belmopan", slug="Belmopan", country="Belize",
    region="Cayo District", type="city", tag="hidden",
    emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("National Assembly Building", None),
                ("Guanacaste National Park", None),
                ("Belize Archives", None),
                ("Blue Hole National Park", None)],
    blurb="The smallest capital city in the Americas — around 25,000 people "
          "— built inland from scratch in 1970 after Hurricane Hattie "
          "flattened Belize City. Its government buildings were modelled on "
          "Maya architecture, and the whole place is set in parkland.",
    fact="The name is a portmanteau of Belize and Mopan, the river and the "
          "Maya people. Moving the capital took nine years and the old "
          "capital is still four times larger.",
    tip="Guanacaste National Park sits at the edge of town where two rivers "
        "meet, and is fifty acres of gallery forest with a huge namesake "
        "tree in it. Twenty minutes' walk from the bus terminal."),
# ======================== EL SALVADOR ========================
# Another country with nothing in the atlas before this batch. Santa Ana is
# both a city and a volcano here, and there is a Santa Ana in California and
# one in Costa Rica, so both records carry a search_name.
"san-salvador": dict(
    name="San Salvador", slug="San_Salvador", country="El Salvador",
    region="San Salvador", type="city", tag="famous",
    emoji="🌋", sounds=["city-hum.mp3"],
    highlights=[("Catedral Metropolitana", None),
                ("Iglesia El Rosario", None),
                ("Teatro Nacional", None),
                ("Monumento al Divino Salvador del Mundo", None),
                ("San Salvador Volcano", "San_Salvador_(volcano)")],
    blurb="The capital, sitting in a valley beneath its own volcano, rebuilt "
          "so many times after earthquakes that the old city is mostly gone. "
          "What is left is a dense, loud, fast-changing place — and El "
          "Rosario, a concrete arc of a church that is one of the great "
          "modernist interiors of Latin America.",
    fact="El Rosario looks like a warehouse from outside and like a "
          "cathedral of light inside: the whole barrel vault is set with "
          "coloured glass so that the nave changes colour through the day. "
          "Almost nobody visiting the city knows it is there.",
    tip="Drive up the Puerta del Diablo on the ridge south of the city for "
        "the valley on one side and the Pacific on the other, then carry on "
        "to Panchimalco for the painted village underneath it."),
"santa-ana-el-salvador": dict(
    name="Santa Ana", slug="Santa_Ana,_El_Salvador", country="El Salvador",
    region="Santa Ana", type="city", tag="hidden",
    emoji="🎭", sounds=["plaza.mp3"],
    search_name="Santa Ana El Salvador city",
    highlights=[("Teatro de Santa Ana", None),
                ("Catedral de Santa Ana", None),
                ("Parque Libertad", None),
                ("Lake Coatepeque", "Lake_Coatepeque")],
    blurb="El Salvador's second city, made rich by coffee at the turn of the "
          "20th century and still showing it — a neo-gothic cathedral in "
          "white, a renaissance-revival theatre, and a plaza that fills in "
          "the evening. The volcano, the lake and the ruins are all within "
          "an hour.",
    fact="The Teatro de Santa Ana opened in 1910 with money from the coffee "
          "barons, was used as a cinema, then abandoned; it was restored in "
          "the 1990s and its painted ceiling and boxes are intact.",
    tip="Base yourself here rather than in the capital for the western "
        "half of the country. Coatepeque, Cerro Verde, Tazumal and the Ruta "
        "de las Flores are all day trips from this plaza."),
"lake-coatepeque": dict(
    name="Lake Coatepeque", slug="Lake_Coatepeque", country="El Salvador",
    region="Santa Ana", type="nature", tag="hidden",
    emoji="💠", sounds=["wind.mp3"],
    highlights=[("Cerro Verde", None),
                ("Isla Teopán", None),
                ("Santa Ana Volcano", "Santa_Ana_Volcano")],
    blurb="A caldera lake 26 km² across in a bowl of green hills, with the "
          "Santa Ana and Izalco volcanoes standing over the far shore. The "
          "water is warm, deep and — a few times a decade — turns bright "
          "turquoise for weeks at a time.",
    fact="Those colour changes are real and still argued over: the working "
          "explanation is a bloom of sulphur-eating bacteria fed by "
          "hydrothermal vents in the caldera floor, which turns the whole "
          "lake milky blue.",
    tip="Most of the shoreline is private, so use one of the restaurant "
        "docks — a few dollars gets you a table, a jetty and swimming. "
        "Morning is glassy; the afternoon wind picks up hard."),
"santa-ana-volcano": dict(
    name="Santa Ana Volcano", slug="Santa_Ana_Volcano",
    country="El Salvador",
    region="Santa Ana", type="mountain", tag="hidden",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    search_name="Santa Ana Volcano Ilamatepec El Salvador",
    highlights=[("Cerro Verde National Park", None),
                ("Izalco", "Izalco_(volcano)"),
                ("Crater lake", None),
                ("Lake Coatepeque", "Lake_Coatepeque")],
    blurb="At 2,381 m the highest volcano in El Salvador, known locally as "
          "Ilamatepec, with a nested crater holding a turquoise sulphur lake "
          "that steams constantly. Two hours up through cloud forest from "
          "Cerro Verde, and one of the best summit views in Central "
          "America.",
    fact="Its neighbour Izalco erupted so regularly between 1770 and 1958 "
          "that sailors called it the Lighthouse of the Pacific. A hotel was "
          "built at Cerro Verde to watch it — and the eruptions stopped the "
          "year the hotel opened.",
    tip="The hike leaves in one guided group each morning, usually at "
        "eleven, with a police escort. Turn up by ten; if you miss it there "
        "is no second departure."),
"joya-de-ceren": dict(
    name="Joya de Cerén", slug="Joya_de_Cerén", country="El Salvador",
    region="La Libertad", type="history", tag="hidden",
    emoji="🌽", sounds=["wilderness.mp3"],
    highlights=[("San Andrés", None),
                ("Loma Caldera", None),
                ("Site museum", None)],
    blurb="A Maya farming village buried under six metres of ash by an "
          "eruption around 600 AD and dug out again in 1976 — with the "
          "houses, the kitchens, the storerooms, the sleeping mats and the "
          "food still on the plates. The Pompeii of the Americas, and "
          "UNESCO listed.",
    fact="It is the only place anywhere that shows how ordinary Maya people "
          "actually lived — every other site is temples and palaces. The "
          "eruption came at night, everyone escaped, and nothing was looted "
          "afterwards.",
    tip="It was found by a bulldozer levelling ground for grain silos; the "
        "driver stopped when clay floors turned up. Combine it with San "
        "Andrés, ten minutes away, in the same morning."),
"tazumal": dict(
    name="Tazumal", slug="Tazumal", country="El Salvador",
    region="Santa Ana", type="history", tag="hidden",
    emoji="🗿", sounds=["plaza.mp3"],
    highlights=[("Casa Blanca", None),
                ("Chalchuapa", "Chalchuapa"),
                ("Site museum", None)],
    blurb="The largest and best-preserved Maya structure in El Salvador, a "
          "stepped pyramid in the middle of the town of Chalchuapa, "
          "surrounded on all sides by houses. The name means 'the place "
          "where the victims were burned'.",
    fact="The site was occupied for around 1,300 years and shows Teotihuacan "
          "influence from central Mexico a thousand kilometres away — the "
          "*talud-tablero* wall profile is unmistakable.",
    tip="A 1950s restoration coated part of the pyramid in cement, which "
        "you can see and which archaeologists still wince at. The small "
        "museum explains what is original and what is not."),
"concepcion-de-ataco": dict(
    name="Concepción de Ataco", slug="Concepción_de_Ataco",
    country="El Salvador",
    region="Ahuachapán", type="nature", tag="hidden",
    emoji="🌺", sounds=["wilderness.mp3"],
    search_name="Concepcion de Ataco Ruta de las Flores",
    highlights=[("Juayúa", "Juayúa"),
                ("Apaneca", "Apaneca"),
                ("Los Chorros de la Calera", None),
                ("Nahuizalco", None)],
    blurb="The prettiest stop on the Ruta de las Flores, a 36 km road "
          "through the coffee highlands linking five small towns and named "
          "for the wild flowers that come out along it between October and "
          "February. Ataco itself is murals on every wall, cold nights at "
          "1,300 m, and coffee roasted on the plaza.",
    fact="Juayúa's *feria gastronómica* has run every Saturday and Sunday "
          "since 1997 and turns the whole plaza into a grill — it started as "
          "an attempt to bring visitors back after the civil war, and it "
          "worked.",
    tip="Do it on a weekend or half of it is closed. Ataco is the prettiest "
        "and the one to sleep in; Apaneca has the coffee farms and the "
        "highest point on the road."),
"perquin": dict(
    name="Perquín", slug="Perquín", country="El Salvador",
    region="Morazán", type="history", tag="hidden",
    emoji="🕊️", sounds=["mountain-wind.mp3"],
    highlights=[("Museo de la Revolución Salvadoreña", None),
                ("El Mozote", "El_Mozote_massacre"),
                ("Río Sapo", None),
                ("Cerro Perquín", None)],
    blurb="A mountain town near the Honduran border that was the "
          "headquarters of the FMLN guerrillas through the 1980s civil war, "
          "and is now a quiet pine-forest village with a small museum run by "
          "former combatants.",
    fact="Radio Venceremos broadcast from caves around this town for the "
          "whole war, moving its transmitter constantly to stay ahead of the "
          "army. The equipment is in the museum.",
    tip="El Mozote, twenty minutes away, is where the army killed around a "
        "thousand villagers in December 1981. There is a memorial and a "
        "garden, and locals who survived will walk you through it. Go, and "
        "go quietly."),
"la-libertad-el-salvador": dict(
    name="La Libertad", slug="La_Libertad,_El_Salvador",
    country="El Salvador",
    region="La Libertad", type="coastal", tag="hidden",
    emoji="🏄", sounds=["ocean-waves.mp3"],
    search_name="La Libertad El Salvador surf coast",
    highlights=[("El Tunco", None),
                ("Playa Sunzal", None),
                ("Punta Roca", None),
                ("El Zonte", None),
                ("Tamanique waterfalls", None)],
    blurb="The Pacific port half an hour from the capital, and the anchor "
          "of El Salvador's surf coast — Punta Roca breaks off the pier "
          "itself, and the black-sand village of El Tunco, named for the "
          "pig-shaped rock offshore, is ten minutes west along the Balsamo "
          "cliffs.",
    fact="El Salvador's Pacific points are consistent enough that the World "
          "Surf League has run championship-tour events at Punta Roca, five "
          "minutes up the coast — the country markets itself as Surf City "
          "for a reason.",
    tip="The sand along this coast is coarse, black and genuinely too hot "
        "to walk on by midday. Learn at Sunzal, which is sandier and far "
        "kinder to beginners than the rocks at El Tunco or the reef at "
        "Punta Roca."),
# ========================== HONDURAS =========================
"copan": dict(
    name="Copán", slug="Copán", country="Honduras",
    region="Copán", type="history", tag="famous",
    emoji="🗿", sounds=["wilderness.mp3"],
    search_name="Copan ruins Honduras Maya",
    highlights=[("Hieroglyphic Stairway", None),
                ("Great Plaza", None),
                ("Rosalila Temple", None),
                ("Altar Q", None),
                ("Copán Ruinas", "Copán_Ruinas")],
    blurb="The southeastern capital of the Maya world, in a river valley "
          "near the Guatemalan border, and the one everybody goes to for the "
          "carving. Copán's sculptors worked in a soft volcanic tuff that let "
          "them cut almost in the round — the portrait stelae here have no "
          "equal anywhere else.",
    fact="The Hieroglyphic Stairway carries around 2,200 glyph blocks across "
          "62 steps — the longest Maya inscription in existence. A "
          "19th-century reconstruction put many of the blocks back in the "
          "wrong order, and scholars are still unpicking the text.",
    tip="Pay the extra for the tunnels under Structure 16: they run past the "
        "Rosalila temple, buried whole and still carrying its original red "
        "and green paint. Ten minutes underground, and the best thing on the "
        "site."),
"roatan": dict(
    name="Roatán", slug="Roatán", country="Honduras",
    region="Islas de la Bahía", type="island", tag="famous",
    emoji="🐠", sounds=["ocean-waves.mp3"],
    highlights=[("West Bay Beach", None),
                ("West End", None),
                ("Mesoamerican Barrier Reef",
                 "Mesoamerican_Barrier_Reef_System"),
                ("Punta Gorda", None),
                ("Sandy Bay", None)],
    blurb="The largest of the Bay Islands, 60 km off the Honduran coast and "
          "lying along the second-biggest barrier reef on Earth. Reef wall "
          "starts a few strokes from the beach, English is widely spoken "
          "from the island's buccaneer past, and diving is cheap.",
    fact="The islands were English-speaking and British-administered until "
          "1861, when Britain handed them to Honduras. Roatán's Punta Gorda "
          "is also the oldest Garifuna settlement anywhere, founded by the "
          "1797 deportees from St Vincent.",
    tip="West End is where the dive shops and the cheap rooms are; West Bay, "
        "twenty minutes away by water taxi, has the beach. Snorkelling "
        "straight off West Bay's sand reaches live coral within 50 m."),
"utila": dict(
    name="Utila", slug="Utila", country="Honduras",
    region="Islas de la Bahía", type="island", tag="hidden",
    emoji="🦈", sounds=["ocean-waves.mp3"],
    highlights=[("Whale shark grounds", None),
                ("Water Cay", None),
                ("Pumpkin Hill", None),
                ("Utila Cays", None)],
    blurb="The smallest and scruffiest of the Bay Islands, with one street, "
          "no cars worth mentioning, and a reputation as one of the cheapest "
          "places in the world to learn to dive. Whale sharks pass the "
          "north shore year-round.",
    fact="The deep water drops away close to the island's north side, which "
          "is why whale sharks feed here in every month of the year rather "
          "than in a short season — Utila is one of only a handful of places "
          "on Earth where that is true.",
    tip="Boils — patches of churning water with birds over them — mean bait "
        "fish at the surface and often a whale shark underneath. Boats look "
        "for them on the way out to the dive sites."),
"tegucigalpa": dict(
    name="Tegucigalpa", slug="Tegucigalpa", country="Honduras",
    region="Francisco Morazán", type="city", tag="famous",
    emoji="⛰️", sounds=["city-hum.mp3"],
    highlights=[("Catedral de San Miguel", None),
                ("Basílica de Suyapa", None),
                ("La Tigra National Park", "La_Tigra_National_Park"),
                ("Parque Central", None),
                ("Valle de Ángeles", None)],
    blurb="The capital, at 990 m in a bowl of mountains, founded as a silver "
          "mining camp in 1578 and grown into a city that climbs every hill "
          "around it. Colonial core, a cathedral of dark stone, and cloud "
          "forest half an hour from the centre.",
    fact="The name is often glossed as 'silver hill', though linguists "
          "dispute it. What is certain is the silver: the town existed "
          "because of the mines, and only became capital in 1880 after "
          "decades of alternating with Comayagua.",
    tip="La Tigra was Central America's first national park and its trails "
          "run through the ruins of an American mining company's town. From "
          "the capital it is an hour, and the birding is superb."),
"la-ceiba": dict(
    name="La Ceiba", slug="La_Ceiba", country="Honduras",
    region="Atlántida", type="city", tag="hidden",
    emoji="🎉", sounds=["city-hum.mp3"],
    highlights=[("Pico Bonito National Park", "Pico_Bonito_National_Park"),
                ("Cangrejal River", None),
                ("Cayos Cochinos", "Cayos_Cochinos"),
                ("Playa de Perú", None)],
    blurb="The north-coast port between the Caribbean and the wall of Pico "
          "Bonito, and the gateway to the Bay Islands. It is the country's "
          "party town — the May carnival is the biggest in Honduras — and "
          "the base for whitewater on the Cangrejal.",
    fact="La Ceiba grew as a banana port for the Standard Fruit Company, and "
          "the old saying is that Tegucigalpa thinks, San Pedro Sula works, "
          "and La Ceiba parties.",
    tip="The Cangrejal valley starts fifteen minutes from town and has "
        "lodges right on the river at the park boundary. Staying up there "
        "rather than in the city gets you rainforest, rapids and no noise."),
"pico-bonito": dict(
    name="Pico Bonito", slug="Pico_Bonito_National_Park", country="Honduras",
    region="Atlántida", type="wilderness", tag="hidden",
    emoji="🦋", sounds=["wilderness.mp3"],
    highlights=[("Cangrejal River", None),
                ("Zacate Falls", None),
                ("Nombre de Dios range", None),
                ("Río Bonito", None)],
    blurb="A national park that rises from near sea level to 2,436 m in "
          "barely 20 km — rainforest, cloud forest and a summit almost "
          "nobody reaches, packed against the Caribbean coast. Over 400 bird "
          "species, jaguars, and rivers that come off the mountain cold and "
          "fast.",
    fact="The main peak has been climbed only a handful of times. There is "
          "no trail, the ridges are knife-edged and permanently wet, and "
          "expeditions have turned back a few hundred metres from the top.",
    tip="You do not need the summit. The Zacate Falls trail from the "
        "Cangrejal side is a couple of hours through primary forest to a "
        "waterfall with a swimming pool, and the guides there are local and "
        "genuinely good on birds."),
"cayos-cochinos": dict(
    name="Cayos Cochinos", slug="Cayos_Cochinos", country="Honduras",
    region="Islas de la Bahía", type="island", tag="hidden",
    emoji="🐡", sounds=["ocean-waves.mp3"],
    highlights=[("Cayo Menor", None),
                ("Chachahuate", None),
                ("Cayo Mayor", None),
                ("Mesoamerican Barrier Reef",
                 "Mesoamerican_Barrier_Reef_System")],
    blurb="Two small forested islands and thirteen sand cays 30 km off the "
          "coast, protected as a marine reserve with no commercial fishing "
          "and no development. Garifuna families live on Chachahuate in "
          "thatched houses on sand, and the reef is as intact as it gets in "
          "the Caribbean.",
    fact="The reserve was the filming location for several seasons of the "
          "Italian and Spanish versions of *Survivor*, which pay a fee that "
          "funds the marine patrols.",
    tip="Day trips run from Sambo Creek near La Ceiba. Chachahuate has "
        "hammocks and fried fish and you can arrange to stay the night with "
        "a family — there is no electricity after dark, which is the point."),
"gracias-honduras": dict(
    name="Gracias", slug="Gracias,_Lempira", country="Honduras",
    region="Lempira", type="history", tag="hidden",
    emoji="♨️", sounds=["plaza.mp3"],
    search_name="Gracias Lempira Honduras town",
    highlights=[("Fuerte San Cristóbal", None),
                ("Celaque National Park", "Celaque_National_Park"),
                ("Aguas Termales", None),
                ("La Campa", None)],
    blurb="A cobbled colonial town in the western highlands that was, "
          "briefly in the 1540s, the administrative capital of all Spanish "
          "Central America. It has a hilltop fort, three old churches, hot "
          "springs in the forest and the country's highest mountain behind "
          "it.",
    fact="Lempira, the Lenca leader who fought the Spanish here and gave "
          "both the department and the currency their name, was killed near "
          "this town in 1537 — reportedly during peace talks.",
    tip="The Aguas Termales are twenty minutes out of town: stone pools of "
        "different temperatures under trees, open into the evening. Go after "
        "dark, when it is lit by candles and full of locals."),
"celaque": dict(
    name="Celaque", slug="Celaque_National_Park", country="Honduras",
    region="Lempira", type="mountain", tag="hidden",
    emoji="☁️", sounds=["mountain-wind.mp3"],
    highlights=[("Cerro Las Minas", None),
                ("Visitor centre trail", None),
                ("Gracias", "Gracias,_Lempira")],
    blurb="A cloud forest massif holding Cerro Las Minas, at 2,870 m the "
          "highest point in Honduras. The name is Lenca for 'box of water' — "
          "eleven rivers rise inside the park — and the summit forest is "
          "hung with moss and bromeliads and usually inside a cloud.",
    fact="Quetzals nest here, and the park's cloud forest is one of the "
          "largest continuous stands left in Central America. The summit is "
          "a two-day walk from the visitor centre, with a basic camp "
          "halfway.",
    tip="If you are not camping, walk the first two hours to the Don Tomás "
        "waterfall and back. You get the forest, the moss and the birds "
        "without committing to the mountain."),
"lago-de-yojoa": dict(
    name="Lago de Yojoa", slug="Lake_Yojoa", country="Honduras",
    region="Cortés", type="nature", tag="hidden",
    emoji="🦆", sounds=["wind.mp3"],
    search_name="Lago de Yojoa Honduras",
    highlights=[("Pulhapanzak Falls", "Pulhapanzak_Falls"),
                ("Cerro Azul Meámbar", None),
                ("Santa Bárbara National Park", None),
                ("Los Naranjos", None)],
    blurb="Honduras's largest natural lake, sitting between two mountain "
          "national parks on the road between the capital and San Pedro "
          "Sula. Over 400 bird species have been counted around it, and the "
          "lakeside stalls sell fried fish by the kilo.",
    fact="Pulhapanzak, a 43 m waterfall ten minutes from the lake, has a "
          "guided route that takes you *behind and through* the falling "
          "water into caves in the rock face. You come out soaked and "
          "shouting.",
    tip="The lake is on the main highway and most people drive past it. "
        "Stop, take a kayak out at dawn for the birds, and eat at one of the "
        "roadside fish shacks on the way out."),
"comayagua": dict(
    name="Comayagua", slug="Comayagua", country="Honduras",
    region="Comayagua", type="history", tag="hidden",
    emoji="🕰️", sounds=["plaza.mp3"],
    highlights=[("Catedral de Comayagua", None),
                ("Iglesia La Merced", None),
                ("Museo Colonial", None),
                ("Parque Central", None)],
    blurb="The colonial capital of Honduras until 1880, an hour and a half "
          "north of Tegucigalpa, with the best-preserved Spanish centre in "
          "the country — a cathedral of pale stone, low arcaded streets and "
          "a plaza that has barely changed in two centuries.",
    fact="The cathedral's clock is Moorish, built in Seville around 1100 for "
          "the Alhambra and given to this town by Philip II. It is "
          "reckoned the oldest working clock in the Americas and one of the "
          "oldest anywhere.",
    tip="Holy Week here is the event: the streets are carpeted in coloured "
        "sawdust in enormous patterns overnight, then walked over by the "
        "procession at dawn."),
# ========================= NICARAGUA =========================
# Granada and León both have far louder Spanish namesakes, and León is also
# a large city in Guanajuato which is in this same batch — both need a
# search_name, and P17 catches the Spanish pages.
"granada-nicaragua": dict(
    name="Granada", slug="Granada,_Nicaragua", country="Nicaragua",
    region="Granada", type="history", tag="famous",
    emoji="🎨", sounds=["plaza.mp3"],
    search_name="Granada Nicaragua colonial city",
    highlights=[("Catedral de Granada", None),
                ("Iglesia La Merced", None),
                ("Calle La Calzada", None),
                ("Las Isletas", None),
                ("Mombacho", "Mombacho")],
    blurb="Founded in 1524 on the shore of Lake Nicaragua, and one of the "
          "oldest European-founded cities on the American mainland. Ochre, "
          "red and blue single-storey houses on a grid, horse carriages "
          "still working the streets, and a volcano behind the town.",
    fact="The American filibuster William Walker declared himself president "
          "of Nicaragua from here in 1856, and when he was driven out the "
          "next year he burned the city and left a sign reading 'Here was "
          "Granada'. Most of what stands was rebuilt afterwards.",
    tip="Climb La Merced's bell tower at five for the rooftops with Mombacho "
        "behind them — it is the photograph of Granada, and it costs a "
        "dollar. Then take a panga out through Las Isletas, 365 small "
        "islands thrown into the lake by the volcano."),
"leon-nicaragua": dict(
    name="León", slug="León,_Nicaragua", country="Nicaragua",
    region="León", type="city", tag="famous",
    emoji="⛪", sounds=["plaza.mp3"],
    search_name="Leon Nicaragua city cathedral",
    highlights=[("León Cathedral", "León_Cathedral,_Nicaragua"),
                ("Cerro Negro", "Cerro_Negro"),
                ("Museo Ortiz-Gurdián", None),
                ("León Viejo", "Ruins_of_León_Viejo"),
                ("Las Peñitas", None)],
    blurb="The intellectual and revolutionary capital of Nicaragua — "
          "university city, mural city, and home to the largest cathedral in "
          "Central America, whose white roof you can walk barefoot across. "
          "Hotter and rougher than Granada, and far more alive.",
    fact="The cathedral's plans were reportedly approved in Madrid for a "
          "much smaller building; the story goes that the architect "
          "submitted modest drawings and built something enormous, which is "
          "why it took 100 years and is now UNESCO listed.",
    tip="Cerro Negro, 40 minutes away, is a young cinder cone you climb in "
        "an hour and then ride back down on a plywood board at 50 km/h. "
        "Volcano boarding was invented here and it is as silly as it "
        "sounds."),
"ometepe": dict(
    name="Ometepe", slug="Ometepe", country="Nicaragua",
    region="Rivas", type="island", tag="famous",
    emoji="🌋", sounds=["wind.mp3"],
    highlights=[("Concepción", "Concepción_(volcano)"),
                ("Maderas", "Maderas"),
                ("Ojo de Agua", None),
                ("Playa Santo Domingo", None),
                ("Charco Verde", None)],
    blurb="An hourglass-shaped island in Lake Nicaragua formed by two "
          "volcanoes joined by a low isthmus — one a perfect smoking cone, "
          "the other extinct and topped with a crater lake in cloud forest. "
          "The ferry from San Jorge takes an hour and the island runs on its "
          "own time.",
    fact="Ometepe is the largest volcanic island inside a freshwater lake "
          "anywhere in the world. The lake also holds bull sharks, which "
          "swim up the Río San Juan from the Caribbean and adapt to fresh "
          "water.",
    tip="Ojo de Agua is a spring-fed pool of cold, absurdly clear volcanic "
        "water in the middle of a banana plantation. Hire a scooter, but "
        "note the road round Maderas is broken concrete and mud."),
"san-juan-del-sur": dict(
    name="San Juan del Sur", slug="San_Juan_del_Sur", country="Nicaragua",
    region="Rivas", type="coastal", tag="hidden",
    emoji="🏄", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Maderas", None),
                ("Cristo de la Misericordia", None),
                ("Playa Hermosa", None),
                ("La Flor Wildlife Refuge", None)],
    blurb="A horseshoe bay on the Pacific near the Costa Rican border, once "
          "a transit port for gold-rush passengers crossing the isthmus and "
          "now Nicaragua's surf town — fishing boats in the bay, a giant "
          "Christ on the headland, and better breaks a short truck ride "
          "north and south.",
    fact="Before the Panama Canal, Cornelius Vanderbilt ran passengers from "
          "New York to California through Nicaragua: up the Río San Juan, "
          "across the lake, then by stagecoach to this bay for the Pacific "
          "steamer.",
    tip="La Flor, an hour south, gets *arribadas* — mass nesting of olive "
        "ridley turtles, thousands coming ashore over a few nights between "
        "July and January. Ranger-guided only, at night, and unforgettable."),
"masaya-volcano": dict(
    name="Masaya Volcano", slug="Masaya_Volcano", country="Nicaragua",
    region="Masaya", type="mountain", tag="famous",
    emoji="🔥", sounds=["mountain-wind.mp3"],
    highlights=[("Santiago Crater", None),
                ("Masaya", "Masaya"),
                ("Laguna de Masaya", None),
                ("Mercado de Artesanías", None)],
    blurb="One of the very few volcanoes on Earth with a lava lake you can "
          "drive to. The road goes to the rim of the Santiago crater, and "
          "when the lake is up you look straight down into moving orange "
          "rock a couple of hundred metres below.",
    fact="The Spanish called it La Boca del Infierno — the mouth of hell — "
          "and in 1529 a friar planted a cross on the rim to exorcise it. "
          "The cross is still replaced.",
    tip="Access is by timed night slot and cars are turned to face out on "
        "arrival, in case of an evacuation. Book ahead; the ten minutes you "
        "get at the rim after dark are worth the whole trip."),
"laguna-de-apoyo": dict(
    name="Laguna de Apoyo", slug="Apoyo_Lagoon_Natural_Reserve",
    country="Nicaragua",
    region="Masaya", type="nature", tag="hidden",
    emoji="💧", sounds=["wind.mp3"],
    search_name="Laguna de Apoyo Nicaragua crater lake",
    highlights=[("Catarina Mirador", None),
                ("Granada", "Granada,_Nicaragua"),
                ("Diriá", None),
                ("Masaya Volcano", "Masaya_Volcano")],
    blurb="A crater lake between Granada and Masaya, 200 m deep and 6 km "
          "across, with warm, faintly mineral water and forested walls all "
          "the way round. Twenty minutes from Granada and the best swim in "
          "the country.",
    fact="The lake holds several species of cichlid fish found nowhere else "
          "on Earth — they evolved inside this crater after the eruption "
          "about 23,000 years ago, and they are a textbook case of rapid "
          "speciation.",
    tip="The mirador at Catarina looks down on the whole lagoon with Granada "
        "and the lake beyond it. Then go down to a lakeside hostel — most "
        "let day visitors use the dock and kayaks for the price of lunch."),
"corn-islands": dict(
    name="Corn Islands", slug="Corn_Islands", country="Nicaragua",
    region="South Caribbean Coast", type="island", tag="hidden",
    emoji="🥥", sounds=["ocean-waves.mp3"],
    highlights=[("Little Corn Island", None),
                ("Big Corn Island", "Big_Corn_Island"),
                ("Otto Beach", None),
                ("Long Bay", None)],
    blurb="Two small Caribbean islands 70 km off Nicaragua's Atlantic coast, "
          "where the language is Creole English, the economy is lobster, and "
          "Little Corn has no cars at all — just sand paths, palms and a "
          "reef that comes in close.",
    fact="The islands were part of the British Mosquito Coast protectorate "
          "and were leased to the United States for 99 years under the 1914 "
          "Bryan–Chamorro Treaty. The lease was only formally cancelled in "
          "1971.",
    tip="Getting there is a flight to Big Corn then a 30-minute panga to "
        "Little Corn that is genuinely rough. Take the morning boat, sit at "
        "the back, and expect to be soaked."),
"somoto-canyon": dict(
    name="Somoto Canyon", slug="Somoto_Canyon", country="Nicaragua",
    region="Madriz", type="nature", tag="hidden",
    emoji="🏞️", sounds=["waterfall.mp3"],
    highlights=[("Río Coco", "Coco_River"),
                ("Somoto", None),
                ("Namancambre falls", None)],
    blurb="A narrow gorge in the far north where the Río Coco cuts 160 m "
          "down through rock that is among the oldest exposed in Central "
          "America. You go through it in the water — swimming, wading and "
          "jumping — because there is no path.",
    fact="The canyon was only 'discovered' by science in 2004, when a Czech "
          "geological team mapped it. Local farmers had of course always "
          "known; it simply had never appeared on a tourist map.",
    tip="Take a local guide from the community co-operative at the entrance "
        "— they run the boats at the deep end and know which jumps are safe "
        "at that week's water level. Dry bag or leave everything behind."),
"esteli": dict(
    name="Estelí", slug="Estelí", country="Nicaragua",
    region="Estelí", type="city", tag="hidden",
    emoji="🚬", sounds=["city-hum.mp3"],
    highlights=[("Miraflor Nature Reserve", None),
                ("Tisey Reserve", None),
                ("Salto Estanzuela", None),
                ("Cigar factories", None)],
    blurb="A working highland city at 800 m, cooler than the lowlands, and "
          "the centre of Nicaragua's cigar industry — the trade moved here "
          "wholesale from Cuba after 1961 and the valley's soil turned out "
          "to suit it. Revolutionary murals still cover the walls.",
    fact="Estelí was fought over three times in the 1978–79 insurrection and "
          "shelled heavily. The murals painted afterwards are one of the "
          "largest collections of revolutionary street art anywhere, and "
          "many are original.",
    tip="Miraflor, an hour up a dirt road, is a protected area of cloud "
        "forest farmed by a co-operative of families who take guests in "
        "their houses. Orchids, quetzals, coffee picked that morning."),
"solentiname": dict(
    name="Solentiname", slug="Solentiname_Islands", country="Nicaragua",
    region="Río San Juan", type="island", tag="hidden",
    emoji="🖌️", sounds=["wind.mp3"],
    highlights=[("Mancarrón", None),
                ("San Fernando", None),
                ("Petroglyphs", None),
                ("Lake Nicaragua", "Lake_Nicaragua")],
    blurb="An archipelago of 36 islands at the far southern end of Lake "
          "Nicaragua, reached by a long boat ride from San Carlos, and home "
          "to a community of primitivist painters and balsa-wood carvers "
          "whose work hangs in galleries worldwide.",
    fact="The painting school began in the 1960s when the priest and poet "
          "Ernesto Cardenal founded a Christian commune here and handed out "
          "brushes to the farmers. The islands later became a base for the "
          "insurrection, and the National Guard burned the community down.",
    tip="Getting here is a serious journey — bus to San Carlos, then a slow "
        "boat. Stay on Mancarrón, visit the painters at home, and take the "
        "sunset out to the archipelago's petroglyph rocks."),
"managua": dict(
    name="Managua", slug="Managua", country="Nicaragua",
    region="Managua", type="city", tag="hidden",
    emoji="🌅", sounds=["city-hum.mp3"],
    highlights=[("Old Cathedral of Managua", None),
                ("Puerto Salvador Allende", None),
                ("Huellas de Acahualinca", "Acahualinca_footprints"),
                ("Loma de Tiscapa", None),
                ("Lake Managua", "Lake_Managua")],
    blurb="The capital, on the shore of Lake Managua, chosen in 1852 as a "
          "compromise between León and Granada, who could not stop fighting "
          "over it. Two earthquakes destroyed the centre, so the city has no "
          "real downtown — it spreads instead, with landmarks scattered "
          "across it.",
    fact="The Acahualinca footprints are human tracks pressed into volcanic "
          "mud on the lakeshore around 2,100 years ago — a group walking, "
          "unhurried, towards the water. They are among the oldest human "
          "traces in Central America.",
    tip="The shell of the old cathedral, wrecked in 1972 and never rebuilt, "
        "still stands over the old plaza with the sky through its roof. Look "
        "from outside — it is structurally unsafe and closed."),
# ========================= COSTA RICA ========================
# san-jose, arenal-volcano, monteverde and manuel-antonio already existed.
# Santa Teresa, Puerto Viejo and Montezuma all have much louder namesakes
# elsewhere in the Americas, so all three declare a search_name.
"tortuguero": dict(
    name="Tortuguero", slug="Tortuguero_National_Park", country="Costa Rica",
    region="Limón Province", type="wilderness", tag="famous",
    emoji="🐢", sounds=["wilderness.mp3"],
    search_name="Tortuguero National Park Costa Rica",
    highlights=[("Tortuguero canals", None),
                ("Cerro Tortuguero", None),
                ("Tortuguero village", None),
                ("Sea Turtle Conservancy", None)],
    blurb="A roadless stretch of Caribbean coast where a network of "
          "freshwater canals runs behind the beach through rainforest. You "
          "arrive by boat or small plane, move by paddle, and the beach "
          "beyond the trees is the most important green turtle nesting "
          "ground in the western hemisphere.",
    fact="Around 30,000 green turtles come ashore here in a season. The "
          "conservancy that protects them has been tagging turtles on this "
          "beach since 1959 — the longest-running sea turtle study "
          "anywhere.",
    tip="Nesting runs July to October, hatching August to November, and "
        "night beach walks are guided and strictly no-light. Outside that "
        "season come anyway and take a canoe up the smaller canals at dawn "
        "for the caimans, sloths and river otters."),
"corcovado": dict(
    name="Corcovado", slug="Corcovado_National_Park", country="Costa Rica",
    region="Puntarenas Province", type="wilderness", tag="famous",
    emoji="🦜", sounds=["wilderness.mp3"],
    search_name="Corcovado National Park Costa Rica Osa",
    highlights=[("Sirena Station", None),
                ("Osa Peninsula", "Osa_Peninsula"),
                ("Drake Bay", "Bahía_Drake"),
                ("Salsipuedes", None)],
    blurb="The wildest place in Costa Rica: 424 km² of lowland tropical "
          "rainforest on the Osa Peninsula, holding the last big stand of "
          "Pacific coast rainforest in Central America. Tapirs, scarlet "
          "macaws, all four of the country's monkeys, and the best chance "
          "anywhere of a jaguar track in the sand.",
    fact="*National Geographic* called the Osa 'the most biologically "
          "intense place on Earth' — around 2.5% of every species on the "
          "planet lives in an area smaller than most cities' commuter belt.",
    tip="Entry is by certified guide only and the Sirena ranger station "
        "books out months ahead. The day trip by boat from Drake Bay is the "
        "realistic version and still puts you deep in the park."),
"drake-bay": dict(
    name="Drake Bay", slug="Bahía_Drake", country="Costa Rica",
    region="Puntarenas Province", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    search_name="Drake Bay Costa Rica Osa Peninsula",
    highlights=[("Caño Island", "Caño_Island"),
                ("Corcovado National Park", "Corcovado_National_Park"),
                ("Agujitas", None),
                ("San Josecito Beach", None)],
    blurb="A bay on the north side of the Osa Peninsula reached by a boat "
          "ride up a river and out through the surf, with a footpath instead "
          "of a coast road and Corcovado starting a few kilometres south. "
          "Humpbacks calve offshore in two separate seasons.",
    fact="Francis Drake is supposed to have careened the *Golden Hind* here "
          "in 1579, which is where the name comes from. Treasure hunters "
          "have been digging the headland ever since on the strength of it.",
    tip="Caño Island, 20 km offshore, has the clearest water in the country "
        "and mysterious pre-Columbian stone spheres in its forest. Snorkel "
        "trips run most mornings from the beach."),
"puerto-viejo-talamanca": dict(
    name="Puerto Viejo de Talamanca", slug="Puerto_Viejo_de_Talamanca",
    country="Costa Rica",
    region="Limón Province", type="coastal", tag="hidden",
    emoji="🎶", sounds=["ocean-waves.mp3"],
    search_name="Puerto Viejo de Talamanca Costa Rica",
    highlights=[("Playa Cocles", None),
                ("Punta Uva", None),
                ("Manzanillo", None),
                ("Jaguar Rescue Center", None),
                ("Salsa Brava", None)],
    blurb="The Caribbean-side beach town, Afro-Caribbean and Bribri rather "
          "than Spanish in feel, with reggae on the beach road, coconut rice "
          "and beans, and a series of yellow-sand bays running south towards "
          "the Panamanian border.",
    fact="Salsa Brava, the reef break right in front of town, is the heaviest "
          "wave in Costa Rica — it breaks in shallow water directly over "
          "coral and locals treat it with real respect.",
    tip="Hire a bike and ride the flat coast road south: Cocles, Chiquita, "
        "Punta Uva, then Manzanillo at the end where the reserve starts. It "
        "is 13 km, entirely shaded, and the best afternoon on this coast."),
"cahuita": dict(
    name="Cahuita", slug="Cahuita", country="Costa Rica",
    region="Limón Province", type="coastal", tag="hidden",
    emoji="🦥", sounds=["ocean-waves.mp3"],
    highlights=[("Cahuita National Park", "Cahuita_National_Park"),
                ("Punta Cahuita", None),
                ("Playa Negra", None),
                ("Coral reef", None)],
    blurb="A slower, smaller village up the coast from Puerto Viejo, with a "
          "national park that starts at the end of the main street — a flat "
          "coastal trail running for 7 km behind white sand, through forest "
          "full of sloths, howlers and capuchins.",
    fact="Entry to the park's Kelly Creek gate is by voluntary donation, one "
          "of the very few national parks in Costa Rica without a fixed fee. "
          "The village fought for that arrangement in the 1990s and keeps "
          "it.",
    tip="Walk the trail out to Punta Cahuita and swim back at the coral. "
        "Take water — there is nothing on the trail — and go early for the "
        "wildlife and the shade."),
"la-fortuna": dict(
    name="La Fortuna", slug="La_Fortuna,_San_Carlos", country="Costa Rica",
    region="Alajuela Province", type="city", tag="famous",
    emoji="♨️", sounds=["waterfall.mp3"],
    search_name="La Fortuna Costa Rica Arenal",
    highlights=[("La Fortuna Waterfall", None),
                ("Arenal Volcano", "Arenal_Volcano"),
                ("Tabacón hot springs", None),
                ("Lake Arenal", "Lake_Arenal"),
                ("Mistico Hanging Bridges", None)],
    blurb="The town at the foot of Arenal, and the country's adventure hub: "
          "hot springs heated by the volcano, a 70 m waterfall in a jungle "
          "gorge below the plaza, hanging bridges through the canopy, and "
          "the cone itself filling the sky north of town on clear "
          "mornings.",
    fact="The town was called El Borio until Arenal's catastrophic 1968 "
          "eruption destroyed villages on the other side of the mountain but "
          "spared this one. It renamed itself La Fortuna — the fortunate "
          "one.",
    tip="The commercial hot springs are expensive. The free alternative is "
        "the Río Chollín, a hot river under the bridge by the Tabacón "
        "entrance, where locals sit in the current for nothing."),
"rio-celeste": dict(
    name="Río Celeste", slug="Tenorio_Volcano_National_Park", country="Costa Rica",
    region="Guanacaste Province", type="nature", tag="hidden",
    emoji="🩵", sounds=["waterfall.mp3"],
    search_name="Rio Celeste Tenorio Costa Rica",
    highlights=[("Los Teñideros", None),
                ("Laguna Azul", None),
                ("Borbollones", None)],
    blurb="A river in Tenorio Volcano National Park that is a startling "
          "opaque sky blue, with a waterfall dropping into a pool of it. A "
          "6 km round trip on a muddy trail takes you to the falls, the blue "
          "lagoon, and the exact point where two clear streams meet and turn "
          "colour.",
    fact="The colour is not a dye or a mineral in solution — it is optics. "
          "Aluminosilicate particles from the volcano grow to a precise size "
          "where they scatter blue light, and it happens within a metre of "
          "the confluence at Los Teñideros.",
    tip="Rain upstream turns the river brown and it stays that way for a "
        "day or two. Check recent photos before driving out, go in the dry "
        "season if you can, and take boots — the trail is deep mud."),
"rincon-de-la-vieja": dict(
    name="Rincón de la Vieja", slug="Rincón_de_la_Vieja_Volcano",
    country="Costa Rica",
    region="Guanacaste Province", type="mountain", tag="hidden",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    highlights=[("Las Pailas", None),
                ("La Cangreja waterfall", None),
                ("Mud pots", None),
                ("Santa María sector", None)],
    blurb="An active volcano in the dry north-west whose lower slopes are a "
          "field of boiling mud pots, steam vents and sulphur springs, "
          "linked by a loop trail through dry tropical forest. The summit is "
          "usually closed for gas; the geothermal circuit is the reason to "
          "come.",
    fact="The mud pots plop and belch continuously and the ground around "
          "them is genuinely thin — the boardwalks are not a formality. "
          "Ground temperatures a few centimetres down exceed 100 °C.",
    tip="Walk the Las Pailas loop in the morning, then continue to La "
        "Cangreja — a waterfall falling into a blue pool 5 km further in, "
        "with almost nobody at it because most people turn back at the mud."),
"poas-volcano": dict(
    name="Poás Volcano", slug="Poás_Volcano", country="Costa Rica",
    region="Alajuela Province", type="mountain", tag="famous",
    emoji="🌫️", sounds=["mountain-wind.mp3"],
    highlights=[("Crater lake", None),
                ("Laguna Botos", None),
                ("La Paz Waterfall Gardens", None),
                ("Cloud forest trail", None)],
    blurb="One of the largest active craters on Earth — 1.6 km across, with "
          "a pale green acid lake at the bottom — and a viewpoint you can "
          "walk to from the car park in ten minutes. Cloud forest, "
          "hummingbirds, and an hour from San José.",
    fact="The crater lake is among the most acidic bodies of water on the "
          "planet, at times below pH 0. Its 2017 eruption threw the "
          "monitoring equipment away and closed the park for over a year.",
    tip="Be there for the opening slot — the crater is clear early and "
        "socked in by cloud from about ten. Visits are timed, capped and "
        "must be booked online; there is no turning up on spec."),
"irazu-volcano": dict(
    name="Irazú Volcano", slug="Irazú_Volcano", country="Costa Rica",
    region="Cartago Province", type="mountain", tag="hidden",
    emoji="🌑", sounds=["mountain-wind.mp3"],
    highlights=[("Diego de la Haya crater", None),
                ("Principal crater", None),
                ("Cartago", "Cartago,_Costa_Rica"),
                ("Prusia forest", None)],
    blurb="At 3,432 m the highest volcano in Costa Rica, with a road right "
          "to the summit and a grey ash moonscape at the top. On the rare "
          "genuinely clear morning you can see both the Pacific and the "
          "Caribbean from the rim at once.",
    fact="Irazú began erupting on the day President Kennedy arrived in Costa "
          "Rica in March 1963 and kept going for two years, burying San José "
          "in ash. The fallout is also why the Central Valley's soil is so "
          "extraordinarily fertile.",
    tip="Go at dawn, in the dry season, and accept that the two-ocean view "
        "is a lottery. Bring a warm layer — it can be near freezing at the "
        "crater while Cartago below is in shirtsleeves."),
"chirripo": dict(
    name="Cerro Chirripó", slug="Cerro_Chirripó", country="Costa Rica",
    region="San José Province", type="mountain", tag="hidden",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Crestones", None),
                ("Valle de los Conejos", None),
                ("San Gerardo de Rivas", None),
                ("Base Crestones refuge", None)],
    blurb="The highest mountain in Costa Rica at 3,821 m, and unlike "
          "anything else in the country at the top: glacial lakes, bare rock "
          "spires and páramo scrub above the tree line, reached by a 14 km "
          "climb from the village of San Gerardo de Rivas.",
    fact="From the summit on a clear dawn you can see the Pacific and the "
          "Caribbean simultaneously — a genuine ocean-to-ocean view, and the "
          "reason people leave the refuge at three in the morning.",
    tip="Permits are limited, released online months in advance, and you "
        "must sleep at the Crestones refuge — no day ascents are allowed. "
        "It is a long, steep, cold walk and altitude is a real factor."),
"uvita": dict(
    name="Uvita", slug="Uvita_(Costa_Rica)", country="Costa Rica",
    region="Puntarenas Province", type="coastal", tag="hidden",
    emoji="🐳", sounds=["ocean-waves.mp3"],
    search_name="Uvita Costa Rica whale tail",
    highlights=[("Marino Ballena National Park",
                 "Marino_Ballena_National_Park"),
                ("Whale's Tail", None),
                ("Nauyaca Waterfalls", None),
                ("Playa Ventanas", None)],
    blurb="A small town on the Costa Ballena where a sandbar runs out into "
          "the sea in the exact shape of a whale's tail, uncovered at low "
          "tide so you can walk out along it. Humpbacks from both "
          "hemispheres pass offshore.",
    fact="Marino Ballena is one of the very few places on Earth visited by "
          "humpbacks from both the northern and southern populations, in two "
          "separate seasons — which gives it roughly eight months of whale "
          "watching a year.",
    tip="Check the tide table and walk out onto the tail an hour before low "
        "water. Nauyaca, inland, is two waterfalls with a deep swimming pool "
        "and a 4 km walk in — go in the afternoon after the tide."),
"tamarindo": dict(
    name="Tamarindo", slug="Tamarindo,_Costa_Rica", country="Costa Rica",
    region="Guanacaste Province", type="coastal", tag="hidden",
    emoji="🏄‍♀️", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Grande", None),
                ("Las Baulas National Marine Park", None),
                ("Playa Langosta", None),
                ("Estuary mangroves", None)],
    blurb="Guanacaste's busiest beach town — a long, forgiving beach break "
          "that has taught thousands of people to surf, a strip of "
          "restaurants behind it, and a mangrove estuary at the north end "
          "full of crocodiles and roseate spoonbills.",
    fact="Playa Grande, across the estuary, is a protected leatherback "
          "nesting beach. Leatherbacks reach 2 m and 700 kg, and the females "
          "that come ashore here have crossed the Pacific to do it.",
    tip="The estuary boat trip at dusk costs little and is far better than "
        "the town. Do not swim across the mouth — the crocodiles are real "
        "and there is a boatman for exactly that reason."),
"nosara": dict(
    name="Nosara", slug="Nosara", country="Costa Rica",
    region="Guanacaste Province", type="coastal", tag="hidden",
    emoji="🧘", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Guiones", None),
                ("Ostional Wildlife Refuge",
                 "Ostional_Wildlife_Refuge"),
                ("Playa Pelada", None),
                ("Nosara River", None)],
    blurb="A scattered settlement on the Nicoya Peninsula behind a 7 km "
          "beach, where a 1970s conservation covenant means the jungle comes "
          "right down to the sand with no buildings visible from the water. "
          "Surf and yoga in roughly equal measure.",
    fact="Ostional, just north, gets *arribadas* of olive ridley turtles — "
          "up to half a million animals coming ashore across a few nights. "
          "It is also the only beach in the world where the community is "
          "legally allowed to harvest a share of the first eggs.",
    tip="The roads in are unpaved, potholed and genuinely hard work in the "
        "wet season; a 4x4 is not optional. Once there, everything is "
        "walkable or a golf cart ride."),
"santa-teresa": dict(
    name="Santa Teresa", slug="Santa_Teresa,_Costa_Rica",
    country="Costa Rica",
    region="Puntarenas Province", type="coastal", tag="hidden",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    search_name="Santa Teresa Costa Rica beach Nicoya",
    highlights=[("Playa Carmen", None),
                ("Mal País", None),
                ("Cabo Blanco Reserve", "Cabo_Blanco_Nature_Reserve"),
                ("Playa Hermosa", None)],
    blurb="A single dirt road running behind kilometres of Pacific beach at "
          "the tip of the Nicoya Peninsula — surf all the way along it, "
          "sunsets straight out to sea, and howler monkeys in the trees over "
          "the road at six every morning.",
    fact="Cabo Blanco, at the end of the peninsula, was Costa Rica's first "
          "protected area, created in 1963 by a Swedish-Danish couple who "
          "bought up cut-over land and let the forest return. The entire "
          "national park system grew out of it.",
    tip="Getting here means the Puntarenas ferry and then an hour of rough "
        "road, which is exactly why it stays as it is. Go at low tide for "
        "the tide pools at the Playa Carmen end."),
"montezuma": dict(
    name="Montezuma", slug="Montezuma,_Costa_Rica", country="Costa Rica",
    region="Puntarenas Province", type="coastal", tag="hidden",
    emoji="💦", sounds=["waterfall.mp3"],
    search_name="Montezuma Costa Rica beach waterfall",
    highlights=[("Montezuma Waterfall", None),
                ("Cabo Blanco Reserve", "Cabo_Blanco_Nature_Reserve"),
                ("Isla Tortuga", None),
                ("Playa Grande", None)],
    blurb="A tiny bohemian village on the south-east corner of the Nicoya "
          "Peninsula, wedged between forested hills and rocky beaches, with "
          "a three-tier waterfall a short scramble up the river behind it.",
    fact="The village has been a counterculture hangout since the 1980s and "
          "locals have long called it Montefuma. It is also almost entirely "
          "solar-lit along the beach road.",
    tip="Walk the coast path north to Playa Grande for an empty beach and a "
        "second waterfall that falls directly onto the sand. The river "
        "scramble to the main falls is slippery — the upper pools have "
        "killed people who jumped."),
"orosi-valley": dict(
    name="Orosi Valley", slug="Orosi,_Cartago", country="Costa Rica",
    region="Cartago Province", type="nature", tag="hidden",
    emoji="☕", sounds=["wilderness.mp3"],
    search_name="Orosi Valley Costa Rica",
    highlights=[("Iglesia de San José de Orosi", None),
                ("Ujarrás ruins", None),
                ("Lake Cachí", None),
                ("Tapantí National Park", None)],
    blurb="A green bowl of coffee terraces south-east of Cartago, with the "
          "oldest church still in use in Costa Rica at its centre, ruins of "
          "an older one across the valley, hot springs, and a rainforest "
          "national park at the head of the river.",
    fact="The Orosi church was built by Franciscans in 1743 and has survived "
          "every earthquake since — including the ones that flattened "
          "Cartago twice. Its adobe walls are over a metre thick.",
    tip="Drive the valley loop road anticlockwise: church, then the Cachí "
        "dam, then the Ujarrás ruins, with a stop at the Mirador Orosi. It "
        "is a half day from San José and almost nobody does it."),
# =========================== PANAMA ==========================
# Panama City competes with Panama City, Florida; David competes with the
# given name; Colón with the Spanish for Columbus. All carry a search_name.
"panama-city": dict(
    name="Panama City", slug="Panama_City", country="Panama",
    region="Panamá Province", type="city", tag="famous",
    emoji="🏙️", sounds=["city-hum.mp3"],
    search_name="Panama City Panama skyline",
    highlights=[("Casco Viejo", "Casco_Viejo,_Panama"),
                ("Panamá Viejo", "Panamá_Viejo"),
                ("Cinta Costera", None),
                ("Biomuseo", "Biomuseo"),
                ("Amador Causeway", None)],
    blurb="A wall of glass towers along a Pacific bay, with a ruined "
          "16th-century city at one end and a restored 18th-century one at "
          "the other, and the entrance to the canal a few kilometres west. "
          "The most vertical skyline in Latin America, built on shipping and "
          "banking.",
    fact="It is the only capital city in the world with a genuine tropical "
          "rainforest inside its limits — Parque Natural Metropolitano, "
          "where sloths and toucans live within sight of the financial "
          "district.",
    tip="Because of the way the isthmus bends, the Pacific entrance of the "
        "canal is *east* of the Caribbean one. Stand on the Amador Causeway "
        "at sunset and you are watching the sun go down over the Pacific "
        "while facing roughly south."),
"casco-viejo": dict(
    name="Casco Viejo", slug="Casco_Viejo,_Panama", country="Panama",
    region="Panamá Province", type="history", tag="famous",
    emoji="🏛️", sounds=["plaza.mp3"],
    search_name="Casco Viejo Panama City old town",
    highlights=[("Plaza de la Independencia", None),
                ("Iglesia de San José", None),
                ("Teatro Nacional", None),
                ("Paseo Esteban Huertas", None),
                ("Plaza Francia", None)],
    blurb="The old walled city, built in 1673 after pirates burned the "
          "original, and now a UNESCO quarter of Spanish, French and "
          "Caribbean facades on a peninsula with the modern skyline "
          "shimmering across the bay behind it.",
    fact="The golden altar in the church of San José survived Henry Morgan's "
          "sack of the old city in 1671 because, the story goes, the priests "
          "painted it black and told the pirates it had already been "
          "stolen.",
    tip="Walk the Paseo Esteban Huertas along the sea wall at dusk — "
        "bougainvillea overhead, the towers lighting up opposite, and rooftop "
        "bars directly above you for afterwards."),
"panama-canal": dict(
    name="Panama Canal", slug="Panama_Canal", country="Panama",
    region="Panamá Province", type="landmark", tag="famous",
    emoji="🚢", sounds=["city-hum.mp3"],
    highlights=[("Miraflores Locks", "Miraflores_locks"),
                ("Gatún Lake", "Gatun_Lake"),
                ("Culebra Cut", "Culebra_Cut"),
                ("Agua Clara Locks", None),
                ("Pedro Miguel Locks", None)],
    blurb="Eighty kilometres of engineering that cut the isthmus in two and "
          "moved world trade: ships lifted 26 m into an artificial lake, "
          "sailed across the continental divide, and dropped back to the "
          "other ocean. Around 14,000 transits a year, still on the original "
          "1914 alignment.",
    fact="The French tried first and lost some 22,000 workers, mostly to "
          "yellow fever and malaria, before abandoning it. The Americans "
          "only succeeded after proving mosquitoes carried both diseases — "
          "the canal is as much a medical achievement as an engineering "
          "one.",
    tip="Miraflores has the visitor centre, but check the transit schedule "
        "before going: ships come through in windows, and between them you "
        "are looking at empty concrete. Agua Clara on the Caribbean side "
        "shows the vast new locks and is far less crowded."),
"bocas-del-toro": dict(
    name="Bocas del Toro", slug="Bocas_Town,_Bocas_del_Toro", country="Panama",
    region="Bocas del Toro Province", type="island", tag="famous",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Isla Colón", "Isla_Colón"),
                ("Red Frog Beach", None),
                ("Cayo Zapatilla", None),
                ("Isla Bastimentos", "Isla_Bastimentos"),
                ("Dolphin Bay", None)],
    blurb="An archipelago in the Caribbean near the Costa Rican border, with "
          "a Creole-speaking main town of wooden houses on stilts, water "
          "taxis instead of roads between islands, and a marine national "
          "park of mangrove and coral around it.",
    fact="Bastimentos is home to the strawberry poison-dart frog, which on "
          "these islands has split into different colour morphs — bright "
          "red, orange, green, blue — island by island, over only a few "
          "thousand years.",
    tip="Bocas Town is loud and the swimming near it is poor. Take a water "
        "taxi out on your first morning — to Bastimentos, Carenero or Isla "
        "Solarte — and stay there instead."),
"boquete": dict(
    name="Boquete", slug="Boquete,_Chiriquí", country="Panama",
    region="Chiriquí Province", type="nature", tag="hidden",
    emoji="☕", sounds=["wilderness.mp3"],
    search_name="Boquete Chiriqui Panama",
    highlights=[("Volcán Barú", "Volcán_Barú"),
                ("Sendero Los Quetzales", None),
                ("Caldera hot springs", None),
                ("Coffee farms", None),
                ("Pipeline Trail", None)],
    blurb="A mountain town at 1,200 m in a green valley below Panama's "
          "highest volcano, permanently cool, and famous for two things: "
          "cloud-forest trails full of quetzals, and coffee that sells for "
          "more per pound than any other on Earth.",
    fact="Geisha coffee, grown on these slopes, has repeatedly broken world "
          "auction records — single lots have gone for over $6,000 a pound "
          "green. The variety came from Ethiopia and only became "
          "extraordinary in this particular soil and altitude.",
    tip="The Pipeline Trail is a flat, easy hour into cloud forest with a "
        "waterfall at the end and a genuine chance of a resplendent quetzal "
        "between January and May. Farms will let you cup Geisha for a "
        "fraction of what a bag costs."),
"volcan-baru": dict(
    name="Volcán Barú", slug="Volcán_Barú", country="Panama",
    region="Chiriquí Province", type="mountain", tag="hidden",
    emoji="🌄", sounds=["mountain-wind.mp3"],
    highlights=[("Boquete", "Boquete,_Chiriquí"),
                ("Sendero Los Quetzales", None),
                ("Volcán", None),
                ("Summit crater", None)],
    blurb="Panama's highest point at 3,474 m, and one of the very few places "
          "on Earth where you can see the Atlantic and Pacific oceans from "
          "the same spot. The reward for a night walk up a brutal rock "
          "track, timed to reach the summit at dawn.",
    fact="The two-ocean view needs a genuinely clear pre-dawn sky and comes "
          "off perhaps a third of the time. When it does, you watch the sun "
          "rise out of the Caribbean while the Pacific is still dark behind "
          "you.",
    tip="Either walk from Boquete overnight — six hours, 1,600 m of "
        "ascent, freezing at the top — or take a 4x4 that leaves at "
        "midnight. Either way, bring a proper jacket; people arrive in "
        "shorts and regret it."),
"guna-yala": dict(
    name="Guna Yala", slug="Guna_Yala", country="Panama",
    region="Guna Yala", type="island", tag="hidden",
    emoji="🐚", sounds=["ocean-waves.mp3"],
    search_name="Guna Yala San Blas islands Panama",
    highlights=[("San Blas Islands", None),
                ("Cayos Holandeses", None),
                ("El Porvenir", None),
                ("Isla Perro", None)],
    blurb="An autonomous Guna territory of some 365 Caribbean islands along "
          "Panama's north-east coast, most of them a sandbar with a few "
          "palms, a handful inhabited. The Guna run it themselves — their "
          "own government, their own rules on who may visit and how.",
    fact="The Guna won that autonomy in an armed revolution in 1925 and it "
          "is one of the oldest indigenous self-governments in the Americas. "
          "Foreign-owned hotels are not permitted anywhere in the "
          "territory.",
    tip="Accommodation is basic cabins on sand run by Guna families, and "
        "that is the only legal option. Buy a *mola* — the reverse-appliqué "
        "panels the women sew — directly from the maker, not in Panama "
        "City."),
"portobelo": dict(
    name="Portobelo", slug="Portobelo,_Colón", country="Panama",
    region="Colón Province", type="history", tag="hidden",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    search_name="Portobelo Panama fort Colon",
    highlights=[("Fuerte San Jerónimo", None),
                ("Iglesia de San Felipe", None),
                ("Fuerte Santiago", None),
                ("Fort San Lorenzo", "Fort_San_Lorenzo")],
    blurb="A Caribbean bay ringed by Spanish forts, through which most of "
          "the silver of Peru passed on its way to Spain. Cannon still point "
          "out to sea from ruins that the jungle is slowly taking back, and "
          "the village that remains is Congo — Afro-Panamanian, and famous "
          "for its drumming.",
    fact="Francis Drake died of dysentery off this bay in 1596 and was "
          "buried at sea in a lead coffin. Divers have been looking for it "
          "ever since; two lead objects found nearby in 2011 may be from his "
          "fleet, but the coffin has never been located.",
    tip="The Black Christ in the village church draws tens of thousands of "
        "pilgrims every 21 October, some crawling the last kilometres. On "
        "any other day the church is empty and the statue is right there."),
"coiba": dict(
    name="Coiba", slug="Coiba", country="Panama",
    region="Veraguas Province", type="island", tag="hidden",
    emoji="🦈", sounds=["ocean-waves.mp3"],
    search_name="Coiba National Park Panama island",
    highlights=[("Granito de Oro", None),
                ("Coiba National Park", None),
                ("Bahía Damas reef", None),
                ("Santa Catalina", None)],
    blurb="The largest island in Central America, a penal colony from 1919 "
          "to 2004 — which is precisely why 80% of it is still untouched "
          "primary rainforest. Now a national park and a UNESCO site, with "
          "the second largest coral reef in the eastern Pacific.",
    fact="The prison's reputation kept everyone away for eighty-five years, "
          "and the island preserved species that vanished on the mainland — "
          "including a subspecies of howler monkey and the last wild "
          "scarlet macaws in the country.",
    tip="Diving here means hammerheads, whitetips and manta rays in "
        "big-water conditions, not gentle reef pottering. Trips run from "
        "Santa Catalina; the crossing takes about 90 minutes and can be "
        "rough."),
"el-valle-de-anton": dict(
    name="El Valle de Antón", slug="El_Valle_de_Antón", country="Panama",
    region="Coclé Province", type="nature", tag="hidden",
    emoji="🐸", sounds=["wilderness.mp3"],
    highlights=[("India Dormida", None),
                ("Chorro El Macho", None),
                ("Pozos Termales", None),
                ("Sunday market", None),
                ("Cerro Gaital", None)],
    blurb="A town sitting inside the flat floor of an extinct volcanic "
          "crater, six kilometres across, two hours from Panama City and "
          "several degrees cooler. Waterfalls off the crater walls, hot "
          "springs, orchids, and a market under the trees.",
    fact="It is one of only a handful of inhabited volcanic craters in the "
          "world. It is also the home of the golden frog, Panama's national "
          "animal, now extinct in the wild and surviving only in a "
          "conservation centre in the town.",
    tip="Walk the India Dormida ridge — named for its resemblance to a "
        "sleeping woman — for the whole crater laid out below. Two hours up "
        "and back, best before the afternoon cloud."),
"pedasi": dict(
    name="Pedasí", slug="Pedasí,_Los_Santos", country="Panama",
    region="Los Santos Province", type="coastal", tag="hidden",
    emoji="🐢", sounds=["ocean-waves.mp3"],
    search_name="Pedasi Los Santos Panama",
    highlights=[("Isla Iguana", "Isla_Iguana_Wildlife_Refuge"),
                ("Playa Venao", None),
                ("Isla Cañas", None),
                ("Playa El Toro", None)],
    blurb="A quiet, tidy town of low painted houses at the tip of the Azuero "
          "Peninsula, with beaches on three sides, an offshore island "
          "reserve, and one of Panama's most reliable surf beaches twenty "
          "minutes away.",
    fact="Isla Cañas, south of town, gets olive ridley *arribadas* between "
          "September and November — tens of thousands of turtles on a single "
          "beach. The island community guides the visits itself.",
    tip="Isla Iguana is a 20-minute boat ride to white sand, live coral and "
        "a colony of several thousand magnificent frigatebirds. Go on a "
        "calm morning; the channel gets choppy by noon."),
"david-panama": dict(
    name="David", slug="David,_Chiriquí", country="Panama",
    region="Chiriquí Province", type="city", tag="hidden",
    emoji="🌵", sounds=["city-hum.mp3"],
    search_name="David Chiriqui Panama city",
    highlights=[("Parque Cervantes", None),
                ("Catedral de San José de David", None),
                ("Boquete", "Boquete,_Chiriquí"),
                ("Playa Las Lajas", None)],
    blurb="Panama's third city and the capital of Chiriquí, on the hot "
          "lowland plain below Barú. It is a working agricultural town "
          "rather than a sight in itself, and the transport hub for "
          "everything in the western highlands.",
    fact="David is one of the oldest continuously inhabited European "
          "settlements in Panama, founded in 1602, and its March feria is "
          "the biggest agricultural fair in the country.",
    tip="Nobody comes here for David. Come for the fact that Boquete, "
        "Volcán, Las Lajas beach and the Costa Rican border are each under "
        "an hour and a half away, and the buses run constantly."),
"darien": dict(
    name="Darién", slug="Darién_National_Park", country="Panama",
    region="Darién Province", type="wilderness", tag="hidden",
    emoji="🌳", sounds=["wilderness.mp3"],
    search_name="Darien National Park Panama rainforest",
    highlights=[("Cana", None),
                ("Cerro Pirre", None),
                ("Río Balsas", None),
                ("Punta Patiño", None)],
    blurb="579,000 hectares of rainforest, swamp and cloud-forest ridge on "
          "the Colombian border — the largest national park in Central "
          "America, a UNESCO site, and the reason the Pan-American Highway "
          "stops dead here and starts again 100 km later.",
    fact="The Darién Gap is the only break in a road system running from "
          "Alaska to Patagonia. Its harpy eagles, four macaw species and "
          "Emberá and Wounaan communities are the reason it is protected — "
          "though much of the region is not safely visitable.",
    tip="Do not attempt the Gap. What is visitable is the western edge: "
        "Punta Patiño reserve on the Gulf of San Miguel, and Emberá village "
        "stays up the Río Sambú, both arranged through operators in Panama "
        "City."),
"isla-taboga": dict(
    name="Isla Taboga", slug="Taboga_Island", country="Panama",
    region="Panamá Province", type="island", tag="hidden",
    emoji="🌺", sounds=["ocean-waves.mp3"],
    search_name="Taboga Island Panama",
    highlights=[("Playa Honda", None),
                ("Iglesia San Pedro", None),
                ("Cerro Vigía", None),
                ("El Morro", None)],
    blurb="The Island of Flowers, half an hour by ferry from Panama City — "
          "a hillside of bougainvillea and narrow lanes with no room for "
          "cars, a church claimed as one of the oldest in the hemisphere, "
          "and a beach the capital comes to on Sundays.",
    fact="Paul Gauguin worked on the canal here in 1887 to fund his "
          "painting, and lived on the island while recovering from fever. "
          "Pizarro is also said to have gathered his ships here before "
          "sailing for Peru.",
    tip="Go on a weekday and the island is nearly empty. Climb Cerro Vigía "
        "for the view back to the skyline across the bay with ships queuing "
        "for the canal in between."),
}

# ---------------------------------------------------------------------------
# FILL — the twelve records that were already here. All of them are complete;
# what they lack is a search_name, and four of them have namesakes loud enough
# to hijack a YouTube query outright.
# ---------------------------------------------------------------------------
FILL = {
    "san-jose": dict(search_name="San José Costa Rica city"),
    "caracol": dict(search_name="Caracol Maya ruins Belize"),
    "monteverde": dict(search_name="Monteverde cloud forest Costa Rica"),
    "manuel-antonio": dict(search_name="Manuel Antonio National Park Costa Rica"),
    "ambergris-caye": dict(search_name="Ambergris Caye San Pedro Belize"),
    "belize-city": dict(search_name="Belize City Belize"),
    "arenal-volcano": dict(search_name="Arenal Volcano Costa Rica"),
    "cancun": dict(search_name="Cancun Quintana Roo Mexico"),
    "mexico-city": dict(search_name="Mexico City CDMX"),
}


if __name__ == "__main__":
    rb.run(REGION, NEW, FILL)
