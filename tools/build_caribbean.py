#!/usr/bin/env python3
"""
build_caribbean.py — the Caribbean batch, and a new region file (2026-08).

WHAT WAS WRONG
    The atlas had **three Caribbean places**: Havana, Trinidad and Varadero,
    all Cuban, all filed under "Latin America". Jamaica, Puerto Rico, the
    Bahamas, Barbados, the Virgin Islands, the whole Lesser Antilles chain —
    nothing. Twenty-eight countries and territories, forty-four million
    people, and the region the rest of the world pictures when it hears the
    word *island*.

WHY A NEW REGION FILE
    Not filing them under Latin America is a factual point, not a tidiness
    one. `region_name` is user-visible: it is printed on the place card and
    used in the region filter. "Latin America" is simply wrong for Barbados,
    Aruba, Sint Maarten and the British Virgin Islands — English-, Dutch- and
    Papiamento-speaking places with no Iberian colonial history at all.

    So `data/caribbean.json` is a new region (id `caribbean`, 🏝️), registered
    in `data/index.json`, and Cuba's three existing records moved into it
    before this generator ran. `js/lib/data.js` loads every enabled region in
    parallel and flattens them, so adding a file is purely additive — no page
    special-cases a region id except `ancient`, `wild` and `observatory`.

WHERE THE LINE IS DRAWN
    In: the Greater Antilles, the Lesser Antilles from the Virgin Islands to
    Trinidad, the Lucayan archipelago (Bahamas, Turks & Caicos) and the ABC
    islands off Venezuela.

    Out: **Bermuda**, which sits at 32°N in the middle of the North Atlantic,
    a thousand kilometres from the nearest Caribbean island, and is not in the
    Caribbean by any definition but the travel-brochure one. The bounding box
    below refuses it on coordinates alone.

    Also out: the Caribbean coasts of the mainland. Belize's cayes, Guatemala's
    Lívingston, Panama's Guna Yala and Nicaragua's Corn Islands are all in
    `latinamerica.json` with the countries they belong to — see
    `build_middleamerica.py`, which ran in the same round.

THE NAMESAKE PROBLEM
    Different in shape from Mexico's, and in some ways worse, because the
    colliding names are *capital cities*:

    · **Kingston** is Jamaica's capital and also a city in Ontario that this
      atlas already contains, plus Kingston upon Thames and Kingston, NY.
    · **Trinidad** is a Cuban town in this file AND an island country in this
      file. Different records, one word.
    · **Soufrière** names a town in Saint Lucia, a volcano in Saint Vincent,
      a volcano in Guadeloupe and a volcano in Montserrat. Four places, one
      name, all in this batch.
    · **Basseterre** (St Kitts) and **Basse-Terre** (Guadeloupe) are two
      capitals one letter apart, 300 km from each other.
    · **Roseau** is Dominica's capital; **Dominica** and the **Dominican
      Republic** are different countries.
    · **San Juan** is Puerto Rico's capital and also a province of Argentina
      already in the atlas, and a city in the Philippines.
    · **Saint Martin** (French) and **Sint Maarten** (Dutch) share one island
      of 87 km², and both are in this file as separate countries, because
      they are.

    Every one of those carries a `search_name`, because no downstream guard
    can catch a namesake — `enrich_media.py` and `enrich_monuments.py` spend
    it as a YouTube query and there is nothing in the answer that says "wrong
    hemisphere".

TERRITORIES
    Sixteen of the twenty-eight entries here are not sovereign states, so
    their Wikidata P17 answers the United States, the United Kingdom, France
    or the Kingdom of the Netherlands rather than the name on the record.
    That is correct and expected, so every one of them is declared in
    `expect_p17` and reported as a quiet TERRITORY line instead of a COUNTRY
    warning — leaving the COUNTRY lines that survive worth actually reading.

    Country names are the join key `build_countries.py` matches on, so they
    are copied from `data/countries.json` where the country already exists
    and from the ISO 3166 short name where it does not.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regionbuild as rb


COUNTRY_CODE = {
    "Cuba": "CU", "Jamaica": "JM", "Haiti": "HT",
    "Dominican Republic": "DO", "Puerto Rico": "PR", "Bahamas": "BS",
    "Cayman Islands": "KY", "Turks and Caicos Islands": "TC",
    "Trinidad and Tobago": "TT", "Barbados": "BB", "Saint Lucia": "LC",
    "Grenada": "GD", "Saint Vincent and the Grenadines": "VC",
    "Antigua and Barbuda": "AG", "Dominica": "DM",
    "Saint Kitts and Nevis": "KN", "Aruba": "AW", "Curaçao": "CW",
    "Bonaire": "BQ", "British Virgin Islands": "VG",
    "United States Virgin Islands": "VI", "Martinique": "MQ",
    "Guadeloupe": "GP", "Saint Barthélemy": "BL", "Saint Martin": "MF",
    "Sint Maarten": "SX", "Anguilla": "AI", "Montserrat": "MS",
}

# Where the country's own article is not just the name with underscores.
COUNTRY_SLUG = {
    "Bahamas": "The_Bahamas",
    "Saint Martin": "Collectivity_of_Saint_Martin",
    "Bonaire": "Bonaire",
    "United States Virgin Islands": "United_States_Virgin_Islands",
}

# The sovereign each dependency's P17 legitimately answers.
EXPECT_P17 = {
    "Puerto Rico": "United_States",
    "United States Virgin Islands": "United_States",
    "British Virgin Islands": "United_Kingdom",
    "Cayman Islands": "United_Kingdom",
    "Turks and Caicos Islands": "United_Kingdom",
    "Anguilla": "United_Kingdom",
    "Montserrat": "United_Kingdom",
    "Aruba": "Kingdom_of_the_Netherlands",
    "Curaçao": "Kingdom_of_the_Netherlands",
    "Bonaire": "Netherlands",
    "Sint Maarten": "Kingdom_of_the_Netherlands",
    "Martinique": "France",
    "Guadeloupe": "France",
    "Saint Barthélemy": "France",
    "Saint Martin": "France",
}

# The hard net. North to the northern Bahamas, south to Trinidad, east to
# Barbados, west to Cuba's western cape — and deliberately short of Bermuda
# at 32.3°N, which is not a Caribbean island.
CB_LAT = (9.8, 27.6)
CB_LNG = (-85.6, -58.8)


def in_box(lat, lng):
    return CB_LAT[0] <= lat <= CB_LAT[1] and CB_LNG[0] <= lng <= CB_LNG[1]


REGION = rb.Region(
    target="caribbean.json",
    continent="North America",
    country_code=COUNTRY_CODE,
    country_slug=COUNTRY_SLUG,
    expect_p17=EXPECT_P17,
    in_box=in_box,
)

# Island states are small enough that a subregion box would be smaller than
# the coordinate error on some of these articles, so there is none here; the
# `region` string is the province, parish or island and is not checked.
NEW = {
# ============================ CUBA ===========================
# havana, trinidad and varadero came across from latinamerica.json and are
# handled in FILL; these are the rest of the island.
"vinales": dict(
    name="Viñales", slug="Viñales_Valley", country="Cuba",
    region="Pinar del Río", type="nature", tag="famous",
    emoji="🚜", sounds=["wilderness.mp3"],
    search_name="Vinales Valley Cuba",
    highlights=[("Mogotes", None),
                ("Cueva del Indio", None),
                ("Mural de la Prehistoria", None),
                ("Los Jazmines viewpoint", None),
                ("Tobacco drying barns", None)],
    blurb="A flat red valley in western Cuba out of which rise *mogotes* — "
          "round-shouldered limestone towers with vertical sides and forest "
          "on top. Between them the tobacco is still worked with oxen, and "
          "the leaf is the best in the world.",
    fact="The mogotes are what is left of a limestone plateau after 160 "
          "million years of water dissolved everything between them. Each "
          "one is a separate ecosystem, and several hold plants found on "
          "that mogote and nowhere else.",
    tip="Stay in a *casa particular* in the village and take a horse out at "
        "six in the morning. The valley fills with mist that the mogotes "
        "stand out of, and it is gone by nine."),
"santiago-de-cuba": dict(
    name="Santiago de Cuba", slug="Santiago_de_Cuba", country="Cuba",
    region="Santiago de Cuba", type="city", tag="famous",
    emoji="🥁", sounds=["plaza.mp3"],
    highlights=[("Castillo del Morro", None),
                ("Parque Céspedes", None),
                ("Cementerio Santa Ifigenia", None),
                ("Casa de la Trova", None),
                ("Cuartel Moncada", None)],
    blurb="Cuba's second city and its hottest, at the eastern end of the "
          "island in a bay ringed by the Sierra Maestra. It is the "
          "Caribbean-facing, Haitian-influenced, musically overwhelming half "
          "of Cuba — son, trova and conga were all born here.",
    fact="The 1953 attack on the Moncada barracks in this city was Fidel "
          "Castro's first move and it failed completely, but it gave the "
          "revolution its name — the 26th of July Movement. He is buried "
          "here too, under a plain granite boulder.",
    tip="Go up to the Morro castle at the harbour mouth for the sunset "
        "cannon, fired by soldiers in 18th-century uniform every evening. "
        "Then come back down for the Casa de la Trova, which does not really "
        "start until ten."),
"cienfuegos": dict(
    name="Cienfuegos", slug="Cienfuegos", country="Cuba",
    region="Cienfuegos", type="city", tag="hidden",
    emoji="🏛️", sounds=["plaza.mp3"],
    highlights=[("Parque José Martí", None),
                ("Palacio de Valle", None),
                ("Teatro Tomás Terry", None),
                ("Punta Gorda", None),
                ("Castillo de Jagua", None)],
    blurb="The one Cuban city founded by the French, in 1819, and it shows: "
          "a grid of neoclassical arcades around an enormous square, on a "
          "bay so sheltered it is nearly a lake. UNESCO calls it the best "
          "surviving example of early 19th-century Spanish-American urban "
          "planning.",
    fact="The Palacio de Valle out at Punta Gorda is a sugar baron's 1917 "
          "fantasy in Moorish, Venetian and Gothic all at once. He is said "
          "to have brought craftsmen from Morocco to finish it.",
    tip="Walk the length of the Paseo del Prado to Punta Gorda at dusk — "
        "Cuba's longest boulevard, ending in a spit of wooden houses in "
        "sherbet colours with water on three sides."),
"camaguey": dict(
    name="Camagüey", slug="Camagüey", country="Cuba",
    region="Camagüey", type="city", tag="hidden",
    emoji="🏺", sounds=["plaza.mp3"],
    highlights=[("Plaza San Juan de Dios", None),
                ("Plaza del Carmen", None),
                ("Catedral de Camagüey", None),
                ("Casino Campestre", None)],
    blurb="A colonial city built as a maze on purpose — the streets bend, "
          "fork and dead-end because the town was laid out in the 1520s to "
          "confuse pirates who got in from the coast. It worked well enough "
          "that the plan survives, UNESCO listed.",
    fact="Every corner has a *tinajón*, a giant clay water jar. The city has "
          "thousands of them, some from the 1700s, and the local saying is "
          "that if you drink from one you will never leave Camagüey.",
    tip="Do not try to navigate by grid — there isn't one. Aim for the "
        "plazas instead: San Juan de Dios is the loveliest and is almost "
        "unchanged since the 18th century."),
"santa-clara-cuba": dict(
    name="Santa Clara", slug="Santa_Clara,_Cuba", country="Cuba",
    region="Villa Clara", type="history", tag="hidden",
    emoji="⭐", sounds=["plaza.mp3"],
    search_name="Santa Clara Cuba Che Guevara",
    highlights=[("Che Guevara Mausoleum", None),
                ("Tren Blindado", None),
                ("Parque Vidal", None),
                ("Teatro La Caridad", None)],
    blurb="The university city in the middle of the island where the Cuban "
          "revolution was effectively won, in December 1958, when Che "
          "Guevara's column derailed an armoured train. Batista fled the "
          "country hours later.",
    fact="The derailed train is still there, four carriages left where they "
          "came off the rails, with the bulldozer that lifted the track "
          "beside them as a monument. Guevara's remains were brought here "
          "from Bolivia in 1997.",
    tip="This is also the most relaxed nightlife in provincial Cuba — Club "
        "Mejunje, in a roofless ruin, has run Cuba's oldest drag show since "
        "the 1990s and is a genuinely open place."),
"baracoa": dict(
    name="Baracoa", slug="Baracoa", country="Cuba",
    region="Guantánamo", type="coastal", tag="hidden",
    emoji="🍫", sounds=["ocean-waves.mp3"],
    highlights=[("El Yunque", None),
                ("Playa Maguana", None),
                ("Río Toa", None),
                ("Catedral de Nuestra Señora de la Asunción", None)],
    blurb="The oldest Spanish town in Cuba, founded 1511, wedged between "
          "mountains and sea at the far eastern tip of the island and cut "
          "off by land until a road was blasted over the pass in 1965. It "
          "cooks with coconut and cocoa and tastes like nowhere else in "
          "Cuba.",
    fact="Its cathedral holds the Cruz de la Parra, a wooden cross that "
          "carbon dating confirms was made from a local tree in the late "
          "1400s — the only surviving cross of the twenty-nine Columbus is "
          "said to have planted in the New World.",
    tip="Order *cucurucho* — cocoa, coconut and fruit in a palm-leaf cone — "
        "from the roadside sellers on La Farola, the mountain road in. It is "
        "made nowhere else."),
"remedios-cuba": dict(
    name="Remedios", slug="Remedios,_Cuba", country="Cuba",
    region="Villa Clara", type="history", tag="hidden",
    emoji="🎆", sounds=["plaza.mp3"],
    search_name="Remedios Villa Clara Cuba",
    highlights=[("Iglesia de San Juan Bautista", None),
                ("Plaza Isabel II", None),
                ("Museo de las Parrandas", None),
                ("Cayo Santa María", None)],
    blurb="One of Cuba's oldest towns, a single perfect square of arcaded "
          "houses and a church with a gilded mahogany altar, almost never "
          "visited — except at Christmas, when it detonates.",
    fact="The *parrandas* of Remedios, running since 1820, split the town "
          "into two neighbourhoods that compete all year in secret and then "
          "spend the night of 24 December trying to out-build and out-firework "
          "each other. It is one of the oldest festivals in Latin America.",
    tip="The church's ceiling and altar were hidden under plaster for a "
        "century and only rediscovered in the 1940s. Go in — there is no "
        "charge, and the gold work is extraordinary."),
"matanzas": dict(
    name="Matanzas", slug="Matanzas", country="Cuba",
    region="Matanzas", type="city", tag="hidden",
    emoji="🌉", sounds=["city-hum.mp3"],
    highlights=[("Teatro Sauto", None),
                ("Cuevas de Bellamar", None),
                ("Río Yumurí", None),
                ("Ediciones Vigía", None)],
    blurb="A port city of bridges over three rivers, half an hour from "
          "Varadero and completely unlike it. Nicknamed the Athens of Cuba "
          "for its 19th-century poets and printers, it is faded, working and "
          "the birthplace of both danzón and rumba.",
    fact="Ediciones Vigía still makes books entirely by hand — handmade "
          "paper, hand-set type, hand-painted covers, editions of two "
          "hundred. It has been doing it since 1985 and you can watch.",
    tip="The Bellamar caves on the edge of town are among the oldest tourist "
        "attractions in Cuba, open since 1861, and 3 km of crystal-lined "
        "galleries. Twenty minutes from the centre by taxi."),
"topes-de-collantes": dict(
    name="Topes de Collantes", slug="Topes_de_Collantes", country="Cuba",
    region="Sancti Spíritus", type="nature", tag="hidden",
    emoji="💦", sounds=["waterfall.mp3"],
    highlights=[("Salto del Caburní", None),
                ("Escambray Mountains", "Escambray_Mountains"),
                ("Vegas Grandes", None),
                ("Hacienda Codina", None)],
    blurb="A cloud-forest reserve in the Escambray mountains above Trinidad, "
          "700 m up and several degrees cooler, with waterfalls dropping into "
          "cold pools at the end of every trail and tree ferns overhead.",
    fact="The Escambray was the base of an anti-Castro insurgency through "
          "the 1960s, and the enormous sanatorium at the centre of the "
          "reserve was built by Batista as a tuberculosis hospital and never "
          "used as one.",
    tip="Caburní is the big one — 62 m, an hour steeply down and a harder "
        "hour back up. Vegas Grandes is shorter and almost as good, and "
        "hardly anyone takes it."),
"playa-giron": dict(
    name="Playa Girón", slug="Playa_Girón", country="Cuba",
    region="Matanzas", type="coastal", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    search_name="Playa Giron Bay of Pigs Cuba",
    highlights=[("Bay of Pigs", "Bay_of_Pigs"),
                ("Caleta Buena", None),
                ("Cueva de los Peces", None),
                ("Ciénaga de Zapata", None)],
    blurb="A village on the Bay of Pigs with a museum about the 1961 "
          "invasion, and — improbably — some of the best shore diving in the "
          "Caribbean, because the reef wall runs a few metres off the rocks "
          "along this whole coast.",
    fact="Roadside billboards along the bay still mark where each invader "
          "was stopped. The Cueva de los Peces, halfway to the village, is a "
          "70 m-deep flooded tectonic fault you can swim in, full of fish "
          "from both fresh and salt water.",
    tip="Caleta Buena, 8 km east, is a series of natural pools cut into the "
        "coral shelf with a bar and nothing else. Snorkel straight off the "
        "steps."),
"cayo-coco": dict(
    name="Cayo Coco", slug="Cayo_Coco", country="Cuba",
    region="Ciego de Ávila", type="island", tag="hidden",
    emoji="🦩", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Pilar", None),
                ("Cayo Guillermo", None),
                ("Laguna La Redonda", None),
                ("Jardines del Rey", None)],
    blurb="A long low key off Cuba's north coast, reached by a 17 km "
          "causeway across the shallows, with white sand on the ocean side "
          "and flamingos in the lagoons behind. Named for the white ibis, "
          "not the palm.",
    fact="Hemingway hunted German submarines in these waters from his "
          "fishing boat *Pilar* during the Second World War, and the beach "
          "at the end of neighbouring Cayo Guillermo is named after her. "
          "*Islands in the Stream* is set here.",
    tip="Playa Pilar, at the far tip of Cayo Guillermo, has the highest "
        "dunes in the Caribbean behind it and is a day trip from the Coco "
        "resorts. Go on a weekday and it is nearly empty."),
"cayo-largo": dict(
    name="Cayo Largo", slug="Cayo_Largo_del_Sur", country="Cuba",
    region="Isla de la Juventud", type="island", tag="hidden",
    emoji="🐢", sounds=["ocean-waves.mp3"],
    search_name="Cayo Largo del Sur Cuba",
    highlights=[("Playa Sirena", None),
                ("Playa Paraíso", None),
                ("Turtle farm", None),
                ("Cayo Rico", None)],
    blurb="A 25 km sandbar in the Canarreos archipelago south of Cuba, "
          "reached only by air, with no town and no Cuban village life — "
          "just white sand, iguanas and one of the calmest stretches of sea "
          "in the country.",
    fact="It is a major nesting site for green and loggerhead turtles, and "
          "the hatchery at the western end releases young turtles most "
          "evenings in season.",
    tip="Playa Sirena, on the sheltered western tip, is a boat ride from the "
        "hotels and is where the water is calmest and the sand finest. There "
        "is one beach bar and nothing else."),
"guardalavaca": dict(
    name="Guardalavaca", slug="Guardalavaca", country="Cuba",
    region="Holguín", type="coastal", tag="hidden",
    emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Esmeralda", None),
                ("Chorro de Maíta", None),
                ("Bahía de Naranjo", None),
                ("Banes", None)],
    blurb="A curve of beach on Cuba's north-east coast with a reef a hundred "
          "metres out and green hills behind — the corner of the island "
          "Columbus described in 1492 as the most beautiful land human eyes "
          "had ever seen.",
    fact="Chorro de Maíta, in the hills above the beach, is the largest "
          "excavated indigenous cemetery in the Caribbean: 108 Taíno burials "
          "left in place, under a roof, exactly as they were found.",
    tip="Skip the resort strip for a morning and take a taxi up to Chorro de "
        "Maíta and the reconstructed Taíno village beside it. It is the best "
        "pre-Columbian site in Cuba and almost nobody goes."),
"sierra-maestra": dict(
    name="Sierra Maestra", slug="Sierra_Maestra", country="Cuba",
    region="Granma", type="mountain", tag="hidden",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Pico Turquino", "Pico_Turquino"),
                ("Comandancia de la Plata", None),
                ("Santo Domingo", None),
                ("Marea del Portillo", None)],
    blurb="The mountain range along Cuba's south-eastern coast, holding the "
          "island's highest peak and its densest forest, and the range the "
          "revolution was fought from between 1956 and 1959.",
    fact="La Plata, Castro's headquarters, is still up there — a scatter of "
          "wooden huts under the canopy including the field hospital and the "
          "radio hut, reachable only on foot and deliberately invisible from "
          "the air.",
    tip="Both the La Plata walk and Pico Turquino are guide-only and start "
        "from Santo Domingo, up a road so steep that ordinary cars cannot "
        "make the last stretch. Arrange it the day before, in Bayamo."),
"las-terrazas": dict(
    name="Las Terrazas", slug="Las_Terrazas", country="Cuba",
    region="Artemisa", type="nature", tag="hidden",
    emoji="🌳", sounds=["wilderness.mp3"],
    highlights=[("Cafetal Buenavista", None),
                ("Río San Juan", None),
                ("Hotel Moka", None),
                ("Sierra del Rosario", None)],
    blurb="A village of 1,000 people in a reforested valley an hour west of "
          "Havana, built in 1971 as part of a project that terraced and "
          "replanted a hillside stripped bare by two centuries of coffee and "
          "charcoal. It is now a UNESCO biosphere reserve.",
    fact="The hotel at the centre has a tree growing up through the middle "
          "of it — the building was designed around a mature specimen rather "
          "than felling it, and it comes out through the roof.",
    tip="The ruined French coffee plantation at Buenavista, up the hill, has "
        "the drying platforms and slave quarters intact and a view over the "
        "whole reserve. Walk up rather than drive; it is 3 km."),
# =========================== JAMAICA =========================
# Kingston collides with Kingston, Ontario — already in this atlas — and
# with Kingston upon Thames. Falmouth collides with Cornwall's.
"kingston-jamaica": dict(
    name="Kingston", slug="Kingston,_Jamaica", country="Jamaica",
    region="Surrey", type="city", tag="famous",
    emoji="🎤", sounds=["city-hum.mp3"],
    search_name="Kingston Jamaica city",
    highlights=[("Bob Marley Museum", "Bob_Marley_Museum"),
                ("Devon House", None),
                ("Trench Town Culture Yard", None),
                ("National Gallery of Jamaica", None),
                ("Emancipation Park", None)],
    blurb="The capital, on the seventh-largest natural harbour in the world "
          "with the Blue Mountains directly behind it — and the reason the "
          "20th century sounds the way it does. Ska, rocksteady, reggae, dub "
          "and dancehall were all made within a few miles of each other "
          "here.",
    fact="UNESCO named Kingston a Creative City of Music in 2015, the first "
          "in the Caribbean. Its density of studios, sound systems and "
          "labels per head has no real parallel anywhere.",
    tip="Trench Town Culture Yard is the government yard Marley grew up in, "
        "run by people from the neighbourhood. Go with the community guides "
        "rather than a coach tour, and go in the day."),
"montego-bay": dict(
    name="Montego Bay", slug="Montego_Bay", country="Jamaica",
    region="Cornwall", type="coastal", tag="famous",
    emoji="🌅", sounds=["ocean-waves.mp3"],
    highlights=[("Doctor's Cave Beach", None),
                ("Rose Hall", "Rose_Hall_(Jamaica)"),
                ("Hip Strip", None),
                ("Martha Brae River", None)],
    blurb="Jamaica's second city and the front door for most visitors — a "
          "wide bay of clear water on the north-west coast, a strip of bars "
          "along the shore, and Georgian great houses in the hills behind "
          "it.",
    fact="Doctor's Cave Beach got its name and its fame in 1906, when a "
          "British osteopath declared the water curative. People came from "
          "across the Atlantic to bathe in it, and the modern Jamaican "
          "tourist industry starts roughly there.",
    tip="Rafting on the Martha Brae is 90 minutes on a bamboo raft poled by "
        "one person down a green river, and it is far better than it sounds. "
        "Go late afternoon when the light is through the trees."),
"negril": dict(
    name="Negril", slug="Negril", country="Jamaica",
    region="Cornwall", type="coastal", tag="famous",
    emoji="🌇", sounds=["ocean-waves.mp3"],
    highlights=[("Seven Mile Beach", None),
                ("Rick's Café", None),
                ("West End cliffs", None),
                ("Booby Cay", None)],
    blurb="Seven miles of white sand on the west end of the island, with a "
          "second, completely different Negril south of it: limestone cliffs "
          "with bars cut into them, caves at the waterline and people "
          "jumping off ledges into deep blue water.",
    fact="Negril faces due west, which on an island where nearly every resort "
          "faces north makes it the only major Jamaican beach where the sun "
          "sets into the sea. The whole cliff-bar economy exists because of "
          "that.",
    tip="The cliffs are the better half. Get there before six, take a spot "
        "on the rocks away from the cliff-diving crowd, and watch the sun go "
        "down from the water."),
"ocho-rios": dict(
    name="Ocho Rios", slug="Ocho_Rios", country="Jamaica",
    region="Middlesex", type="coastal", tag="famous",
    emoji="💦", sounds=["waterfall.mp3"],
    highlights=[("Dunn's River Falls", "Dunn's_River_Falls"),
                ("Blue Hole", None),
                ("Mystic Mountain", None),
                ("Fern Gully", None),
                ("James Bond Beach", None)],
    blurb="A cruise port on the north coast built around a waterfall you "
          "climb — 180 m of terraced limestone with the water running over "
          "it, ascended in a human chain. Behind the town the hills go "
          "straight up into fern forest.",
    fact="Ian Fleming wrote every James Bond novel at Goldeneye, twenty "
          "minutes east of here, over two months of each year for fourteen "
          "years. The beach where Ursula Andress walks out of the sea in "
          "*Dr. No* is up the coast at Laughing Waters.",
    tip="Dunn's River is packed whenever a ship is in. The Blue Hole "
        "upriver — rope swings, jumps, a cave — is wilder, cheaper and "
        "usually quiet; go with one of the local guides at the gate."),
"port-antonio": dict(
    name="Port Antonio", slug="Port_Antonio", country="Jamaica",
    region="Surrey", type="coastal", tag="hidden",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    highlights=[("Frenchman's Cove", None),
                ("Blue Lagoon", None),
                ("Rio Grande", None),
                ("Reach Falls", None),
                ("Winnifred Beach", None)],
    blurb="The old banana port on the wet north-east coast, greener and "
          "quieter than anywhere else on the island, with two harbours, a "
          "lagoon that is 60 m deep and blue-black, and rivers coming out of "
          "the Blue Mountains behind.",
    fact="Rafting on the Rio Grande began as a way to move bananas "
          "downriver, and became a tourist trip when Errol Flynn — who "
          "bought an island here in the 1940s — started racing the rafts "
          "with his friends for bets.",
    tip="Frenchman's Cove is a small beach where a cold freshwater river "
        "runs straight into the sea, so you can swim from one to the other. "
        "It has a small entry fee and is worth it."),
"blue-mountains-jamaica": dict(
    name="Blue Mountains", slug="Blue_Mountains_(Jamaica)", country="Jamaica",
    region="Surrey", type="mountain", tag="hidden",
    emoji="☕", sounds=["mountain-wind.mp3"],
    search_name="Blue Mountains Jamaica coffee",
    highlights=[("Blue Mountain Peak", None),
                ("Holywell", None),
                ("Craighton Estate", None),
                ("Cinchona Gardens", None)],
    blurb="The range behind Kingston, rising to 2,256 m, permanently misted "
          "and blue-looking at distance, and the source of what is arguably "
          "the most sought-after coffee on Earth. A national park, and "
          "UNESCO listed for both nature and Maroon heritage.",
    fact="The Windward Maroons — escaped enslaved people who fought the "
          "British to a treaty in 1739 — held these mountains and their "
          "descendants still live in them. The peak walk starts at "
          "midnight so you reach the top for dawn, when Cuba is sometimes "
          "visible 200 km away.",
    tip="You do not have to do the peak. Holywell, an hour from Kingston, "
        "has short cloud-forest trails, cabins and a view down over the "
        "whole city and harbour — and it is 10 °C cooler."),
"port-royal": dict(
    name="Port Royal", slug="Port_Royal", country="Jamaica",
    region="Surrey", type="history", tag="hidden",
    emoji="🏴‍☠️", sounds=["ocean-waves.mp3"],
    search_name="Port Royal Jamaica",
    highlights=[("Fort Charles", None),
                ("Giddy House", None),
                ("Palisadoes", None),
                ("Lime Cay", None)],
    blurb="A fishing village on a sand spit at the mouth of Kingston "
          "harbour that was, in the 1600s, the richest and most notorious "
          "port in the Americas — Henry Morgan's base, and called the "
          "wickedest city on Earth.",
    fact="An earthquake in 1692 dropped two-thirds of the town into the sea "
          "in minutes and killed a third of its people. The submerged "
          "streets are still down there, silted over, and are the only "
          "sunken city in the western hemisphere.",
    tip="The Giddy House, an artillery store tilted 45° by the 1907 "
        "earthquake, genuinely disorients you when you walk into it. Eat "
        "fried fish and festival at Gloria's afterwards — it is why "
        "Kingston drives out here on Sundays."),
"treasure-beach": dict(
    name="Treasure Beach", slug="Treasure_Beach", country="Jamaica",
    region="Middlesex", type="coastal", tag="hidden",
    emoji="🎣", sounds=["ocean-waves.mp3"],
    highlights=[("Pelican Bar", None),
                ("Great Bay", None),
                ("Lover's Leap", None),
                ("YS Falls", None)],
    blurb="A string of fishing coves on the dry south coast, with dark sand, "
          "cactus on the hills, no resorts, and a community tourism model "
          "the rest of the island points at. Jamaica with the volume turned "
          "down.",
    fact="Floyd's Pelican Bar stands on stilts on a sandbank a kilometre out "
          "to sea, built out of driftwood in 2001 by a fisherman who dreamed "
          "it. You get there by boat, and it has been rebuilt after every "
          "hurricane since.",
    tip="Take a boat from Great Bay to the Pelican Bar in the late "
        "afternoon and arrange for the boatman to come back at sunset. "
        "There is nothing else out there — just the bar, the sea and the "
        "sandbank."),
"falmouth-jamaica": dict(
    name="Falmouth", slug="Falmouth,_Jamaica", country="Jamaica",
    region="Cornwall", type="history", tag="hidden",
    emoji="✨", sounds=["ocean-waves.mp3"],
    search_name="Falmouth Jamaica Trelawny",
    highlights=[("Luminous Lagoon", None),
                ("Water Square", None),
                ("Baptist Manse", None),
                ("Good Hope Estate", None)],
    blurb="A Georgian port town in Trelawny, built on sugar money in the "
          "1790s and left behind when the trade collapsed — which is why it "
          "still has one of the finest collections of Georgian architecture "
          "anywhere in the Caribbean, much of it unrestored.",
    fact="The Luminous Lagoon beside the town glows when disturbed: "
          "bioluminescent dinoflagellates concentrate where the Martha Brae "
          "meets the sea in just the right salinity. Swimming in it at night "
          "makes you outlined in blue-green light.",
    tip="Falmouth had piped water before New York City did — 1799, from the "
        "reservoir at Water Square. Take the lagoon boat on a moonless "
        "night; a full moon washes the glow out completely."),
"black-river-jamaica": dict(
    name="Black River", slug="Black_River,_Jamaica", country="Jamaica",
    region="Middlesex", type="nature", tag="hidden",
    emoji="🐊", sounds=["wilderness.mp3"],
    search_name="Black River Jamaica St Elizabeth",
    highlights=[("Great Morass", None),
                ("YS Falls", None),
                ("Bamboo Avenue", None),
                ("Parottee Bay", None)],
    blurb="Jamaica's longest navigable river, running out through the Great "
          "Morass — the island's largest wetland — with mangrove tunnels, "
          "American crocodiles basking on the banks and egrets everywhere. "
          "The town at its mouth was the first place in Jamaica to get "
          "electricity.",
    fact="The water is not black. It is clear, and it looks dark because the "
          "peat on the bottom of the morass absorbs the light — the same "
          "reason a peat pool in Scotland looks like tea.",
    tip="Bamboo Avenue, a few miles inland, is four kilometres of road under "
        "a continuous arch of bamboo planted in the 1700s. Drive it with the "
        "windows down; the temperature drops noticeably."),
# ============================ HAITI ==========================
"port-au-prince": dict(
    name="Port-au-Prince", slug="Port-au-Prince", country="Haiti",
    region="Ouest", type="city", tag="famous",
    emoji="🎨", sounds=["city-hum.mp3"],
    highlights=[("Musée du Panthéon National", None),
                ("Marché en Fer", None),
                ("Champ de Mars", None),
                ("Cathédrale Sainte-Trinité", None)],
    blurb="The capital of the first Black republic in the world, in a bay "
          "under steep hills, and a city that has been through more in "
          "twenty years than most go through in two hundred — the 2010 "
          "earthquake, storms, and continuing instability.",
    fact="Haiti won its independence in 1804 by defeating Napoleon's army, "
          "the only successful slave revolution in history to found a state. "
          "France then demanded 150 million francs in compensation for lost "
          "'property', a debt Haiti paid off over 122 years.",
    tip="Much of the country is not currently safe for casual travel and "
        "advisories should be read before anything is booked. What is always "
        "reachable is the art: Haitian painting and metalwork are among the "
        "great traditions of the Americas, and the Nader collection is "
        "extraordinary."),
"cap-haitien": dict(
    name="Cap-Haïtien", slug="Cap-Haïtien", country="Haiti",
    region="Nord", type="city", tag="hidden",
    emoji="🏘️", sounds=["plaza.mp3"],
    search_name="Cap-Haitien Haiti",
    highlights=[("Citadelle Laferrière", "Citadelle_Laferrière"),
                ("Sans-Souci Palace", "Sans-Souci_Palace"),
                ("Cathédrale Notre-Dame", None),
                ("Labadie", None)],
    blurb="Haiti's second city on the north coast, once *Cap-Français*, the "
          "richest colonial city in the Caribbean and known as the Paris of "
          "the Antilles. Grid streets of arcaded, balconied houses in "
          "faded colours, backed by mountains.",
    fact="The revolution began in the plains behind this city in 1791. "
          "Within two years the colony that produced 40% of the world's "
          "sugar and 60% of its coffee had destroyed itself, and the "
          "colonists had burned the city rather than surrender it.",
    tip="This is the base for the Citadelle and Sans-Souci, an hour inland "
        "at Milot, and the north is considerably calmer than the capital. "
        "Check current advisories all the same."),
"citadelle-laferriere": dict(
    name="Citadelle Laferrière", slug="Citadelle_Laferrière",
    country="Haiti",
    region="Nord", type="history", tag="famous",
    emoji="🏰", sounds=["mountain-wind.mp3"],
    highlights=[("Sans-Souci Palace", "Sans-Souci_Palace"),
                ("Milot", None),
                ("Bonnet à l'Evêque", None)],
    blurb="The largest fortress in the Americas, built on a 900 m peak by "
          "20,000 workers between 1805 and 1820 — a mountain of stone with "
          "4 m walls and 365 cannon, put there by Henri Christophe to stop "
          "the French ever coming back.",
    fact="They never came. The guns were never fired in anger, and the "
          "cannonballs are still stacked in pyramids where they were left "
          "two hundred years ago. It was Haiti's first UNESCO site, listed "
          "in 1982.",
    tip="It is a steep hour on foot from Milot, or you can hire a horse at "
        "the bottom. Go early: the mountain generates its own cloud by "
        "midday and the whole point is the view over the northern plain."),
"jacmel": dict(
    name="Jacmel", slug="Jacmel", country="Haiti",
    region="Sud-Est", type="coastal", tag="hidden",
    emoji="🎭", sounds=["ocean-waves.mp3"],
    highlights=[("Bassin Bleu", None),
                ("Rue du Commerce", None),
                ("Kabic Beach", None),
                ("Carnival workshops", None)],
    blurb="A port on the south coast of iron-framed mansions imported from "
          "France in the 1890s, and the artistic capital of Haiti — "
          "papier-mâché mask workshops on every street and a carnival with "
          "no equal in the Caribbean.",
    fact="The cast-iron shopfronts of Jacmel were ordered from the same "
          "European catalogues as New Orleans's French Quarter, and the two "
          "cities look startlingly alike. Jacmel also had electricity before "
          "Paris did.",
    tip="Bassin Bleu, an hour inland, is three cobalt pools under waterfalls, "
        "reached on foot and by rope down the last drop. Local guides at "
        "the trailhead are compulsory and worth it."),
"labadee": dict(
    name="Labadee", slug="Labadie,_Haiti", country="Haiti",
    region="Nord", type="coastal", tag="hidden",
    emoji="⛱️", sounds=["ocean-waves.mp3"],
    search_name="Labadee Haiti beach",
    highlights=[("Cap-Haïtien", "Cap-Haïtien"),
                ("Belly Beach", None),
                ("Cormier Plage", None)],
    blurb="A private peninsula on the north coast leased to a cruise line, "
          "with white sand, forested hills and calm water — and next to it "
          "the village of Labadie, which has no road and is reached by boat "
          "from Cap-Haïtien.",
    fact="For many years cruise passengers were told only that they were in "
          "Hispaniola, not Haiti. The arrangement is controversial, though "
          "it is also one of the country's most reliable sources of foreign "
          "earnings and employs several hundred people directly.",
    tip="Skip the fenced peninsula and take a small boat from Cap-Haïtien to "
        "Labadie village or Cormier Plage instead. Same water, and the money "
        "goes to the fishermen who run the boats."),
"ile-a-vache": dict(
    name="Île-à-Vache", slug="Île-à-Vache", country="Haiti",
    region="Sud", type="island", tag="hidden",
    emoji="🐄", sounds=["ocean-waves.mp3"],
    search_name="Ile a Vache Haiti island",
    highlights=[("Port Morgan", None),
                ("Madame Bernard", None),
                ("Abaka Bay", None),
                ("Les Cayes", None)],
    blurb="A green island of 20,000 people off Haiti's southern coast, with "
          "no cars and no paved roads — you walk, ride or take a boat. "
          "Beaches on the south side, mangrove on the north, and a market at "
          "Madame Bernard on Mondays and Thursdays.",
    fact="Henry Morgan used the island as a base and staged his 1670 raid on "
          "Panama from it. In 1862 Abraham Lincoln's administration settled "
          "over 450 freed African Americans here in a colonisation scheme "
          "that collapsed within a year; the survivors were brought back.",
    tip="It is a 40-minute boat ride from Les Cayes. Go on a market day, "
        "when boats come in from all around the bay and the whole island "
        "converges on one field."),
# ====================== DOMINICAN REPUBLIC ===================
"santo-domingo": dict(
    name="Santo Domingo", slug="Santo_Domingo",
    country="Dominican Republic",
    region="Distrito Nacional", type="history", tag="famous",
    emoji="⚓", sounds=["plaza.mp3"],
    highlights=[("Zona Colonial", "Colonial_City_of_Santo_Domingo"),
                ("Catedral Primada de América", None),
                ("Alcázar de Colón", None),
                ("Calle Las Damas", None),
                ("Fortaleza Ozama", None)],
    blurb="The oldest permanently inhabited European city in the Americas, "
          "founded 1498, and the place every institution of the Spanish New "
          "World started: the first cathedral, the first university, the "
          "first hospital, the first paved street. All of it still standing, "
          "and all of it lived in.",
    fact="Calle Las Damas, laid in 1502, is the oldest paved street in the "
          "Americas — named for the ladies of the viceroy's court, who "
          "promenaded along it in the evenings. Diego Columbus's palace is "
          "at the end of it.",
    tip="The Zona Colonial is small enough to walk in a morning but is best "
        "at night, when the stone is lit and the bars fill Plaza España. "
        "Start at Fortaleza Ozama, the oldest fort in the Americas."),
"punta-cana": dict(
    name="Punta Cana", slug="Punta_Cana", country="Dominican Republic",
    region="La Altagracia", type="coastal", tag="famous",
    emoji="🌴", sounds=["ocean-waves.mp3"],
    highlights=[("Bávaro Beach", None),
                ("Hoyo Azul", None),
                ("Isla Saona", "Saona_Island"),
                ("Macao Beach", None)],
    blurb="Fifty kilometres of coconut palm and white sand on the eastern "
          "tip of the island, and the most-visited stretch of coast in the "
          "Caribbean — a purpose-built resort landscape that did not exist "
          "before 1969.",
    fact="The whole thing started when a group of investors bought 58 km² of "
          "roadless jungle coastline sight-unseen, and then built the "
          "airport themselves in 1984 because no government would. It is "
          "still privately owned.",
    tip="Get out of the compound at least once: Macao, a public beach twenty "
        "minutes north, has surf, food shacks and Dominicans on it, which "
        "the resort strip does not."),
"samana": dict(
    name="Samaná", slug="Samaná_Province", country="Dominican Republic",
    region="Samaná", type="coastal", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    search_name="Samana Dominican Republic peninsula",
    highlights=[("El Limón waterfall", None),
                ("Los Haitises National Park", "Los_Haitises_National_Park"),
                ("Cayo Levantado", None),
                ("Las Galeras", None)],
    blurb="A green peninsula on the north-east coast, coconut plantations "
          "and steep headlands, with a deep bay behind it where thousands of "
          "humpback whales come to breed every winter.",
    fact="Between January and March, around 3,000 humpbacks — most of the "
          "entire North Atlantic population — gather in Samaná Bay. It is "
          "one of the largest and most reliable whale congregations on "
          "Earth.",
    tip="Los Haitises, across the bay, is mangrove channels between "
        "limestone knobs with caves full of Taíno rock art. Boats go from "
        "Samaná town; take the early one before the wind gets up."),
"las-terrenas": dict(
    name="Las Terrenas", slug="Las_Terrenas",
    country="Dominican Republic",
    region="Samaná", type="coastal", tag="hidden",
    emoji="🥥", sounds=["ocean-waves.mp3"],
    highlights=[("Playa Bonita", None),
                ("Playa Cosón", None),
                ("El Limón waterfall", None),
                ("Pueblo de los Pescadores", None)],
    blurb="A fishing village on the north side of the Samaná peninsula that "
          "French and Italian expatriates turned into something like a "
          "Mediterranean beach town — long empty sands with palms leaning "
          "over them, and good food on a road that ends at the water.",
    fact="Until 1946 the village was a penal settlement; the government sent "
          "families here to farm. The road over the mountain from Sánchez "
          "only opened in the 1970s, which is why it stayed small.",
    tip="Playa Cosón, five minutes west, is a several-kilometre curve with "
        "almost nothing on it. Ride out on a *motoconcho* and take lunch at "
        "the one shack at the far end."),
"puerto-plata": dict(
    name="Puerto Plata", slug="Puerto_Plata,_Dominican_Republic",
    country="Dominican Republic",
    region="Puerto Plata", type="city", tag="hidden",
    emoji="🚡", sounds=["ocean-waves.mp3"],
    search_name="Puerto Plata Dominican Republic",
    highlights=[("Mount Isabel de Torres", None),
                ("Fortaleza San Felipe", None),
                ("Victorian centre", None),
                ("Damajagua waterfalls", None)],
    blurb="The old amber port on the north coast, with a Victorian centre of "
          "gingerbread houses in bright paint, a 16th-century fort on the "
          "point, and a cable car up a 800 m mountain that stands straight "
          "out of the sea behind the town.",
    fact="The Dominican amber found in these hills is 15–20 million years "
          "old and unusually clear, and the insect-bearing pieces are the "
          "best in the world. The mosquito in *Jurassic Park* was Dominican "
          "amber.",
    tip="The 27 Charcos de Damajagua, half an hour inland, is a canyon you "
        "descend by jumping and sliding down 27 waterfalls into pools. "
        "Helmets and guides provided; it is the best day on this coast."),
"cabarete": dict(
    name="Cabarete", slug="Cabarete", country="Dominican Republic",
    region="Puerto Plata", type="coastal", tag="hidden",
    emoji="🪁", sounds=["ocean-waves.mp3"],
    highlights=[("Kite Beach", None),
                ("Encuentro", None),
                ("El Choco caves", None),
                ("Playa Cabarete", None)],
    blurb="A single road along a bay on the north coast that has become one "
          "of the world's great wind-sports towns — reef-protected water "
          "inside, a reliable side-onshore trade wind every afternoon, and "
          "several hundred kites in the air by three o'clock.",
    fact="The geography does it: the bay faces north-east into the trades "
          "and the mountains behind funnel the thermal, so the wind switches "
          "on at almost the same time every day for most of the year.",
    tip="Mornings are flat and the surfers go to Encuentro; the wind comes "
        "in around midday and the kiters take over. Plan the day around the "
        "wind, not the clock."),
"jarabacoa": dict(
    name="Jarabacoa", slug="Jarabacoa", country="Dominican Republic",
    region="La Vega", type="nature", tag="hidden",
    emoji="🌲", sounds=["waterfall.mp3"],
    highlights=[("Salto de Jimenoa", None),
                ("Salto de Baiguate", None),
                ("Río Yaque del Norte", None),
                ("Pico Duarte", "Pico_Duarte")],
    blurb="A pine-forest town at 530 m in the central highlands, cool enough "
          "to need a jacket at night, with whitewater on the Yaque del "
          "Norte, waterfalls on every side and the trailhead for the "
          "Caribbean's highest mountain.",
    fact="This is the Dominican Alps in local usage, and the pine forest is "
          "genuinely temperate — *Pinus occidentalis*, found only on "
          "Hispaniola. It grows above 800 m where the Caribbean lowland "
          "species cannot.",
    tip="Salto de Jimenoa Uno falls 60 m into a walled amphitheatre reached "
        "by a footbridge over the river. The rafting on the Yaque is class "
        "II–III and runs year-round."),
"pico-duarte": dict(
    name="Pico Duarte", slug="Pico_Duarte", country="Dominican Republic",
    region="La Vega", type="mountain", tag="hidden",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Valle del Tetero", None),
                ("La Ciénaga", None),
                ("Armando Bermúdez National Park", None),
                ("Jarabacoa", "Jarabacoa")],
    blurb="At 3,098 m the highest mountain in the Caribbean, and nothing "
          "like the picture the word Caribbean produces: pine forest, frost "
          "on the ground at dawn, and a two- or three-day walk in through "
          "the Cordillera Central to reach it.",
    fact="Temperatures at the summit drop below freezing most clear nights, "
          "and snow has been recorded. It is the highest point on any "
          "Atlantic island, and higher than anything east of the Mississippi "
          "in North America.",
    tip="The standard route from La Ciénaga is 46 km round trip with mules "
        "for the gear and park guides who are compulsory. Go in the dry "
        "season, December to March, and expect real cold at the huts."),
"bahia-de-las-aguilas": dict(
    name="Bahía de las Águilas", slug="Bahía_de_las_Águilas",
    country="Dominican Republic",
    region="Pedernales", type="coastal", tag="hidden",
    emoji="🦅", sounds=["ocean-waves.mp3"],
    highlights=[("Jaragua National Park", None),
                ("Cabo Rojo", None),
                ("Laguna de Oviedo", None),
                ("Pedernales", None)],
    blurb="Eight kilometres of white sand against dry limestone cliffs in "
          "the far south-west, inside a national park, with no buildings of "
          "any kind on it and no road to most of its length. Reached by boat "
          "from a fishing village.",
    fact="It is regularly named the most beautiful beach in the Caribbean, "
          "and it is empty because it is protected: Jaragua National Park "
          "has kept development off the entire coastline since 1983.",
    tip="It is eight hours from Santo Domingo and the last stretch is dirt. "
        "Take everything you need — water, food, shade — because there is "
        "nothing there at all, which is exactly the point."),
"isla-saona": dict(
    name="Isla Saona", slug="Saona_Island", country="Dominican Republic",
    region="La Altagracia", type="island", tag="hidden",
    emoji="⭐", sounds=["ocean-waves.mp3"],
    search_name="Isla Saona Dominican Republic",
    highlights=[("Cotubanamá National Park", None),
                ("Piscina Natural", None),
                ("Mano Juan", None),
                ("Bayahibe", None)],
    blurb="A flat island of palm and mangrove inside a national park off the "
          "south-eastern tip, with two fishing villages, no cars, and a "
          "sandbar in open water a kilometre offshore where you can stand "
          "waist-deep surrounded by starfish.",
    fact="Columbus named it after Savona in Italy, the home town of a "
          "crewman. The island's Mano Juan village runs a turtle hatchery, "
          "and the wooden houses along its single sand street are painted "
          "every colour there is.",
    tip="Every catamaran trip stops at the natural pool with music blaring. "
        "The small-boat tours from Bayahibe get there before them and "
        "actually stop at Mano Juan."),
"santiago-de-los-caballeros": dict(
    name="Santiago de los Caballeros",
    slug="Santiago_de_los_Caballeros",
    country="Dominican Republic",
    region="Santiago", type="city", tag="hidden",
    emoji="🚬", sounds=["city-hum.mp3"],
    highlights=[("Monumento a los Héroes", None),
                ("Centro León", None),
                ("Cigar factories", None),
                ("Calle del Sol", None)],
    blurb="The Dominican Republic's second city, in the fertile Cibao "
          "valley, and the capital of two things: merengue and cigars. Most "
          "of the world's premium hand-rolled cigars come out of this "
          "valley.",
    fact="Trujillo built the enormous marble monument on the hill as a "
          "monument to himself; after his assassination in 1961 it was "
          "rededicated to the heroes of the Restoration. The murals inside "
          "are by the Spanish painter Vela Zanetti.",
    tip="Tour a cigar factory — several of the big names take visitors — and "
        "then go to the Centro León, which is one of the best museums in the "
        "Caribbean and almost never mentioned."),
# ========================= PUERTO RICO =======================
# San Juan collides with San Juan Province, Argentina — already in this atlas
# — and with San Juan, Philippines.
"san-juan-puerto-rico": dict(
    name="San Juan", slug="San_Juan,_Puerto_Rico", country="Puerto Rico",
    region="San Juan", type="city", tag="famous",
    emoji="🏰", sounds=["plaza.mp3"],
    search_name="San Juan Puerto Rico old city",
    highlights=[("Castillo San Felipe del Morro",
                 "Castillo_San_Felipe_del_Morro"),
                ("Old San Juan", "Old_San_Juan"),
                ("Castillo San Cristóbal", None),
                ("Paseo de la Princesa", None),
                ("La Perla", None)],
    blurb="Founded in 1521 and the second-oldest European-founded city in "
          "the Americas — a walled headland of blue cobbles and buildings "
          "painted every colour, with two enormous Spanish forts guarding "
          "the harbour mouth, and a modern city of half a million behind "
          "it.",
    fact="El Morro's walls are up to 5.5 m thick and took 250 years to "
          "finish. They held off Francis Drake in 1595 and a Dutch fleet in "
          "1625; the only force ever to take San Juan by land was the Earl "
          "of Cumberland in 1598, and dysentery drove him out within "
          "months.",
    tip="The cobbles are *adoquines*, cast from iron-smelting slag and "
        "brought over as ship ballast — which is why they are blue. Walk the "
        "sea wall from La Puntilla to El Morro at sunset; the whole promenade "
        "is free."),
"el-yunque": dict(
    name="El Yunque", slug="El_Yunque_National_Forest",
    country="Puerto Rico",
    region="Río Grande", type="wilderness", tag="famous",
    emoji="🐸", sounds=["wilderness.mp3"],
    search_name="El Yunque National Forest Puerto Rico",
    highlights=[("La Mina Falls", None),
                ("Yokahú Tower", None),
                ("El Yunque Peak", None),
                ("Juan Diego Falls", None)],
    blurb="The only tropical rainforest in the United States National Forest "
          "system — 11,000 hectares of it on the eastern end of the island, "
          "getting up to 5 m of rain a year, with waterfalls, stone towers "
          "from the 1930s and coquí frogs calling from every direction after "
          "dark.",
    fact="The coquí is the size of a thumbnail and the national symbol of "
          "Puerto Rico. Its two-note call reaches 100 decibels at a metre — "
          "as loud as a lawnmower, from a frog you can barely see.",
    tip="Reservations are required for the main road corridor and sell out "
        "days ahead. Book the first slot; the forest makes its own rain most "
        "afternoons, and the morning is when you get the views."),
"vieques": dict(
    name="Vieques", slug="Vieques", country="Puerto Rico",
    region="Vieques", type="island", tag="hidden",
    emoji="✨", sounds=["ocean-waves.mp3"],
    highlights=[("Mosquito Bay", None),
                ("Playa Caracas", None),
                ("Sun Bay", None),
                ("Wild horses", None),
                ("Fortín Conde de Mirasol", None)],
    blurb="An island 13 km off the east coast with wild horses on the roads, "
          "empty beaches inside a wildlife refuge that used to be a US Navy "
          "bombing range, and the brightest bioluminescent bay on Earth.",
    fact="Mosquito Bay holds the Guinness record for the brightest "
          "bioluminescent bay measured anywhere — up to 700,000 "
          "dinoflagellates per litre. A hand through the water leaves a "
          "trail of blue fire.",
    tip="Kayak the bay on a moonless night; tours are cancelled around the "
        "full moon for good reason. Sunscreen and insect repellent kill the "
        "organisms and are banned in the water."),
"culebra": dict(
    name="Culebra", slug="Culebra,_Puerto_Rico", country="Puerto Rico",
    region="Culebra", type="island", tag="hidden",
    emoji="🐠", sounds=["ocean-waves.mp3"],
    search_name="Culebra Puerto Rico Flamenco Beach",
    highlights=[("Flamenco Beach", None),
                ("Tamarindo Beach", None),
                ("Culebrita", None),
                ("Zoni Beach", None)],
    blurb="A small dry island east of the mainland with one town, no rivers, "
          "no chain hotels and a beach — Flamenco — that is routinely put in "
          "the world's top five. Snorkelling straight off the sand at "
          "Tamarindo, and turtles in the shallows.",
    fact="Two rusted US Army tanks sit on Flamenco Beach, left from when the "
          "Navy used the island for target practice until protests forced "
          "them out in 1975. They are now covered in graffiti and are the "
          "island's most photographed object.",
    tip="Day-trippers come on the ferry and leave on the ferry. Stay a "
        "night: the island empties completely and the sky over it, with no "
        "streetlights to speak of, is extraordinary."),
"ponce": dict(
    name="Ponce", slug="Ponce,_Puerto_Rico", country="Puerto Rico",
    region="Ponce", type="city", tag="hidden",
    emoji="🚒", sounds=["plaza.mp3"],
    search_name="Ponce Puerto Rico city",
    highlights=[("Parque de Bombas", None),
                ("Museo de Arte de Ponce", None),
                ("Plaza Las Delicias", None),
                ("Castillo Serrallés", None),
                ("Tibes Ceremonial Center", None)],
    blurb="The southern capital, hotter and drier than San Juan and "
          "architecturally its rival — neoclassical and creole facades round "
          "a plaza with a red-and-black striped wooden firehouse in the "
          "middle of it that has become the symbol of the whole city.",
    fact="The Museo de Arte de Ponce holds the best collection of European "
          "art in the Caribbean, including Frederic Leighton's *Flaming "
          "June* — one of the most reproduced Victorian paintings in "
          "existence, bought here in 1963 for £2,000 when nobody wanted it.",
    tip="Tibes, just north, is the oldest excavated ceremonial site in the "
        "Antilles — pre-Taíno ball courts and plazas from around 700 AD, and "
        "almost unvisited."),
"rincon-puerto-rico": dict(
    name="Rincón", slug="Rincón,_Puerto_Rico", country="Puerto Rico",
    region="Rincón", type="coastal", tag="hidden",
    emoji="🏄", sounds=["ocean-waves.mp3"],
    search_name="Rincon Puerto Rico surf",
    highlights=[("Domes Beach", None),
                ("Punta Higüero lighthouse", None),
                ("Steps Beach", None),
                ("Tres Palmas", None)],
    blurb="The surf town on the western tip, facing the Mona Passage, where "
          "the winter north swells arrive with the whole Atlantic behind "
          "them. Humpbacks pass close in from January, watched from a "
          "lighthouse park on the point.",
    fact="Rincón was put on the map by the 1968 World Surfing Championships, "
          "which came here after Puerto Rico was proposed as a long shot. "
          "Tres Palmas holds up at double overhead and is one of the biggest "
          "rideable waves in the Caribbean.",
    tip="Summer is flat and the water is glass — good for snorkelling Steps "
        "Beach's reef. Winter is for surfing and whales. They are two "
        "completely different towns."),
"cabo-rojo": dict(
    name="Cabo Rojo", slug="Cabo_Rojo,_Puerto_Rico", country="Puerto Rico",
    region="Cabo Rojo", type="coastal", tag="hidden",
    emoji="🧂", sounds=["ocean-waves.mp3"],
    search_name="Cabo Rojo Puerto Rico lighthouse",
    highlights=[("Los Morrillos Lighthouse", None),
                ("Playa Sucia", None),
                ("Salinas de Cabo Rojo", None),
                ("La Parguera", None)],
    blurb="The south-western corner of the island: white limestone cliffs "
          "over turquoise water, an 1882 lighthouse on the point, pink salt "
          "flats behind it and one of the Caribbean's most important "
          "shorebird stopovers.",
    fact="The salt pans here have been worked since before the Spanish "
          "arrived and are among the oldest continuously operated industries "
          "in the Americas. The pink is *Dunaliella salina*, an alga that "
          "thrives in brine — the same thing that colours flamingos.",
    tip="Walk out to the lighthouse in the late afternoon and look down the "
        "cliffs at Playa Sucia. It is a dry, cactus-covered walk with no "
        "shade — take water and go after four."),
"camuy-caves": dict(
    name="Río Camuy Caves", slug="Parque_Nacional_de_las_Cavernas_del_Río_Camuy",
    country="Puerto Rico",
    region="Camuy", type="nature", tag="hidden",
    emoji="🦇", sounds=["waterfall.mp3"],
    search_name="Rio Camuy Cave Park Puerto Rico",
    highlights=[("Cueva Clara", None),
                ("Sumidero Tres Pueblos", None),
                ("Río Camuy", None),
                ("Karst country", None)],
    blurb="One of the largest cave systems in the western hemisphere, cut by "
          "the third-largest underground river on Earth through the karst "
          "belt of northern Puerto Rico. The main chamber is 52 m high with "
          "a river running through the floor of it.",
    fact="Only about ten of the system's 220 known caves have been mapped in "
          "any detail. The Tres Pueblos sinkhole is 122 m deep and 200 m "
          "across, and three municipalities meet at its rim.",
    tip="Check it is open before driving out — the park closed for years "
        "after Hurricane María and has reopened in stages. The karst road "
        "through the *mogotes* around it is worth the trip on its own."),
"guanica": dict(
    name="Guánica", slug="Guánica_State_Forest", country="Puerto Rico",
    region="Guánica", type="nature", tag="hidden",
    emoji="🌵", sounds=["wilderness.mp3"],
    search_name="Guanica dry forest Puerto Rico",
    highlights=[("Gilligan's Island", None),
                ("Ballena Trail", None),
                ("Fuerte Caprón", None),
                ("Playa Santa", None)],
    blurb="The best-preserved subtropical dry forest anywhere in the "
          "Caribbean, and a UNESCO biosphere reserve — cactus, scrub and "
          "700-year-old guayacán trees on white limestone, with the sea at "
          "the bottom of every trail.",
    fact="Dry forest is far rarer than rainforest: less than 1% of the "
          "original Caribbean dry forest survives. Half of Puerto Rico's "
          "bird species have been recorded in this one reserve, including "
          "the endangered Puerto Rican nightjar.",
    tip="Gilligan's Island, a mangrove cay a few minutes offshore by ferry, "
        "has channels of clear shallow water between the roots. Go on a "
        "weekday; local families fill it at weekends."),
# =========================== BAHAMAS =========================
# Nassau collides with Nassau County, New York and with Nassau in Germany.
"nassau": dict(
    name="Nassau", slug="Nassau,_Bahamas", country="Bahamas",
    region="New Providence", type="city", tag="famous",
    emoji="🏴‍☠️", sounds=["plaza.mp3"],
    search_name="Nassau Bahamas",
    highlights=[("Fort Charlotte", None),
                ("Queen's Staircase", None),
                ("Straw Market", None),
                ("Parliament Square", None),
                ("Paradise Island", None)],
    blurb="The Bahamian capital on New Providence, pink and pastel Georgian "
          "government buildings around a square, a harbour full of cruise "
          "ships, and a history as the pirate republic of the Caribbean "
          "before the Royal Navy took it back in 1718.",
    fact="Between 1706 and 1718 Nassau had no functioning government at all "
          "and was run by pirates — Blackbeard, Charles Vane and Benjamin "
          "Hornigold among them. The colonial motto afterwards was *Expulsis "
          "piratis, restituta commercia*: pirates expelled, commerce "
          "restored.",
    tip="The Queen's Staircase is 66 steps cut by hand out of solid "
        "limestone in the 1790s, in a cool green cleft five minutes from the "
        "main street. Go early, before the ships dock."),
"exuma": dict(
    name="Exuma", slug="Exuma", country="Bahamas",
    region="Exuma", type="island", tag="famous",
    emoji="🐖", sounds=["ocean-waves.mp3"],
    search_name="Exuma Bahamas cays",
    highlights=[("Big Major Cay", None),
                ("Thunderball Grotto", None),
                ("Exuma Cays Land and Sea Park", None),
                ("Tropic of Cancer Beach", None),
                ("Stocking Island", None)],
    blurb="A chain of 365 cays running 200 km through water so shallow and "
          "clear that the sandbanks between them are visible from orbit. "
          "Swimming pigs on one island, iguanas on another, and the oldest "
          "marine protected area in the world in the middle.",
    fact="The Exuma Cays Land and Sea Park, established in 1958, was the "
          "first of its kind anywhere, and has been a complete no-take zone "
          "since 1986. Conch and grouper densities inside it are several "
          "times those outside.",
    tip="Thunderball Grotto is an air-filled cave you snorkel into through "
        "an underwater opening — used in two Bond films. Go at slack low "
        "tide; the current through the entrance runs hard otherwise."),
"harbour-island": dict(
    name="Harbour Island", slug="Harbour_Island,_Bahamas",
    country="Bahamas",
    region="Harbour Island", type="island", tag="hidden",
    emoji="🌸", sounds=["ocean-waves.mp3"],
    search_name="Harbour Island Bahamas pink sand",
    highlights=[("Pink Sands Beach", None),
                ("Dunmore Town", None),
                ("Lone Tree", None),
                ("Eleuthera", "Eleuthera")],
    blurb="Five kilometres long, reached by water taxi from Eleuthera, with "
          "golf carts instead of cars, a New England-looking clapboard town, "
          "and five kilometres of beach the colour of the inside of a "
          "shell.",
    fact="The pink comes from foraminifera — single-celled organisms with "
          "pink-red shells that live on the reef and wash ashore crushed "
          "into the white sand. The concentration on this particular beach "
          "is unusually high.",
    tip="The colour is strongest in the low sun at either end of the day, "
        "and photographs at noon look plain white. Walk the beach at seven "
        "in the morning."),
"eleuthera": dict(
    name="Eleuthera", slug="Eleuthera", country="Bahamas",
    region="Eleuthera", type="island", tag="hidden",
    emoji="🕳️", sounds=["ocean-waves.mp3"],
    highlights=[("Glass Window Bridge", None),
                ("Queen's Bath", None),
                ("Lighthouse Beach", None),
                ("Governor's Harbour", None),
                ("Preacher's Cave", None)],
    blurb="A 180 km sliver of island, in places only a few dozen metres "
          "wide, with the deep dark Atlantic on one side and the pale "
          "turquoise bank on the other — and one point where you can see "
          "both at once with a road bridge between them.",
    fact="At the Glass Window the two oceans are separated by a strip of "
          "rock a few metres across, and the colour difference is absolute. "
          "Winter storm waves have knocked the bridge sideways more than "
          "once — the current one is offset from its abutments.",
    tip="Lighthouse Beach at the southern tip needs a high-clearance vehicle "
        "down several kilometres of rough track, and is one of the emptiest "
        "great beaches in the Bahamas."),
"andros-bahamas": dict(
    name="Andros", slug="Andros,_Bahamas", country="Bahamas",
    region="Andros", type="island", tag="hidden",
    emoji="🕳️", sounds=["wilderness.mp3"],
    search_name="Andros Bahamas blue holes",
    highlights=[("Andros Barrier Reef", None),
                ("Blue Holes National Park", None),
                ("Tongue of the Ocean", None),
                ("Red Bays", None)],
    blurb="The largest and least visited island in the Bahamas — bigger than "
          "all the others put together, mostly pine forest and mangrove "
          "creek, with the third-largest barrier reef on the planet along "
          "its eastern edge.",
    fact="Andros has more blue holes than anywhere else on Earth: over 175 "
          "inland and around 50 offshore, some more than 100 m deep. The "
          "reef drops off into the Tongue of the Ocean, a 2,000 m trench "
          "that comes within a couple of kilometres of the shore.",
    tip="This is the bonefishing capital of the world and the flats on the "
        "west side are enormous. For everyone else, Captain Bill's Blue Hole "
        "is a short drive inland and you can swim in it."),
"grand-bahama": dict(
    name="Grand Bahama", slug="Grand_Bahama", country="Bahamas",
    region="Grand Bahama", type="island", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Lucayan National Park", None),
                ("Gold Rock Beach", None),
                ("Ben's Cave", None),
                ("Freeport", None),
                ("West End", None)],
    blurb="The northernmost of the main islands, 90 km off Florida, with one "
          "of the longest underwater cave systems in the world running "
          "beneath a national park of pine, mangrove and one very good "
          "beach.",
    fact="Human remains found in Ben's Cave in the 1980s are Lucayan and "
          "about a thousand years old — among the earliest evidence of "
          "people in the Bahamas, preserved because the cave's fresh water "
          "sits on salt and excludes oxygen.",
    tip="Gold Rock Beach only appears properly at low tide, when it becomes "
        "a vast rippled sand flat you can walk out across. Check the tide "
        "table; at high water there is barely a beach at all."),
"bimini": dict(
    name="Bimini", slug="Bimini", country="Bahamas",
    region="Bimini", type="island", tag="hidden",
    emoji="🦈", sounds=["ocean-waves.mp3"],
    highlights=[("Bimini Road", None),
                ("Sapona wreck", None),
                ("Healing Hole", None),
                ("Alice Town", None)],
    blurb="Two small islands 80 km from Miami, the closest Bahamian land to "
          "the United States, and a game-fishing legend — Hemingway spent "
          "three summers here in the 1930s and set *Islands in the Stream* "
          "partly on them.",
    fact="The Bimini Road is a half-kilometre line of rectangular limestone "
          "blocks lying in 5 m of water, found in 1968. Geologists call it "
          "natural beach rock fractured into blocks; a great many other "
          "people call it Atlantis.",
    tip="Great hammerheads gather here between December and March and can be "
        "dived with in shallow, clear water — one of the few reliable places "
        "on Earth for it."),
"abaco": dict(
    name="Abaco", slug="Abaco_Islands", country="Bahamas",
    region="Abaco", type="island", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    search_name="Abaco Islands Bahamas",
    highlights=[("Hope Town", None),
                ("Elbow Reef Lighthouse", None),
                ("Green Turtle Cay", None),
                ("Treasure Cay Beach", None),
                ("Marsh Harbour", None)],
    blurb="A 200 km chain of cays enclosing a sheltered sound, and the "
          "sailing capital of the Bahamas — loyalist settlements of white "
          "clapboard and picket fences, a candy-striped lighthouse, and calm "
          "water the whole way down inside the reef.",
    fact="The Elbow Reef lighthouse at Hope Town, built in 1864, is the last "
          "manually operated kerosene lighthouse in the world. A keeper "
          "still winds the weight-driven mechanism by hand every two hours "
          "through the night.",
    tip="The islands were hit extremely hard by Hurricane Dorian in 2019 and "
        "recovery is uneven — some cays are fully back, others are not. "
        "Check before booking, and spend money locally when you go."),
# ======================== CAYMAN ISLANDS =====================
"george-town-cayman": dict(
    name="George Town", slug="George_Town,_Cayman_Islands",
    country="Cayman Islands",
    region="Grand Cayman", type="city", tag="hidden",
    emoji="🏦", sounds=["city-hum.mp3"],
    search_name="George Town Grand Cayman",
    highlights=[("Seven Mile Beach", None),
                ("Cayman Islands National Museum", None),
                ("Elmslie Memorial Church", None),
                ("Smith Cove", None)],
    blurb="The capital of the Cayman Islands and one of the largest offshore "
          "financial centres in the world — a low, tidy, cruise-served town "
          "on a shoreline of ironshore rock, with the reef wall a few "
          "hundred metres out.",
    fact="Around 100,000 companies are registered in the Cayman Islands, "
          "more than the islands' population. Ugland House in George Town is "
          "the registered address of some 19,000 of them.",
    tip="Smith Cove, a five-minute drive south, is a small ironshore cove "
        "with calm clear water and no cruise crowd — where residents swim "
        "before work."),
"seven-mile-beach": dict(
    name="Seven Mile Beach", slug="Seven_Mile_Beach,_Grand_Cayman",
    country="Cayman Islands",
    region="Grand Cayman", type="coastal", tag="famous",
    emoji="🏖️", sounds=["ocean-waves.mp3"],
    search_name="Seven Mile Beach Grand Cayman",
    highlights=[("Cemetery Reef", None),
                ("Stingray City", None),
                ("Governor's Beach", None),
                ("West Bay", None)],
    blurb="A continuous crescent of coral sand on Grand Cayman's western "
          "shore — actually about 5.5 miles — with calm water, no surf and "
          "public access along its whole length, however built up the strip "
          "behind it has become.",
    fact="Every beach in the Cayman Islands is public to the high-water "
          "mark by law, so there is no such thing as a private stretch of "
          "Seven Mile Beach no matter which resort stands behind it.",
    tip="Cemetery Reef, at the northern end, has live coral within 50 m of "
        "the sand and a public car park beside it — the best free "
        "snorkelling on the island."),
"little-cayman": dict(
    name="Little Cayman", slug="Little_Cayman", country="Cayman Islands",
    region="Little Cayman", type="island", tag="hidden",
    emoji="🪸", sounds=["ocean-waves.mp3"],
    highlights=[("Bloody Bay Wall", None),
                ("Booby Pond Nature Reserve", None),
                ("Point of Sand", None),
                ("Owen Island", None)],
    blurb="Sixteen square kilometres, around 200 residents, one airstrip and "
          "an iguana crossing sign that is not a joke — and offshore, one of "
          "the great wall dives on Earth, dropping from 6 m to well over a "
          "kilometre.",
    fact="Booby Pond holds the largest red-footed booby colony in the "
          "western hemisphere — around 20,000 birds — and the island's "
          "rock iguanas outnumber its people by roughly ten to one.",
    tip="Bloody Bay Wall starts shallow enough that snorkellers can see the "
        "lip of it and look over the edge into blue. You do not need a tank "
        "to understand why divers come."),
"cayman-brac": dict(
    name="Cayman Brac", slug="Cayman_Brac", country="Cayman Islands",
    region="Cayman Brac", type="island", tag="hidden",
    emoji="🧗", sounds=["ocean-waves.mp3"],
    highlights=[("The Bluff", None),
                ("MV Captain Keith Tibbetts", None),
                ("Parrot Reserve", None),
                ("Great Cave", None)],
    blurb="The middle Cayman island, named for the Gaelic word for a bluff — "
          "a limestone ridge that rises steadily along its length to a 43 m "
          "cliff at the eastern end, which is a mountain by Caymanian "
          "standards.",
    fact="A Soviet-built Cuban frigate was deliberately sunk off the north "
          "shore in 1996 and is the only Russian warship divable in the "
          "western hemisphere. It sits in 25 m of water with its guns still "
          "trained.",
    tip="The bluff has bolted sport-climbing routes and caves you can walk "
        "into, and the trail along the top ends at a lighthouse with nothing "
        "below it but sea. Nobody else will be up there."),
# ====================== TURKS AND CAICOS =====================
"providenciales": dict(
    name="Providenciales", slug="Providenciales",
    country="Turks and Caicos Islands",
    region="Providenciales", type="island", tag="famous",
    emoji="🐚", sounds=["ocean-waves.mp3"],
    highlights=[("Grace Bay", None),
                ("Chalk Sound", None),
                ("Sapodilla Bay", None),
                ("Northwest Point", None),
                ("Bight Reef", None)],
    blurb="The most developed of the Turks and Caicos, and the reason most "
          "people come — Grace Bay runs for five kilometres of powder sand "
          "behind a barrier reef, with water so still it barely qualifies as "
          "sea.",
    fact="Chalk Sound, a lagoon on the island's south side, is a bright "
          "unbroken turquoise dotted with hundreds of tiny rock islets, and "
          "is cut off from the ocean — the colour comes from white marl on "
          "the bottom in very shallow water.",
    tip="Bight Reef is a protected snorkel trail 30 m off a public beach "
        "with mooring buoys marking the route. Free, and the best "
        "introduction to the reef on the island."),
"grand-turk": dict(
    name="Grand Turk", slug="Grand_Turk_Island",
    country="Turks and Caicos Islands",
    region="Grand Turk", type="island", tag="hidden",
    emoji="🐴", sounds=["ocean-waves.mp3"],
    search_name="Grand Turk Island Turks and Caicos",
    highlights=[("Cockburn Town", None),
                ("Grand Turk Lighthouse", None),
                ("The Wall", None),
                ("Salt salinas", None)],
    blurb="The capital island, eleven kilometres long and flat, with donkeys "
          "and horses wandering the streets of a Bermudian-style colonial "
          "town, salt pans left from the industry that built the place, and "
          "a 2,100 m drop-off 400 m from shore.",
    fact="John Glenn splashed down off Grand Turk in 1962 after the first "
          "American orbital flight and spent his first hours back on Earth "
          "on this island. There is a small memorial by the cruise pier.",
    tip="The wall is close enough that shore diving is genuinely practical — "
        "you swim out from the beach at Cockburn Town and it is right "
        "there. Humpbacks pass through the channel January to April."),
"middle-caicos": dict(
    name="Middle Caicos", slug="Middle_Caicos",
    country="Turks and Caicos Islands",
    region="Middle Caicos", type="island", tag="hidden",
    emoji="🕳️", sounds=["ocean-waves.mp3"],
    highlights=[("Mudjin Harbour", None),
                ("Conch Bar Caves", None),
                ("Bambarra Beach", None),
                ("Crossing Place Trail", None)],
    blurb="The largest island in the Turks and Caicos and one of the "
          "emptiest — about 200 people, a limestone coast of cliffs and "
          "blowholes, and the biggest cave system in the Bahamian "
          "archipelago running under it.",
    fact="The Crossing Place Trail along the north coast was cut by enslaved "
          "people and their descendants to walk between settlements, and "
          "parts of it are still the only way to reach some beaches. Taíno "
          "artefacts have been found in the Conch Bar Caves.",
    tip="Mudjin Harbour is the one sight nobody forgets — a beach at the "
        "foot of a cliff, reached through a staircase cut down inside the "
        "rock, with a sea arch offshore."),
"salt-cay-turks": dict(
    name="Salt Cay", slug="Salt_Cay,_Turks_Islands",
    country="Turks and Caicos Islands",
    region="Salt Cay", type="island", tag="hidden",
    emoji="🐋", sounds=["ocean-waves.mp3"],
    search_name="Salt Cay Turks and Caicos",
    highlights=[("Balfour Town", None),
                ("Salinas", None),
                ("Endymion wreck", None),
                ("North Beach", None)],
    blurb="Four square miles, about sixty residents, donkeys in the lanes "
          "and the whole island still laid out as the salt works it was for "
          "three centuries — windmills, sluice gates and evaporation pans "
          "left where the industry stopped.",
    fact="Salt raked here was shipped to Newfoundland and New England in "
          "such quantity that the Turks Islands became known as the "
          "Bermudian salt colony. The trade collapsed in the 1960s and the "
          "island has barely changed since.",
    tip="Humpbacks pass through the Turks Island Passage between January and "
        "April on the way to the Silver Bank, close enough to see from "
        "shore. The Endymion, a British warship sunk in 1790, lies in 12 m "
        "of water offshore."),
# ==================== TRINIDAD AND TOBAGO ====================
# `trinidad` is already taken by the Cuban town, so these records are named
# for the places themselves.
"port-of-spain": dict(
    name="Port of Spain", slug="Port_of_Spain",
    country="Trinidad and Tobago",
    region="Trinidad", type="city", tag="famous",
    emoji="🥁", sounds=["city-hum.mp3"],
    highlights=[("Queen's Park Savannah", None),
                ("Magnificent Seven", None),
                ("Fort George", None),
                ("Maracas Bay", None),
                ("Woodford Square", None)],
    blurb="The capital of Trinidad and Tobago, at the foot of the Northern "
          "Range on the Gulf of Paria — an oil-and-gas city, the least "
          "touristic capital in the Caribbean, and the birthplace of "
          "calypso, soca, the limbo and the steelpan.",
    fact="The steelpan is the only acoustic instrument invented in the 20th "
          "century, and it was made here in the 1930s out of discarded oil "
          "drums after the colonial government banned skin drums. It is "
          "now the national instrument.",
    tip="Go to a panyard in the weeks before Carnival, when the big steel "
        "orchestras rehearse outdoors most nights. It is free, it is not for "
        "tourists, and a hundred pans at full volume is something else."),
"tobago": dict(
    name="Tobago", slug="Tobago", country="Trinidad and Tobago",
    region="Tobago", type="island", tag="hidden",
    emoji="🐦", sounds=["ocean-waves.mp3"],
    highlights=[("Pigeon Point", None),
                ("Buccoo Reef", None),
                ("Main Ridge Forest Reserve", None),
                ("Englishman's Bay", None),
                ("Scarborough", None)],
    blurb="The smaller, greener, slower half of the country — 300 km² of "
          "rainforest ridge and bays, with reef on the Caribbean side, surf "
          "on the Atlantic side, and none of Trinidad's industry.",
    fact="The Main Ridge Forest Reserve, set aside in 1776 specifically to "
          "protect rainfall, is the oldest legally protected forest reserve "
          "in the western hemisphere — 250 years of continuous protection.",
    tip="Englishman's Bay on the north coast is a perfect empty crescent "
        "with one shack selling food and forest coming down to the sand. "
        "The road there is a spectacular drive in itself."),
"pitch-lake": dict(
    name="Pitch Lake", slug="Pitch_Lake", country="Trinidad and Tobago",
    region="Trinidad", type="nature", tag="hidden",
    emoji="🖤", sounds=["wilderness.mp3"],
    search_name="Pitch Lake La Brea Trinidad",
    highlights=[("La Brea", None),
                ("Museum", None),
                ("Sulphur pools", None)],
    blurb="The largest natural asphalt deposit in the world — 40 hectares of "
          "grey-black tar, 75 m deep at the centre, that you can walk out "
          "onto. It is solid enough to bear weight and slow enough that "
          "anything left on it sinks over months.",
    fact="Walter Raleigh caulked his ships with it in 1595. The lake "
          "regenerates from below as fast as it is dug out, and asphalt from "
          "here has surfaced roads in London, New York and Cairo.",
    tip="Go with a guide from the site office — the middle of the lake is "
        "the 'mother' and is genuinely soft. Prehistoric trees and animal "
        "bones surface in it periodically."),
"caroni-swamp": dict(
    name="Caroni Swamp", slug="Caroni_Swamp",
    country="Trinidad and Tobago",
    region="Trinidad", type="wilderness", tag="hidden",
    emoji="🦩", sounds=["wilderness.mp3"],
    search_name="Caroni Swamp Trinidad scarlet ibis",
    highlights=[("Scarlet ibis roost", None),
                ("Mangrove channels", None),
                ("Caroni Bird Sanctuary", None)],
    blurb="Five and a half thousand hectares of mangrove on Trinidad's west "
          "coast, and every evening the national bird comes home to it — "
          "scarlet ibis by the thousand, arriving in flights over the water "
          "and turning whole islands red.",
    fact="The scarlet ibis gets its colour from carotenoids in the crabs it "
          "eats; captive birds fade to pink without them. It shares the "
          "national coat of arms with Tobago's cocrico, and killing one is a "
          "serious offence.",
    tip="Boats leave around four in the afternoon and the birds come in as "
        "the light goes. Bring binoculars — the roost islands are kept at a "
        "distance deliberately."),
"maracas-bay": dict(
    name="Maracas Bay", slug="Maracas_Bay",
    country="Trinidad and Tobago",
    region="Trinidad", type="coastal", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    highlights=[("Bake and shark stalls", None),
                ("Las Cuevas", None),
                ("North Coast Road", None),
                ("Northern Range", None)],
    blurb="Trinidad's best-known beach, over the Northern Range from the "
          "capital on a mountain road with viewpoints all the way — a deep "
          "bay of brown-gold sand with forested headlands at each end and "
          "real Atlantic surf.",
    fact="Bake and shark — fried shark in fried bread, then loaded from a "
          "counter of a dozen sauces and salads yourself — was invented at "
          "the stalls on this beach and is the national street food.",
    tip="Richard's is the famous stall but the queue is long; the others are "
        "as good. Load it with shadon beni sauce, tamarind and pineapple, "
        "and eat it on the sand."),
# ========================== BARBADOS =========================
"bridgetown": dict(
    name="Bridgetown", slug="Bridgetown", country="Barbados",
    region="Saint Michael", type="city", tag="famous",
    emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Parliament Buildings", None),
                ("Garrison Savannah", None),
                ("Carlisle Bay", None),
                ("Nidhe Israel Synagogue", None),
                ("Chamberlain Bridge", None)],
    blurb="The capital of Barbados and one of the oldest towns in the "
          "Americas — Georgian streets around a careenage full of boats, a "
          "gothic-revival parliament, and a UNESCO listing for the "
          "historic centre and its garrison.",
    fact="The Nidhe Israel Synagogue here, founded in 1654 by Sephardic Jews "
          "fleeing Brazil, is among the oldest in the western hemisphere. "
          "Its mikvah was rediscovered under a car park in 2008.",
    tip="Oistins Fish Fry on a Friday night, twenty minutes down the coast, "
        "is the real weekly event on this island — grilled marlin and "
        "flying fish, plastic chairs, and everyone dancing by ten."),
"bathsheba": dict(
    name="Bathsheba", slug="Bathsheba,_Barbados", country="Barbados",
    region="Saint Joseph", type="coastal", tag="hidden",
    emoji="🌊", sounds=["ocean-waves.mp3"],
    highlights=[("Soup Bowl", None),
                ("Andromeda Botanic Gardens", None),
                ("Barclays Park", None),
                ("Bathsheba rock formations", None)],
    blurb="The wild Atlantic east coast, the opposite of everything the "
          "Barbados brochures show — a beach of enormous mushroom-shaped "
          "coral boulders left standing by the surf, and a village of "
          "chattel houses behind it.",
    fact="The Soup Bowl breaks here, one of the best right-hand waves in "
          "the Caribbean; Kelly Slater has called it a favourite. The name "
          "comes from the white foam churning across the reef flats.",
    tip="Do not swim — the currents on this coast kill people. There are "
        "natural rock pools at low tide that are safe and warm, which is "
        "what locals use."),
"harrisons-cave": dict(
    name="Harrison's Cave", slug="Harrison's_Cave", country="Barbados",
    region="Saint Thomas", type="nature", tag="hidden",
    emoji="💧", sounds=["waterfall.mp3"],
    search_name="Harrison's Cave Barbados",
    highlights=[("Great Hall", None),
                ("Underground waterfall", None),
                ("Welchman Hall Gully", None)],
    blurb="A crystallised limestone cavern in the middle of the island, with "
          "flowing streams, deep emerald pools and a 15-metre waterfall "
          "underground — toured on an electric tram that runs a mile into "
          "the rock.",
    fact="Barbados is a coral island pushed up out of the sea rather than a "
          "volcanic one, and rain has been dissolving passages through that "
          "coral limestone for hundreds of thousands of years. Most of the "
          "island's drinking water comes from the same aquifer.",
    tip="Welchman Hall Gully next door is a collapsed cave section that "
        "became a forested ravine, with wild green monkeys most afternoons."),
"animal-flower-cave": dict(
    name="Animal Flower Cave", slug="Animal_Flower_Cave",
    country="Barbados",
    region="Saint Lucy", type="coastal", tag="hidden",
    emoji="🕳️", sounds=["tidal-waves.mp3"],
    highlights=[("North Point", None),
                ("Sea anemone pools", None),
                ("Coral floor", None)],
    blurb="A sea cave at the northernmost tip of Barbados, open to the "
          "Atlantic through a wide mouth, with rock pools on the floor and "
          "the ocean smashing into the cliffs directly below.",
    fact="It is named for the sea anemones in its pools, which open like "
          "flowers underwater. The cave floor is coral that formed between "
          "400,000 and 500,000 years ago, when this was seabed.",
    tip="It only opens when the sea state allows, so call ahead. Whales are "
        "sometimes visible from the cliff above between February and April."),
# ========================= SAINT LUCIA =======================
"castries": dict(
    name="Castries", slug="Castries", country="Saint Lucia",
    region="Castries", type="city", tag="famous",
    emoji="⛪", sounds=["city-hum.mp3"],
    highlights=[("Derek Walcott Square", None),
                ("Cathedral of the Immaculate Conception", None),
                ("Castries Market", None),
                ("Morne Fortune", None),
                ("Vigie Beach", None)],
    blurb="The capital of Saint Lucia, wrapped around a deep volcanic "
          "harbour with hills on three sides — a working port town with a "
          "Saturday market that fills several streets and a cathedral "
          "painted floor to ceiling by a local artist.",
    fact="Saint Lucia has produced two Nobel laureates — Arthur Lewis in "
          "economics and Derek Walcott in literature — from a population "
          "under 180,000. That is the highest number of Nobel prizes per "
          "head of any sovereign country on Earth.",
    tip="Go up Morne Fortune for the view over the harbour and the Pitons on "
        "a clear day. The old military buildings at the top are now a "
        "college."),
"soufriere-st-lucia": dict(
    name="Soufrière", slug="Soufrière,_Saint_Lucia",
    country="Saint Lucia",
    region="Soufrière", type="town", tag="famous",
    emoji="🌋", sounds=["ocean-waves.mp3"],
    search_name="Soufriere Saint Lucia town Pitons",
    highlights=[("Sulphur Springs", None),
                ("Diamond Falls", None),
                ("Anse Chastanet", None),
                ("Toraille Waterfall", None)],
    blurb="The old French capital, sitting in a bay directly beneath the "
          "Pitons, with a collapsed volcanic caldera behind it that you can "
          "drive into — steaming vents, grey mud baths and a smell of "
          "sulphur over the whole valley.",
    fact="Sulphur Springs is marketed as the world's only drive-in volcano, "
          "which is roughly true: the road runs into the crater of the "
          "Soufrière volcano, which last erupted around 1766.",
    tip="The hot mud baths downhill from the vents are open to anyone and "
        "cost a few dollars. Wear a swimsuit you do not care about — the "
        "iron and sulphur stain fabric permanently."),
"pitons": dict(
    name="The Pitons", slug="Pitons_(Saint_Lucia)", country="Saint Lucia",
    region="Soufrière", type="mountain", tag="famous",
    emoji="⛰️", sounds=["mountain-wind.mp3"],
    search_name="Pitons Saint Lucia Gros Piton",
    highlights=[("Gros Piton", None),
                ("Petit Piton", None),
                ("Sugar Beach", None),
                ("Pitons Management Area", None)],
    blurb="Two volcanic plugs rising almost vertically out of the sea on "
          "Saint Lucia's south-west coast — Gros Piton at 771 m and Petit "
          "Piton at 743 m — the most photographed thing in the Caribbean "
          "and the shape on the national beer.",
    fact="They are not classic volcanoes but lava domes: the cooled cores of "
          "old vents, left standing after the softer cone around them "
          "eroded away. The coral reef between them is protected as part of "
          "the same World Heritage site.",
    tip="Gros Piton is the one you can hike — two hours up with a compulsory "
        "guide from the Fond Gens Libre trailhead. Petit Piton is steeper, "
        "unmaintained and genuinely dangerous."),
"marigot-bay": dict(
    name="Marigot Bay", slug="Marigot_Bay", country="Saint Lucia",
    region="Castries", type="coastal", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    highlights=[("Hurricane hole", None),
                ("Ferry crossing", None),
                ("Palm spit", None)],
    blurb="A narrow inlet hidden behind a palm-covered sand spit, deep "
          "enough for yachts and invisible from the sea — which is exactly "
          "why the British navy used it to hide a fleet from the French.",
    fact="James Michener called it the most beautiful bay in the Caribbean. "
          "The 1967 Doctor Dolittle film was shot here, and the bay is a "
          "designated hurricane hole where boats ride out storms.",
    tip="A small ferry runs across the bay all day for a couple of dollars. "
        "The far side has the beach; the near side has the road."),
# =========================== GRENADA =========================
"st-georges-grenada": dict(
    name="St. George's", slug="St._George's,_Grenada", country="Grenada",
    region="Saint George", type="city", tag="famous",
    emoji="🌶️", sounds=["city-hum.mp3"],
    search_name="St George's Grenada capital",
    highlights=[("Carenage", None),
                ("Fort George", None),
                ("Grand Anse Beach", None),
                ("Underwater Sculpture Park", None),
                ("Market Square", None)],
    blurb="Widely called the prettiest capital in the Caribbean — red-tiled "
          "roofs stacked around a horseshoe harbour in a drowned volcanic "
          "crater, with an 18th-century French fort on the headland above.",
    fact="Grenada produces around a fifth of the world's nutmeg from an "
          "island 34 km long. The nutmeg is on the national flag, and the "
          "spice trade is why this is called the Isle of Spice.",
    tip="Molinere Bay just north has the world's first underwater sculpture "
        "park — dozens of concrete figures on the seabed at 5 m, now grown "
        "over with coral. Snorkel or glass-bottom boat from the Carenage."),
"mount-saint-catherine": dict(
    name="Mount Saint Catherine", slug="Mount_Saint_Catherine_(Grenada)",
    country="Grenada",
    region="Saint Andrew", type="mountain", tag="hidden",
    emoji="🐒", sounds=["wilderness.mp3"],
    search_name="Mount Saint Catherine Grenada rainforest",
    highlights=[("Grand Etang Lake", None),
                ("Seven Sisters Falls", None),
                ("Mona monkeys", None),
                ("Concord Falls", None)],
    blurb="Grenada's highest point at 840 m, the northern end of the "
          "volcanic spine that runs down the middle of the island — cloud "
          "forest, elfin woodland on the ridge, and crater lakes and "
          "waterfalls in the valleys below.",
    fact="Mona monkeys, brought from West Africa during the slave trade, "
          "live wild in these forests and come to the roadside near Grand "
          "Etang. The crater lake down the ridge has never been "
          "convincingly sounded, and locals will tell you it has no bottom.",
    tip="Seven Sisters Falls, a short muddy hike off the interior road, is a "
        "chain of falls with pools you can jump into. Go early — the "
        "afternoon cloud sits on this ridge nearly every day."),
"gouyave": dict(
    name="Gouyave", slug="Gouyave", country="Grenada",
    region="Saint John", type="town", tag="hidden",
    emoji="🐟", sounds=["ocean-waves.mp3"],
    search_name="Gouyave Grenada Fish Friday",
    highlights=[("Gouyave Nutmeg Processing Station", None),
                ("Fish Friday", None),
                ("Dougaldston Estate", None),
                ("Black sand beach", None)],
    blurb="A fishing town on Grenada's west coast, painted in every colour "
          "and stacked along one street between the mountains and a black "
          "sand shore — the island's nutmeg capital and the place it eats "
          "on a Friday night.",
    fact="The nutmeg station here still sorts and grades by hand exactly as "
          "it did a century ago: nuts are floated in water to find the good "
          "ones, then dried on wooden racks for months. The building has no "
          "machinery in it worth the name.",
    tip="Fish Friday closes two streets every week for grilled tuna, "
        "lambi and jack, cooked at stalls by townspeople rather than "
        "caterers. It starts around six and runs late."),
"carriacou": dict(
    name="Carriacou", slug="Carriacou", country="Grenada",
    region="Carriacou", type="island", tag="hidden",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    highlights=[("Hillsborough", None),
                ("Sandy Island", None),
                ("Anse La Roche", None),
                ("Windward", None)],
    blurb="Thirty kilometres north of Grenada, thirteen square miles of dry "
          "hills and empty beaches, reached by a ferry that takes ninety "
          "minutes and is used mostly by people who live there.",
    fact="The village of Windward still builds wooden sloops by eye on the "
          "beach, without plans, using a Scottish shipbuilding tradition "
          "brought over in the 19th century. The launches are island-wide "
          "events.",
    tip="Sandy Island is a sandbar with a few palms in the middle of a "
        "marine park, ten minutes out by water taxi from Hillsborough. "
        "Take everything you need — there is nothing on it."),
# ============ SAINT VINCENT AND THE GRENADINES ===============
"kingstown": dict(
    name="Kingstown", slug="Kingstown",
    country="Saint Vincent and the Grenadines",
    region="Saint George", type="city", tag="hidden",
    emoji="🌿", sounds=["city-hum.mp3"],
    search_name="Kingstown Saint Vincent capital",
    highlights=[("Botanical Gardens", None),
                ("Fort Charlotte", None),
                ("La Soufrière", None),
                ("Arches of Kingstown", None)],
    blurb="A working capital of stone arcades and covered pavements built "
          "for rain, under green mountains on the leeward coast of Saint "
          "Vincent — a yachting hub for the Grenadines, and almost nobody's "
          "beach holiday.",
    fact="The Botanical Gardens here, founded in 1765, are the oldest in the "
          "western hemisphere, and hold a breadfruit tree grown from the "
          "seedlings Captain Bligh finally delivered in 1793 after the "
          "Bounty mutiny stopped his first attempt.",
    tip="Fort Charlotte's guns point inland, not out to sea — they were "
        "aimed at the Black Caribs, who the British considered the greater "
        "threat. The view over the harbour from up there is the best in "
        "town."),
"bequia": dict(
    name="Bequia", slug="Bequia",
    country="Saint Vincent and the Grenadines",
    region="Grenadines", type="island", tag="hidden",
    emoji="⚓", sounds=["ocean-waves.mp3"],
    highlights=[("Port Elizabeth", None),
                ("Princess Margaret Beach", None),
                ("Admiralty Bay", None),
                ("Moonhole", None)],
    blurb="Eighteen square kilometres an hour's ferry south of Saint "
          "Vincent, and the most loved anchorage in the eastern Caribbean — "
          "a working boatbuilding island where the harbour front is a "
          "footpath and everybody arrives by sea.",
    fact="Bequia holds one of the few remaining aboriginal whaling licences "
          "in the world, permitting up to four humpbacks a year taken by "
          "hand-thrown harpoon from open sailing boats. Most years they "
          "catch none.",
    tip="Walk the Belmont Walkway from Port Elizabeth around the rocks to "
        "Princess Margaret Beach at dusk, when the anchored yachts turn "
        "their lights on."),
"tobago-cays": dict(
    name="Tobago Cays", slug="Tobago_Cays",
    country="Saint Vincent and the Grenadines",
    region="Grenadines", type="island", tag="hidden",
    emoji="🐢", sounds=["ocean-waves.mp3"],
    highlights=[("Horseshoe Reef", None),
                ("Baradal turtle sanctuary", None),
                ("Petit Tabac", None),
                ("Mayreau", None)],
    blurb="Five uninhabited islands inside a horseshoe reef, with nothing on "
          "them but sand, scrub and iguanas — boats anchor in water that is "
          "flat because the reef takes the Atlantic a kilometre out, and "
          "you swim with turtles off the beach.",
    fact="Petit Tabac, the smallest of them, is the island Jack Sparrow and "
          "Elizabeth Swann are marooned on in the first Pirates of the "
          "Caribbean film. The rum-burning scene was shot on its beach.",
    tip="The turtle sanctuary off Baradal is roped and patrolled — swim, do "
        "not touch, do not chase. Boat boys sell lobster grilled on the "
        "beach in the evening, which is the whole point of coming."),
"mustique": dict(
    name="Mustique", slug="Mustique",
    country="Saint Vincent and the Grenadines",
    region="Grenadines", type="island", tag="hidden",
    emoji="🌴", sounds=["ocean-waves.mp3"],
    highlights=[("Macaroni Beach", None),
                ("Basil's Bar", None),
                ("Britannia Bay", None),
                ("Lagoon Bay", None)],
    blurb="A privately owned island of about 1,400 hectares run by a company "
          "the homeowners collectively own — a hundred villas, no hotels to "
          "speak of, no cars beyond mules and buggies, and a strict cap on "
          "how much gets built.",
    fact="Colin Tennant bought the island for £45,000 in 1958 and gave "
          "Princess Margaret a plot as a wedding present, which is how it "
          "became the discreet celebrity island it still is.",
    tip="Day visitors can arrive by boat and use Macaroni Beach and Basil's "
        "Bar, a wooden bar on stilts over the water that has been the "
        "island's social centre since 1976."),
# ==================== ANTIGUA AND BARBUDA ====================
"st-johns-antigua": dict(
    name="St. John's", slug="St._John's,_Antigua_and_Barbuda",
    country="Antigua and Barbuda",
    region="Saint John", type="city", tag="famous",
    emoji="🏏", sounds=["city-hum.mp3"],
    search_name="St John's Antigua capital",
    highlights=[("St. John's Cathedral", None),
                ("Redcliffe Quay", None),
                ("Sir Vivian Richards Stadium", None),
                ("Fort James", None),
                ("Dickenson Bay", None)],
    blurb="The capital of Antigua and Barbuda, a low town of wooden "
          "shopfronts and a white baroque cathedral with twin towers, on a "
          "harbour that takes cruise ships almost daily.",
    fact="Antigua claims 365 beaches, one for every day of the year. The "
          "count is generous but the island genuinely is ringed with them, "
          "because the coastline is deeply indented by drowned valleys.",
    tip="Redcliffe Quay is restored 18th-century warehousing that once held "
        "enslaved people before auction — the plaques say so plainly, which "
        "is more than most of the Caribbean's prettified waterfronts do."),
"english-harbour": dict(
    name="English Harbour", slug="English_Harbour",
    country="Antigua and Barbuda",
    region="Saint Paul", type="history", tag="famous",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    highlights=[("Nelson's Dockyard", None),
                ("Shirley Heights", None),
                ("Fort Berkeley", None),
                ("Galleon Beach", None)],
    blurb="A Georgian naval dockyard still in use as a working marina — the "
          "only one of its kind left anywhere — in a hurricane-proof "
          "harbour on Antigua's south coast, with the sail lofts, capstans "
          "and officers' quarters all still standing.",
    fact="Horatio Nelson was based here from 1784 to 1787 as a young captain "
          "and hated the place, calling it a vile hole. It is now a UNESCO "
          "World Heritage site named after him.",
    tip="Shirley Heights on a Sunday evening: steel band, then reggae, over "
        "the best view in Antigua as the sun goes down behind Montserrat "
        "and the harbour lights come on below."),
"barbuda": dict(
    name="Barbuda", slug="Barbuda", country="Antigua and Barbuda",
    region="Barbuda", type="island", tag="hidden",
    emoji="🕊️", sounds=["ocean-waves.mp3"],
    highlights=[("Codrington Lagoon", None),
                ("Frigate bird sanctuary", None),
                ("Pink Sand Beach", None),
                ("Darby Cave", None)],
    blurb="A flat coral island 40 km north of Antigua with about 1,500 "
          "people on it, seventeen miles of empty beach, and a lagoon "
          "holding one of the largest frigate bird colonies on Earth.",
    fact="Land on Barbuda is communally owned by the Barbudan people rather "
          "than held in individual title — a system dating from "
          "emancipation, and the subject of a long legal fight since "
          "Hurricane Irma flattened the island in 2017.",
    tip="The frigate bird sanctuary is reached only by boat across the "
        "lagoon; in breeding season the males inflate scarlet throat "
        "pouches the size of footballs and the noise carries a long way."),
# ========================== DOMINICA =========================
"roseau": dict(
    name="Roseau", slug="Roseau", country="Dominica",
    region="Saint George", type="city", tag="hidden",
    emoji="🍋", sounds=["city-hum.mp3"],
    search_name="Roseau Dominica capital",
    highlights=[("Old Market", None),
                ("Botanical Gardens", None),
                ("Trafalgar Falls", None),
                ("Morne Bruce", None)],
    blurb="The small capital of the Nature Island — French colonial "
          "cottages with jalousie shutters and overhanging balconies "
          "crammed into a grid between the mountains and the sea, with "
          "rainforest starting about ten minutes uphill.",
    fact="A school bus crushed under a baobab tree, flattened by Hurricane "
          "David in 1979, has been left exactly where it fell in the "
          "Botanical Gardens as a memorial. The tree regrew around it.",
    tip="Trafalgar Falls is twenty minutes inland: two waterfalls side by "
        "side, one hot and one cold, with a scramble over boulders down to "
        "pools where the two waters mix."),
"boiling-lake": dict(
    name="Boiling Lake", slug="Boiling_Lake", country="Dominica",
    region="Saint Patrick", type="nature", tag="hidden",
    emoji="♨️", sounds=["waterfall.mp3"],
    search_name="Boiling Lake Dominica hike",
    highlights=[("Valley of Desolation", None),
                ("Titou Gorge", None),
                ("Morne Trois Pitons National Park", None)],
    blurb="A flooded fumarole 60 m across in the mountains of Dominica, "
          "grey-blue and permanently steaming, with the centre at a rolling "
          "boil — the second largest hot lake in the world, and reachable "
          "only on foot.",
    fact="The hike is six hours return through the Valley of Desolation, a "
          "sulphur-stained moonscape of vents and hot streams where the "
          "forest has been killed off entirely. The lake's level and "
          "temperature swing unpredictably.",
    tip="Take a guide, start at dawn, and expect to be wet the entire day. "
        "Titou Gorge at the trailhead — a slot canyon you swim up to a "
        "waterfall — is the traditional way to finish."),
"morne-trois-pitons": dict(
    name="Morne Trois Pitons", slug="Morne_Trois_Pitons_National_Park",
    country="Dominica",
    region="Saint George", type="wilderness", tag="hidden",
    emoji="🌋", sounds=["wilderness.mp3"],
    highlights=[("Emerald Pool", None),
                ("Freshwater Lake", None),
                ("Middleham Falls", None),
                ("Boeri Lake", None)],
    blurb="Seventy square kilometres of volcanic rainforest around a 1,342 m "
          "peak, with five volcanoes, crater lakes, fumaroles and "
          "waterfalls inside it — the first natural World Heritage site in "
          "the eastern Caribbean.",
    fact="Dominica has nine active volcanoes, more per square mile than "
          "anywhere on Earth, and the island is still growing. The Waitukubuli "
          "Trail crosses the whole park on the way from one end of the "
          "island to the other.",
    tip="Emerald Pool is a fifteen-minute walk from the road and gets the "
        "cruise crowds; Middleham Falls is an hour in and you will often "
        "have the 60 m drop to yourself."),
"portsmouth-dominica": dict(
    name="Portsmouth", slug="Portsmouth,_Dominica", country="Dominica",
    region="Saint John", type="town", tag="hidden",
    emoji="🚣", sounds=["ocean-waves.mp3"],
    search_name="Portsmouth Dominica Indian River",
    highlights=[("Indian River", None),
                ("Cabrits National Park", None),
                ("Fort Shirley", None),
                ("Prince Rupert Bay", None)],
    blurb="Dominica's second town, on a wide bay in the north, with a "
          "restored British garrison on the headland and a black-water "
          "river behind it that you row up under arching bloodwood roots.",
    fact="Fort Shirley on the Cabrits was the site of a 1802 mutiny by the "
          "8th West India Regiment that led directly to Britain granting "
          "freedom to all enslaved soldiers in its army — an emancipation "
          "three decades before the general one.",
    tip="Indian River boats are rowed, not motored, by licensed guides only. "
        "Go in the early morning for the herons and the light through the "
        "roots."),
# =================== SAINT KITTS AND NEVIS ===================
"basseterre": dict(
    name="Basseterre", slug="Basseterre",
    country="Saint Kitts and Nevis",
    region="Saint George Basseterre", type="city", tag="hidden",
    emoji="🚂", sounds=["city-hum.mp3"],
    search_name="Basseterre Saint Kitts capital",
    highlights=[("The Circus", None),
                ("Independence Square", None),
                ("St. Kitts Scenic Railway", None),
                ("Port Zante", None)],
    blurb="The capital of the smallest sovereign state in the Americas — a "
          "Georgian grid around a green clock-tower circus modelled on "
          "Piccadilly, with the volcano behind it and cane fields, now "
          "abandoned, all around.",
    fact="The last sugar train in the Caribbean still runs here, on a narrow-"
          "gauge line built in 1912 to carry cane to the mill. The industry "
          "closed in 2005; the railway now carries passengers around the "
          "island's edge.",
    tip="Independence Square was the slave market. There is no plaque saying "
        "so on the square itself — the National Museum in the old treasury "
        "building at the port covers it properly."),
"brimstone-hill": dict(
    name="Brimstone Hill", slug="Brimstone_Hill_Fortress_National_Park",
    country="Saint Kitts and Nevis",
    region="Saint Thomas Middle Island", type="history", tag="hidden",
    emoji="🏰", sounds=["mountain-wind.mp3"],
    search_name="Brimstone Hill Fortress Saint Kitts",
    highlights=[("Fort George Citadel", None),
                ("Prince of Wales Bastion", None),
                ("Sandy Point Town", None)],
    blurb="A fortress on a volcanic outcrop 230 m above the sea, built over "
          "a century by enslaved Africans out of the black stone it stands "
          "on — the largest and best-preserved fortification in the eastern "
          "Caribbean.",
    fact="It was called the Gibraltar of the West Indies. In 1782 eight "
          "thousand French troops besieged a garrison of about a thousand "
          "for a month before it surrendered; the British got it back the "
          "next year by treaty.",
    tip="On a clear day you can see six islands from the citadel — Nevis, "
        "Montserrat, Saba, Sint Eustatius, Saint Barthélemy and Sint "
        "Maarten. Green vervet monkeys are all over the lower ramparts."),
"nevis": dict(
    name="Nevis", slug="Nevis", country="Saint Kitts and Nevis",
    region="Nevis", type="island", tag="hidden",
    emoji="☁️", sounds=["ocean-waves.mp3"],
    highlights=[("Nevis Peak", None),
                ("Charlestown", None),
                ("Pinney's Beach", None),
                ("Botanical Gardens of Nevis", None)],
    blurb="A near-perfect volcanic cone with a permanent cloud on the "
          "summit, three kilometres across a channel from Saint Kitts — "
          "green, quiet, and full of stone plantation great houses now run "
          "as small inns.",
    fact="Alexander Hamilton was born in Charlestown in 1755; the house is "
          "now the island's museum and the seat of the Nevis assembly. "
          "Nelson married a Nevisian widow, Fanny Nisbet, on the island in "
          "1787.",
    tip="Sunshine's on Pinney's Beach makes the Killer Bee, a rum punch with "
        "an enforced three-drink limit. The Nevis Peak climb is short, near-"
        "vertical, and involves pulling yourself up on tree roots."),
# =========================== ARUBA ===========================
"oranjestad-aruba": dict(
    name="Oranjestad", slug="Oranjestad,_Aruba", country="Aruba",
    region="Oranjestad", type="city", tag="famous",
    emoji="🏘️", sounds=["city-hum.mp3"],
    search_name="Oranjestad Aruba capital",
    highlights=[("Fort Zoutman", None),
                ("Wilhelminastraat", None),
                ("Renaissance Island", None),
                ("Linear Park", None)],
    blurb="Aruba's capital, a small Dutch Caribbean port of pastel gabled "
          "buildings in pistachio, mango and rose, with a tram running the "
          "main street and a cruise pier at the end of it.",
    fact="Aruba sits outside the hurricane belt and gets about 500 mm of "
          "rain a year, which is why the interior is cactus and divi-divi "
          "trees permanently bent north-west by the trade wind rather than "
          "rainforest.",
    tip="Papiamento is the everyday language here — a creole of Portuguese, "
        "Spanish, Dutch, English and African languages. 'Bon bini' is "
        "welcome, and using it goes down well."),
"arikok": dict(
    name="Arikok National Park", slug="Arikok_National_Park",
    country="Aruba",
    region="Santa Cruz", type="desert", tag="hidden",
    emoji="🌵", sounds=["desert-wind.mp3"],
    highlights=[("Conchi Natural Pool", None),
                ("Fontein Cave", None),
                ("Dos Playa", None),
                ("Jamanota", None)],
    blurb="Almost a fifth of Aruba, kept as raw desert — cactus, divi-divi, "
          "gold-mine ruins and volcanic boulder fields running down to a "
          "windward coast the Atlantic hammers all year.",
    fact="Fontein Cave has Arawak drawings on its ceiling in red-brown ochre, "
          "made by the island's Caquetío people. There are also names "
          "scratched by 19th-century visitors, which is its own record.",
    tip="Conchi, the natural pool, is a rock basin in the surf on the north "
        "coast — reachable only by 4x4, horse or a long hot walk. Do not "
        "take a rental sedan down that track."),
"eagle-beach": dict(
    name="Eagle Beach", slug="Eagle_Beach", country="Aruba",
    region="Oranjestad", type="coastal", tag="famous",
    emoji="🌴", sounds=["ocean-waves.mp3"],
    search_name="Eagle Beach Aruba",
    highlights=[("Fofoti trees", None),
                ("Palm Beach", None),
                ("Turtle nesting sites", None)],
    blurb="A wide white strip on Aruba's leeward side, consistently rated "
          "among the best beaches in the world, and known everywhere by two "
          "wind-bent fofoti trees standing alone on the sand.",
    fact="Those two trees are the most photographed objects in Aruba and are "
          "usually mislabelled as divi-divi. They lean north-west because "
          "the trade wind here blows from the same direction all year, "
          "every year.",
    tip="Four species of sea turtle nest on this beach between March and "
        "September; roped-off nests are marked and lit-up beachfront is "
        "kept dark for them. Do not walk inside the tape."),
# ========================== CURAÇAO ==========================
"willemstad": dict(
    name="Willemstad", slug="Willemstad", country="Curaçao",
    region="Willemstad", type="city", tag="famous",
    emoji="🎨", sounds=["city-hum.mp3"],
    search_name="Willemstad Curacao Handelskade",
    highlights=[("Handelskade", None),
                ("Queen Emma Bridge", None),
                ("Punda", None),
                ("Otrobanda", None),
                ("Mikvé Israel-Emanuel Synagogue", None)],
    blurb="A row of Dutch gabled merchant houses in sherbet colours along a "
          "harbour channel, split into Punda and Otrobanda by a floating "
          "pontoon bridge that swings open for every ship — a UNESCO site "
          "and the most photogenic waterfront in the Caribbean.",
    fact="The buildings are painted because a 19th-century governor blamed "
          "his migraines on the glare off whitewash and banned white — then "
          "turned out to own the island's paint business.",
    tip="The Queen Emma Bridge swings aside dozens of times a day. When it "
        "does, free ferries run instead, and standing on the deck as a "
        "tanker slides through the channel is worth timing."),
"christoffel-park": dict(
    name="Christoffel Park", slug="Christoffelpark",
    country="Curaçao",
    region="Bandabou", type="nature", tag="hidden",
    emoji="🦌", sounds=["desert-wind.mp3"],
    search_name="Christoffel National Park Curacao",
    highlights=[("Mount Christoffel", "Christoffelberg"),
                ("Savonet Museum", None),
                ("Boka Grandi", None),
                ("Curaçao white-tailed deer", None)],
    blurb="Twenty-three square kilometres of thorn scrub and limestone at "
          "the wild west end of Curaçao, built on three old plantations, "
          "with the island's highest hill in the middle of it.",
    fact="A subspecies of white-tailed deer survives here and nowhere else — "
          "probably brought by Amerindians from the mainland thousands of "
          "years ago, and now down to a few hundred animals.",
    tip="The Christoffel summit climb is only 372 m but it is bare rock in "
        "full sun; the park makes you start before ten in the morning, and "
        "they are right to."),
"westpunt": dict(
    name="Westpunt", slug="Westpunt", country="Curaçao",
    region="Bandabou", type="coastal", tag="hidden",
    emoji="💥", sounds=["tidal-waves.mp3"],
    search_name="Westpunt Curacao Grote Knip",
    highlights=[("Grote Knip", None),
                ("Playa Forti", None),
                ("Shete Boka", None),
                ("Boka Pistol", None),
                ("Watamula", None)],
    blurb="The village at Curaçao's far north-western tip, and the base for "
          "the wild end of the island — turquoise coves cut into limestone "
          "on the sheltered side, and on the other, seven inlets where the "
          "Atlantic detonates against undercut cliffs.",
    fact="Boka Pistol along the north coast is named for the sound: water "
          "forced through a narrow channel comes out as a crack you hear "
          "before you see it. The rock arches there are actively "
          "collapsing.",
    tip="Grote Knip is the famous cove and gets busy by ten; Kleine Knip "
        "next door rarely does. At Playa Forti people jump from the "
        "eleven-metre cliff, which locals do and visitors should think "
        "about twice."),
# ========================== BONAIRE ==========================
"kralendijk": dict(
    name="Kralendijk", slug="Kralendijk", country="Bonaire",
    region="Bonaire", type="town", tag="hidden",
    emoji="🤿", sounds=["ocean-waves.mp3"],
    search_name="Kralendijk Bonaire",
    highlights=[("Fort Oranje", None),
                ("Bonaire National Marine Park", None),
                ("Salt pans", None),
                ("Flamingo sanctuary", None)],
    blurb="A one-street capital of ochre and mint buildings facing the "
          "island of Klein Bonaire, and the base for what is probably the "
          "best shore diving on Earth — the entire leeward coast is a "
          "marine park you can walk into.",
    fact="Bonaire protected all its surrounding waters to a depth of 60 m in "
          "1979, one of the first places anywhere to do so, and anchoring is "
          "banned island-wide. Yellow-painted rocks on the coast road number "
          "the dive sites.",
    tip="Rent a pickup, load tanks in the back, and drive the coast road "
        "stopping wherever you like. That is genuinely how diving works "
        "here."),
"washington-slagbaai": dict(
    name="Washington Slagbaai", slug="Washington_Slagbaai_National_Park",
    country="Bonaire",
    region="Bonaire", type="desert", tag="hidden",
    emoji="🦜", sounds=["desert-wind.mp3"],
    search_name="Washington Slagbaai National Park Bonaire",
    highlights=[("Brandaris", None),
                ("Wayaka", None),
                ("Boka Slagbaai", None),
                ("Salina Matijs", None)],
    blurb="Two former plantations at the north end of Bonaire, now 5,600 "
          "hectares of cactus desert, salt flats and volcanic hills, with a "
          "one-way dirt loop that takes half a day to drive.",
    fact="It was the first nature sanctuary in the Netherlands Antilles, "
          "created in 1969 when the owner sold the land to the government on "
          "condition it never be developed. Yellow-shouldered amazon "
          "parrots, down to a few hundred birds, nest in the cliffs.",
    tip="Take water and a spare tyre; there is no fuel, no shade and patchy "
        "phone signal inside. Wayaka and Boka Slagbaai both have shore "
        "entries with reef straight off the beach."),
"klein-bonaire": dict(
    name="Klein Bonaire", slug="Klein_Bonaire", country="Bonaire",
    region="Bonaire", type="island", tag="hidden",
    emoji="🐠", sounds=["ocean-waves.mp3"],
    highlights=[("No Name Beach", None),
                ("Ebo's Reef", None),
                ("Turtle nesting beaches", None)],
    blurb="A flat uninhabited islet of six square kilometres half a mile off "
          "Kralendijk, ringed by reef, with one beach, no buildings, no "
          "shade and no water — a ten-minute water taxi and then nothing "
          "but coral.",
    fact="The island was bought by the Bonairean government and conservation "
          "groups in 1999 specifically to stop a resort being built on it, "
          "after decades in private hands. It is now part of the marine "
          "park.",
    tip="Boats run on a schedule from the pier by Karel's Bar and the last "
        "one back is early. Bring everything, take everything away — "
        "nothing is sold on the island."),
# ==================== BRITISH VIRGIN ISLANDS =================
"road-town": dict(
    name="Road Town", slug="Road_Town", country="British Virgin Islands",
    region="Tortola", type="town", tag="hidden",
    emoji="⛵", sounds=["city-hum.mp3"],
    search_name="Road Town Tortola British Virgin Islands",
    highlights=[("Main Street", None),
                ("J.R. O'Neal Botanic Gardens", None),
                ("Sage Mountain", None),
                ("Cane Garden Bay", None)],
    blurb="The capital on Tortola, wrapped around a harbour full of charter "
          "yachts — the busiest bareboat sailing base in the world, and the "
          "starting point for almost everyone who cruises these islands.",
    fact="The Virgin Islands are the drowned tops of a single mountain range "
          "on one shallow bank, which is why the water between them is "
          "sheltered and line-of-sight — you can sail from anchorage to "
          "anchorage all week without ever losing sight of land.",
    tip="Sage Mountain, 521 m, holds the last patch of the primeval forest "
        "that once covered these islands, planted back up by Laurance "
        "Rockefeller in 1964. Cool, wet and completely unlike the coast."),
"the-baths": dict(
    name="The Baths", slug="The_Baths", country="British Virgin Islands",
    region="Virgin Gorda", type="coastal", tag="famous",
    emoji="🪨", sounds=["ocean-waves.mp3"],
    search_name="The Baths Virgin Gorda BVI",
    highlights=[("Devil's Bay", None),
                ("Spring Bay", None),
                ("The Caves", None),
                ("Virgin Gorda Peak", None)],
    blurb="House-sized granite boulders piled on a beach at the south end of "
          "Virgin Gorda, forming grottoes and tidal pools you scramble, "
          "wade and squeeze through on a marked route to the next bay.",
    fact="The granite is the giveaway that these islands are not coral — it "
          "is 40-million-year-old plutonic rock, cooled underground and "
          "then exposed and rounded, and geologically it does not belong "
          "anywhere else in the eastern Caribbean.",
    tip="Get there before the day-charter boats, around eight. The trail "
        "from the car park to Devil's Bay takes twenty minutes and involves "
        "ladders, ropes and being knee-deep in seawater."),
"jost-van-dyke": dict(
    name="Jost Van Dyke", slug="Jost_Van_Dyke",
    country="British Virgin Islands",
    region="Jost Van Dyke", type="island", tag="hidden",
    emoji="🍹", sounds=["ocean-waves.mp3"],
    highlights=[("White Bay", None),
                ("Great Harbour", None),
                ("Bubbly Pool", None),
                ("Sandy Spit", None)],
    blurb="Eight square kilometres and about 300 residents, and yet one of "
          "the best-known anchorages in the Caribbean — sailors come for "
          "White Bay, a curve of sand behind a reef with bars built out "
          "onto it.",
    fact="The Soggy Dollar Bar got its name because there is no dock: you "
          "swim ashore from your boat and pay with wet money. The Painkiller "
          "cocktail was invented there in the 1970s.",
    tip="The Bubbly Pool on the north-east coast is a rock basin the Atlantic "
        "surges into through a gap, turning it into a jacuzzi. It only works "
        "with swell — flat days give you a warm puddle."),
"anegada": dict(
    name="Anegada", slug="Anegada", country="British Virgin Islands",
    region="Anegada", type="island", tag="hidden",
    emoji="🦞", sounds=["ocean-waves.mp3"],
    highlights=[("Horseshoe Reef", None),
                ("Loblolly Bay", None),
                ("Cow Wreck Beach", None),
                ("Flamingo pond", None)],
    blurb="The odd one out — a flat coral and limestone island whose highest "
          "point is 8 m, invisible until you are almost on it, ringed by "
          "the third-largest barrier reef in the world and hundreds of "
          "wrecks.",
    fact="Its name is Spanish for 'the drowned land'. Over 300 ships have "
          "gone onto Horseshoe Reef, and charter companies traditionally "
          "forbid their boats from sailing here without a guide.",
    tip="Anegada lobster, grilled in a split oil drum on the beach, is the "
        "reason most people come. Order it in the morning for the evening — "
        "the restaurants catch to order."),
# ================= UNITED STATES VIRGIN ISLANDS ==============
"charlotte-amalie": dict(
    name="Charlotte Amalie", slug="Charlotte_Amalie,_U.S._Virgin_Islands",
    country="United States Virgin Islands",
    region="Saint Thomas", type="city", tag="famous",
    emoji="🏴‍☠️", sounds=["city-hum.mp3"],
    search_name="Charlotte Amalie St Thomas USVI",
    highlights=[("Blackbeard's Castle", None),
                ("Fort Christian", None),
                ("99 Steps", None),
                ("Magens Bay", None),
                ("Emancipation Garden", None)],
    blurb="A Danish colonial capital stacked up three steep hills around a "
          "deep harbour, with stepped alleys, warehouse arcades on the "
          "waterfront, and up to five cruise ships a day.",
    fact="The stone step-streets were built by the Danes using ballast brick "
          "from ships arriving empty to load sugar. The famous flight of 99 "
          "steps actually has 103.",
    tip="Magens Bay on the north side is a mile-long horseshoe usually "
        "listed among the world's best beaches. Skedaddle up to Drake's "
        "Seat on the ridge first for the view down onto it."),
"st-john-usvi": dict(
    name="St. John", slug="Saint_John,_U.S._Virgin_Islands",
    country="United States Virgin Islands",
    region="Saint John", type="island", tag="famous",
    emoji="🐢", sounds=["ocean-waves.mp3"],
    search_name="St John US Virgin Islands national park",
    highlights=[("Trunk Bay", None),
                ("Virgin Islands National Park", None),
                ("Cinnamon Bay", None),
                ("Annaberg Sugar Plantation", None),
                ("Cruz Bay", None)],
    blurb="Two thirds of this island is national park, given to the nation "
          "by Laurance Rockefeller in 1956 — which is why it looks like the "
          "Virgin Islands did before the resorts, all forest ridges running "
          "down to empty white bays.",
    fact="Trunk Bay has an underwater snorkelling trail with plaques bolted "
          "to the seabed naming the coral as you swim over it. The ruins of "
          "the Annaberg sugar works up the hill are kept unrestored on "
          "purpose.",
    tip="The ferry from Red Hook on St. Thomas takes twenty minutes and runs "
        "hourly. Reef Bay Trail drops through the forest past petroglyphs "
        "carved by the Taíno beside a freshwater pool."),
"st-croix": dict(
    name="St. Croix", slug="Saint_Croix,_U.S._Virgin_Islands",
    country="United States Virgin Islands",
    region="Saint Croix", type="island", tag="hidden",
    emoji="🥃", sounds=["ocean-waves.mp3"],
    search_name="St Croix US Virgin Islands Christiansted",
    highlights=[("Christiansted", None),
                ("Buck Island Reef", None),
                ("Frederiksted", None),
                ("Point Udall", None),
                ("Cruzan Rum Distillery", None)],
    blurb="The largest and flattest of the US Virgins, 65 km south of the "
          "others and much less visited — two Danish towns of yellow "
          "arcaded buildings, a rainforest on the west end, and cane "
          "country in between.",
    fact="Point Udall on the east end is the easternmost point of the United "
          "States, and the first place in the country to see the sunrise. "
          "Columbus landed on this island in 1493 and met armed resistance, "
          "the first recorded fight between Europeans and Native Americans.",
    tip="Buck Island Reef, a national monument off the north-east coast, has "
        "a marked snorkel trail through an elkhorn coral barrier. Day boats "
        "run from Christiansted."),
# ========================= MARTINIQUE ========================
"fort-de-france": dict(
    name="Fort-de-France", slug="Fort-de-France", country="Martinique",
    region="Martinique", type="city", tag="famous",
    emoji="🇫🇷", sounds=["city-hum.mp3"],
    highlights=[("Bibliothèque Schoelcher", None),
                ("Fort Saint-Louis", None),
                ("La Savane", None),
                ("Saint-Louis Cathedral", None),
                ("Grand Marché", None)],
    blurb="The capital of Martinique and the largest city in the French "
          "Antilles — an outpost of France with euros, boulangeries and "
          "gendarmes, on a bay under volcanic hills.",
    fact="The Schoelcher Library was built in Paris for the 1889 World's "
          "Fair, then taken apart, shipped across the Atlantic and "
          "reassembled here piece by piece. It is named for the man who "
          "drove French abolition through in 1848.",
    tip="Martinique makes rhum agricole from fresh cane juice rather than "
        "molasses, under an appellation d'origine contrôlée — the only one "
        "for rum anywhere. The distilleries north of the city all pour."),
"mount-pelee": dict(
    name="Mount Pelée", slug="Mount_Pelée", country="Martinique",
    region="Martinique", type="mountain", tag="hidden",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    search_name="Mount Pelee Martinique volcano",
    highlights=[("Aileron trail", None),
                ("Saint-Pierre", None),
                ("Grande Savane", None)],
    blurb="The volcano that destroyed a city — 1,397 m of stratovolcano at "
          "the north end of Martinique, usually in cloud, with trails up "
          "through elfin forest to a summit dome that is still growing.",
    fact="On 8 May 1902 a pyroclastic flow came off this mountain and killed "
          "around 30,000 people in Saint-Pierre in under a minute. Two men "
          "survived; one was in the town jail. The word 'pyroclastic flow' "
          "was coined to describe what happened here.",
    tip="Start from the Aileron car park early — the summit clears in the "
        "morning and closes in by eleven most days. Three hours return, and "
        "genuinely cold at the top."),
"saint-pierre-martinique": dict(
    name="Saint-Pierre", slug="Saint-Pierre,_Martinique",
    country="Martinique",
    region="Martinique", type="history", tag="hidden",
    emoji="🕯️", sounds=["ocean-waves.mp3"],
    search_name="Saint-Pierre Martinique 1902",
    highlights=[("Théâtre ruins", None),
                ("Cachot de Cyparis", None),
                ("Musée Frank A. Perret", None),
                ("Bay wrecks", None)],
    blurb="Once the Paris of the Caribbean, the richest and most cultured "
          "city in the Antilles, erased in ninety seconds in 1902 — now a "
          "small town living among its own ruins, with the theatre steps "
          "and jail cell left as they were.",
    fact="Twelve ships in the harbour were burnt and sunk by the same blast. "
          "They are still on the bottom of the bay at 30 to 60 m and are "
          "now the best wreck dives in the French Caribbean.",
    tip="Cyparis's cell — a thick stone cachot with one small vent — is a "
        "few minutes' walk from the theatre ruins and is the single most "
        "affecting thing on the island."),
# ========================= GUADELOUPE ========================
"pointe-a-pitre": dict(
    name="Pointe-à-Pitre", slug="Pointe-à-Pitre", country="Guadeloupe",
    region="Grande-Terre", type="city", tag="hidden",
    emoji="🏙️", sounds=["city-hum.mp3"],
    search_name="Pointe-a-Pitre Guadeloupe",
    highlights=[("Mémorial ACTe", None),
                ("Marché Saint-Antoine", None),
                ("Place de la Victoire", None),
                ("Musée Schoelcher", None)],
    blurb="Guadeloupe's commercial capital on the hinge between the "
          "archipelago's two wings, with a spice market, a big Creole "
          "waterfront and the most serious museum of slavery anywhere in "
          "the Caribbean.",
    fact="The Mémorial ACTe, opened in 2015 on the site of what was once one "
          "of the largest sugar factories in the region, is a national "
          "centre for the memory of the slave trade — silver filigree over "
          "black granite, meant to read as roots over a burial ground.",
    tip="Guadeloupe is shaped like a butterfly: flat limestone Grande-Terre "
        "for beaches, mountainous volcanic Basse-Terre for rainforest. The "
        "bridge between them is five minutes from the city."),
"basse-terre": dict(
    name="Basse-Terre", slug="Basse-Terre", country="Guadeloupe",
    region="Basse-Terre", type="town", tag="hidden",
    emoji="🌋", sounds=["wilderness.mp3"],
    search_name="Basse-Terre Guadeloupe town La Soufriere",
    highlights=[("La Grande Soufrière", None),
                ("Parc national de la Guadeloupe", None),
                ("Chutes du Carbet", None),
                ("Fort Louis Delgrès", None)],
    blurb="The administrative capital, a quiet colonial town of shuttered "
          "houses squeezed between an active volcano and the sea, at the "
          "foot of the rainforest that covers Guadeloupe's western wing.",
    fact="La Grande Soufrière behind the town is the highest point in the "
          "Lesser Antilles at 1,467 m. A 1976 eruption scare emptied the "
          "town and 70,000 people were evacuated for months; the eruption "
          "never came.",
    tip="The Chutes du Carbet are three waterfalls in the national park, the "
        "second of them a 110 m drop about twenty minutes' walk from the "
        "road. Columbus saw them from his ship in 1493."),
"les-saintes": dict(
    name="Les Saintes", slug="Îles_des_Saintes", country="Guadeloupe",
    region="Les Saintes", type="island", tag="hidden",
    emoji="⛵", sounds=["ocean-waves.mp3"],
    search_name="Les Saintes Guadeloupe Terre-de-Haut",
    highlights=[("Terre-de-Haut", None),
                ("Fort Napoléon", None),
                ("Pain de Sucre", None),
                ("Plage de Pompierre", None)],
    blurb="A cluster of small islands off southern Guadeloupe with one "
          "village of red-roofed white houses, a bay often called one of "
          "the loveliest in the world, and scooters as the only real "
          "traffic.",
    fact="The islands were too dry for sugar, so no plantation economy ever "
          "took hold and no large enslaved population was brought here. "
          "The population descends largely from Breton and Norman fishermen, "
          "and the local sailing boats still show it.",
    tip="Ferries from Trois-Rivières take twenty minutes. Walk up to Fort "
        "Napoléon for the view down over the bay and the iguanas that have "
        "taken over its cactus garden."),
"marie-galante": dict(
    name="Marie-Galante", slug="Marie-Galante", country="Guadeloupe",
    region="Marie-Galante", type="island", tag="hidden",
    emoji="🐂", sounds=["ocean-waves.mp3"],
    highlights=[("Grand-Bourg", None),
                ("Anse Canot", None),
                ("Habitation Murat", None),
                ("Gueule Grand Gouffre", None)],
    blurb="A flat round limestone island an hour south of Guadeloupe, "
          "nicknamed the island of a hundred windmills for the stone sugar "
          "mills standing in its cane fields — still worked in places by "
          "ox cart.",
    fact="Marie-Galante distilleries bottle rum at 59% because the local "
          "market expects it; it is the strongest routinely sold rum in "
          "France. Around a hundred old mill towers survive across the "
          "island.",
    tip="Rent something with wheels at Grand-Bourg and just drive the ring "
        "road. Anse Canot and Anse de Vieux-Fort on the north-west coast "
        "are usually empty."),
# ====================== SAINT BARTHÉLEMY =====================
"gustavia": dict(
    name="Gustavia", slug="Gustavia,_Saint_Barthélemy",
    country="Saint Barthélemy",
    region="Saint Barthélemy", type="town", tag="hidden",
    emoji="🛥️", sounds=["ocean-waves.mp3"],
    search_name="Gustavia Saint Barthelemy St Barts",
    highlights=[("Shell Beach", None),
                ("Fort Karl", None),
                ("Gustavia Lighthouse", None),
                ("Saint-Jean Bay", None)],
    blurb="The harbour town of St Barts, red-roofed and steep-sided, filled "
          "in winter with superyachts moored stern-to along a quay of Hermès "
          "and Cartier — and still, underneath, a small Swedish-founded "
          "port.",
    fact="Sweden owned this island from 1784 to 1878, which is why the "
          "capital is named for King Gustav III and why the streets have "
          "Swedish names. It is the only Swedish colony in the Caribbean "
          "there has ever been.",
    tip="Saint-Jean beach sits directly under the approach to the airport, "
        "where small planes drop over a hill and touch down metres from the "
        "sand. Shell Beach, a five-minute walk from the harbour, is made "
        "almost entirely of broken shells."),
# ======================== SAINT MARTIN =======================
"marigot": dict(
    name="Marigot", slug="Marigot,_Saint_Martin", country="Saint Martin",
    region="Saint Martin", type="town", tag="hidden",
    emoji="🥖", sounds=["ocean-waves.mp3"],
    search_name="Marigot Saint Martin French side",
    highlights=[("Fort Louis", None),
                ("Marina Royale", None),
                ("Grand Case", None),
                ("Pinel Island", None)],
    blurb="The capital of the French half of an island split between two "
          "countries since 1648 — a waterfront market of spices and pareos, "
          "a hill fort above it, and a border you cross without noticing.",
    fact="Saint Martin and Sint Maarten together form the smallest inhabited "
          "landmass on Earth divided between two sovereign states, at 87 "
          "km². There is no checkpoint; a roadside monument is the only "
          "marker.",
    tip="Grand Case up the coast is the eating town — a single street of "
        "restaurants plus the lolos, open-air barbecue shacks doing ribs and "
        "snapper for a fraction of the price."),
# ======================== SINT MAARTEN =======================
"philipsburg": dict(
    name="Philipsburg", slug="Philipsburg,_Sint_Maarten",
    country="Sint Maarten",
    region="Sint Maarten", type="town", tag="famous",
    emoji="✈️", sounds=["ocean-waves.mp3"],
    search_name="Philipsburg Sint Maarten",
    highlights=[("Front Street", None),
                ("Great Bay Beach", None),
                ("Maho Beach", None),
                ("Fort Amsterdam", None)],
    blurb="The Dutch-side capital, built on a sandbar between Great Bay and "
          "a salt pond — two long parallel streets of duty-free shops and a "
          "boardwalk, backed by one of the busiest cruise ports in the "
          "region.",
    fact="Maho Beach, at the other end of the island, sits directly under "
          "the threshold of Princess Juliana airport's runway. Widebody "
          "jets pass about twenty metres overhead; the jet blast on takeoff "
          "has thrown people across the road and killed one.",
    tip="Do not hold the fence at Maho. Fort Amsterdam above Great Bay, the "
        "first Dutch fort in the Caribbean, is a short walk with the best "
        "view over the harbour."),
# ========================== ANGUILLA =========================
"the-valley-anguilla": dict(
    name="The Valley", slug="The_Valley,_Anguilla", country="Anguilla",
    region="Anguilla", type="town", tag="hidden",
    emoji="🐐", sounds=["ocean-waves.mp3"],
    search_name="The Valley Anguilla capital",
    highlights=[("Wallblake House", None),
                ("Heritage Collection Museum", None),
                ("Sandy Ground", "Sandy_Ground,_Anguilla"),
                ("Crocus Bay", None)],
    blurb="A capital that is really a scatter of buildings at a crossroads, "
          "on a flat coral island of scrub, goats and thirty-odd beaches "
          "that regularly top the world lists.",
    fact="Anguilla staged a revolution in 1967 — against being governed by "
          "Saint Kitts, and in favour of remaining British. London "
          "eventually sent 300 paratroopers and 40 Metropolitan Police in "
          "1969; nobody was hurt, and Anguilla got its wish.",
    tip="Sandy Ground on a weekend night is where the island actually goes — "
        "Bankie Banx's Dune Preserve, a bar built out of driftwood and a "
        "wrecked boat on the beach at Rendezvous Bay, is the institution."),
"sandy-ground-anguilla": dict(
    name="Sandy Ground", slug="Sandy_Ground,_Anguilla", country="Anguilla",
    region="Anguilla", type="coastal", tag="hidden",
    emoji="🛶", sounds=["ocean-waves.mp3"],
    search_name="Sandy Ground Anguilla Road Bay",
    highlights=[("Road Bay", None),
                ("Sandy Island", None),
                ("Road Salt Pond", None),
                ("Anguilla boat racing", None)],
    blurb="Anguilla's harbour village, a single sandy strip between Road Bay "
          "and a salt pond, with the island's boats pulled up on the beach "
          "and its bars built directly on it — the closest thing this very "
          "quiet island has to a nightlife.",
    fact="Boat racing in locally built wooden sloops is Anguilla's national "
          "sport, not cricket. Crews shift ballast by hand while sailing, "
          "and the August Monday race out of Sandy Ground empties the "
          "island onto the beach.",
    tip="Sandy Island, a sandbar with a few palms and one bar on it, is a "
        "ten-minute boat ride from the pier here. Shoal Bay East on the "
        "north coast is the beach everyone photographs."),
# ========================= MONTSERRAT ========================
"plymouth-montserrat": dict(
    name="Plymouth", slug="Plymouth,_Montserrat", country="Montserrat",
    region="Montserrat", type="ruin", tag="hidden",
    emoji="🌫️", sounds=["wind.mp3"],
    search_name="Plymouth Montserrat buried capital",
    highlights=[("Exclusion Zone", None),
                ("Montserrat Volcano Observatory", None),
                ("Garibaldi Hill", None),
                ("Richmond Hill", None)],
    blurb="A capital city buried in volcanic ash and abandoned — the only "
          "ghost town that is still officially the seat of government of a "
          "living territory, sealed inside an exclusion zone since 1997.",
    fact="Montserrat is the only place on Earth with a de jure capital that "
          "nobody may enter. Two thirds of the island's population left for "
          "good and the government moved to Brades in the north; Plymouth "
          "remains the legal capital on paper.",
    tip="You cannot go in, but Garibaldi Hill and the observatory's terrace "
        "look straight down onto the buried streets. The observatory's "
        "briefing on what happened is excellent and honest."),
"soufriere-hills": dict(
    name="Soufrière Hills", slug="Soufrière_Hills", country="Montserrat",
    region="Montserrat", type="mountain", tag="hidden",
    emoji="🌋", sounds=["mountain-wind.mp3"],
    search_name="Soufriere Hills volcano Montserrat",
    highlights=[("Montserrat Volcano Observatory", None),
                ("Jack Boy Hill", None),
                ("Little Bay", None),
                ("Rendezvous Bay", None)],
    blurb="The volcano that took the southern half of Montserrat — dormant "
          "for centuries, awake since 1995, and still monitored around the "
          "clock from a ridge on the safe side of the island.",
    fact="Its lava dome has collapsed and rebuilt repeatedly; a 2010 "
          "collapse sent pyroclastic flows into the sea and added new land "
          "to the coast. Nineteen people who had gone back into the "
          "exclusion zone were killed in 1997.",
    tip="Jack Boy Hill on the east side looks over the buried old airport "
        "and has a telescope. Rendezvous Bay in the north is the island's "
        "only white-sand beach, reached on foot over a hill or by kayak — "
        "everything else here is volcanic black."),
}

FILL = {
    # the three Cuban records migrated in from latinamerica.json
    "havana":   dict(search_name="Havana Cuba"),
    "trinidad": dict(search_name="Trinidad Cuba Sancti Spiritus"),
    "varadero": dict(search_name="Varadero Cuba beach"),
}

if __name__ == "__main__":
    rb.run(REGION, NEW, FILL)
